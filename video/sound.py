"""Score and sound effects for the film, synthesised with numpy (no samples, no licences).

score(times, total)  an ambient pad that follows the film's arc (one chord per scene, a soft pulse while
                     the networks are explained, a lift in the honesty scene, a resolve at the end)
sfx(times, total)    the tooth grind at 213 hits a second, the slow-down and the snap, a boom on the title,
                     the fracture in the wear scene, a chime on the decision, the final hit
Both return float32 stereo arrays [n, 2] at SR. `times` maps scene id -> start time of that scene in the film.
"""

import numpy as np
from scipy.signal import fftconvolve

SR = 48000
rng = np.random.default_rng(7)


def hz(note: str) -> float:
    names = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
             "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
    name, octave = note[:-1], int(note[-1])
    return 440.0 * 2 ** ((names[name] + 12 * (octave + 1) - 69) / 12)


def smooth_env(n, points):
    """Piecewise-linear envelope through (time_s, value) points, sampled at SR, length n."""
    t = np.arange(n) / SR
    ts, vs = zip(*points)
    return np.interp(t, ts, vs).astype(np.float32)


def reverb(x, seconds=2.2, mix=0.25):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(x.shape[1]):
        ir = rng.standard_normal(n).astype(np.float32) * np.exp(-t * 6.9 / seconds).astype(np.float32)
        ir[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
        ir /= np.sqrt((ir ** 2).sum())
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return (1 - mix) * x + mix * out


# ----------------------------------------------------------------------------------------------- score

# One chord per scene (bass + voicing). D minor world; lifts to Bb/F for the networks, a suspended build in
# the honesty scene, tension on the decision, D major (Picardy) at the close.
CHORDS = {
    "s01_cold_open": ["D2", "A2", "D3"],
    "s02_title": ["D2", "A2", "F3", "E4", "A4"],
    "s03_wear": ["D2", "A2", "F3", "C4"],
    "s04_settings": ["Bb1", "F2", "D3", "A3"],
    "s05_signals": ["G1", "D2", "Bb2", "F3", "A3"],
    "s06_bits": ["D2", "A2", "E3", "A3"],
    "s07_autoencoder": ["Bb1", "F2", "C3", "D3", "A3"],
    "s08_tcn": ["F1", "C2", "A2", "E3", "G3"],
    "s09_honesty": ["G1", "D2", "A2", "C3", "D4", "G4"],
    "s10_decision": ["A1", "E2", "G2", "C#3", "E3"],
    "s11_close": ["D2", "A2", "D3", "F#3", "A3", "E4"],
}
LEVEL = {"s01_cold_open": 0.5, "s02_title": 0.9, "s03_wear": 0.7, "s04_settings": 0.75, "s05_signals": 0.8,
         "s06_bits": 0.85, "s07_autoencoder": 0.9, "s08_tcn": 0.95, "s09_honesty": 1.05, "s10_decision": 1.0, "s11_close": 1.1}
BRIGHT = {"s01_cold_open": 2.0, "s02_title": 4.0, "s03_wear": 3.0, "s04_settings": 3.5, "s05_signals": 4.0, "s06_bits": 5.0,
          "s07_autoencoder": 5.5, "s08_tcn": 6.0, "s09_honesty": 7.0, "s10_decision": 6.0, "s11_close": 8.0}
PULSE = {"s06_bits", "s07_autoencoder", "s08_tcn", "s09_honesty"}


def pad_voice(f, n, amp_env, bright_env, detune=0.0025, harmonics=10):
    """A soft detuned saw-like voice by additive synthesis; brightness (how many harmonics speak) varies in time."""
    t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    for side, d in ((0, -detune), (1, detune)):
        ph0 = rng.uniform(0, 2 * np.pi)
        for k in range(1, harmonics + 1):
            if f * k > 9000:
                break
            w = (1.0 / k) * np.exp(-(k - 1) / bright_env)
            out[:, side] += (w * np.sin(2 * np.pi * f * k * (1 + d) * t + ph0 * k)).astype(np.float32)
    return out * amp_env[:, None]


def score(times: dict, total: float) -> np.ndarray:
    n = int(total * SR)
    order = sorted(times, key=times.get)
    ends = {sid: (times[order[i + 1]] if i + 1 < len(order) else total) for i, sid in enumerate(order)}
    # every distinct note gets one voice whose loudness follows the scenes it belongs to (crossfades of 2.5 s)
    notes = sorted({nt for c in CHORDS.values() for nt in c}, key=hz)
    mix = np.zeros((n, 2), np.float32)
    bright_pts = [(0, 2.0)]
    for sid in order:
        bright_pts += [(times[sid] + 1.5, BRIGHT[sid]), (ends[sid], BRIGHT[sid])]
    bright = np.maximum(smooth_env(n, bright_pts), 1.0)
    for nt in notes:
        pts = [(0, 0.0)]
        for sid in order:
            on = nt in CHORDS[sid]
            lvl = LEVEL[sid] * (0.8 if hz(nt) < 100 else 0.5) if on else 0.0
            pts += [(times[sid] + 1.2, lvl), (max(times[sid] + 1.3, ends[sid] - 1.3), lvl)]
        pts += [(total - 3.0, pts[-1][1]), (total, 0.0)]
        mix += pad_voice(hz(nt), n, smooth_env(n, pts), bright)
    # slow breathing swell
    t = np.arange(n) / SR
    mix *= (0.85 + 0.15 * np.sin(2 * np.pi * t / 9.0))[:, None].astype(np.float32)
    # soft plucked pulse (D minor pentatonic arpeggio, 100 bpm eighths) while the networks are explained
    pent = ["D4", "F4", "G4", "A4", "C5", "D5", "A4", "F4"]
    step = 60 / 100 / 2
    plen = int(0.9 * SR)
    tp = np.arange(plen) / SR
    for sid in PULSE:
        k = 0
        for t0 in np.arange(times[sid] + 1.0, ends[sid] - 0.6, step):
            f = hz(pent[k % len(pent)]) * (2 if sid == "s09_honesty" and k % 4 == 3 else 1)
            p = (np.sin(2 * np.pi * f * tp) + 0.25 * np.sin(4 * np.pi * f * tp)) * np.exp(-tp * 7)
            i = int(t0 * SR)
            j = min(n, i + plen)
            pan = 0.5 + 0.35 * np.sin(k * 0.9)
            amp = 0.10 * (1.15 if k % 4 == 0 else 0.8)
            mix[i:j, 0] += (amp * (1 - pan) * p[: j - i]).astype(np.float32)
            mix[i:j, 1] += (amp * pan * p[: j - i]).astype(np.float32)
            k += 1
    mix = reverb(mix, 3.0, 0.35)
    return (mix / (np.abs(mix).max() + 1e-9) * 0.5).astype(np.float32)


# ----------------------------------------------------------------------------------------------- effects

def place(buf, x, t0, gain=1.0, pan=0.5):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x))
    x = x[: j - i]
    if x.ndim == 1:
        buf[i:j, 0] += gain * (1 - pan) * 2 * x * 0.5
        buf[i:j, 1] += gain * pan * 2 * x * 0.5
    else:
        buf[i:j] += gain * x


