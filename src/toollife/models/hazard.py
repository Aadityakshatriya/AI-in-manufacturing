"""Failure curves: the discrete-time hazard used by every model in this project.

After a cutter has survived cut t, the model gives h(k) = the chance it fails at the k-th next cut,
given that it survived the cuts before that (k = 1 … K). Everything else follows from h:
  survival  S(k) = Π_{m ≤ k} (1 − h(m))
  P(fail within the next N cuts) = 1 − S(N)
  median remaining life = smallest k with S(k) ≤ 0.5
For a cutter that really failed at step κ, the log-likelihood is log h(κ) + Σ_{k<κ} log(1 − h(k));
a cutter still alive at the horizon (censored) contributes Σ_{k ≤ K} log(1 − h(k)).

The curve is smooth: logit h(k) is a combination of a few B-spline bumps over log k, so 13 failures
only have to fit about 6 numbers per prediction instead of K separate probabilities.
"""

import numpy as np
import torch
from scipy.interpolate import BSpline

K = 160  # longest look-ahead, in the dataset's own decision unit (cycles for Rzeszów)


def spline_basis(n_basis: int = 6, horizon: int = K, degree: int = 3) -> np.ndarray:
    """[horizon, n_basis] B-spline basis over log k, k = 1 … horizon."""
    x = np.log(np.arange(1, horizon + 1))
    inner = np.linspace(x[0], x[-1], n_basis - degree + 1)
    knots = np.r_[[x[0]] * degree, inner, [x[-1]] * degree]
    basis = np.stack([BSpline(knots, np.eye(n_basis)[i], degree, extrapolate=False)(x) for i in range(n_basis)], 1)
    return np.nan_to_num(basis)


def hazard_nll(logits: torch.Tensor, event_k: torch.Tensor, observed: torch.Tensor) -> torch.Tensor:
    """Negative log-likelihood per row.

    logits   [n, K]  hazard logits for k = 1 … K
    event_k  [n]     step of failure (1-based); for censored rows, the last step known alive
    observed [n]     1 if the failure was seen at event_k, 0 if censored
    """
    n, horizon = logits.shape
    k = torch.arange(1, horizon + 1, device=logits.device).expand(n, horizon)
    ek = event_k.clamp(1, horizon).unsqueeze(1)
    log_surv = torch.nn.functional.logsigmoid(-logits)  # log(1 − h)
    log_haz = torch.nn.functional.logsigmoid(logits)  # log h
    before = (k < ek).float()
    at = (k == ek).float() * observed.unsqueeze(1)
    censored_at = (k == ek).float() * (1 - observed.unsqueeze(1))
    ll = (log_surv * (before + censored_at)).sum(1) + (log_haz * at).sum(1)
    return -ll


def blur(h: np.ndarray, sigma: float) -> np.ndarray:
    """Widen failure curves: blur each predicted failure time in log-time by a Gaussian of width sigma.

    A model trained on 12 cutters is too sure of exactly when a cutter will fail. Blurring spreads
    each prediction over nearby cycles (proportionally: ±10% of the predicted time for sigma = 0.1),
    keeping the curve's centre roughly in place. sigma is chosen on cutters the model did not train on.
    """
    if sigma <= 0:
        return h
    n, horizon = h.shape
    s = np.cumprod(1.0 - h, axis=1)
    s_prev = np.concatenate([np.ones((n, 1)), s[:, :-1]], axis=1)
    pmf = np.concatenate([h * s_prev, s[:, -1:]], axis=1)  # [n, K+1]; last = still alive after K
    x = np.log(np.arange(1, horizon + 2))
    kernel = np.exp(-0.5 * ((x[None, :] - x[:, None]) / sigma) ** 2)
    kernel /= kernel.sum(1, keepdims=True)
    new = pmf @ kernel
    s_new = 1.0 - np.cumsum(new[:, :horizon], axis=1)
    s_new_prev = np.concatenate([np.ones((n, 1)), s_new[:, :-1]], axis=1)
    return np.clip(new[:, :horizon] / np.clip(s_new_prev, 1e-9, None), 1e-6, 1 - 1e-6)


def nll_np(h: np.ndarray, event_k: np.ndarray) -> float:
    """Mean negative log-likelihood of observed failures at step event_k (1-based) under hazards h."""
    k = np.arange(1, h.shape[1] + 1)[None, :]
    ek = np.clip(event_k, 1, h.shape[1])[:, None]
    ll = (np.log1p(-h) * (k < ek)).sum(1) + np.log(h[np.arange(len(h)), ek[:, 0] - 1])
    return float(-ll.mean())


def fit_blur(h: np.ndarray, event_k: np.ndarray) -> float:
    """Blur width that best predicts the failures of cutters the model did not train on."""
    grid = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5]
    scores = [nll_np(blur(h, g), event_k) for g in grid]
    return grid[int(np.argmin(scores))]


def curves(logits: np.ndarray, temperature: float = 1.0, sigma: float = 0.0) -> dict:
    """Hazard, survival and summaries from logits [n, K], optionally widened by blur(sigma)."""
    h = blur(1.0 / (1.0 + np.exp(-logits / temperature)), sigma)
    s = np.cumprod(1.0 - h, axis=1)
    horizon = h.shape[1]

    def quantile(q):
        # Smallest k with S(k) ≤ 1 − q, i.e. the cutter has failed by then with probability ≥ q.
        hit = s <= 1.0 - q
        return np.where(hit.any(1), hit.argmax(1) + 1, horizon + 1)

    return dict(
        hazard=h,
        survival=s,
        rul_q10=quantile(0.1),
        rul_q50=quantile(0.5),
        rul_q90=quantile(0.9),
        rmst=s.sum(1),  # restricted mean remaining life up to the horizon
        p_fail_1=1 - s[:, 0],
        p_fail_3=1 - s[:, 2],
        p_fail_5=1 - s[:, 4],
    )


def fit_temperature(logits: np.ndarray, event_k: np.ndarray, observed: np.ndarray) -> float:
    """One temperature on the hazard logits, chosen to minimise the out-of-fold NLL."""
    lg, ek, ob = (torch.as_tensor(a, dtype=torch.float32) for a in (logits, event_k, observed))
    grid = np.exp(np.linspace(np.log(0.3), np.log(3.0), 61))
    nll = [hazard_nll(lg / t, ek.long(), ob).mean().item() for t in grid]
    return float(grid[int(np.argmin(nll))])


def tool_conformal_margin(q10: np.ndarray, rul: np.ndarray, tool: np.ndarray, alpha: float = 0.1) -> float:
    """Grouped conformal correction for the lower remaining-life bound.

    One score per tool: the worst over-estimate of its lower quantile anywhere along its life.
    The margin is the ⌈(1 − α)(n + 1)⌉-th smallest score; with 12 calibration tools and α = 0.1
    that is simply the largest score, i.e. the worst miss seen on any other tool.
    """
    scores = np.array([np.max(q10[tool == t] - rul[tool == t]) for t in np.unique(tool)])
    n = len(scores)
    rank = int(np.ceil((1 - alpha) * (n + 1)))
    if rank > n:
        return float("inf")
    return float(np.sort(scores)[rank - 1])
