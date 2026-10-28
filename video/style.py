"""Shared look and timing for every scene of the ToolLife Policy film.

Every scene file does `from style import *` and subclasses TLScene. The film is assembled from one
render per scene; narration is added afterwards (video/assemble.py), so renders are silent.

Timing contract: a scene lasts LEAD + narration + TAIL seconds. Narration starts at LEAD. Phrase times
from cues.json are available as self.cue(i) (already shifted by LEAD). Use self.wait_until(t) to hold
until a moment, and self.finish() as the last call, which fades everything out and pads to the exact length.
"""

import json
from pathlib import Path

import numpy as np
from manim import *  # noqa: F401,F403

HERE = Path(__file__).resolve().parent
CUES = json.loads((HERE / "cues.json").read_text())
DATA = json.loads((HERE / "data.json").read_text())

LEAD = 0.5   # silence before the narration starts
TAIL = 0.9   # breathing room after it ends (the last 0.5 s is the fade-out)

config.background_color = "#0B0E13"
config.frame_rate = 60
config.pixel_width = 1920
config.pixel_height = 1080

# Palette: 3Blue1Brown-like on a near-black ground. Use these names, not raw hex, in scenes.
BG = "#0B0E13"
INK = "#ECEFF4"        # main text and lines
DIM = "#6B7684"        # secondary text, axes, past/inactive things
FAINT = "#2A313B"      # grids, ghosts
STEEL = "#8C99A6"      # steel workpiece
CARBIDE = "#C9D3DD"    # the cutter
SIGNAL = "#58C4DD"     # signals, data, the model's view (3b1b blue)
DATA_C = "#5CD0B3"     # numbers, bits (teal)
WARN = "#F7C948"       # attention, highlights, sparks (yellow)
HEAT = "#FF8A3D"       # heat, wear, force (orange)
DANGER = "#FC6255"     # fracture, breakage, failure (red)
GOOD = "#83C167"       # healthy, correct, saved (green)

FONT = "Avenir Next"   # all text; no LaTeX on this machine (MathTex/Tex will fail)
MONO = "Menlo"         # numbers and bits


def T(text, size=36, color=INK, weight=NORMAL, font=FONT, **kw):
    """Text in the film's font. Keep on-screen words few: the narration carries the story."""
    return Text(text, font=font, font_size=size, color=color, weight=weight, **kw)


def N(text, size=32, color=DATA_C, **kw):
    """Monospaced numbers and bits."""
    return Text(text, font=MONO, font_size=size, color=color, **kw)


def end_mill(radius=1.6, teeth=4, color=CARBIDE, edge=WARN, stroke=3):
    """A 4-flute end mill seen end-on: a disc with curved flutes cut out and a bright cutting edge on
    each tooth. Rotate it with .rotate(angle) or an updater. Returns VGroup(body, edges)."""
    pts = []
    for k in range(teeth):
        a0 = TAU * k / teeth
        # tooth: from the flute bottom out to the tip, then along the land, then a curved flute back in
        for s in np.linspace(0, 1, 18):
            a = a0 + 0.55 * s * TAU / teeth
            r = radius * (0.55 + 0.45 * np.sqrt(s)) if s < 0.75 else radius
            pts.append([r * np.cos(a), r * np.sin(a), 0])
        for s in np.linspace(0, 1, 14):
            a = a0 + (0.55 + 0.45 * s) * TAU / teeth
            r = radius * (1 - 0.45 * np.sin(np.pi * s * 0.5))
            pts.append([r * np.cos(a), r * np.sin(a), 0])
    body = Polygon(*pts, color=color, fill_color=color, fill_opacity=0.18, stroke_width=stroke)
    edges = VGroup(*[
        Dot(radius * np.array([np.cos(TAU * k / teeth + 0.55 * 0.75 * TAU / teeth), np.sin(TAU * k / teeth + 0.55 * 0.75 * TAU / teeth), 0]),
            radius=0.05 * radius, color=edge)
        for k in range(teeth)])
    hub = Circle(radius=0.18 * radius, color=color, stroke_width=stroke * 0.7)
    return VGroup(body, hub, edges)


class TLScene(MovingCameraScene):
    """Base scene: knows its narration cues and its exact length."""

    SID = None  # e.g. "s01_cold_open" — must match narration.json / cues.json

    @property
    def cues(self):
        return CUES[self.SID]["phrases"]

    def cue(self, i):
        """Start time (s, scene clock) of narration phrase i."""
        return LEAD + self.cues[i]["t"]

    def cue_end(self, i):
        return LEAD + self.cues[i]["end"]

    @property
    def total(self):
        return LEAD + CUES[self.SID]["duration"] + TAIL

    @property
    def now(self):
        return self.renderer.time

    def wait_until(self, t):
        dt = t - self.now
        if dt > 1 / 120:
            self.wait(dt)

    def finish(self, fade=0.5):
        """Fade everything out and end exactly at the scene's length."""
        self.wait_until(self.total - fade)
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=fade)
        self.wait_until(self.total)