def noise_band(n, lo, hi):
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    x = np.fft.irfft(spec, n).astype(np.float32)
    return x / (np.abs(x).max() + 1e-9)


def grind(t0, t1, slow_from, stop_at):
    """Tooth hits at 213 per second, slowing from slow_from to a stop at stop_at (scene times in s)."""
    n = int((stop_at - t0) * SR)
    t = np.arange(n) / SR + t0
    rate = np.where(t < slow_from, 213.0, 213.0 * np.clip((stop_at - t) / (stop_at - slow_from), 0.05, 1) ** 1.6)
    phase = np.cumsum(rate / SR)
    hits = np.flatnonzero(np.diff(np.floor(phase)) > 0)
    out = np.zeros(n, np.float32)
    click = noise_band(int(0.004 * SR), 1500, 9000) * np.exp(-np.arange(int(0.004 * SR)) / (0.0008 * SR))
    body = np.sin(2 * np.pi * 900 * np.arange(int(0.006 * SR)) / SR) * np.exp(-np.arange(int(0.006 * SR)) / (0.0015 * SR))
    for h in hits:
        g = 0.6 + 0.4 * rng.random()
        out[h:h + len(click)] += g * click[: max(0, min(len(click), n - h))]
        out[h:h + len(body)] += 0.5 * g * body[: max(0, min(len(body), n - h))]
    # sparks crackle on top while at full speed
    crackle = noise_band(n, 3000, 12000) * (rng.random(n) < 0.002) * 3
    out += (crackle * (t < slow_from)).astype(np.float32)
    fade_in = np.clip((t - t0) / 1.2, 0, 1)
    return out * fade_in.astype(np.float32) * 0.35


