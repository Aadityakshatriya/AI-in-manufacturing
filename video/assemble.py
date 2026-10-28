"""Assemble the film: scene renders in order + narration + score + effects → out/toollife_policy.mp4.

Each scene render lasts LEAD + narration + TAIL; its narration is placed LEAD seconds after the scene starts.
The score is ducked under the voice. Usage (inside video/, venv active): python assemble.py [--preview]
--preview uses the 480p15 renders where a 1080p60 one is missing (for checking timing early).
"""

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

from sound import SR, score, sfx

HERE = Path(__file__).resolve().parent
LEAD = 0.5
SCENES = [("s01_cold_open", "S01ColdOpen"), ("s02_title", "S02Title"), ("s03_wear", "S03Wear"),
          ("s04_settings", "S04Settings"), ("s05_signals", "S05Signals"), ("s06_bits", "S06Bits"),
          ("s07_autoencoder", "S07Autoencoder"), ("s08_tcn", "S08TCN"), ("s09_honesty", "S09Honesty"),
          ("s10_decision", "S10Decision"), ("s11_close", "S11Close")]


def duration(path: Path) -> float:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = err.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        assert w.getframerate() == SR, path
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x


def main():
    preview = "--preview" in sys.argv
    cues = json.loads((HERE / "cues.json").read_text())
    clips, times, t = [], {}, 0.0
    for sid, cls in SCENES:
        hi = HERE / "media" / "videos" / sid / "1080p60" / f"{cls}.mp4"
        lo = HERE / "media" / "videos" / sid / "480p15" / f"{cls}.mp4"
        path = hi if hi.exists() else (lo if preview and lo.exists() else None)
        if path is None:
            raise SystemExit(f"missing render for {sid} ({hi})")
        times[sid] = t
        d = duration(path)
        expect = LEAD + cues[sid]["duration"] + 0.9
        flag = "" if abs(d - expect) < 0.05 else f"   <-- expected {expect:.2f}"
        print(f"{sid:18s} {t:7.2f}s  +{d:6.2f}s  {path.parent.name}{flag}")
        clips.append(path)
        t += d
    total = t

    # audio: narration + ducked score + effects
    n = int(total * SR)
    voice = np.zeros(n, np.float32)
    for sid, _ in SCENES:
        x = read_wav(HERE / "audio" / f"{sid}.wav")
        i = int((times[sid] + LEAD) * SR)
        voice[i:i + len(x)] += x[: max(0, min(len(x), n - i))]
    env = np.sqrt(np.convolve(voice ** 2, np.ones(int(0.25 * SR)) / int(0.25 * SR), "same"))
    talking = np.clip(env / 0.02, 0, 1)
    k = int(0.4 * SR)
    talking = np.convolve(talking, np.ones(k) / k, "same")  # smooth the ducking
    music = score(times, total)
    duck = (1 - 0.55 * talking)[:, None]
    fx = sfx(times, cues, LEAD, total)
    mix = 0.95 * np.stack([voice, voice], 1) + 0.40 * music * duck + 0.55 * fx
    peak = np.abs(mix).max()
    mix = np.tanh(mix / peak * 1.2) / np.tanh(1.2) * 0.89  # gentle limiter, peak -1 dBFS
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    wav = out / "mix.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())

    # loudness: measure (EBU R128) and bring the whole film to -15 LUFS with a fixed gain and a peak limiter
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(wav), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    measured = float(err.split("Summary:")[1].split("I:")[1].split("LUFS")[0])
    gain_db = -15.0 - measured
    print(f"loudness {measured:.1f} LUFS -> -15.0 (gain {gain_db:+.1f} dB)")

    # video: concatenate, re-encode once, mux
    lst = out / "concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in clips))
    name = "toollife_policy_preview.mp4" if preview else "toollife_policy.mp4"
    fps = ["-r", "60"] if not preview else ["-r", "30", "-vf", "scale=1920:1080:flags=lanczos"]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(wav),
                    *fps, "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                    "-af", f"volume={gain_db:.2f}dB,alimiter=limit=0.84:level=false",
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", str(out / name)], check=True)
    print(f"wrote {out / name}  ({total:.1f} s)")


if __name__ == "__main__":
    main()
