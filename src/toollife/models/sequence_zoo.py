"""Sequence zoo: other network shapes that read a cutter's cycles and draw the same failure curve as the TCN.

Why: the TCN in history.py does well, but with 13 cutters we cannot tell which part earns it: reading
the past cycles, the hazard-curve head, or simply the inputs. Each model here swaps one piece and keeps
everything else exactly as in history.py: same per-cycle inputs, same first dense layer, same hazard
head (6 spline coefficients over log k) and "life used" gauge, same tool-balanced loss, same AdamW,
400 full-batch passes, gradient clip and dropout. So a difference in error comes from the shape alone.

Every trunk maps [tools, T, F] → [tools, T, 64] and is causal: the output at cycle t sees cycles ≤ t only.
  linear_hazard  no trunk at all: the 6 spline coefficients are a weighted sum of today's inputs
                 (a discrete-time logistic hazard model, the classic statistics model)
  mlp_now        two dense layers applied to each cycle on its own: today's inputs only, no history
  gru, lstm      recurrent: a learned running summary of the whole past, updated once per cycle
  transformer    2 layers of causal self-attention: each cycle can look directly at any earlier cycle
  tcn_direct     the stock TCN trunk with a plain regression head instead of the hazard curve

tcn_direct predicts log(1 + cycles left) with a Huber loss. Log rather than raw cycles because the
hazard head also reads time on a log scale, and because on raw cycles the early life of the three
longest-lived cutters (100–150 cycles left) would swamp the loss while the last 20% of life, where the
decisions are made, would barely count. The Huber loss is linear beyond ±0.25 (about ±28%), so it aims
at the median like rul_q50 does, and the median survives the log transform unchanged.
"""

import math

import numpy as np
import torch
from torch import nn

from toollife.models.hazard import K, spline_basis
from toollife.models.history import CausalBlock, Sequences, loss_fn

ARCHS = ("linear_hazard", "mlp_now", "gru", "lstm", "transformer", "tcn_direct")

# The one exception to the shared recipe. The linear hazard model is the classic statistics model, fitted
# to convergence as a statistician would. With lr 3e-3, Adam moves each weight by at most ~0.003 per pass,
# so in 400 passes its baseline risk (logit) cannot get from 0 to the −4 it needs: it stalls near −1.1,
# predicts ~2 cycles left everywhere, and its training loss is 6.2 against 2.7 when converged (checked
# 28 Oct on hidden cutters 9 and 2). Networks do not have this problem: many weights move the output at once.
RECIPE = {"linear_hazard": dict(lr=0.1, epochs=1500)}


def input_layer(n_features: int, hidden: int, dropout: float) -> nn.Sequential:
    """The same first layer as HistoryModel.inp: one dense layer per cycle."""
    return nn.Sequential(nn.Linear(n_features, hidden), nn.GELU(), nn.Dropout(dropout))


