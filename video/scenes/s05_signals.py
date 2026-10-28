"""s05_signals — the machine feels the wear: fog over the edge, a schematic machine waking up, the real
table-motor current curves (x2.7), the real vibration waveform and spectrum of cutter 8 (new -> worn), the
once-per-turn beat, and a chipped tooth beating in time with it."""

import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from style import *  # noqa: F401,F403

DEG = PI / 180


def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def ramp(t, t0, t1):
    return smooth01((t - t0) / max(t1 - t0, 1e-6))


def mix(a, b, t):
    return ManimColor(a).interpolate(ManimColor(b), float(np.clip(t, 0, 1)))


def redraw(func):
    """Like always_redraw, but swaps in the freshly built children each frame instead of morphing the old
    ones (always_redraw's family alignment glitches when the number of parts changes between frames)."""
    holder = VGroup(func())

    def upd(m):
        m.remove(*m.submobjects)
        m.add(func())

    holder.add_updater(upd)
    return holder


def P(x, y):
    return np.array([x, y, 0.0])


# --------------------------------------------------------------------------- shared geometry (s05 -> s06)
WX0, WX1, WY, WA = -4.7, 6.2, 1.85, 0.42      # waveform strip
SX0, SX1, SY, SH = -4.7, 6.2, -3.0, 3.0       # spectrum
FMAX = 1100.0
SPEC_REF = 1055.6                              # worn tooth peak, sqrt scale reference


def wave_points(vals, n_show=None):
    v = np.asarray(vals)
    n = len(v)
    xs = WX0 + np.arange(n) / (n - 1) * (WX1 - WX0)
    ys = WY + WA * v
    k = n if n_show is None else max(2, int(n_show))
    return [P(x, y) for x, y in zip(xs[:k], ys[:k])]


def wave_xy(i, vals):
    n = len(vals)
    return P(WX0 + i / (n - 1) * (WX1 - WX0), WY + WA * vals[int(i)])


def spec_x(f):
    return SX0 + f / FMAX * (SX1 - SX0)


def spec_y(m):
    return SY + SH * np.sqrt(max(m, 0.0) / SPEC_REF)


from manim.utils.family import extract_mobject_family_members as _fam
from manim.utils.iterables import list_update as _list_update


class LiveFamilies:
    """Scene mixin: hand the camera the moving *top-level* mobjects so their current children are drawn
    each frame. (Manim's default flattens families once per play(), so children swapped in by redraw()
    would be drawn stale.)"""

    def get_moving_and_static_mobjects(self, animations):
        tops = _list_update(self.mobjects, self.foreground_mobjects)
        z = self.renderer.camera.use_z_index
        flat = self.get_moving_mobjects(*animations)
        if not flat:
            return [], _fam(tops, use_z_index=z, only_those_with_points=True)
        first = flat[0]
        idx = next((i for i, m in enumerate(tops) if first in m.get_family()), 0)
        return tops[idx:], _fam(tops[:idx], use_z_index=z, only_those_with_points=True)


