"""History model: a TCN that reads one cutter's cycles in order and draws a failure curve after each one.

Per cycle the input is a vector of numbers (physics features, settings, age, and optionally the
autoencoder's fingerprint and health score). The TCN (temporal convolutional network) is four layers
of 1-D convolutions along the sequence of cycles. Each is causal (looks only at this cycle and earlier
ones, never later) and dilated (layer gaps 1, 2, 4, 8), so the last layer sees about 31 cycles back.
Two heads: the hazard curve over the next K cycles (6 spline coefficients) and a 0→1 "life used" gauge.

Training is tool-balanced: each cutter's cycles are averaged first, then cutters are averaged, so a
150-cycle cutter does not outweigh a 30-cycle one five to one.
"""

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

from toollife.models.hazard import K, hazard_nll, spline_basis


@dataclass
class Sequences:
    """Padded per-cutter sequences."""

    x: torch.Tensor  # [tools, T, F] inputs
    mask: torch.Tensor  # [tools, T] 1 where a real cycle exists
    event_k: torch.Tensor  # [tools, T] cycles from this one to failure (rul), ≥ 1
    observed: torch.Tensor  # [tools, T] 1 if the failure is inside the horizon
    life_frac: torch.Tensor  # [tools, T]
    tools: list


def make_sequences(df, feature_cols: list[str], tool_col="tool", order_col="age", rul_col="rul",
                   frac_col="life_frac", mean=None, std=None) -> tuple[Sequences, np.ndarray, np.ndarray]:
    """Rows with rul ≥ 1 only: after the breaking cycle there is no decision left to make."""
    df = df[df[rul_col] >= 1].sort_values([tool_col, order_col])
    x_all = df[feature_cols].to_numpy(np.float32)
    if mean is None:
        mean, std = np.nanmean(x_all, 0), np.nanstd(x_all, 0) + 1e-6
    tools = list(df[tool_col].unique())
    T = df.groupby(tool_col).size().max()
    n, f = len(tools), len(feature_cols)
    x = np.zeros((n, T, f), np.float32)
    mask = np.zeros((n, T), np.float32)
    ek = np.ones((n, T), np.int64)
    obs = np.zeros((n, T), np.float32)
    frac = np.zeros((n, T), np.float32)
    for i, t in enumerate(tools):
        g = df[df[tool_col] == t]
        L = len(g)
        xi = (g[feature_cols].to_numpy(np.float32) - mean) / std
        x[i, :L] = np.nan_to_num(xi)
        mask[i, :L] = 1
        r = g[rul_col].to_numpy()
        ek[i, :L] = np.minimum(r, K)
        obs[i, :L] = (r <= K).astype(np.float32)
        frac[i, :L] = g[frac_col].to_numpy(np.float32)
    seq = Sequences(*(torch.as_tensor(a) for a in (x, mask, ek, obs, frac)), tools=tools)
    return seq, mean, std


class CausalBlock(nn.Module):
    """Two causal dilated convolutions with a shortcut (residual) connection."""

    def __init__(self, channels: int, dilation: int, kernel: int = 3, dropout: float = 0.2):
        super().__init__()
        self.pad = (kernel - 1) * dilation  # pad only on the left, so no future cycle leaks in
        self.conv1 = nn.Conv1d(channels, channels, kernel, dilation=dilation)
        self.conv2 = nn.Conv1d(channels, channels, kernel, dilation=dilation)
        self.act, self.drop = nn.GELU(), nn.Dropout(dropout)

    def forward(self, x):  # x [tools, channels, T]
        h = self.drop(self.act(self.conv1(nn.functional.pad(x, (self.pad, 0)))))
        h = self.drop(self.act(self.conv2(nn.functional.pad(h, (self.pad, 0)))))
        return x + h


class HistoryModel(nn.Module):
    def __init__(self, n_features: int, hidden: int = 64, n_basis: int = 6, dropout: float = 0.2,
                 dilations: tuple = (1, 2, 4, 8)):
        super().__init__()
        self.inp = nn.Sequential(nn.Linear(n_features, hidden), nn.GELU(), nn.Dropout(dropout))
        self.tcn = nn.Sequential(*[CausalBlock(hidden, d, dropout=dropout) for d in dilations])
        self.haz = nn.Sequential(nn.Linear(hidden, hidden), nn.GELU(), nn.Linear(hidden, n_basis))
        self.gauge = nn.Sequential(nn.Linear(hidden, hidden), nn.GELU(), nn.Linear(hidden, 1))
        self.register_buffer("basis", torch.as_tensor(spline_basis(n_basis), dtype=torch.float32))

    def forward(self, x):
        h = self.tcn(self.inp(x).transpose(1, 2)).transpose(1, 2)  # [tools, T, hidden]
        coef = self.haz(h)  # [tools, T, n_basis]
        logits = coef @ self.basis.T  # [tools, T, K]
        return logits, torch.sigmoid(self.gauge(h)).squeeze(-1)


def loss_fn(model, seq: Sequences, gauge_weight: float = 0.5, smooth_weight: float = 1e-3):
    logits, gauge = model(seq.x)
    n, T, horizon = logits.shape
    nll = hazard_nll(logits.reshape(-1, horizon), seq.event_k.reshape(-1), seq.observed.reshape(-1)).reshape(n, T)
    huber = nn.functional.huber_loss(gauge, seq.life_frac, reduction="none", delta=0.1)
    per_tool = ((nll + gauge_weight * huber) * seq.mask).sum(1) / seq.mask.sum(1)
    smooth = (logits[..., 2:] - 2 * logits[..., 1:-1] + logits[..., :-2]).pow(2).mean()
    return per_tool.mean() + smooth_weight * smooth


def train(seq: Sequences, val: Sequences | None, n_features: int, seed: int, epochs: int = 400,
          lr: float = 3e-3, weight_decay: float = 1e-2, patience: int = 60, **kw) -> HistoryModel:
    torch.manual_seed(seed)
    model = HistoryModel(n_features, **kw)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    best, best_state, bad = np.inf, None, 0
    for _ in range(epochs):
        model.train()
        opt.zero_grad()
        loss = loss_fn(model, seq)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if val is not None:
            model.eval()
            with torch.no_grad():
                v = loss_fn(model, val).item()
            if v < best - 1e-4:
                best, best_state, bad = v, {k: t.clone() for k, t in model.state_dict().items()}, 0
            else:
                bad += 1
                if bad >= patience:
                    break
    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    return model


@torch.no_grad()
def predict(models: list[HistoryModel], seq: Sequences) -> tuple[np.ndarray, np.ndarray]:
    """Ensemble average in probability space; returns per-row hazard logits [rows, K] and gauge [rows]."""
    probs, gauges = [], []
    for m in models:
        lg, g = m(seq.x)
        probs.append(torch.sigmoid(lg))
        gauges.append(g)
    p = torch.stack(probs).mean(0).clamp(1e-6, 1 - 1e-6)
    keep = seq.mask.bool()
    logits = torch.log(p / (1 - p))[keep].numpy()
    return logits, torch.stack(gauges).mean(0)[keep].numpy()