def snap(big=True):
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    crack = noise_band(n, 800, 14000) * np.exp(-t / 0.035)
    thump = np.sin(2 * np.pi * (70 - 30 * t) * t) * np.exp(-t / 0.25)
    ring = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in
               ((1180, 0.35, 0.9), (3257, 0.22, 0.6), (6372, 0.12, 0.35), (10502, 0.06, 0.2)))
    x = (1.0 * crack + 0.9 * thump + (0.6 if big else 0.35) * ring).astype(np.float32)
    return x / np.abs(x).max()


def boom():
    n = int(3.5 * SR)
    t = np.arange(n) / SR
    sweep = np.sin(2 * np.pi * np.cumsum(90 - 55 * np.clip(t / 1.2, 0, 1)) / SR) * np.exp(-t / 1.1)
    air = noise_band(n, 200, 3000) * np.exp(-t / 0.5) * 0.25
    x = (sweep + air).astype(np.float32)
    return x / np.abs(x).max()


def whoosh(seconds=1.2, up=True):
    n = int(seconds * SR)
    t = np.linspace(0, 1, n)
    env = (t ** 2 if up else (1 - t) ** 2) * np.sin(np.pi * t) ** 0.5
    return (noise_band(n, 300, 6000) * env).astype(np.float32)


def chime(f=880.0):
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / d) for m, a, d in ((1, 1, 1.2), (2.01, 0.4, 0.7), (3.0, 0.2, 0.4), (4.2, 0.1, 0.25)))
    return (x * np.clip(t / 0.004, 0, 1)).astype(np.float32) / 1.7


def sfx(times: dict, cues: dict, lead: float, total: float) -> np.ndarray:
    n = int(total * SR)
    buf = np.zeros((n, 2), np.float32)
    c = lambda sid, i: times[sid] + lead + cues[sid]["phrases"][i]["t"]
    # s01: grind from the start, slows on "without any warning", snaps on "it snaps"
    t_slow, t_snap = c("s01_cold_open", 2), c("s01_cold_open", 3)
    place(buf, grind(times["s01_cold_open"] + 0.3, None, t_slow, t_snap), times["s01_cold_open"] + 0.3, 1.0, 0.45)
    place(buf, snap(True), t_snap, 0.9)
    place(buf, whoosh(0.8, True), t_snap - 0.8, 0.25)
    # s02: boom under the title
    place(buf, boom(), times["s02_title"] + 0.35, 0.8)
    # s03: smaller fracture on "ends in fracture" (about 2 s into the last phrase)
    place(buf, snap(False), c("s03_wear", 6) + 2.0, 0.55, 0.6)
    # gentle whooshes into each new chapter
    for sid in ("s04_settings", "s05_signals", "s06_bits", "s07_autoencoder", "s08_tcn", "s09_honesty", "s10_decision"):
        place(buf, whoosh(0.9, True), times[sid] - 0.6, 0.12, 0.5)
    # s10: chime on "change it"
    place(buf, chime(880), c("s10_decision", 2) + 0.6, 0.35, 0.55)
    # s11: final hit on the title
    place(buf, boom(), c("s11_close", 3) - 0.1, 0.7)
    place(buf, chime(587.33), c("s11_close", 3) + 0.05, 0.25, 0.5)
    return reverb(buf, 1.6, 0.2)