class NowMLP(nn.Module):
    """Two dense layers on each cycle by itself: no cycle ever sees another."""

    def __init__(self, n_features: int, hidden: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(input_layer(n_features, hidden, dropout),
                                 nn.Linear(hidden, hidden), nn.GELU(), nn.Dropout(dropout))

    def forward(self, x):
        return self.net(x)


class Recurrent(nn.Module):
    """GRU or LSTM running forward over the cycles; 2 layers, 64 numbers of memory each."""

    def __init__(self, n_features: int, hidden: int, dropout: float, cell: str = "gru", layers: int = 2):
        super().__init__()
        self.inp = input_layer(n_features, hidden, dropout)
        rnn = nn.GRU if cell == "gru" else nn.LSTM
        self.rnn = rnn(hidden, hidden, num_layers=layers, batch_first=True, dropout=dropout)
        self.drop = nn.Dropout(dropout)

    def forward(self, x):
        # Sequences are padded at the end, so padding is only ever read after the real cycles.
        h, _ = self.rnn(self.inp(x))
        return self.drop(h)


def position_signal(T: int, d: int) -> torch.Tensor:
    """Sine and cosine waves of the cycle index (as in the original transformer), so attention knows order.

    Fixed rather than learned: a hidden cutter can be longer than every training cutter (cutter 9).
    """
    pos = torch.arange(T, dtype=torch.float32).unsqueeze(1)
    freq = torch.exp(torch.arange(0, d, 2, dtype=torch.float32) * (-math.log(10000.0) / d))
    pe = torch.zeros(T, d)
    pe[:, 0::2], pe[:, 1::2] = torch.sin(pos * freq), torch.cos(pos * freq)
    return pe


class CausalTransformer(nn.Module):
    """2 layers, 4 heads, width 64; a causal mask stops any cycle from attending to later ones."""

    def __init__(self, n_features: int, hidden: int, dropout: float, layers: int = 2, heads: int = 4):
        super().__init__()
        self.hidden = hidden
        self.inp = input_layer(n_features, hidden, dropout)
        layer = nn.TransformerEncoderLayer(hidden, heads, dim_feedforward=4 * hidden, dropout=dropout,
                                           activation="gelu", batch_first=True, norm_first=True)
        self.enc = nn.TransformerEncoder(layer, layers, norm=nn.LayerNorm(hidden), enable_nested_tensor=False)

    def forward(self, x):
        T = x.shape[1]
        h = self.inp(x) + position_signal(T, self.hidden)
        mask = nn.Transformer.generate_square_subsequent_mask(T)  # −inf above the diagonal = no peeking ahead
        return self.enc(h, mask=mask, is_causal=True)


class TCNTrunk(nn.Module):
    """The stock trunk of HistoryModel: first dense layer, then 4 causal dilated blocks (gaps 1, 2, 4, 8)."""

    def __init__(self, n_features: int, hidden: int, dropout: float, dilations: tuple = (1, 2, 4, 8)):
        super().__init__()
        self.inp = input_layer(n_features, hidden, dropout)
        self.tcn = nn.Sequential(*[CausalBlock(hidden, d, dropout=dropout) for d in dilations])

    def forward(self, x):
        return self.tcn(self.inp(x).transpose(1, 2)).transpose(1, 2)


class ZooModel(nn.Module):
    """A trunk, then the same two heads as HistoryModel: failure curve (6 spline coefficients) and gauge.

    linear_hazard has no trunk and single-layer heads straight from the inputs. tcn_direct swaps the
    hazard head for one that outputs log(1 + cycles left).
    """

    def __init__(self, arch: str, n_features: int, hidden: int = 64, n_basis: int = 6, dropout: float = 0.2):
        super().__init__()
        self.arch = arch
        self.register_buffer("basis", torch.as_tensor(spline_basis(n_basis), dtype=torch.float32))
        if arch == "linear_hazard":
            self.trunk = nn.Identity()
            self.haz, self.gauge = nn.Linear(n_features, n_basis), nn.Linear(n_features, 1)
            return
        self.trunk = {
            "mlp_now": lambda: NowMLP(n_features, hidden, dropout),
            "gru": lambda: Recurrent(n_features, hidden, dropout, "gru"),
            "lstm": lambda: Recurrent(n_features, hidden, dropout, "lstm"),
            "transformer": lambda: CausalTransformer(n_features, hidden, dropout),
            "tcn_direct": lambda: TCNTrunk(n_features, hidden, dropout),
        }[arch]()
        n_out = 1 if arch == "tcn_direct" else n_basis
        self.haz = nn.Sequential(nn.Linear(hidden, hidden), nn.GELU(), nn.Linear(hidden, n_out))
        self.gauge = nn.Sequential(nn.Linear(hidden, hidden), nn.GELU(), nn.Linear(hidden, 1))

    def forward(self, x):
        h = self.trunk(x)  # [tools, T, hidden] (or the raw inputs for linear_hazard)
        out = self.haz(h)
        if self.arch == "tcn_direct":
            out = out.squeeze(-1)  # [tools, T] predicted log(1 + cycles left)
        else:
            out = out @ self.basis.T  # [tools, T, K] hazard logits
        return out, torch.sigmoid(self.gauge(h)).squeeze(-1)


def direct_loss(model: ZooModel, seq: Sequences, gauge_weight: float = 0.5, delta: float = 0.25):
    """Huber on log(1 + cycles left) plus the same gauge term, tool-balanced as in history.loss_fn."""
    pred, gauge = model(seq.x)
    # event_k is the true cycles left whenever the failure is inside the horizon K (always true here).
    assert bool(seq.observed[seq.mask.bool()].all()), "a cutter lives past the horizon; event_k is clipped"
    reg = nn.functional.huber_loss(pred, torch.log1p(seq.event_k.float()), reduction="none", delta=delta)
    huber = nn.functional.huber_loss(gauge, seq.life_frac, reduction="none", delta=0.1)
    per_tool = ((reg + gauge_weight * huber) * seq.mask).sum(1) / seq.mask.sum(1)
    return per_tool.mean()


def train(seq: Sequences, n_features: int, arch: str, seed: int, epochs: int = 400, lr: float = 3e-3,
          weight_decay: float = 1e-2) -> ZooModel:
    """history.train without early stopping (script 13 never uses it): fixed passes, full batch."""
    epochs, lr = RECIPE.get(arch, {}).get("epochs", epochs), RECIPE.get(arch, {}).get("lr", lr)
    torch.manual_seed(seed)
    model = ZooModel(arch, n_features)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    objective = direct_loss if arch == "tcn_direct" else loss_fn
    for _ in range(epochs):
        model.train()
        opt.zero_grad()
        loss = objective(model, seq)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    model.eval()
    return model


@torch.no_grad()
def predict_direct(models: list[ZooModel], seq: Sequences) -> np.ndarray:
    """tcn_direct ensemble: average the seeds' log(1 + cycles left), then turn it back into cycles.

    Each seed's answer is first held to 0 … K cycles, the same range the hazard head can express, so one
    input far outside the training range cannot send a seed (and the average) off to infinity; the hazard
    head saturates at 1 or K + 1 cycles instead.
    """
    log_rul = torch.stack([m(seq.x)[0].clamp(0, math.log1p(K)) for m in models]).mean(0)
    return torch.expm1(log_rul)[seq.mask.bool()].numpy()


def n_params(model: nn.Module) -> int:
    """Learned numbers in one model (the ensemble has 5 of them)."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
