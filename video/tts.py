"""Narration with Sarvam Bulbul: one WAV per scene in video/audio/, plus durations.json.

The key is read from the environment (SARVAM_API_KEY, loaded from ~/.kivi/secrets.env) and never printed.
Usage: set -a; source ~/.kivi/secrets.env; set +a; python video/tts.py [scene_id ...]
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "audio"


def synth(text: str, voice: dict, **extra) -> bytes:
    body = {"model": voice["model"], "text": text, "target_language_code": voice["language"],
            "speaker": voice["speaker"], **extra}
    req = urllib.request.Request("https://api.sarvam.ai/text-to-speech", data=json.dumps(body).encode(),
                                 headers={"api-subscription-key": os.environ["SARVAM_API_KEY"],
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return base64.b64decode(json.load(r)["audios"][0])


def main() -> None:
    cfg = json.loads((HERE / "narration.json").read_text())
    only = set(sys.argv[1:])
    OUT.mkdir(exist_ok=True)
    extra = cfg["voice"].get("extra", {"pace": 0.95, "speech_sample_rate": 48000})
    for sid, text in cfg["scenes"]:
        if only and sid not in only:
            continue
        try:
            audio = synth(text, cfg["voice"], **extra)
        except urllib.error.HTTPError as e:
            print(sid, "HTTP", e.code, e.read().decode()[:300])
            raise
        (OUT / f"{sid}.wav").write_bytes(audio)
    durations = {}
    for sid, _ in cfg["scenes"]:
        p = OUT / f"{sid}.wav"
        if p.exists():
            with wave.open(str(p)) as w:
                durations[sid] = round(w.getnframes() / w.getframerate(), 2)
    (HERE / "durations.json").write_text(json.dumps(durations, indent=1))
    print(json.dumps(durations, indent=1), "total", round(sum(durations.values()), 1))


if __name__ == "__main__":
    main()