class S05Signals(LiveFamilies, TLScene):
    SID = "s05_signals"

    def construct(self):
        clock = ValueTracker(0.0)
        # renderer.time advances once per written frame; the tracker mirrors it so cached
        # partial movies are invalidated when timing changes
        clock.add_updater(lambda m, dt: m.set_value(self.renderer.time))
        self.add(clock)
        tnow = lambda: self.renderer.time
        c = self.cue
        TOTAL = self.total
        rng = np.random.default_rng(11)

        # =========================================================== machine (drawn in "machine space")
        # mt: 0 = close-up in the fog, 1 = full machine, 2 = small icon on the left
        mt = ValueTracker(0.0)
        P_CUT = P(0.2, -0.1)
        P_CEN = P(0.45, 0.78)
        keys = [(2.3, P(0, -0.1) - 2.3 * P_CUT), (1.0, P(0, 0.05) - P_CEN), (0.38, P(-5.25, 0.15) - 0.38 * P_CEN)]
        refs = [P_CUT, P_CEN]

        def mxf():
            u = float(np.clip(mt.get_value(), 0, 2 - 1e-9))
            k = int(u)
            f = u - k
            (s0, o0), (s1, o1) = keys[k], keys[k + 1]
            s = s0 ** (1 - f) * s1 ** f
            pr = refs[k]
            scr = (o0 + s0 * pr) * (1 - f) + (o1 + s1 * pr) * f
            return s, scr - s * pr

        def M(p):
            s, o = mxf()
            return o + s * np.asarray(p)

        vis_core = ValueTracker(0.0)     # cutter, workpiece, table
        cut_bright = ValueTracker(0.35)  # the cutter is dim in the fog
        vis_mach = ValueTracker(0.0)     # the rest of the machine
        vis_lab = ValueTracker(0.0)
        wake = ValueTracker(0.0)         # meter needles
        tmotor = ValueTracker(0.0)       # table motor working harder
        sens_on = ValueTracker(0.0)
        mach_fade = ValueTracker(1.0)    # whole-machine fade at the vibration beat

        def rect(x0, y0, x1, y1, stroke, fill, fop, op, sw=1.8):
            pts = [M(P(x0, y0)), M(P(x1, y0)), M(P(x1, y1)), M(P(x0, y1))]
            r = Polygon(*pts, color=stroke, stroke_width=sw)
            r.set_stroke(opacity=op).set_fill(fill, opacity=fop * op)
            return r

        def gauge(cx, cy, ang, op):
            s, _ = mxf()
            g = VGroup()
            arc = Arc(radius=0.3 * s, start_angle=20 * DEG, angle=140 * DEG, arc_center=M(P(cx, cy)),
                      stroke_width=2, color=DIM).set_stroke(opacity=op)
            ticks = VGroup(*[Line(M(P(cx + 0.24 * np.cos(a), cy + 0.24 * np.sin(a))),
                                  M(P(cx + 0.3 * np.cos(a), cy + 0.3 * np.sin(a))), stroke_width=1.5, color=DIM)
                             .set_stroke(opacity=op) for a in np.linspace(20 * DEG, 160 * DEG, 5)])
            nd = Line(M(P(cx, cy)), M(P(cx + 0.27 * np.cos(ang), cy + 0.27 * np.sin(ang))), stroke_width=2.4,
                      color=INK).set_stroke(opacity=op)
            pv = Dot(M(P(cx, cy)), radius=0.035 * s, color=INK).set_fill(opacity=op)
            g.add(arc, ticks, nd, pv)
            return g

        SENSORS = [P(-1.95, -0.62), P(1.35, -1.2), P(-1.25, -1.2)]

        def make_machine():
            t = tnow()
            s, _ = mxf()
            fade = mach_fade.get_value()
            vc = vis_core.get_value() * fade
            vm = vis_mach.get_value() * fade
            g = VGroup()
            if vm > 0.005:
                g.add(rect(-3.2, -2.3, 2.8, -1.55, DIM, mix(BG, STEEL, 0.10), 1.0, vm))     # base
                g.add(rect(-3.2, -1.55, -2.4, 3.05, DIM, mix(BG, STEEL, 0.10), 1.0, vm))    # column
                g.add(rect(-2.4, 2.2, 0.95, 3.05, DIM, mix(BG, STEEL, 0.10), 1.0, vm))      # arm
                g.add(rect(-0.35, 3.05, 0.75, 3.85, STEEL, mix(BG, STEEL, 0.16), 1.0, vm))  # spindle motor
                g.add(Circle(radius=0.22 * s, color=STEEL, stroke_width=1.8).move_to(M(P(0.2, 3.45)))
                      .set_stroke(opacity=vm))
                g.add(T("M", size=20, color=STEEL).scale(s).move_to(M(P(0.2, 3.45))).set_opacity(vm))
                g.add(rect(-0.15, 1.0, 0.55, 2.2, STEEL, mix(BG, STEEL, 0.14), 1.0, vm))    # spindle housing
                # lead screw + table motor
                hot = tmotor.get_value()
                g.add(Line(M(P(2.6, -1.38)), M(P(3.15, -1.38)), stroke_width=2, color=STEEL).set_stroke(opacity=vm))
                zz = [M(P(2.62 + 0.06 * j, -1.38 + (0.07 if j % 2 else -0.07))) for j in range(9)]
                g.add(VMobject(stroke_width=1.2, color=DIM).set_points_as_corners(zz).set_stroke(opacity=vm))
                if hot > 0.01:
                    pulse = 0.5 + 0.5 * np.sin(TAU * 1.6 * t)
                    g.add(RoundedRectangle(width=1.25 * s, height=1.1 * s, corner_radius=0.12 * s, stroke_width=0)
                          .move_to(M(P(3.6, -1.38))).set_fill(HEAT, opacity=(0.10 + 0.08 * pulse) * hot * vm))
                g.add(rect(3.15, -1.75, 4.05, -1.0, mix(STEEL, HEAT, hot), mix(BG, STEEL, 0.16), 1.0, vm))
                g.add(Circle(radius=0.2 * s, color=mix(STEEL, HEAT, hot), stroke_width=1.8)
                      .move_to(M(P(3.6, -1.38))).set_stroke(opacity=vm))
                g.add(T("M", size=18, color=mix(STEEL, HEAT, hot)).scale(s).move_to(M(P(3.6, -1.38)))
                      .set_opacity(vm))
                # meters
                wk = wake.get_value()
                a_sp = 160 * DEG - wk * (62 * DEG + 5 * DEG * np.sin(TAU * 2.3 * t) + 3 * DEG * np.sin(TAU * 5.1 * t))
                a_tb = 160 * DEG - wk * (45 * DEG + 85 * DEG * hot + 4 * DEG * np.sin(TAU * 3.1 * t + 1))
                g.add(gauge(1.45, 3.45, a_sp, vm))
                g.add(gauge(3.6, -0.5, a_tb, vm))
            if vc > 0.005:
                feed = 0.05 * np.sin(TAU * 0.35 * t)
                g.add(rect(-2.3 + feed, -1.55, 2.6 + feed, -1.2, STEEL, mix(BG, STEEL, 0.20), 1.0, vc))   # table
                g.add(rect(-1.9 + feed, -1.2, 0.12, -0.05, STEEL, mix(BG, STEEL, 0.34), 1.0, vc))          # workpiece
                cb = cut_bright.get_value()
                g.add(rect(0.06, -0.4, 0.34, 1.0, CARBIDE, CARBIDE, 0.22, vc * cb))                        # cutter
                ph = (t * 3.0) % 1.0
                for j in range(6):
                    ya = 0.45 - (j + ph) * 0.15
                    yb = ya - 0.13
                    if yb < -0.4:
                        continue
                    g.add(Line(M(P(0.06, ya)), M(P(0.34, yb)), stroke_width=1.4, color=CARBIDE)
                          .set_stroke(opacity=0.7 * vc * cb))
            return g

        machine = redraw(make_machine)

        def make_sensors():
            t = tnow()
            s, _ = mxf()
            v = vis_mach.get_value() * mach_fade.get_value()
            g = VGroup()
            if v < 0.005:
                return g
            so = sens_on.get_value()
            for k, p in enumerate(SENSORS):
                q = M(p)
                g.add(Dot(q, radius=0.075 * s, color=SIGNAL).set_fill(opacity=v))
                if so > 0.01:
                    ph = (t * 1.3 + k * 0.33) % 1.0
                    g.add(Circle(radius=(0.08 + 0.35 * ph) * s, color=SIGNAL, stroke_width=1.6)
                          .move_to(q).set_stroke(opacity=(1 - ph) * 0.8 * so * v))
            return g

        sensors = redraw(make_sensors)

        def make_labels():
            v = vis_lab.get_value() * mach_fade.get_value()
            s, _ = mxf()
            g = VGroup()
            if v < 0.005:
                return g
            g.add(T("table motor", size=22, color=mix(DIM, HEAT, tmotor.get_value())).scale(s)
                  .move_to(M(P(3.75, -2.05))).set_opacity(v))
            g.add(T("sensors", size=22, color=SIGNAL).scale(s).move_to(M(P(-1.0, 0.35))).set_opacity(v))
            return g

        labels = redraw(make_labels)

        # fog of chips and coolant around the cutting point
        NF = 230
        fr = np.sqrt(rng.uniform(0.0, 1.0, NF)) * 1.9
        fa = rng.uniform(0, TAU, NF)
        fz = rng.uniform(0.012, 0.05, NF)
        fo = rng.uniform(0.15, 0.55, NF)
        fw = rng.uniform(0.3, 0.9, NF)
        fcol = [rng.choice([DIM, STEEL, STEEL, SIGNAL, HEAT], p=[0.35, 0.3, 0.15, 0.12, 0.08]) for _ in range(NF)]
        NB = 26
        br = np.sqrt(rng.uniform(0.0, 1.0, NB)) * 1.4
        ba = rng.uniform(0, TAU, NB)
        bz = rng.uniform(0.25, 0.6, NB)
        fog_in = ValueTracker(0.0)
        fog_out = ValueTracker(0.0)
        fog = VGroup(*[Dot(radius=1.0, color=fcol[i]) for i in range(NF)],
                     *[Dot(radius=1.0, color=STEEL) for _ in range(3 * NB)])

        def upd_fog(g, dt):
            t = tnow()
            s, _ = mxf()
            fi, fo_ = fog_in.get_value(), fog_out.get_value()
            vis = fi * (1 - smooth01(fo_ * 1.3))
            push = 1 + 2.6 * fo_ ** 1.6
            for i in range(NF):
                fa[i] += fw[i] * dt * (0.8 / (0.4 + fr[i]))
                r = fr[i] * push + 0.06 * np.sin(1.7 * t + i)
                p = P_CUT + P(r * np.cos(fa[i]) * 1.15, r * np.sin(fa[i]) * 0.85 + 0.15)
                d = g[i]
                d.scale_to_fit_width(2 * fz[i] * s)
                d.move_to(M(p))
                d.set_fill(opacity=fo[i] * vis)
            for j in range(NB):
                ba[j] += 0.25 * dt
                r = br[j] * push
                p = P_CUT + P(r * np.cos(ba[j]), r * np.sin(ba[j]) * 0.8 + 0.1)
                for q, fr_ in enumerate((1.0, 0.68, 0.4)):      # three nested discs = a soft puff
                    d = g[NF + 3 * j + q]
                    d.scale_to_fit_width(2 * bz[j] * fr_ * s)
                    d.move_to(M(p))
                    d.set_fill(opacity=0.022 * vis)

        fog.add_updater(upd_fog)

        self.add(machine, sensors, labels, fog)

        # ---- A: we cannot see the edge
        self.play(vis_core.animate.set_value(1.0), fog_in.animate.set_value(1.0), run_time=1.0)
        self.wait_until(c(1) - 0.05)
        # ---- B: but the machine can feel it
        self.play(mt.animate(rate_func=smooth).set_value(1.0), fog_out.animate.set_value(1.0),
                  cut_bright.animate.set_value(1.0), vis_mach.animate(rate_func=lambda a: smooth01((a - 0.25) / 0.6)).set_value(1.0),
                  run_time=1.6)
        self.remove(fog)
        self.play(wake.animate.set_value(1.0), sens_on.animate.set_value(1.0), vis_lab.animate.set_value(1.0),
                  run_time=0.8)
        self.wait_until(c(2))
        # ---- C: the table motor works harder
        self.play(tmotor.animate.set_value(1.0), run_time=0.7)
        self.play(mt.animate(rate_func=smooth).set_value(2.0), vis_lab.animate.set_value(0.0), run_time=0.9)

        # table current plot (real data, 12 normal-holder cutters)
        ax = Axes(x_range=[0, 1, 0.25], y_range=[0.6, 3.2, 0.5], x_length=8.4, y_length=4.7, tips=False,
                  axis_config={"color": DIM, "stroke_width": 2, "include_ticks": False})
        ax.move_to(P(1.95, -0.2))
        grid = VGroup()
        for yv in (1, 2, 3):
            ln = DashedLine(ax.c2p(0, yv), ax.c2p(1, yv), dash_length=0.07, dashed_ratio=0.45,
                            stroke_width=1.3 if yv > 1 else 1.8, color=FAINT if yv > 1 else DIM)
            grid.add(ln)
        ylabs = VGroup(*[N(f"×{yv}", size=24, color=DIM).next_to(ax.c2p(0, yv), LEFT, buff=0.18) for yv in (1, 2, 3)])
        xl0 = N("0", size=22, color=DIM).next_to(ax.c2p(0, 0.6), DOWN, buff=0.18)
        xl1 = N("100%", size=22, color=DIM).next_to(ax.c2p(1, 0.6), DOWN, buff=0.18)
        xcap = T("life used", size=24, color=DIM).next_to(ax.c2p(0.5, 0.6), DOWN, buff=0.2)
        ycap = T("table motor current", size=24, color=DIM).next_to(ax.c2p(0, 3.2), RIGHT, buff=0.2).shift(UP * 0.05)
        plot_static = VGroup(ax, grid, ylabs, xl0, xl1, xcap, ycap)

        series = {}
        for k, v in DATA["table_current_rel"].items():
            if k == "10":
                continue
            a = np.array(v)
            n = len(a)
            w = max(2, int(0.1 * n))
            y = np.array([a[max(0, i - w + 1):i + 1, 1].mean() for i in range(n)])
            series[k] = (a[:, 0], np.clip(y, 0.6, 3.2))
        TOP = "3"
        xcut = ValueTracker(0.0)
        dim_rest = ValueTracker(0.0)
        hi = ValueTracker(0.0)

        def make_lines():
            xc = xcut.get_value()
            g = VGroup()
            for k, (xs, ys) in series.items():
                m = xs <= xc
                if m.sum() < 2:
                    continue
                pts = [ax.c2p(x, y) for x, y in zip(xs[m], ys[m])]
                j = m.sum()
                if j < len(xs) and xs[j] > xs[j - 1]:
                    f = (xc - xs[j - 1]) / (xs[j] - xs[j - 1])
                    pts.append(ax.c2p(xc, ys[j - 1] + f * (ys[j] - ys[j - 1])))
                is_top = (k == TOP)
                h = hi.get_value() if is_top else 0.0
                op = (0.6 * (1 - 0.65 * dim_rest.get_value())) if not is_top else 0.6 + 0.4 * h
                col = mix(SIGNAL, WARN, h) if is_top else SIGNAL
                ln = VMobject(stroke_width=2.0 + 1.6 * h, color=col).set_points_as_corners(pts)
                ln.set_stroke(opacity=op)
                g.add(ln)
            if 0.003 < xc < 0.999:
                g.add(Line(ax.c2p(xc, 0.6), ax.c2p(xc, 3.2), stroke_width=1.2, color=SIGNAL).set_stroke(opacity=0.35))
            return g

        lines = redraw(make_lines)

        band = Rectangle(width=ax.c2p(1, 0)[0] - ax.c2p(0.9, 0)[0], height=4.7, stroke_width=0)
        band.set_fill(WARN, opacity=0.07).move_to((ax.c2p(0.9, 0.6) + ax.c2p(1, 3.2)) / 2)

        xt, yt = series[TOP][0][-1], series[TOP][1][-1]
        p_top = ax.c2p(xt, yt)
        lab27 = N("×2.7", size=40, color=WARN).next_to(p_top, UL, buff=0.12).shift(LEFT * 0.05)

        def make_endpulse():
            h = hi.get_value()
            g = VGroup()
            if h < 0.01:
                return g
            ph = (tnow() * 1.2) % 1.0
            g.add(Dot(p_top, radius=0.07, color=WARN).set_fill(opacity=h))
            g.add(Circle(radius=0.08 + 0.32 * ph, color=WARN, stroke_width=2).move_to(p_top)
                  .set_stroke(opacity=(1 - ph) * h))
            return g

        endpulse = redraw(make_endpulse)

        self.play(Create(ax), FadeIn(grid), FadeIn(ylabs), FadeIn(xl0), FadeIn(xl1), FadeIn(xcap), FadeIn(ycap),
                  run_time=0.7)
        self.add(lines)
        self.play(xcut.animate.set_value(1.0), run_time=c(2) + 4.45 - self.now, rate_func=linear)
        self.wait_until(c(3) + 0.1)                       # "near the end"
        self.play(FadeIn(band), dim_rest.animate.set_value(1.0), run_time=0.6)
        self.wait_until(c(3) + 1.45)                      # "two point seven times"
        self.add(endpulse)
        self.play(hi.animate.set_value(1.0), FadeIn(lab27, shift=UP * 0.12), run_time=0.6)
        self.wait_until(c(4) - 0.52)

        # =========================================================== D: vibration
        vib_new = np.array(DATA["vibration"]["new"])
        vib_worn = np.array(DATA["vibration"]["worn"])
        spec = DATA["spectrum"]
        fq = np.array(spec["freq_hz"])
        s_new = np.array(spec["new"])
        s_worn = np.array(spec["worn"])
        i0 = int(np.searchsorted(fq, 36.0))

        def spec_curve(mags, color=SIGNAL):
            pts = [P(spec_x(fq[i0]), SY)] + [P(spec_x(f), spec_y(m)) for f, m in zip(fq[i0:], mags[i0:])] + \
                  [P(spec_x(fq[-1]), SY)]
            ln = VMobject(stroke_width=2.4, color=color).set_points_as_corners(pts)
            ln.set_fill(color, opacity=0.13)
            return ln

        # sensor icon (one machine sensor flies to the left column and becomes the "ear")
        ear_pos = P(-5.95, WY)
        sens_move = ValueTracker(0.0)
        vis_ear = ValueTracker(0.0)

        def make_ear():
            v = vis_ear.get_value()
            g = VGroup()
            if v < 0.005:
                return g
            f = smooth01(sens_move.get_value())
            s, _ = mxf()
            q = M(SENSORS[0]) * (1 - f) + ear_pos * f
            r = 0.075 * s * (1 - f) + 0.13 * f
            ph = (tnow() * 1.5) % 1.0
            g.add(Dot(q, radius=r, color=SIGNAL).set_fill(opacity=v))
            for k in range(2):
                pk = (ph + 0.5 * k) % 1.0
                g.add(Circle(radius=r + (0.05 + 0.45 * pk) * f, color=SIGNAL, stroke_width=1.6).move_to(q)
                      .set_stroke(opacity=(1 - pk) * 0.8 * v * f))
            return g

        ear = redraw(make_ear)

        self.add(ear)
        vis_ear.set_value(1.0)
        self.play(FadeOut(plot_static), FadeOut(lines), FadeOut(band), FadeOut(lab27), FadeOut(endpulse),
                  tmotor.animate.set_value(0.0), run_time=0.5)
        self.remove(lines, endpulse)
        self.play(sens_move.animate.set_value(1.0), mach_fade.animate.set_value(0.0), run_time=0.8)
        self.remove(machine, sensors, labels)

        base = DashedLine(P(WX0, WY), P(WX1, WY), dash_length=0.06, dashed_ratio=0.4, stroke_width=1.2, color=FAINT)
        tag_new = T("new", size=24, color=GOOD).move_to(P(WX0, WY + 1.12), aligned_edge=LEFT)
        tag_worn = T("worn", size=24, color=HEAT).move_to(P(WX0, WY + 1.12), aligned_edge=LEFT)
        rate = N("25,000 / s", size=24, color=DIM).move_to(P(WX1, WY + 1.12), aligned_edge=RIGHT)
        self.play(Create(base), FadeIn(tag_new), run_time=0.4)

        wcut = ValueTracker(0.0)

        def make_stream():
            n = wcut.get_value() * 1199
            g = VGroup()
            if n < 2:
                return g
            pts = wave_points(vib_new, n + 1)
            g.add(VMobject(stroke_width=2.2, color=SIGNAL).set_points_as_corners(pts))
            if n < 1198:
                g.add(Dot(pts[-1], radius=0.1, color=SIGNAL).set_fill(opacity=0.25))
                g.add(Dot(pts[-1], radius=0.045, color=INK))
            return g

        stream = redraw(make_stream)
        self.add(stream)
        self.wait_until(c(4) + 1.28)                      # "listening twenty-five thousand times a second"
        self.play(wcut.animate(rate_func=linear).set_value(1.0),
                  FadeIn(rate, rate_func=lambda a: smooth01((a - 0.5) / 0.3)), run_time=1.7)
        self.remove(stream)
        wave = VMobject(stroke_width=2.2, color=SIGNAL).set_points_as_corners(wave_points(vib_new))
        self.add(wave)
        self.wait(0.1)

        # spectrum
        s_axis = Line(P(SX0, SY), P(SX1, SY), stroke_width=2, color=DIM)
        flabs = VGroup(N("0", size=20, color=DIM).next_to(P(spec_x(0), SY), DOWN, buff=0.16),
                       N("1000 Hz", size=20, color=DIM).next_to(P(spec_x(1000), SY), DOWN, buff=0.16),
                       Line(P(spec_x(0), SY), P(spec_x(0), SY - 0.09), stroke_width=1.6, color=DIM),
                       Line(P(spec_x(1000), SY), P(spec_x(1000), SY - 0.09), stroke_width=1.6, color=DIM))
        flabs[1].shift(RIGHT * 0.33)
        spec_new = spec_curve(s_new)
        spec_worn = spec_curve(s_worn)
        tooth_hz = spec["tooth_hz"]
        tticks = VGroup(*[Line(P(spec_x(k * tooth_hz), SY), P(spec_x(k * tooth_hz), SY + 0.12),
                               stroke_width=2, color=INK) for k in (1, 2, 3, 4)])
        lab213 = VGroup(N("213 Hz", size=24, color=INK), T("tooth hits", size=20, color=DIM)).arrange(DOWN, buff=0.06)
        lab213.move_to(P(spec_x(tooth_hz) + 0.95, SY + 1.55))

        wave_copy = wave.copy()
        self.play(Create(s_axis), FadeIn(flabs), ReplacementTransform(wave_copy, spec_new), run_time=0.8)
        self.play(FadeIn(tticks), FadeIn(lab213, shift=UP * 0.1), run_time=0.4)
        self.wait_until(c(4) + 4.78)                      # "hear a new beat"
        wave_w = VMobject(stroke_width=2.2, color=SIGNAL).set_points_as_corners(wave_points(vib_worn))
        self.play(Transform(wave, wave_w), Transform(spec_new, spec_worn), FadeOut(tag_new), FadeIn(tag_worn),
                  lab213.animate.move_to(P(spec_x(tooth_hz) + 0.95, SY + 2.15)), run_time=0.9)

        # ---- once per turn
        turn_hz = spec["turn_hz"]
        comb = VGroup()
        for k in range(1, 21):
            if k % 4 == 0:
                continue
            x = spec_x(k * turn_hz)
            comb.add(DashedLine(P(x, SY), P(x, SY + 2.1), dash_length=0.05, dashed_ratio=0.45, stroke_width=1.3,
                                color=WARN).set_stroke(opacity=0.45))
        risers = []
        for k in range(1, 21):
            if k % 4 == 0:
                continue
            i = int(np.argmin(np.abs(fq - k * turn_hz)))
            sl = slice(max(i - 1, 0), i + 2)
            jn = sl.start + int(np.argmax(s_worn[sl]))
            if s_worn[sl].max() / s_new[sl].max() >= 1.5:
                risers.append(P(spec_x(fq[jn]), spec_y(s_worn[jn])))
        xa, xb = spec_x(13 * turn_hz), spec_x(14 * turn_hz)
        yb_ = SY + 2.25
        br53 = VGroup(Line(P(xa, yb_), P(xb, yb_), stroke_width=2, color=WARN),
                      Line(P(xa, yb_ - 0.08), P(xa, yb_ + 0.08), stroke_width=2, color=WARN),
                      Line(P(xb, yb_ - 0.08), P(xb, yb_ + 0.08), stroke_width=2, color=WARN))
        lab53 = N("53 Hz", size=24, color=WARN).next_to(br53, UP, buff=0.1)

        HITS = [361, 829]
        ha, hb = wave_xy(HITS[0], vib_worn), wave_xy(HITS[1], vib_worn)
        yt_ = WY + 0.78
        br_turn = VGroup(Line(P(ha[0], yt_), P(hb[0], yt_), stroke_width=2, color=WARN),
                         Line(P(ha[0], yt_ - 0.08), P(ha[0], yt_ + 0.08), stroke_width=2, color=WARN),
                         Line(P(hb[0], yt_ - 0.08), P(hb[0], yt_ + 0.08), stroke_width=2, color=WARN))
        lab_turn = T("1 turn", size=24, color=WARN).next_to(br_turn, UP, buff=0.08)

        # playhead + chipped tooth timing
        t_ph0, t_ph1 = c(6) + 0.3, TOTAL - 0.55
        n_s = len(vib_worn)

        def ph_sample(t):
            return (t - t_ph0) / (t_ph1 - t_ph0) * (n_s - 1)

        def t_of_sample(i):
            return t_ph0 + i / (n_s - 1) * (t_ph1 - t_ph0)

        hit_times = [t_of_sample(i) for i in HITS]
        TURN = 468.75

        def beat(t):
            """Pulse 0..1 for the once-per-turn hits; before the playhead runs, a steady once-per-turn pulse."""
            if t < t_ph0:
                per = TURN / (n_s - 1) * (t_ph1 - t_ph0)
                ph = ((t - (t_ph0 - 2 * per)) / per) % 1.0
                return np.exp(-ph / 0.22)
            v = 0.0
            for th in hit_times:
                if t >= th:
                    v = max(v, np.exp(-(t - th) / 0.28))
            return v

        vis_opt = ValueTracker(0.0)

        def make_marks():
            v = vis_opt.get_value()
            g = VGroup()
            if v < 0.005:
                return g
            b = beat(tnow())
            for p in risers:
                g.add(Dot(p, radius=0.16 + 0.1 * b, color=WARN).set_fill(opacity=(0.18 + 0.3 * b) * v))
                g.add(Dot(p, radius=0.055, color=WARN).set_fill(opacity=v))
            for p in (ha, hb):
                g.add(Dot(p, radius=0.17 + 0.12 * b, color=WARN).set_fill(opacity=(0.18 + 0.35 * b) * v))
                g.add(Dot(p, radius=0.06, color=WARN).set_fill(opacity=v))
            return g

        marks = redraw(make_marks)
        self.wait_until(c(5) - 0.05)
        self.add(marks)
        self.play(LaggedStart(*[Create(cl) for cl in comb], lag_ratio=0.05), vis_opt.animate.set_value(1.0),
                  FadeIn(br_turn), FadeIn(lab_turn), FadeIn(br53), FadeIn(lab53), run_time=0.6)

        # ---- the sound of a chipped tooth
        RT = 0.62
        vis_tooth = ValueTracker(0.0)

        def chip_angle(t):
            # chipped tooth at the contact point (bottom) exactly when the playhead crosses a big hit
            return -90.0 + 360.0 * (ph_sample(t) - HITS[0]) / TURN

        TIPOFF = 0.55 * 90.0

        def make_tooth():
            t = tnow()
            v = vis_tooth.get_value()
            g = VGroup()
            if v < 0.005:
                return g
            a = chip_angle(t)
            mill = end_mill(radius=RT, color=CARBIDE, stroke=2.2)
            body = VGroup(mill[0], mill[1])
            body.rotate((a - TIPOFF) * DEG, about_point=ORIGIN).shift(ear_pos)
            body[0].set_stroke(opacity=v).set_fill(opacity=0.16 * v)
            body[1].set_stroke(opacity=0.8 * v)
            g.add(body)
            # the chip: a bite out of one cutting corner
            ar = a * DEG
            tip = ear_pos + RT * np.array([np.cos(ar), np.sin(ar), 0])
            tng = np.array([-np.sin(ar), np.cos(ar), 0])
            rad = np.array([np.cos(ar), np.sin(ar), 0])
            q1, q2, q3 = tip - tng * 0.2, tip - tng * 0.09 - rad * 0.11, tip - rad * 0.17 + tng * 0.01
            notch = Polygon(tip + tng * 0.05 + rad * 0.05, tip - tng * 0.2 + rad * 0.05, q1, q2, q3,
                            tip + tng * 0.05 - rad * 0.17, stroke_width=0)
            notch.set_fill(BG, opacity=v)
            g.add(notch)
            g.add(VMobject(stroke_width=2.6, color=DANGER).set_points_as_corners([q1, q2, q3]).set_stroke(opacity=v))
            for k in range(1, 4):
                ak = (a + 90 * k) * DEG
                g.add(Dot(ear_pos + RT * 0.985 * np.array([np.cos(ak), np.sin(ak), 0]), radius=0.04,
                          color=CARBIDE).set_fill(opacity=0.8 * v))
            # contact surface under the cutter
            g.add(Line(ear_pos + P(-0.75, -RT - 0.04), ear_pos + P(0.75, -RT - 0.04), stroke_width=2.2,
                       color=STEEL).set_stroke(opacity=0.8 * v))
            b = beat(t) if t >= t_ph0 else 0.0
            if b > 0.02:
                cp = ear_pos + P(0, -RT)
                rr = 0.08 + 0.42 * (1 - b)
                g.add(Arc(radius=rr, start_angle=PI, angle=PI, arc_center=cp, stroke_width=2.6, color=WARN)
                      .set_stroke(opacity=b * v))
                g.add(Dot(cp, radius=0.06 + 0.06 * b, color=WARN).set_fill(opacity=b * v))
            return g

        tooth = redraw(make_tooth)

        def make_head():
            t = tnow()
            g = VGroup()
            if t < t_ph0 or t > t_ph1 + 0.02:
                return g
            i = min(n_s - 1, max(0, ph_sample(t)))
            p = wave_xy(i, vib_worn)
            g.add(Line(P(p[0], WY - 0.95), P(p[0], WY + 0.62), stroke_width=1.4, color=INK).set_stroke(opacity=0.45))
            g.add(Dot(p, radius=0.05, color=INK))
            return g

        head = redraw(make_head)

        self.wait_until(c(6))
        self.add(tooth, head)
        self.play(vis_tooth.animate.set_value(1.0), vis_ear.animate.set_value(0.0), run_time=0.3)
        self.remove(ear)
        self.wait_until(t_ph1 + 0.05)

        self.remove(clock)
        for m in self.mobjects:      # freeze live parts so the closing fade sees fixed shapes
            m.clear_updaters()
        self.finish()
