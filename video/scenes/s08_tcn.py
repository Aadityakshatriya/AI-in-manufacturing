"""s08 — the TCN: the cutter's history read like a sentence; dilated causal convolutions (1, 2, 4, 8;
two convolutions per block, kernel 3 -> 61 cycles of reach); never the future; then the real risk curve
for hidden cutter 103 at cycles 6 -> 31 -> 51.

Timing: word beats below were measured from audio/s08_tcn.wav (narration clock). cues.json has
"one, two, four, eight cycles back" ending at 10.93 s; in the audio the numbers fall at about
9.65 / 10.15 / 10.5 / 11.1 s, "cycles back" ends at 12.15 s and "Never into the future" is 12.5-13.65 s.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from style import *  # noqa: F401,F403

NB = dict(
    history=0.0, tcn=4.18, layer=6.54, one=9.65, two=10.15, four=10.5, eight=11.1, back=11.3,
    back_end=12.15, never=12.5, future=13.45, after=13.94, draws=15.1, risk=16.1, chance=17.2,
    each=18.25, still=19.5, end=20.32,
)


def B(k):
    return LEAD + NB[k]


# ---------------------------------------------------------------- geometry
S = 0.1            # one cycle along the row
TOK = 0.08         # token size
X_NOW = 0.0
ROW_Y = -2.9
LY = [-2.35, -1.97, -1.40, -1.02, -0.45, -0.07, 0.50, 0.88]   # 8 conv layers, 2 per block
DIL = [1, 1, 2, 2, 4, 4, 8, 8]
HEAD_Y = 1.55
WALL_X = X_NOW + S / 2
BAR_BASE = ROW_Y + 0.085
BAR_H = 3.45       # bar height for probability P_TOP
P_TOP = 0.40

# receptive-field cone of the newest output, top-down: positions (cycles back) per layer
CONE = [None] * 9
CONE[8] = [0]                       # index 8 = the top layer's node at "now" feeds the head
_cur = {0}
for _i in range(7, -1, -1):
    _cur = {p + j * DIL[_i] for p in _cur for j in range(3)}
    CONE[_i] = sorted(_cur)         # CONE[i] = positions needed at the input of layer i (layer i-1 or tokens)
# CONE[0] = inputs needed (0..60)
REACH = max(CONE[0]) + 1            # 61 cycles


def layer_y(i):
    """y of layer i (0 = tokens, 1..8 = conv layers)."""
    return ROW_Y if i == 0 else LY[i - 1]


def px(k):
    return X_NOW - k * S


# ---------------------------------------------------------------- data
def feature_cols(tool):
    """Per-cycle feature levels (0..1) for a cutter: table current, once-per-turn, health score."""
    cols = []
    for key in ("table_current_rel", "once_per_turn_rel", "health_rel"):
        v = np.array([p[1] for p in DATA[key][str(tool)]], dtype=float)
        lv = np.log(np.clip(v, 0.3, None))
        lo, hi = np.percentile(lv, 5), np.percentile(lv, 95)
        cols.append(np.clip((lv - lo) / max(hi - lo, 1e-6), 0, 1))
    return np.array(cols).T   # (cycles, 3)


OPEN_TOOL, OPEN_NOW = 101, 80          # opening sentence: cutter 101 up to cycle 80 (unlabelled)
FEAT_OPEN = feature_cols(OPEN_TOOL)
FEAT103 = feature_cols(103)   # the hidden cutter (cycles 1..59; it broke on cycle 60)
HZ = {int(k): np.array(v) for k, v in DATA["tcn_cutter103"]["hazard_at"].items()}


def break_prob(h):
    """The model outputs hazards: chance of breaking on cycle k given it survived until then.
    The chance of breaking ON cycle k (seen from now) is h_k times the chance of surviving to k."""
    surv = np.cumprod(np.concatenate([[1.0], 1 - h[:-1]]))
    return h * surv


PB = {c: break_prob(h) for c, h in HZ.items()}   # sums: ~0.06 at cycle 6, ~1.0 at 31 and 51
K60 = np.arange(1, 61)


def risk_at(n):
    """Bar heights (probabilities) for the next 60 cycles at cycle n. Real at n = 6, 31, 51; in between,
    the two real curves are cross-faded while held to the absolute cycles they predict (so they slide)."""
    if n <= 6:
        return PB[6]
    if n >= 51:
        return PB[51]
    n0, n1 = (6, 31) if n <= 31 else (31, 51)
    a = (n - n0) / (n1 - n0)
    return ((1 - a) * np.interp(K60 + (n - n0), K60, PB[n0], left=0, right=0)
            + a * np.interp(K60 - (n1 - n), K60, PB[n1], left=0, right=0))


def feat_color(u):
    u = float(np.clip(u, 0, 1))
    if u < 0.5:
        return interpolate_color(ManimColor(DATA_C), ManimColor(WARN), u / 0.5)
    return interpolate_color(ManimColor(WARN), ManimColor(HEAT), (u - 0.5) / 0.5)


def make_token(feats=None, ghost=False, broke=False):
    box = RoundedRectangle(width=TOK, height=TOK, corner_radius=0.016, stroke_width=0.9,
                           stroke_color=DIM if not ghost else FAINT, stroke_opacity=1.0,
                           fill_color="#121821", fill_opacity=1.0)
    g = VGroup(box)
    if feats is not None and not ghost:
        for j, u in enumerate(feats):
            g.add(Dot([0, (1 - j) * 0.022, 0], radius=0.0095, color=feat_color(u)))
    if broke:
        box.set_stroke(DANGER, width=1.2)
        g.add(Line([-0.022, -0.022, 0], [0.022, 0.022, 0], stroke_color=DANGER, stroke_width=1.2),
              Line([-0.022, 0.022, 0], [0.022, -0.022, 0], stroke_color=DANGER, stroke_width=1.2))
    return g


def bracket(x0, x1, y, color=DIM):
    return VGroup(
        Line([x0, y, 0], [x1, y, 0], stroke_color=color, stroke_width=1.5),
        Line([x0, y, 0], [x0, y + 0.08, 0], stroke_color=color, stroke_width=1.5),
        Line([x1, y, 0], [x1, y + 0.08, 0], stroke_color=color, stroke_width=1.5),
    )


class S08TCN(TLScene):
    SID = "s08_tcn"

    def wait_until(self, t):
        if self.now > t + 0.02:
            print(f"[s08 late] at {self.now:.2f}s, beat was {t:.2f}s")
        super().wait_until(t)

    def construct(self):
        frame = self.camera.frame
        frame.set(width=3.3).move_to([-1.45, -2.72, 0])
        self.add(frame)

        # ------------------------------------------------ 1. the sentence (0.5 - 4.4)
        toks = VGroup()
        for k in range(0, 74):
            c = OPEN_NOW - k
            t = make_token(FEAT_OPEN[c - 1])
            t.move_to([px(k), ROW_Y, 0])
            t.k = k
            toks.add(t)
        toks.submobjects.reverse()   # oldest first
        frame.add_updater(lambda m, dt: m.shift(RIGHT * 0.02 * dt).scale(1 - 0.01 * dt))
        self.wait_until(LEAD)
        self.add(*[t for t in toks if t.k > 33])          # older words, off to the left
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.6) for t in toks if t.k <= 33], lag_ratio=0.2),
                  run_time=3.3)
        newest = toks[-1]
        self.play(newest[0].animate.set_stroke(INK, width=1.4), run_time=0.4)

        # ------------------------------------------------ 2. layers of nodes (4.68)
        self.wait_until(B("tcn"))
        frame.clear_updaters()
        lattice = VGroup()
        for i in range(8):
            row = VGroup(*[Dot([px(k), LY[i], 0], radius=0.014, color=FAINT) for k in range(0, 72)])
            lattice.add(row)
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.05) for r in lattice], lag_ratio=0.2),
                  frame.animate.set(width=8.2).move_to([-2.9, -1.35, 0]), run_time=2.0)

        # ------------------------------------------------ 3. the dilated causal cone (7.04)
        blocks = [VGroup() for _ in range(4)]
        cone_nodes = [VGroup() for _ in range(4)]
        kern = [VGroup() for _ in range(4)]
        for i in range(8):                       # conv layer i (0-based) reads layer below with DIL[i]
            d = DIL[i]
            y_top, y_bot = LY[i], layer_y(i)
            bot_off = TOK / 2 if i == 0 else 0.014
            for p in CONE[i + 1]:
                for j in range(3):
                    q = p + j * d
                    ln = Line([px(p), y_top - 0.014, 0], [px(q), y_bot + bot_off, 0],
                              stroke_color=SIGNAL, stroke_width=0.9, stroke_opacity=0.55)
                    blocks[i // 2].add(ln)
                    if p == 0:
                        kern[i // 2].add(Line([px(p), y_top - 0.014, 0], [px(q), y_bot + bot_off, 0],
                                              stroke_color=WARN, stroke_width=2.4))
            for p in CONE[i + 1]:
                cone_nodes[i // 2].add(Dot([px(p), y_top, 0], radius=0.02, color=SIGNAL))
        head = Dot([X_NOW, HEAD_Y, 0], radius=0.065, color=WARN)
        head_glow = VGroup(*[Circle(radius=0.065 * r, stroke_width=0, fill_color=WARN, fill_opacity=o).move_to(head)
                             for r, o in [(1.8, 0.18), (2.8, 0.08), (4.2, 0.035)]])
        head_link = Line([X_NOW, LY[7] + 0.02, 0], [X_NOW, HEAD_Y - 0.065, 0], stroke_color=WARN, stroke_width=1.6)

        self.wait_until(B("layer"))
        self.play(frame.animate.set(width=config.frame_width).move_to([0, -0.68, 0]),
                  Succession(*[AnimationGroup(Create(blocks[b], lag_ratio=0.002), FadeIn(cone_nodes[b]),
                                              run_time=0.62) for b in range(4)],
                             AnimationGroup(Create(head_link), GrowFromCenter(head), FadeIn(head_glow),
                                            run_time=0.35)),
                  run_time=2.85, rate_func=smooth)

        # 1, 2, 4, 8 — each block lights on its word
        dil_lbls = VGroup()
        for b, word in enumerate(["one", "two", "four", "eight"]):
            ylo, yhi = LY[2 * b], LY[2 * b + 1]
            xl = px(max(CONE[2 * b])) - 0.3
            lbl = N(str(2 ** b), 30, WARN).move_to([xl, (ylo + yhi) / 2, 0])
            dil_lbls.add(lbl)
        for b, word in enumerate(["one", "two", "four", "eight"]):
            self.wait_until(B(word) - 0.05)
            prev = [blocks[b - 1].animate.set_stroke(opacity=0.5, width=0.9), FadeOut(kern[b - 1])] if b else []
            self.play(blocks[b].animate.set_stroke(opacity=1.0, width=1.5), FadeIn(kern[b]),
                      FadeIn(dil_lbls[b], scale=1.5), *prev, run_time=0.28)
        # 61 cycles back
        br_past = bracket(px(REACH - 1), px(0), ROW_Y - 0.2)
        lbl_past = T(f"{REACH} cycles", 24, INK).move_to([px(30), ROW_Y - 0.48, 0])
        self.play(blocks[3].animate.set_stroke(opacity=0.5, width=0.9), FadeOut(kern[3]),
                  GrowFromPoint(br_past, [px(0), ROW_Y - 0.2, 0]),
                  Succession(Wait(run_time=0.3), FadeIn(lbl_past, shift=UP * 0.1, run_time=0.45)), run_time=0.8)

        # ------------------------------------------------ 4. never into the future (13.0)
        ghosts = VGroup()
        for k in range(1, 67):
            g = make_token(ghost=True).move_to([px(-k), ROW_Y, 0])
            ghosts.add(g)
        wall = Line([WALL_X, ROW_Y - 0.35, 0], [WALL_X, HEAD_Y - 0.3, 0], stroke_color=INK, stroke_width=2.2)
        now_lbl = T("now", 26, INK).move_to([WALL_X, HEAD_Y + 0.5, 0])
        mirror = VGroup(*[l.copy().set_stroke(color=DIM, opacity=0.45, width=0.8)
                          .apply_function(lambda p: np.array([2 * WALL_X - p[0], p[1], p[2]]))
                          for b in blocks for l in b])
        self.wait_until(B("never"))
        self.play(Create(wall), FadeIn(now_lbl, shift=DOWN * 0.1),
                  LaggedStart(*[FadeIn(g) for g in ghosts], lag_ratio=0.01), run_time=0.45)
        self.play(Create(mirror, lag_ratio=0.0015), run_time=0.45)
        self.wait_until(B("future") - 0.05)
        self.play(mirror.animate.set_stroke(color=DANGER, opacity=0.8), wall.animate.set_stroke(color=DANGER, width=3.5),
                  run_time=0.15)
        self.play(FadeOut(mirror, shift=RIGHT * 0.25), wall.animate.set_stroke(color=INK, width=2.2), run_time=0.35)

        # ------------------------------------------------ 5. risk curve for hidden cutter 103 (14.44)
        now = ValueTracker(6.0)
        LIFE = 60
        real_toks, ghost_toks = VGroup(), VGroup()
        for c in range(1, LIFE + 1):
            if c < LIFE:
                rt = make_token(FEAT103[c - 1])
            else:
                rt = make_token(broke=True)
            gt = make_token(ghost=True, broke=(c == LIFE))
            rt.c = gt.c = c
            real_toks.add(rt)
            ghost_toks.add(gt)
        broke_line = DashedLine([0, BAR_BASE, 0], [0, BAR_BASE + BAR_H, 0], dash_length=0.06,
                                stroke_color=DANGER, stroke_width=1.4, stroke_opacity=0.7)
        broke_lbl = T("broke", 20, DANGER)

        def place_row(m=None):
            n = now.get_value()
            for rt, gt in zip(real_toks, ghost_toks):
                x = X_NOW + (rt.c - n) * S
                rt.move_to([x, ROW_Y, 0])
                gt.move_to([x, ROW_Y, 0])
                a = float(np.clip((WALL_X - x) / S + 0.5, 0, 1))    # 1 = past (seen), 0 = future
                rt.set_opacity(a)
                gt.set_opacity(1 - a)
            xb = X_NOW + (LIFE - n) * S
            broke_line.move_to([xb, BAR_BASE + BAR_H / 2, 0])
            broke_lbl.next_to(broke_line, UP, buff=0.08)
        place_row()
        real_toks.set_opacity(0)   # fade in below
        for rt in real_toks:
            if rt.c <= 6:
                rt.target_op = 1

        cycle_cache = {}

        def cycle_text(c):
            if c not in cycle_cache:
                cycle_cache[c] = N(f"cycle {c}", 26, INK).move_to([WALL_X, HEAD_Y + 0.5, 0])
            return cycle_cache[c]

        counter = cycle_text(6).copy()
        hidden_lbl = T("hidden cutter 103", 24, DIM).move_to([4.7, HEAD_Y + 0.5, 0])

        self.wait_until(B("after"))
        old_past = VGroup(*[t for t in toks])
        self.add(real_toks)
        self.play(FadeOut(old_past, shift=LEFT * 0.3), FadeOut(ghosts),
                  FadeIn(ghost_toks), *[rt.animate.set_opacity(1) for rt in real_toks if rt.c <= 6],
                  Succession(FadeOut(now_lbl, run_time=0.3), FadeIn(counter, run_time=0.4)),
                  FadeIn(hidden_lbl, shift=DOWN * 0.1),
                  *[b.animate.set_stroke(opacity=0.28) for b in blocks],
                  *[cn.animate.set_opacity(0.4) for cn in cone_nodes],
                  lattice.animate.set_opacity(0.5),
                  run_time=0.8)
        # from now on the row follows the cycle counter
        real_toks.add_updater(place_row)

        # bars over the next 60 cycles
        emit = ValueTracker(0.0)
        bars = VGroup(*[Rectangle(width=0.068, height=0.01, stroke_width=0, fill_color=WARN, fill_opacity=0.9)
                        for _ in range(60)])
        outline = VMobject(stroke_color=INK, stroke_width=2.2)

        def bars_upd(m):
            h = risk_at(now.get_value())
            e = emit.get_value()
            pts = []
            for j, (bar, p) in enumerate(zip(bars, h)):
                vis = float(np.clip((e * 1.35 - j / 60) / 0.35, 0, 1))
                hh = max(p / P_TOP * BAR_H * vis, 0.004)
                bar.stretch_to_fit_height(hh)
                bar.move_to([X_NOW + (j + 1) * S, BAR_BASE + hh / 2, 0])
                bar.set_fill(color=interpolate_color(ManimColor(WARN), ManimColor(DANGER), float(np.clip(p / P_TOP, 0, 1))),
                             opacity=0.9 * vis)
                if vis > 0:
                    pts.append([X_NOW + (j + 1) * S, BAR_BASE + hh, 0])
            if len(pts) >= 2:
                outline.set_points_as_corners(pts)
                outline.set_stroke(opacity=1)
            else:
                outline.set_points_as_corners([[X_NOW + S, BAR_BASE, 0], [X_NOW + S + 0.001, BAR_BASE, 0]])
                outline.set_stroke(opacity=0)
        bars.add_updater(bars_upd)
        bars_upd(bars)
        self.add(bars, outline)

        y25 = BAR_BASE + 0.25 / P_TOP * BAR_H
        top_line = DashedLine([X_NOW + S * 0.6, y25, 0], [X_NOW + 60.4 * S, y25, 0],
                              dash_length=0.07, stroke_color=FAINT, stroke_width=1.4)
        lbl_100 = N("25%", 20, DIM).next_to(top_line, RIGHT, buff=0.1)
        lbl_risk = T("chance of breaking", 24, INK).move_to([X_NOW + 30 * S, BAR_BASE + BAR_H + 0.72, 0])
        br_fut = bracket(px(-1), px(-60), ROW_Y - 0.2)
        lbl_fut = T("next 60 cycles", 24, INK).move_to([px(-30.5), ROW_Y - 0.48, 0])

        self.wait_until(B("draws") + 0.4)
        beam = Line(head.get_center(), [X_NOW + 30 * S, BAR_BASE + 0.2, 0], stroke_color=WARN, stroke_width=4)
        self.play(head.animate.scale(1.6), head_glow.animate.scale(1.6), ShowPassingFlash(beam, time_width=1.0),
                  run_time=0.45)
        self.play(head.animate.scale(1 / 1.6), head_glow.animate.scale(1 / 1.6),
                  emit.animate.set_value(1.0), Create(top_line), FadeIn(lbl_100),
                  GrowFromPoint(br_fut, [px(-1), ROW_Y - 0.2, 0]), FadeIn(lbl_fut),
                  FadeIn(broke_line), FadeIn(broke_lbl), run_time=1.1, rate_func=smooth)
        self.play(FadeIn(lbl_risk, shift=DOWN * 0.1), run_time=0.4)

        # step 6 -> 31 -> 51 (only the real cycles get a number; the counter cross-fades)
        def step(n1, rt):
            new = cycle_text(n1).copy()
            self.play(now.animate(run_time=rt, rate_func=smooth).set_value(n1),
                      Succession(Wait(run_time=rt * 0.35), FadeOut(counter, run_time=rt * 0.2),
                                 FadeIn(new, run_time=rt * 0.3)),
                      Succession(Wait(run_time=rt * 0.75), head.animate(run_time=rt * 0.25, rate_func=there_and_back)
                                 .scale(1.5)))
            return new

        self.wait_until(B("chance") + 0.1)
        counter = step(31, 1.3)
        self.wait_until(B("each") + 0.6)
        counter = step(51, 1.2)

        self.wait_until(self.total - 0.55)
        for m in (bars, real_toks):
            m.clear_updaters()
        self.remove(frame)
        self.finish()
