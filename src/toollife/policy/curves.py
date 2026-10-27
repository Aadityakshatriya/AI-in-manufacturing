"""Small helpers for failure curves (discrete-time hazards).

Convention used everywhere in the decision layer (same as PLAN.md §6 and model-design.md §5.1):

  h[j-1] = hazard_j = P(the cutter fails during the j-th next cycle | it survived the j-1 cycles before it)
  S(j)   = prod_{m <= j} (1 - h[m-1])      chance of surviving the next j cycles, S(0) = 1
  "steps to failure" J = the j at which the cutter fails (J = 1 means the very next cycle breaks).
  In the Rzeszów tables J equals the column `rul` (cycles to failure counted from the current row).

Beyond the stored horizon K we assume the hazard stays at its last value h[K-1] (constant-hazard tail).
This is only used for remaining-life quantiles far beyond K and for time-warping; decisions use the
first K steps.
"""

import numpy as np

EPS = 1e-12


def survival(h: np.ndarray) -> np.ndarray:
    """S(0..K) for hazard curves h[..., K]. Returns shape [..., K+1] with S(0) = 1."""
    h = np.clip(np.asarray(h, dtype=float), 0.0, 1.0)
    s = np.cumprod(1.0 - h, axis=-1)
    return np.concatenate([np.ones(s.shape[:-1] + (1,)), s], axis=-1)


def extend(h: np.ndarray, horizon: int) -> np.ndarray:
    """Pad curves to `horizon` steps with their last hazard (constant-hazard tail)."""
    h = np.asarray(h, dtype=float)
    k = h.shape[-1]
    if horizon <= k:
        return h[..., :horizon]
    pad = np.repeat(h[..., -1:], horizon - k, axis=-1)
    return np.concatenate([h, pad], axis=-1)


def shift(h: np.ndarray, steps: int) -> np.ndarray:
    """Curve after surviving `steps` more cycles with no new information: drop the first steps,
    pad the end with the last hazard. Used to carry a prediction forward over missing cycles."""
    if steps <= 0:
        return np.asarray(h, dtype=float)
    k = h.shape[-1]
    return extend(np.asarray(h, dtype=float)[..., steps:], k) if steps < k else np.repeat(h[..., -1:], k, axis=-1)


def surv_at(h: np.ndarray, x) -> np.ndarray:
    """S(x) at fractional step positions x (linear interpolation between whole steps).
    h is a single curve [K]; x may be an array. Beyond K the constant-hazard tail is used."""
    h = np.asarray(h, dtype=float)
    x = np.asarray(x, dtype=float)
    need = int(np.ceil(np.max(x))) + 1 if x.size else 1
    s = survival(extend(h, max(need, h.shape[-1])))
    return np.interp(x, np.arange(s.shape[-1]), s)


def fail_within(h: np.ndarray, n) -> np.ndarray:
    """P(fail within the next n cycles) = 1 - S(n); n may be fractional (slow cutting)."""
    return 1.0 - surv_at(h, n)


def rul_quantiles(h: np.ndarray, qs=(0.1, 0.5, 0.9), cap: int = 2000) -> np.ndarray:
    """Quantiles of the steps-to-failure J for curves h[N, K]: the smallest j >= 1 with
    P(J <= j) >= q. Past K, the constant-hazard tail gives a closed form. Capped at `cap`.
    Returns [N, len(qs)] floats."""
    h = np.atleast_2d(np.asarray(h, dtype=float))
    n, k = h.shape
    s = survival(h)  # [N, K+1]
    out = np.empty((n, len(qs)))
    for i, q in enumerate(qs):
        target = 1.0 - q  # first j with S(j) <= 1 - q
        hit = s[:, 1:] <= target + EPS
        inside = hit.any(axis=1)
        first = np.argmax(hit, axis=1) + 1
        # Tail: S(K + m) = S(K) * (1 - h_K)^m  =>  m = ceil(log(target / S(K)) / log(1 - h_K))
        sk = np.maximum(s[:, -1], EPS)
        hk = np.clip(h[:, -1], EPS, 1 - EPS)
        m = np.ceil(np.log(target / sk) / np.log(1.0 - hk))
        tail = np.minimum(k + np.maximum(m, 1), cap)
        out[:, i] = np.where(inside, first, tail)
    return out


def stretch(h: np.ndarray, w: float) -> np.ndarray:
    """Time-warp a curve by factor w (rl-design §4.11): the stretched survival is S'(j) = S(j / w).
    w > 1 makes the cutter look longer-lived. Returns a curve with the same K."""
    h = np.asarray(h, dtype=float)
    k = h.shape[-1]
    x = np.arange(k + 1) / w
    sp = surv_at(h, x)
    sp = np.maximum(sp, EPS)
    hp = 1.0 - sp[1:] / sp[:-1]
    return np.clip(hp, 0.0, 1.0)
