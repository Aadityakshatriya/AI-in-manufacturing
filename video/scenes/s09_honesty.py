import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from style import *

ZOO = sorted(DATA["zoo"], key=lambda r: r["whole_life"])        # 31 models, best first
NAMES = [r["model"] for r in ZOO]
OURS = NAMES.index("TCN: physics features")
LC = DATA["learning_curve"]
# One-random-start spread of our TCN (from the brief). Drawn as a band, never printed as numbers.
NOISE_LO, NOISE_HI = 21.7, 24.1


def _wrap(a):
    return (a + PI) % TAU - PI


def _ss(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def _stairs(t0, moves, dwells):
    """Ring rotation vs time: one smooth step per hidden cutter, each followed by a dwell."""
    starts, t = [], t0
    for m, d in zip(moves, dwells):
        starts.append(t)
        t += m + d

    def f(t):
        r = 0.0
        for i, (s, m) in enumerate(zip(starts, moves)):
            if t <= s:
                break
            r = i + smooth(min((t - s) / m, 1.0))
        return r
    return f


def _camera_path(keys):
    """(t, cx, cy, width) keyframes -> smooth function of t."""
    def f(t):
        if t <= keys[0][0]:
            return keys[0][1:]
        for a, b in zip(keys, keys[1:]):
            if t <= b[0]:
                u = _ss((t - a[0]) / (b[0] - a[0]))
                return tuple(a[i] + (b[i] - a[i]) * u for i in (1, 2, 3))
        return keys[-1][1:]
    return f


class S09Honesty(TLScene):
    SID = "s09_honesty"

    def construct(self):
        frame = self.camera.frame
        T_race = self.cue(2)            # "We raced our network against thirty others"
        T_fam = self.cue(3)             # "trees, recurrent nets, transformers, convolutions on raw sound"
        cam = _camera_path([
            (0.0, 0.0, 0.2, 13.4), (3.1, 0.0, 0.25, 12.9),                   # the leak
            (4.0, -0.1, -0.1, 12.2), (T_race - 0.85, -0.1, -0.1, 11.6),        # the ring
            (T_race - 0.05, 0.0, 0.0, 14.5), (self.cue(5) + 0.15, 0.0, 0.0, 14.25),   # the race
            (self.cue(5) + 1.05, 0.0, 0.0, 14.0), (self.total, 0.3, 0.0, 13.4),     # the learning curve
        ])
        clock = ValueTracker(0.0)
        rtr = ValueTracker(0.0)          # ring rotation, in steps (one step = next cutter hidden)
        moves, dwells = np.linspace(0.22, 0.1, 12), np.linspace(0.12, 0.03, 12)
        t_steps = T_race - 1.08 - float(moves.sum() + dwells.sum())   # quick round of the ring, done before the race
        steps = _stairs(t_steps, moves, dwells)

        def tick(m, dt):  # dt keeps this a time-based updater; the clock itself is the renderer's
            t = self.renderer.time
            m.set_value(t)
            rtr.set_value(steps(t))
            cx, cy, w = cam(t)
            frame.set_width(w)
            frame.move_to([cx, cy, 0])

        clock.add_updater(tick)
        self.add(clock)
        tt = clock.get_value

        # ================= A. "Then we tried to fool ourselves, and caught it." =================
        Cc = np.array([-0.9, -0.15, 0.0])          # ring centre (beat B)
        R, D = 1.95, 1.3
        slot = Cc + RIGHT * (R + D)                 # where the hidden cutter sits

        cl_c = np.array([-2.6, 0.25, 0.0])
        train_pts = []
        for i in range(12):
            r = 0.98 * np.sqrt((i + 0.6) / 12.0)
            a = i * 2.39996 + 0.4
            train_pts.append(cl_c + np.array([1.2 * r * np.cos(a), r * np.sin(a), 0.0]))
        test_pt = np.array([2.7, 0.25, 0.0])
        dots = VGroup(*[Dot(p, radius=0.085, color=INK) for p in [test_pt] + train_pts])
        dots[0].set_color(WARN)

        ring_tr = DashedVMobject(Ellipse(width=3.4, height=2.7).move_to(cl_c), num_dashes=48)
        ring_tr.set_stroke(DIM, 1.6, 0.7)
        ring_te = DashedVMobject(Circle(radius=0.48).move_to(test_pt), num_dashes=16)
        ring_te.set_stroke(DIM, 1.6, 0.7)
        lab_train = T("train", 24, DIM).next_to(ring_tr, DOWN, buff=0.16)
        lab_test = T("test", 24, DIM).next_to(ring_te, DOWN, buff=0.16)

        tgt = max(train_pts, key=lambda p: p[0] - 0.5 * abs(p[1] - test_pt[1]))
        leak = ArcBetweenPoints(test_pt + LEFT * 0.14, tgt + RIGHT * 0.14, angle=0.85)
        leak.set_stroke(DANGER, 2.6)
        mid = leak.point_from_proportion(0.5)

        lk = ValueTracker(0.0)
        pulse = Dot(radius=0.05, color=WARN)

        def pulse_upd(m):
            f = (tt() * 0.9) % 1.0
            m.move_to(leak.point_from_proportion(f))
            m.set_opacity(lk.get_value() * np.sin(PI * f))
        pulse.add_updater(pulse_upd)

        lens_ring = Circle(radius=0.5).set_stroke(INK, 3.5).set_fill(SIGNAL, 0.07)
        hd = np.array([np.cos(-PI / 4), np.sin(-PI / 4), 0.0])
        handle = Line(0.5 * hd, 1.15 * hd).set_stroke(CARBIDE, 9)
        glint = Arc(radius=0.36, start_angle=PI * 0.58, angle=PI * 0.32).set_stroke(INK, 2)
        lens = VGroup(lens_ring, handle, glint)
        lpath = VMobject().set_points_smoothly([
            np.array([-5.6, -2.7, 0.0]), np.array([-3.9, -1.0, 0.0]), np.array([-2.6, 0.55, 0.0]),
            np.array([-0.9, 1.25, 0.0]), mid])
        lp, lo = ValueTracker(0.0), ValueTracker(0.0)

        def lens_upd(m):
            c = lpath.point_from_proportion(min(max(lp.get_value(), 0.0), 1.0))
            m.shift(c - m[0].get_center())
            o = lo.get_value()
            m[0].set_stroke(opacity=o).set_fill(opacity=0.07 * o)
            m[1].set_stroke(opacity=o)
            m[2].set_stroke(opacity=0.5 * o)
        lens.add_updater(lens_upd)
        leak_lab = T("leak", 26, DANGER).move_to(mid + UP * 0.82)

        self.wait_until(0.5)
        self.add(lens, pulse)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in dots[1:]], lag_ratio=0.05),
                  GrowFromCenter(dots[0]), Create(ring_tr), Create(ring_te),
                  FadeIn(lab_train, shift=UP * 0.1), FadeIn(lab_test, shift=UP * 0.1), run_time=0.7)
        self.play(Create(leak, run_time=0.5), lk.animate(run_time=0.4).set_value(1.0),
                  lp.animate(run_time=1.1, rate_func=smooth).set_value(1.0),
                  lo.animate(run_time=0.3).set_value(1.0), run_time=1.1)
        # the lens settles on the leak
        self.play(leak.animate.set_stroke(DANGER, 4.5), FadeIn(leak_lab, scale=0.8),
                  lens.animate.scale(1.08), run_time=0.3)
        self.wait_until(2.62)
        # cut it
        h1 = leak.copy().pointwise_become_partial(leak, 0.0, 0.5)
        h2 = leak.copy().pointwise_become_partial(leak, 0.5, 1.0)
        h2.reverse_points()
        lk.set_value(0.0)
        self.remove(leak)
        self.add(h1, h2)
        snap = Circle(radius=0.08).move_to(mid).set_stroke(INK, 3)
        self.play(Uncreate(h1), Uncreate(h2), snap.animate.scale(7).set_stroke(opacity=0),
                  leak_lab.animate.set_color(DIM), run_time=0.45)
        self.remove(snap, pulse)

        # ================= B. "We hid one whole cutter at a time ..." =================
        dtr, fin = ValueTracker(1.0), ValueTracker(0.0)

        def ring_state(k):
            a = TAU * (k - rtr.get_value()) / 13
            w = float(np.exp(-(_wrap(a) / 0.17) ** 2))
            r = R + D * w * dtr.get_value()
            return Cc + r * np.array([np.cos(a), np.sin(a), 0.0]), w

        ring0 = [ring_state(k)[0] for k in range(13)]
        self.play(*[d.animate.move_to(ring0[k]) for k, d in enumerate(dots)],
                  FadeOut(lens), FadeOut(leak_lab), FadeOut(ring_tr), FadeOut(ring_te),
                  FadeOut(lab_train), FadeOut(lab_test), run_time=0.85)
        lens.clear_updaters()
        self.remove(lens)

        c_ink, c_warn = ManimColor(INK), ManimColor(WARN)
        for k, d in enumerate(dots):
            def dupd(m, k=k):
                p, w = ring_state(k)
                m.move_to(p)
                m.set_color(interpolate_color(c_ink, c_warn, w * dtr.get_value()))
            d.add_updater(dupd)

        halos = VGroup(*[Circle(radius=0.17).set_stroke(SIGNAL, 1.8, 0.0) for _ in range(13)])
        for k, h in enumerate(halos):
            def hupd(m, k=k):
                m.move_to(ring_state(k)[0])
                j = float(np.clip((rtr.get_value() - k - 0.2) * 4, 0, 1))
                if k == 12:
                    j = max(j, fin.get_value())
                m.set_stroke(opacity=0.85 * j)
            h.add_updater(hupd)

        # the model box at the centre of the ring
        box = RoundedRectangle(width=1.3, height=1.0, corner_radius=0.14).move_to(Cc)
        box.set_stroke(SIGNAL, 2.4).set_fill(SIGNAL, 0.07)
        cols, xs_ = [3, 4, 3], [-0.3, 0.0, 0.3]
        layers = [[Cc + np.array([x, (j - (n - 1) / 2) * 0.1 + 0.13, 0.0]) for j in range(n)]
                  for n, x in zip(cols, xs_)]
        net_e = VGroup(*[Line(a, b).set_stroke(SIGNAL, 0.9, 0.5)
                         for L1, L2 in zip(layers, layers[1:]) for a in L1 for b in L2])
        net_n = VGroup(*[Dot(p, radius=0.03, color=INK) for L_ in layers for p in L_])
        box_lab = T("model", 20, DIM).move_to(Cc + DOWN * 0.27)
        model = VGroup(box, net_e, net_n, box_lab)

        def box_edge(p):
            v = p - Cc
            v[2] = 0.0
            u = v / max(np.linalg.norm(v), 1e-6)
            tb = min(0.65 / max(abs(u[0]), 1e-6), 0.5 / max(abs(u[1]), 1e-6))
            return Cc + u * (tb + 0.06)

        spk = ValueTracker(0.0)
        spokes = VGroup(*[Line(LEFT, RIGHT).set_stroke(SIGNAL, 1.2, 0.0) for _ in range(13)])
        for k, s_ in enumerate(spokes):
            def supd(m, k=k):
                p, w = ring_state(k)
                e = box_edge(p)
                u = (e - p) / np.linalg.norm(e - p)
                m.put_start_and_end_on(p + u * 0.13, e)
                m.set_stroke(opacity=0.3 * spk.get_value() * (1 - w))
            s_.add_updater(supd)
        parts = VGroup()
        for k in range(13):
            for ph in (0.0, 0.5):
                pd = Dot(radius=0.032, color=SIGNAL)

                def pupd(m, k=k, ph=ph + 0.13 * k):
                    p, w = ring_state(k)
                    e = box_edge(p)
                    f = (tt() * 0.75 + ph) % 1.0
                    m.move_to(p + (e - p) * f)
                    m.set_opacity(spk.get_value() * (1 - w) * np.sin(PI * f) * 0.95)
                pd.add_updater(pupd)
                parts.add(pd)

        veil = RoundedRectangle(width=0.64, height=0.64, corner_radius=0.12).move_to(slot)
        veil.set_stroke(width=0).set_fill("#151A22", 0.84).set_z_index(3)
        veil_edge = DashedVMobject(RoundedRectangle(width=0.64, height=0.64, corner_radius=0.12).move_to(slot),
                                   num_dashes=20).set_stroke(WARN, 2).set_z_index(4)
        hid_lab = T("hidden", 24, WARN).next_to(veil, UP, buff=0.18)

        gsh = ValueTracker(0.0)

        def guess_level():
            w0 = max(ring_state(k)[1] for k in range(13))
            return gsh.get_value() * _ss((w0 - 0.55) / 0.45)

        beam = Line(Cc + RIGHT * 0.7, slot + LEFT * 0.38).set_stroke(SIGNAL, 2.6, 0.0)
        beam.add_updater(lambda m: m.set_stroke(opacity=0.85 * guess_level()))
        beam_tips = VGroup(*[Dot(radius=0.045, color=SIGNAL) for _ in range(2)])
        for i, bt in enumerate(beam_tips):
            def btupd(m, i=i):
                f = (tt() * 1.5 + 0.5 * i) % 1.0
                m.move_to(beam.point_from_proportion(f))
                m.set_opacity(guess_level() * np.sin(PI * f))
            bt.add_updater(btupd)
        veil_edge.add_updater(lambda m: m.set_stroke(
            interpolate_color(c_warn, ManimColor(SIGNAL), 0.6 * guess_level() * (0.5 + 0.5 * np.sin(tt() * 9)))))

        self.add(spokes, parts, halos, beam, beam_tips)
        self.play(Create(box), FadeIn(net_e), LaggedStart(*[GrowFromCenter(n_) for n_ in net_n], lag_ratio=0.05),
                  FadeIn(box_lab), run_time=0.5)
        self.play(FadeIn(veil, shift=DOWN * 0.25), Create(veil_edge), FadeIn(hid_lab, shift=DOWN * 0.1), run_time=0.4)
        self.play(spk.animate.set_value(1.0), run_time=0.5)
        self.play(gsh.animate.set_value(1.0), run_time=0.4)
        self.wait_until(T_race - 1.05)   # the ring turns by itself (steps schedule in tick)
        self.play(dtr.animate.set_value(0.0), fin.animate.set_value(1.0), gsh.animate.set_value(0.0),
                  FadeOut(veil), FadeOut(veil_edge), FadeOut(hid_lab), run_time=0.35)

        # ================= C. "We raced our network against thirty others" =================
        x0, sc = -4.15, 0.262
        ytop, dy, bh = 3.15, 0.2017, 0.128
        ys = [ytop - i * dy for i in range(len(ZOO))]

        def X(v):
            return x0 + sc * v

        base = Line([x0, ytop + 0.16, 0], [x0, ys[-1] - 0.24, 0]).set_stroke(DIM, 2)
        ax_y = ys[-1] - 0.24
        axis = Line([x0, ax_y, 0], [X(36), ax_y, 0]).set_stroke(DIM, 1.6)
        ticks = VGroup(*[Line([X(v), ax_y, 0], [X(v), ax_y - 0.07, 0]).set_stroke(DIM, 1.6) for v in (0, 10, 20, 30)])
        tnums = VGroup(*[N(str(v), 18, DIM).next_to([X(v), ax_y - 0.07, 0], DOWN, buff=0.07) for v in (0, 10, 20, 30)])
        cap = T("error, cycles", 20, DIM).next_to([X(36), tnums[0].get_bottom()[1], 0], DOWN, buff=0.1,
                                                   aligned_edge=RIGHT)
        better = T("← better", 18, DIM).move_to([X(5), tnums[0].get_y(), 0])

        # the few bars that get a name: a label column left of the chart, with leader lines
        named = {OURS: "ours",
                 NAMES.index("Zoo: Causal transformer"): "transformer",
                 NAMES.index("LightGBM: 120 summaries only"): "LightGBM",
                 NAMES.index("Zoo: LSTM"): "LSTM",
                 NAMES.index("Zoo: GRU"): "GRU",
                 NAMES.index("Zoo: Random forest"): "random forest",
                 NAMES.index("Zoo: 1-D CNN on raw table vibration"): "raw-sound CNN"}
        rows_n = sorted(named)
        ly = [ys[i] for i in rows_n]
        for _ in range(200):          # spread labels to a minimum gap
            for j in range(len(ly) - 1):
                g = ly[j] - ly[j + 1]
                if g < 0.33:
                    ly[j] += (0.33 - g) / 2
                    ly[j + 1] -= (0.33 - g) / 2
        lab_y = dict(zip(rows_n, ly))

        def name_label(i, color):
            txt = T(named[i], 20, color).next_to([x0 - 0.5, lab_y[i], 0], LEFT, buff=0.08)
            lead = Line([x0 - 0.48, lab_y[i], 0], [x0 - 0.06, ys[i], 0]).set_stroke(color, 1.2, 0.6)
            return VGroup(txt, lead)

        ours_lab = name_label(OURS, SIGNAL)

        vt = ValueTracker(0.0)
        bars, tips = VGroup(), VGroup()
        for i, r in enumerate(ZOO):
            val, y = r["whole_life"], ys[i]
            col, op = (SIGNAL, 1.0) if i == OURS else (STEEL, 0.5)
            b = Rectangle(width=0.01, height=bh).set_stroke(width=0).set_fill(col, op)

            def bupd(m, val=val, y=y):
                w = max(0.004, sc * min(vt.get_value(), val))
                m.set_points_as_corners([[x0, y + bh / 2, 0], [x0 + w, y + bh / 2, 0], [x0 + w, y - bh / 2, 0],
                                         [x0, y - bh / 2, 0], [x0, y + bh / 2, 0]])
            b.add_updater(bupd)
            bupd(b)
            tip = Dot(radius=0.05, color=INK if i != OURS else SIGNAL)

            def tupd(m, val=val, y=y):
                v = vt.get_value()
                m.move_to([X(min(v, val)), y, 0])
                o = 1.0 if v < val else max(0.0, 1 - (v - val) / 3)
                m.set_opacity(o if v > 0.05 else 0.0)
            tip.add_updater(tupd)
            bars.add(b)
            tips.add(tip)
        ours_val = N(f"{ZOO[OURS]['whole_life']:.1f}", 18, SIGNAL).next_to([X(ZOO[OURS]["whole_life"]), ys[OURS], 0],
                                                                           RIGHT, buff=0.14)
        ours_val.add_updater(lambda m: m.set_opacity(float(np.clip((vt.get_value() - ZOO[OURS]["whole_life"]) / 1.5, 0, 1))))
        ours_val.set_opacity(0)

        ring_stuff = VGroup(dots, halos, spokes, parts, beam, beam_tips)
        for m in ring_stuff.get_family():   # the ring is at rest now; freeze it so the fade wins
            m.clear_updaters()
        self.play(FadeOut(ring_stuff, scale=0.85), FadeOut(VGroup(box, net_e, net_n, box_lab), scale=0.85),
                  FadeIn(ours_lab, shift=RIGHT * 0.15),
                  Create(base), Create(axis), FadeIn(ticks), FadeIn(tnums), FadeIn(cap), FadeIn(better),
                  run_time=0.7)
        for m in ring_stuff.get_family():
            m.clear_updaters()
        self.remove(ring_stuff)
        self.add(bars, tips, ours_val)
        self.wait_until(T_race)
        self.play(vt.animate.set_value(35.0), run_time=2.0, rate_func=linear)
        for m in [*bars, *tips, ours_val]:
            m.clear_updaters()
        self.remove(tips)

        # "trees, recurrent nets, transformers, convolutions on raw sound"
        trees = [i for i, nm in enumerate(NAMES) if "LightGBM" in nm or "Random forest" in nm]
        fams = [
            (T_fam + 0.05, trees, {NAMES.index("LightGBM: 120 summaries only"): "LightGBM",
                            NAMES.index("Zoo: Random forest"): "random forest"}),
            (T_fam + 0.8, [NAMES.index("Zoo: LSTM"), NAMES.index("Zoo: GRU")],
             {NAMES.index("Zoo: LSTM"): "LSTM", NAMES.index("Zoo: GRU"): "GRU"}),
            (T_fam + 2.03, [NAMES.index("Zoo: Causal transformer")], {NAMES.index("Zoo: Causal transformer"): "transformer"}),
            (T_fam + 3.11, [NAMES.index("Zoo: 1-D CNN on raw table vibration")],
             {NAMES.index("Zoo: 1-D CNN on raw table vibration"): "raw-sound CNN"}),
        ]
        prev_rows, prev_labs, all_labs = [], [], VGroup()
        for t0, rows, labs in fams:
            self.wait_until(t0)
            new_labs = [name_label(i, WARN) for i in labs]
            all_labs.add(*new_labs)
            self.play(*[bars[i].animate.set_fill(STEEL, 0.5) for i in prev_rows if i not in rows],
                      *[l_.animate.set_color(DIM) for l_ in prev_labs],
                      *[bars[i].animate.set_fill(WARN, 0.95) for i in rows],
                      *[FadeIn(l_, shift=RIGHT * 0.12) for l_ in new_labs], run_time=0.22)
            prev_rows, prev_labs = rows, new_labs
        self.wait_until(self.cue_end(3) - 0.2)
        self.play(*[bars[i].animate.set_fill(STEEL, 0.5) for i in prev_rows],
                  *[l_.animate.set_color(DIM) for l_ in prev_labs], run_time=0.4)

        # "The good ones finished within the noise of each other."
        btop, bbot = ytop + 0.2, ys[-1] - 0.12
        band = Rectangle(width=sc * (NOISE_HI - NOISE_LO), height=btop - bbot).set_stroke(width=0)
        band.set_fill(SIGNAL, 0.13).move_to([X((NOISE_LO + NOISE_HI) / 2), (btop + bbot) / 2, 0])
        edges = VGroup(*[DashedLine([X(v), btop, 0], [X(v), bbot, 0], dash_length=0.06).set_stroke(SIGNAL, 1.5, 0.7)
                         for v in (NOISE_LO, NOISE_HI)])
        noise_lab = T("noise", 24, SIGNAL).next_to(band, UP, buff=0.1)
        self.wait_until(self.cue(4))
        self.play(GrowFromEdge(band, UP), Create(edges), FadeIn(noise_lab, shift=DOWN * 0.1), run_time=0.8)
        good = [i for i, r in enumerate(ZOO) if r["whole_life"] <= NOISE_HI]
        self.wait_until(self.cue(4) + 1.05)
        self.play(*[bars[i].animate.set_fill(INK, 0.92) for i in good if i != OURS],
                  *[bars[i].animate.set_fill(STEEL, 0.2) for i in range(len(ZOO)) if i not in good],
                  band.animate.set_fill(SIGNAL, 0.2), run_time=0.6)

        # ================= D. "With thirteen cutters, the limit is not the model." =================
        ax = Axes(x_range=[0, 16, 1], y_range=[0, 45, 5], x_length=8.6, y_length=5.0, tips=False,
                  axis_config={"stroke_color": DIM, "stroke_width": 2, "include_ticks": False})
        ax.shift(np.array([-4.7, -2.55, 0]) - ax.c2p(0, 0))
        ns = [r["n_train"] for r in LC]
        P = [ax.c2p(r["n_train"], r["whole_life_mean"]) for r in LC]
        xt = VGroup(*[Line(ax.c2p(n, 0), ax.c2p(n, 0) + DOWN * 0.08).set_stroke(DIM, 2) for n in ns])
        xn = VGroup(*[N(str(n), 22, DIM).next_to(ax.c2p(n, 0) + DOWN * 0.08, DOWN, buff=0.08) for n in ns])
        xcap = T("training cutters", 22, DIM).next_to([ax.c2p(16, 0)[0], xn.get_bottom()[1], 0], DOWN, buff=0.1,
                                                      aligned_edge=RIGHT)
        ycap = T("error", 22, DIM).next_to(ax.c2p(0, 45), UP, buff=0.12)
        whisk = VGroup()
        for r in LC:
            if r["whole_life_max"] - r["whole_life_min"] < 0.05:
                continue
            a_, b_ = ax.c2p(r["n_train"], r["whole_life_min"]), ax.c2p(r["n_train"], r["whole_life_max"])
            whisk.add(VGroup(Line(a_, b_), Line(a_ + LEFT * 0.07, a_ + RIGHT * 0.07),
                             Line(b_ + LEFT * 0.07, b_ + RIGHT * 0.07)).set_stroke(SIGNAL, 1.8, 0.45))
        curve = VMobject().set_points_as_corners(P).set_stroke(SIGNAL, 4)
        pdots = VGroup(*[Dot(p, radius=0.075, color=SIGNAL) for p in P])
        v_first = N(f"{LC[0]['whole_life_mean']:.1f}", 22, SIGNAL).next_to(P[0], LEFT, buff=0.18)
        v_last = N(f"{LC[-1]['whole_life_mean']:.1f}", 22, SIGNAL).next_to(P[-1], UR, buff=0.12)

        ours_bar = bars[OURS]
        travel = Dot([X(ZOO[OURS]["whole_life"]), ys[OURS], 0], radius=0.075, color=SIGNAL)
        others = VGroup(*[b for i, b in enumerate(bars) if i != OURS])
        chart_rest = VGroup(others, all_labs, band, edges, noise_lab, base, axis, ticks, tnums, cap, better, ours_val)
        self.wait_until(self.cue(5) - 0.24)
        self.play(FadeOut(chart_rest), ours_bar.animate.stretch_to_fit_width(0.01, about_edge=RIGHT),
                  FadeIn(travel), FadeOut(ours_lab), run_time=0.55)
        self.remove(ours_bar, ours_lab)
        self.play(travel.animate.move_to(P[-1]), Create(ax), FadeIn(xt), FadeIn(xn, shift=UP * 0.1),
                  FadeIn(xcap), FadeIn(ycap), run_time=0.9)
        self.wait_until(self.cue(5) + 1.26)
        self.add(curve, pdots[:-1])
        for d in pdots[:-1]:
            d.scale(0.01)
        self.play(Create(curve, rate_func=linear),
                  LaggedStart(*[d.animate.scale(100) for d in pdots[:-1]], lag_ratio=0.6),
                  LaggedStart(*[FadeIn(w_) for w_ in whisk], lag_ratio=0.6),
                  FadeIn(v_first, run_time=0.5), run_time=1.6)
        self.play(FadeIn(v_last, shift=LEFT * 0.1), Indicate(travel, color=SIGNAL, scale_factor=1.5), run_time=0.6)

        # ================= E. "It is the data." =================
        slope = (LC[-1]["whole_life_mean"] - LC[-2]["whole_life_mean"]) / (LC[-1]["n_train"] - LC[-2]["n_train"])
        n_end = 15.2
        end = ax.c2p(n_end, LC[-1]["whole_life_mean"] + slope * (n_end - LC[-1]["n_train"]))
        dash = DashedLine(P[-1], end, dash_length=0.12).set_stroke(DATA_C, 3.5)
        u = (end - P[-1]) / np.linalg.norm(end - P[-1])
        pv = np.array([-u[1], u[0], 0.0])
        head = Polygon(end + u * 0.2, end + pv * 0.09, end - pv * 0.09).set_stroke(width=0).set_fill(DATA_C, 1)
        more = T("more cutters", 28, DATA_C).next_to(end + u * 0.2, DR, buff=0.1)
        self.wait_until(self.cue(6) - 0.04)
        self.play(Create(dash), FadeIn(head, run_time=0.3), run_time=0.75)
        self.play(FadeIn(more, shift=UP * 0.1), run_time=0.4)

        self.remove(*[m for m in self.mobjects if isinstance(m, ValueTracker)])
        self.finish()
