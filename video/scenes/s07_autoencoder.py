"""s07 — the autoencoder: an hourglass network squeezes 20,480 numbers through 64, rebuilds healthy
vibration, fails on worn vibration, and that failure becomes the health score (real curves).

Timing: word beats below were measured from audio/s07_autoencoder.wav (narration clock). Note that
cues.json puts "We trained it only on healthy cutting" at 8.34 s; in the audio, 8.34-10.28 is still
"...then tries to rebuild the original." and "We trained..." starts at 10.68.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from style import *  # noqa: F401,F403

# narration-clock beats (seconds), from the audio
NB = dict(
    squeeze=3.34, twenty=4.22, through=5.80, bottleneck=6.05, sixtyfour=7.26,
    rebuild=8.34, rebuild_end=10.28, trained=10.68, trained_end=13.06,
    worn=13.46, fails=15.40, worn_end=15.80, size=16.02, failure=17.62, score=19.40, end=20.48,
)


def B(k):
    return LEAD + NB[k]


# ---------------------------------------------------------------- data
VIB_NEW = np.array(DATA["vibration"]["new"], dtype=float)
VIB_WORN = np.array(DATA["vibration"]["worn"], dtype=float)
HEALTH = DATA["health_rel"]


def movavg(a, k):
    pad = k // 2
    ap = np.concatenate([a[pad:0:-1], a, a[-2:-pad - 2:-1]])
    return np.convolve(ap, np.ones(k) / k, mode="same")[pad:pad + len(a)]


WIN = 400
HEALTHY_WINDOWS = [VIB_NEW[0:WIN], VIB_NEW[400:800], VIB_NEW[800:1200], VIB_NEW[150:550]]
WORN_WINDOW = VIB_WORN[0:WIN]


def rebuild_healthy(a):
    # a good autoencoder output: the same wave, minus the finest jitter
    return movavg(a, 9)


def rebuild_worn(a):
    # trained on healthy cutting only, it can only produce a healthy-sized, healthy-shaped wave
    return movavg(a, 21) * (VIB_NEW.std() / VIB_WORN.std())


# ---------------------------------------------------------------- layout
PANEL_W = 2.3
AMP = 0.6
NET_Y = 0.1
LEFT_C = np.array([-5.45, NET_Y, 0])
RIGHT_C = np.array([5.45, NET_Y, 0])

XS = [-3.6, -2.4, -1.2, 0.0, 1.2, 2.4, 3.6]
SIZES = [16, 11, 7, 5, 7, 11, 16]
GAPS = [0.335, 0.39, 0.43, 0.36, 0.43, 0.39, 0.335]
RADII = [0.085, 0.095, 0.105, 0.115, 0.105, 0.095, 0.085]
BN = 3  # bottleneck layer index

# health chart (log y)
CH_O = np.array([-4.9, -2.75, 0])
CH_W, CH_H = 9.8, 5.0
LOG_LO, LOG_HI = np.log10(0.5), np.log10(40)


def ch(frac, val):
    v = np.log10(np.clip(val, 0.5, 40))
    return CH_O + np.array([frac * CH_W, (v - LOG_LO) / (LOG_HI - LOG_LO) * CH_H, 0])


def wave_points(a, center, width=PANEL_W, amp=AMP):
    xs = np.linspace(-width / 2, width / 2, len(a))
    return np.array([center + np.array([x, amp * y, 0]) for x, y in zip(xs, a)])


def wave(a, center, color, width=2.2, opacity=1.0):
    m = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity)
    m.set_points_as_corners(wave_points(a, center))
    return m


def gap_slivers(a, b, center, n=150, color=DANGER, opacity=0.6):
    """The area between two curves as thin vertical slivers (so it can later be stacked into a bar)."""
    pa, pb = wave_points(a, center), wave_points(b, center)
    idx = np.linspace(0, len(a) - 1, n).astype(int)
    dx = PANEL_W / (n - 1)
    out = VGroup()
    for i in idx:
        ya, yb = pa[i][1], pb[i][1]
        h = max(abs(ya - yb), 0.004)
        r = Rectangle(width=dx * 1.15, height=h, stroke_width=0, fill_color=color, fill_opacity=opacity)
        r.move_to([pa[i][0], (ya + yb) / 2, 0])
        r.h = h
        out.add(r)
    return out


def check_mark(color=GOOD, s=0.22, width=5):
    return VMobject(stroke_color=color, stroke_width=width).set_points_as_corners(
        [[-0.5 * s, 0.02 * s, 0], [-0.12 * s, -0.4 * s, 0], [0.6 * s, 0.5 * s, 0]])


class S07Autoencoder(TLScene):
    SID = "s07_autoencoder"

    def wait_until(self, t):
        if self.now > t + 0.02:
            print(f"[s07 late] at {self.now:.2f}s, beat was {t:.2f}s")
        super().wait_until(t)

    # ------------------------------------------------------------ network
    def build_network(self):
        layers = []
        for li, (x, n, g, r) in enumerate(zip(XS, SIZES, GAPS, RADII)):
            ys = (np.arange(n) - (n - 1) / 2) * g
            col = VGroup(*[
                Circle(radius=r, stroke_color=INK, stroke_width=1.6, stroke_opacity=0.9,
                       fill_color=WARN if li == BN else SIGNAL, fill_opacity=0).move_to([x, NET_Y - y, 0])
                for y in ys])
            layers.append(col)
        edges, xm = [], []
        for li in range(len(layers) - 1):
            for a in layers[li]:
                for b in layers[li + 1]:
                    pa, pb = a.get_center(), b.get_center()
                    d = (pb - pa) / np.linalg.norm(pb - pa)
                    e = Line(pa + d * RADII[li], pb - d * RADII[li + 1], stroke_width=0.9,
                             stroke_color=DIM, stroke_opacity=0.4)
                    edges.append(e)
                    xm.append((pa[0] + pb[0]) / 2)
        order = np.argsort(xm, kind="stable")
        edges = VGroup(*[edges[i] for i in order])
        self.edge_xm = np.array(xm)[order]
        self.layers = layers
        self.edges = edges
        self.nodes = VGroup(*layers)

        # glow around the bottleneck
        halos = VGroup()
        for n in layers[BN]:
            for k, (rr, op) in enumerate([(1.7, 0.16), (2.5, 0.08), (3.6, 0.04), (5.0, 0.02)]):
                c = Circle(radius=RADII[BN] * rr, stroke_width=0, fill_color=WARN, fill_opacity=op)
                c.move_to(n.get_center())
                c.base_op = op
                halos.add(c)
        self.halos = halos
        return edges, self.nodes, halos

    def set_acts(self, inp, out=None, seed=0):
        """Per-node activation levels for one pass: the input column shows |samples|."""
        rng = np.random.default_rng(seed)
        acts = []
        for li, n in enumerate(SIZES):
            if li == 0:
                acts.append(inp)
            elif li == len(SIZES) - 1:
                acts.append(out if out is not None else inp)
            elif li == BN:
                acts.append(0.65 + 0.35 * rng.random(n))
            else:
                acts.append(0.15 + 0.7 * rng.random(n))
        self.acts = acts

    @staticmethod
    def column_acts(a):
        idx = np.linspace(0, len(a) - 1, SIZES[0]).astype(int)
        v = np.abs(a[idx])
        return 0.15 + 0.8 * v / max(v.max(), 1e-6)

    def network_updater(self):
        front, gain, pcol = self.front, self.gain, self
        state = {"key": None}

        def upd(_m):
            f, g = front.get_value(), gain.get_value()
            key = (round(f, 4), round(g, 4), pcol.pulse_color)
            if key == state["key"]:
                return
            state["key"] = key
            bump = np.exp(-((self.edge_xm - f) / 0.38) ** 2) * g
            base = ManimColor(DIM)
            hot = ManimColor(pcol.pulse_color)
            for e, b in zip(self.edges, bump):
                e.set_stroke(color=interpolate_color(base, hot, min(1, b)), width=0.9 + 0.9 * b,
                             opacity=0.4 + 0.4 * b)
            for li, col in enumerate(self.layers):
                s = 1 / (1 + np.exp(-(f - XS[li]) / 0.1))
                for k, n in enumerate(col):
                    n.set_fill(opacity=float(self.acts[li][k] * s * g))
        return upd

    # ------------------------------------------------------------ helpers
    def fly_samples(self, a, center, color, run_time=0.9):
        """Dots leave the waveform and land on the input column."""
        idx = np.linspace(0, len(a) - 1, SIZES[0]).astype(int)
        pts = wave_points(a, center)
        dots = VGroup(*[Dot(pts[i], radius=0.045, color=color) for i in idx])
        targets = [n.get_center() for n in self.layers[0]]
        self.play(FadeIn(dots, scale=0.5), run_time=0.25)
        self.play(LaggedStart(*[d.animate(path_arc=-0.6).move_to(t).scale(0.6) for d, t in zip(dots, targets)],
                              lag_ratio=0.04),
                  self.front.animate.set_value(-3.15), run_time=run_time - 0.25, rate_func=smooth)
        self.remove(dots, *dots)

    def out_dots(self, rebuilt, center):
        idx = np.linspace(0, len(rebuilt) - 1, SIZES[-1]).astype(int)
        pts = wave_points(rebuilt, center)
        dots = VGroup(*[Dot(n.get_center(), radius=0.04, color=INK) for n in self.layers[-1]])
        return dots, [pts[i] for i in idx]

    # ------------------------------------------------------------ scene
    def construct(self):
        frame = self.camera.frame
        clock = ValueTracker(0)
        clock.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(clock)

        # gentle push-in for the whole network part
        frame.add_updater(lambda m, dt: m.scale(1 - 0.0016 * dt))
        self.add(frame)

        edges, nodes, halos = self.build_network()
        self.front = ValueTracker(-10)
        self.gain = ValueTracker(1)
        self.pulse_color = SIGNAL
        self.set_acts(self.column_acts(HEALTHY_WINDOWS[0]))

        glow_amt = ValueTracker(0)

        def halo_upd(m):
            t = clock.get_value()
            g = glow_amt.get_value()
            for i, c in enumerate(m):
                breathe = 1 + 0.12 * np.sin(TAU * t / 2.4 + 0.7 * (i // 4))
                c.set_fill(opacity=c.base_op * g * breathe)
        halos.add_updater(halo_upd)

        # ---- 1. the hourglass draws itself (0.5 - 3.5)
        self.wait_until(LEAD)
        node_anims = []
        for li in [0, 6, 1, 5, 2, 4, 3]:
            node_anims.append(LaggedStart(*[GrowFromCenter(n) for n in self.layers[li]], lag_ratio=0.06))
        self.add(halos)
        self.play(LaggedStart(*node_anims, lag_ratio=0.18), run_time=1.4)
        self.play(Create(edges, lag_ratio=0.004), run_time=1.2, rate_func=smooth)
        edges.add_updater(self.network_updater())
        self.play(glow_amt.animate.set_value(1.0), run_time=0.5)

        # ---- 2. healthy waveform in (3.84)
        self.wait_until(B("squeeze"))
        w0 = HEALTHY_WINDOWS[0]
        wave_in = wave(w0, LEFT_C, SIGNAL)
        base_l = Line(LEFT_C + LEFT * PANEL_W / 2, LEFT_C + RIGHT * PANEL_W / 2, stroke_color=FAINT, stroke_width=1.5)
        base_r = Line(RIGHT_C + LEFT * PANEL_W / 2, RIGHT_C + RIGHT * PANEL_W / 2, stroke_color=FAINT, stroke_width=1.5)
        self.play(Create(base_l), Create(base_r), Create(wave_in), run_time=0.85, rate_func=smooth)

        lbl_in = N("20,480", 30, DATA_C).move_to([XS[0], -3.0, 0])
        lbl_in_sub = T("5 × 4,096", 20, DIM).next_to(lbl_in, DOWN, buff=0.12)
        self.wait_until(B("twenty"))
        self.play(FadeIn(lbl_in, shift=UP * 0.15), FadeIn(lbl_in_sub, shift=UP * 0.1), run_time=0.5)

        # samples fly into the input column
        self.fly_samples(w0, LEFT_C, SIGNAL, run_time=1.0)

        # ---- 3. squeeze to the bottleneck (6.3)
        self.wait_until(B("through"))
        self.play(self.front.animate.set_value(0.05), run_time=1.2, rate_func=smooth)
        lbl_bn = N("64", 36, WARN).move_to([0, NET_Y - 1.3, 0])
        self.wait_until(B("sixtyfour") - 0.15)
        self.play(FadeIn(lbl_bn, scale=1.4), glow_amt.animate.set_value(2.2), run_time=0.45)
        self.play(glow_amt.animate.set_value(1.2), run_time=0.5)

        # ---- 4. rebuild (8.84)
        self.wait_until(B("rebuild"))
        lbl_out = N("20,480", 30, DIM).move_to([XS[-1], -3.0, 0])
        self.play(self.front.animate.set_value(3.75), FadeIn(lbl_out, shift=UP * 0.15), run_time=0.75, rate_func=smooth)
        r0 = rebuild_healthy(w0)
        dots, targets = self.out_dots(r0, RIGHT_C)
        rebuilt = wave(r0, RIGHT_C, INK, width=2.2)
        self.add(dots)
        self.play(LaggedStart(*[d.animate(path_arc=-0.6).move_to(t) for d, t in zip(dots, targets)], lag_ratio=0.04),
                  run_time=0.45)
        self.play(Create(rebuilt), *[FadeOut(d) for d in dots], run_time=0.45, rate_func=smooth)
        self.remove(dots, *dots)
        # the original arcs over the network and lands under the rebuild: they match
        ghost = wave_in.copy()
        self.play(ghost.animate(path_arc=-0.9).shift(RIGHT_C - LEFT_C).set_stroke(width=5, opacity=0.5),
                  run_time=0.65, rate_func=smooth)
        self.bring_to_front(rebuilt)
        tick = check_mark().move_to(RIGHT_C + UP * 1.05)
        self.play(Create(tick), rebuilt.animate.set_stroke(color=GOOD), run_time=0.4)

        # ---- 5. trained only on healthy cutting (11.18)
        self.wait_until(B("trained") + 0.35)
        healthy_lbl = T("healthy only", 30, GOOD)
        hl_tick = check_mark(s=0.3, width=6)
        hl = VGroup(hl_tick, healthy_lbl).arrange(RIGHT, buff=0.2).move_to([0, 3.05, 0])
        cur_in, cur_ghost, cur_reb = wave_in, ghost, rebuilt
        for k, w in enumerate(HEALTHY_WINDOWS[1:]):
            nw = wave(w, LEFT_C, SIGNAL)
            extra = [FadeIn(hl, shift=DOWN * 0.15), FadeOut(tick)] if k == 0 else []
            self.play(FadeTransform(cur_in, nw), self.gain.animate.set_value(0.0), *extra, run_time=0.16)
            self.set_acts(self.column_acts(w), seed=k + 3)
            self.front.set_value(-4.5)
            self.gain.set_value(1.0)
            self.play(self.front.animate.set_value(3.9), run_time=0.38, rate_func=linear)
            nr = wave(rebuild_healthy(w), RIGHT_C, INK)
            ng = wave(w, RIGHT_C, SIGNAL, width=5, opacity=0.5)
            self.play(FadeTransform(cur_reb, nr), FadeTransform(cur_ghost, ng), run_time=0.16)
            cur_in, cur_ghost, cur_reb = nw, ng, nr

        # ---- 6. a worn tool (13.96)
        self.wait_until(B("worn") - 0.2)
        self.pulse_color = HEAT
        wv = WORN_WINDOW
        worn_in = wave(wv, LEFT_C, HEAT)
        self.set_acts(self.column_acts(wv), out=self.column_acts(rebuild_worn(wv)), seed=11)
        self.front.set_value(-4.5)
        self.gain.set_value(1.0)
        self.play(Transform(cur_in, worn_in), FadeOut(cur_ghost), FadeOut(cur_reb),
                  hl.animate.set_opacity(0.45), run_time=0.5)
        self.play(self.front.animate.set_value(3.9), run_time=0.8, rate_func=smooth)
        rw = rebuild_worn(wv)
        rebuilt_w = wave(rw, RIGHT_C, INK)
        self.play(Create(rebuilt_w), run_time=0.4)
        worn_ghost = worn_in.copy()
        self.play(worn_ghost.animate(path_arc=-0.9).shift(RIGHT_C - LEFT_C), run_time=0.5, rate_func=smooth)
        self.bring_to_front(rebuilt_w)
        gap = gap_slivers(wv, rw, RIGHT_C)
        self.wait_until(B("fails") + 0.05)
        self.add(gap)
        self.bring_to_front(worn_ghost, rebuilt_w)
        self.play(gap.animate.set_fill(opacity=0.95), run_time=0.2)
        self.play(gap.animate.set_fill(opacity=0.6), run_time=0.35)

        # ---- 7. the size of that failure becomes a health score (16.52)
        self.wait_until(B("size"))
        edges.clear_updaters()
        halos.clear_updaters()
        frame.clear_updaters()
        net_stuff = VGroup(edges, nodes, halos, lbl_in, lbl_in_sub, lbl_bn, lbl_out, hl, cur_in,
                           base_l, base_r)
        p_end = ch(115 / 116, dict(HEALTH["8"])[0.9914])
        # the red slivers stack into one bar, standing where cycle 115 of cutter 8 sits on the chart
        bar_w, bar_h = 0.26, p_end[1] - CH_O[1]
        hs = np.array([r.h for r in gap])
        hs = hs / hs.sum() * bar_h
        y0 = CH_O[1]
        targets = []
        for h in hs:
            t = Rectangle(width=bar_w, height=h * 1.02, stroke_width=0, fill_color=DANGER, fill_opacity=0.9)
            t.move_to([p_end[0], y0 + h / 2, 0])
            targets.append(t)
            y0 += h

        # axes (log y)
        x_axis = Line(CH_O, CH_O + RIGHT * (CH_W + 0.2), stroke_color=DIM, stroke_width=2)
        y_axis = Line(CH_O, CH_O + UP * (CH_H + 0.15), stroke_color=DIM, stroke_width=2)
        ticks = VGroup()
        for v, s in [(1, "1×"), (2, "2×"), (5, "5×"), (10, "10×"), (20, "20×")]:
            p = ch(0, v)
            ticks.add(Line(p, p + LEFT * 0.1, stroke_color=DIM, stroke_width=2))
            ticks.add(N(s, 20, DIM).next_to(p + LEFT * 0.1, LEFT, buff=0.1))
        one_line = DashedLine(ch(0, 1), ch(1, 1), dash_length=0.08, stroke_color=FAINT, stroke_width=1.5)
        x_lbl = T("life used", 22, DIM).next_to(CH_O + RIGHT * CH_W, DOWN, buff=0.18).align_to(CH_O + RIGHT * CH_W, RIGHT)
        x_new = T("new", 22, DIM).next_to(CH_O, DOWN, buff=0.18).align_to(CH_O, LEFT)
        self.play(FadeOut(net_stuff), FadeOut(rebuilt_w), FadeOut(worn_ghost),
                  frame.animate.move_to(ORIGIN).set(width=config.frame_width),
                  LaggedStart(*[Transform(g, t) for g, t in zip(gap, targets)], lag_ratio=0.012),
                  Create(x_axis), Create(y_axis), run_time=1.1, rate_func=smooth)
        self.remove(*gap)
        self.add(gap)
        self.play(FadeIn(ticks), Create(one_line), FadeIn(x_lbl), FadeIn(x_new), run_time=0.4)

        # bar -> a point on a curve
        dot_end = Dot(p_end, radius=0.08, color=DANGER)
        h8 = np.array(HEALTH["8"])
        p_start = ch(h8[3, 0], h8[3, 1])
        dot_start = Dot(p_start, radius=0.08, color=GOOD)
        self.play(ReplacementTransform(gap, dot_end), FadeIn(dot_start, scale=2), run_time=0.45, rate_func=smooth)

        def curve(tool, color, width, opacity):
            a = np.array(HEALTH[tool])
            m = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity)
            m.set_points_as_corners([ch(f, v) for f, v in a])
            return m

        c8 = curve("8", SIGNAL, 3.2, 1.0)
        self.play(Create(c8), run_time=1.1, rate_func=smooth)
        self.add(dot_start, dot_end)

        others = VGroup(*[curve(t, SIGNAL, 1.6, 0.38) for t in HEALTH if t not in ("8", "10")])
        score_lbl = T("health score", 26, INK).next_to(CH_O + UP * (CH_H + 0.15), UP, buff=0.15).align_to(CH_O, LEFT).shift(LEFT * 0.4)
        self.wait_until(B("score") - 0.3)
        self.play(AnimationGroup(Create(others, lag_ratio=0.06, run_time=1.4),
                                 Succession(Wait(run_time=0.5), FadeIn(score_lbl, shift=DOWN * 0.1, run_time=0.45))))
        self.bring_to_front(c8, dot_start, dot_end)

        self.remove(frame)
        self.remove(clock)
        self.finish()
