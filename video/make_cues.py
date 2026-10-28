"""Phrase timings for each scene's narration (cues.json), from word timestamps (faster-whisper, base.en).

Each narration phrase (split at sentence ends, colons and the ellipsis) is aligned to the recognised words;
a phrase starts at the recognised word that follows the longest gap at its boundary. Recognition errors
("breeds" for "reads") do not matter: only the timing is used.
Usage (inside video/, venv active): python make_cues.py
"""

import difflib
import json
import re
import subprocess
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def load16k(path):
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return resample_poly(x, 1, 3).astype(np.float32)


def pauses(path):
    """Silences of 0.1 s or more (ffmpeg silencedetect), as (start, end) pairs."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-38dB:d=0.10",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    return list(zip([float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)],
                    [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]))


def snap(prev_end, start, gaps):
    """Recognisers glue a pause onto the next word, so a phrase's first word often "starts" where the previous
    word ended. Use the real silence there instead: the longest one that begins between 0.3 s before the
    previous word's end and 0.5 s after the recognised start, and ends no later than 0.8 s after it."""
    near = [g for g in gaps if prev_end - 0.3 <= g[0] <= start + 0.5 and prev_end <= g[1] <= start + 0.8]
    return max(near, key=lambda g: g[1] - g[0]) if near else None


def main():
    cfg = json.loads((HERE / "narration.json").read_text())
    dur = json.loads((HERE / "durations.json").read_text())
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    cues = {}
    for sid, text in cfg["scenes"]:
        segs, _ = model.transcribe(load16k(HERE / "audio" / f"{sid}.wav"), word_timestamps=True, language="en")
        rec = [w for s in segs for w in s.words]
        phrases = [p.strip() for p in re.split(r"(?<=[.:?!])\s+|\.\.\.\s*", text) if p.strip()]
        orig = [w for p in phrases for w in p.split()]
        first = np.cumsum([0] + [len(p.split()) for p in phrases])  # first original word of each phrase
        sm = difflib.SequenceMatcher(None, [norm(w) for w in orig], [norm(w.word) for w in rec], autojunk=False)
        o2r = {}
        for a, b, size in sm.get_matching_blocks():
            for k in range(size):
                o2r[a + k] = b + k
        gaps = pauses(HERE / "audio" / f"{sid}.wav")
        starts, ends = [rec[0].start], []
        for i in range(1, len(phrases)):
            last = first[i] - 1
            if last in o2r and o2r[last] + 1 < len(rec):
                j = o2r[last] + 1  # the previous phrase's last word was recognised: start right after it
            else:
                prev = max([o2r[k] for k in range(first[i - 1], first[i]) if k in o2r], default=0)
                nxt = min([o2r[k] for k in range(first[i], first[i + 1]) if k in o2r], default=prev + 1)
                cands = range(max(prev + 1, 1), max(nxt, prev + 1) + 1)
                j = max(cands, key=lambda j: rec[j].start - rec[j - 1].end)
            g = snap(rec[j - 1].end, rec[j].start, gaps)
            starts.append(g[1] if g else rec[j].start)
            ends.append(g[0] if g else rec[j - 1].end)
        ends.append(min(dur[sid], rec[-1].end))
        cues[sid] = {"duration": dur[sid], "phrases": [
            {"t": round(float(a), 2), "end": round(float(b), 2), "text": p} for a, b, p in zip(starts, ends, phrases)]}
    (HERE / "cues.json").write_text(json.dumps(cues, indent=1))
    old = json.loads((HERE / "cues_pauses_old.json").read_text()) if (HERE / "cues_pauses_old.json").exists() else {}
    for sid, c in cues.items():
        print(sid, c["duration"])
        for i, p in enumerate(c["phrases"]):
            o = old.get(sid, {}).get("phrases", [{}] * 99)[i].get("t") if old else None
            d = "" if o is None else f"  (was {o:5.2f}, {p['t'] - o:+.2f})"
            print(f"   {p['t']:6.2f}-{p['end']:6.2f}  {p['text'][:58]:58s}{d}")


if __name__ == "__main__":
    main()
