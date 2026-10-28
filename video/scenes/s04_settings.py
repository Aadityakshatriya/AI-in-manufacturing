"""s04_settings — how hard we push the cutter: radial bite, holder length (diving board + chatter),
and the real lives of the 13 cutters as a bar chart."""

import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from style import *  # noqa: F401,F403

DEG = PI / 180


def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def redraw(func):
    """Like always_redraw, but swaps in the freshly built children each frame instead of morphing the old
    ones (always_redraw's family alignment glitches when the number of parts changes between frames)."""
    holder = VGroup(func())

    def upd(m):
        m.remove(*m.submobjects)
        m.add(func())

    holder.add_updater(upd)
    return holder


def mix(a, b, t):
    return ManimColor(a).interpolate(ManimColor(b), float(t))


def ramp(t, t0, t1):
    """0 before t0, 1 after t1, smooth in between."""
    return smooth01((t - t0) / max(t1 - t0, 1e-6))


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


class S04Settings(LiveFamilies, TLScene):
    SID = "s04_settings"

    def construct(self):
        # ------------------------------------------------------------------ clock
        clock = ValueTracker(0.0)
        # renderer.time advances once per written frame; the tracker mirrors it so cached
        # partial movies are invalidated when timing changes
        clock.add_updater(lambda m, dt: m.set_value(self.renderer.time))
        self.add(clock)
        tnow = lambda: self.renderer.time

        c = self.cue
        TOTAL = self.total

        # ================================================================== TOP VIEW
        C = np.array([0.3, 0.75, 0.0])     # cutter centre
        R = 1.5                             # cutter radius (5 mm)
        kmm = R / 5.0                       # scene units per mm
        y_b = C[1] - R                      # machined surface behind the cutter
        ae = ValueTracker(4.5)              # radial depth of cut, mm
        vis_top = ValueTracker(0.0)
        vis_arc = ValueTracker(0.0)
        vis_dim = ValueTracker(0.0)
        vis_cnt = ValueTracker(0.0)

        def th_e():
            return np.arcsin(np.clip((ae.get_value() - 5.0) / 5.0, -1, 1))

        def y_a():
            return C[1] + kmm * (ae.get_value() - 5.0)

        # spin profile: fast, then eases almost to a stop with two teeth inside the wide bite
        t_dec0, t_dec1 = c(1) + 1.75, c(1) + 2.45
        w0, w1 = 210.0, 8.0                 # deg/s
        grid = np.arange(0.0, TOTAL + 1.0, 1 / 600)
        w = w0 + (w1 - w0) * smooth01((grid - t_dec0) / (t_dec1 - t_dec0))
        phi_raw = np.concatenate([[0.0], np.cumsum(w[:-1]) / 600])
        TIP0 = 0.55 * 90.0                  # cutting corner (land meets flute) in end_mill(), degrees
        target = -79.0                       # trailing engaged tooth angle at t_dec1
        raw_at = np.interp(t_dec1, grid, phi_raw) + TIP0
        off = (target - raw_at) % 90.0
        phi_tab = phi_raw + off

        def phi(t):
            return float(np.interp(t, grid, phi_tab))

        def wrap(a):
            return (a + 180.0) % 360.0 - 180.0

        def tooth_angles(t):
            return [wrap(phi(t) + TIP0 + 90.0 * k) for k in range(4)]

        def engaged(a):
            return -90.0 <= a <= th_e() / DEG

        # steel slab
        c_top = mix(BG, STEEL, 0.42)
        c_bot = mix(BG, STEEL, 0.08)

        def make_steel():
            th = np.linspace(-PI / 2, th_e(), 48)
            arc = [C + R * np.array([np.cos(a), np.sin(a), 0]) for a in th]
            pts = [np.array([-7.9, -4.7, 0]), np.array([-7.9, y_b, 0]), *arc,
                   np.array([7.9, y_a(), 0]), np.array([7.9, -4.7, 0])]
            p = Polygon(*pts, stroke_width=0)
            p.set_fill([c_top, c_bot], opacity=vis_top.get_value())
            p.set_sheen_direction(DOWN)
            v = vis_top.get_value()
            x_e = C[0] + R * np.cos(th_e())
            machined = Line([-7.9, y_b, 0], [C[0], y_b, 0], stroke_width=2.2, color=INK,
                            stroke_opacity=0.55 * v)
            ahead = Line([x_e, y_a(), 0], [7.9, y_a(), 0], stroke_width=2.2, color=STEEL,
                         stroke_opacity=0.9 * v)
            ghost = DashedLine([-7.9, y_a(), 0], [C[0] - R - 0.12, y_a(), 0], dash_length=0.09,
                               dashed_ratio=0.5, stroke_width=1.6, color=DIM).set_stroke(opacity=0.8 * v)
            return VGroup(p, machined, ahead, ghost)

        steel = redraw(make_steel)

        # grain streaks flowing left (the steel feeds past the cutter)
        rng = np.random.default_rng(7)
        G = 120
        gx = rng.uniform(-7.9, 7.9, G)
        gy = rng.uniform(-4.3, 1.95, G)
        gl = rng.uniform(0.10, 0.34, G)
        go = rng.uniform(0.10, 0.30, G)
        grains = VGroup(*[Line(LEFT * l / 2, RIGHT * l / 2, stroke_width=1.4, color=STEEL) for l in gl])

        def upd_grains(g, dt):
            gx[:] -= 0.6 * dt
            gx[gx < -7.9] += 15.8
            ya = y_a()
            v = vis_top.get_value()
            for i, ln in enumerate(g):
                x, y = gx[i], gy[i]
                hw = gl[i] / 2 + 0.05
                if x + hw < C[0]:
                    inside = y < y_b - 0.12
                elif x - hw > C[0]:
                    inside = y < ya - 0.12 and (abs(x - C[0]) - hw) ** 2 + (y - C[1]) ** 2 > (R + 0.15) ** 2
                else:
                    inside = y < y_b - 0.12
                ln.move_to([x, y, 0])
                ln.set_stroke(opacity=go[i] * v if inside else 0.0)

        grains.add_updater(upd_grains)

        # cutter body (rotates with phi)
        mill = end_mill(radius=R, color=CARBIDE, stroke=2.4)
        body = VGroup(mill[0], mill[1]).shift(C)
        body.cur = 0.0

        def upd_body(m):
            a = phi(tnow())
            m.rotate((a - m.cur) * DEG, about_point=C)
            m.cur = a
            v = vis_top.get_value()
            m[0].set_stroke(opacity=v).set_fill(opacity=0.16 * v)
            m[1].set_stroke(opacity=0.8 * v)

        body.add_updater(upd_body)

        def make_teeth():
            v = vis_top.get_value()
            g = VGroup()
            for a in tooth_angles(tnow()):
                p = C + R * 0.985 * np.array([np.cos(a * DEG), np.sin(a * DEG), 0])
                if engaged(a) and vis_arc.get_value() > 0.01:
                    s = vis_arc.get_value()
                    g.add(Dot(p, radius=0.22, color=WARN).set_fill(opacity=0.22 * v * s))
                    g.add(Dot(p, radius=0.085, color=WARN).set_fill(opacity=v))
                else:
                    g.add(Dot(p, radius=0.055, color=CARBIDE).set_fill(opacity=0.75 * v))
            return g

        teeth = redraw(make_teeth)

        def make_arc():
            s = vis_arc.get_value() * vis_top.get_value()
            span = th_e() + PI / 2
            a1 = Arc(radius=R + 0.02, start_angle=-PI / 2, angle=span, arc_center=C,
                     stroke_width=12, color=HEAT).set_stroke(opacity=0.20 * s)
            a2 = Arc(radius=R + 0.02, start_angle=-PI / 2, angle=span, arc_center=C,
                     stroke_width=3.6, color=HEAT).set_stroke(opacity=s)
            return VGroup(a1, a2)

        arc = redraw(make_arc)

        # chips flung from the exit point of the bite
        NP = 64
        chips = VGroup(*[Dot(radius=0.032, color=HEAT) for _ in range(NP)])
        cs = np.zeros((NP, 6))  # x, y, vx, vy, age, life
        cs[:, 5] = -1
        chips.prev = tooth_angles(0.0)
        chips.next_slot = 0

        def upd_chips(g, dt):
            t = tnow()
            cur = tooth_angles(t)
            te = th_e() / DEG
            v = vis_top.get_value()
            for k in range(4):
                a0, a1 = chips.prev[k], cur[k]
                if a0 < te <= a1 and a1 - a0 < 90 and v > 0.3:
                    ex = C + R * np.array([np.cos(te * DEG), np.sin(te * DEG), 0])
                    tang = np.array([-np.sin(te * DEG), np.cos(te * DEG)])
                    for _ in range(6):
                        j = chips.next_slot
                        chips.next_slot = (j + 1) % NP
                        sp = rng.uniform(1.2, 2.6)
                        ang = rng.normal(0, 0.35)
                        d = np.array([tang[0] * np.cos(ang) - tang[1] * np.sin(ang),
                                      tang[0] * np.sin(ang) + tang[1] * np.cos(ang)])
                        cs[j] = [ex[0], ex[1], d[0] * sp - 0.3, d[1] * sp, 0.0, rng.uniform(0.45, 0.9)]
            chips.prev = cur
            for j, dot in enumerate(g):
                if cs[j, 5] <= 0:
                    dot.set_fill(opacity=0)
                    continue
                cs[j, 4] += dt
                if cs[j, 4] > cs[j, 5]:
                    cs[j, 5] = -1
                    dot.set_fill(opacity=0)
                    continue
                cs[j, 2:4] *= np.exp(-2.2 * dt)
                cs[j, 0] += cs[j, 2] * dt - 0.6 * dt
                cs[j, 1] += cs[j, 3] * dt
                f = cs[j, 4] / cs[j, 5]
                dot.move_to([cs[j, 0], cs[j, 1], 0])
                dot.set_fill(mix(WARN, HEAT, min(1, 2 * f)), opacity=(1 - f) * v)

        chips.add_updater(upd_chips)

        # bite dimension (left of the cutter, in free air above the machined surface)
        x_d = C[0] - R - 0.55

        def make_dim():
            s = vis_dim.get_value() * vis_top.get_value()
            ya = y_a()
            ln = Line([x_d, y_b, 0], [x_d, ya, 0], stroke_width=2, color=INK).set_stroke(opacity=0.8 * s)
            t1 = Line([x_d - 0.1, y_b, 0], [x_d + 0.1, y_b, 0], stroke_width=2, color=INK).set_stroke(opacity=0.8 * s)
            t2 = Line([x_d - 0.1, ya, 0], [x_d + 0.1, ya, 0], stroke_width=2, color=INK).set_stroke(opacity=0.8 * s)
            a = ae.get_value()
            txt = "8 mm" if a > 7.97 else ("4.5 mm" if a < 4.53 else f"{a:.1f} mm")
            lab = N(txt, size=28, color=INK).set_opacity(s)
            lab.next_to(ln, LEFT, buff=0.22)
            return VGroup(ln, t1, t2, lab)

        dim = redraw(make_dim)

        dia = T("Ø 10 mm", size=22, color=DIM).move_to(C + UP * (R + 0.32))
        dia.add_updater(lambda m: m.set_opacity(vis_dim.get_value() * vis_top.get_value()))

        # tooth count labels (appear once the spin has eased)
        ang_settle = tooth_angles(t_dec1 + 0.05)
        ae_wide_te = np.arcsin(0.6) / DEG
        idx = [k for k, a in enumerate(ang_settle) if -90 <= a <= ae_wide_te]
        idx.sort(key=lambda k: -ang_settle[k])

        def make_counts():
            s = vis_cnt.get_value() * vis_top.get_value()
            g = VGroup()
            angs = tooth_angles(tnow())
            for n, k in enumerate(idx):
                a = angs[k] * DEG
                p = C + (R - 0.42) * np.array([np.cos(a), np.sin(a), 0])
                g.add(N(str(n + 1), size=34, color=WARN).move_to(p).set_opacity(s))
            return g

        counts = redraw(make_counts)

        self.add(steel, grains, arc, chips, body, teeth, dim, dia, counts)

        # slow camera: push toward the cutter in the top view; a gentle drift for the rest
        frame = self.camera.frame
        FW = frame.width
        t_snap = c(2) + 0.45
        cam_target = np.array([0.6, 0.35, 0])

        def upd_frame(m):
            t = tnow()
            if t < t_snap:
                k = ramp(t, 0.0, t_snap - 0.6)
                m.set(width=FW * (1 - 0.08 * k))
                m.move_to(cam_target * k)
            else:
                kp = ramp(t, c(3) + 0.05, c(3) + 2.0)        # follow the holder as it grows
                kb = ramp(t, c(4) - 0.2, TOTAL)              # slow push on the bar chart
                ctr = np.array([-2.4, 0.3, 0]) * (1 - kp) + np.array([0.15, 0.0, 0]) * kp
                m.set(width=FW * (0.86 + 0.14 * kp) * (1 - 0.045 * kb))
                m.move_to(ctr)

        frame.add_updater(upd_frame)
        self.add(frame)

        # ---- timeline: top view
        self.play(vis_top.animate.set_value(1.0), run_time=1.3, rate_func=smooth)
        self.wait_until(c(0) + 2.35)                    # "...depends on how hard we push it"
        self.play(vis_arc.animate.set_value(1.0), run_time=0.9)
        self.play(vis_dim.animate.set_value(1.0), run_time=0.6)
        self.wait_until(c(1) + 0.05)                    # "A wider bite"
        self.play(ae.animate.set_value(8.0), run_time=1.5, rate_func=smooth)
        self.wait_until(t_dec1)                         # "...more teeth into the steel at once"
        self.play(vis_cnt.animate.set_value(1.0), run_time=0.4)
        self.wait_until(c(2) - 0.15)

        # ================================================================== SIDE VIEW
        y0 = 0.75
        x0 = -3.9
        L1 = 3.0
        Lc = 1.15
        h = 0.40
        d1 = 0.15
        Lt = ValueTracker(L1)
        dstat = ValueTracker(0.0)
        vis_side = ValueTracker(0.0)
        vis_force = ValueTracker(0.0)
        vis_delta = ValueTracker(0.0)
        vis_Ldim = ValueTracker(0.0)
        t_chat0 = c(3) + 3.3                            # "until it starts to shake"
        t_chat_end = c(4) + 0.05
        chat_on = ValueTracker(0.0)
        red = ValueTracker(0.0)

        def chat_amp(t):
            if t < t_chat0:
                return 0.0
            a = 0.02 * np.exp(1.7 * (t - t_chat0))
            a = min(a, 0.48)
            return a * chat_on.get_value()

        FCH = 4.3  # chatter frequency (visual), Hz

        def tip_defl(t):
            return dstat.get_value() + chat_amp(t) * np.sin(TAU * FCH * (t - t_chat0))

        def beam_parts(L, dtip, op, outline=False, phase=0.0):
            def yc_of(sv):
                return y0 - dtip * sv ** 2 * (3 * L - sv) / (2 * L ** 3)

            def poly(s0, s1, n, fill, stroke, fop):
                sv = np.linspace(s0, s1, n)
                yc = yc_of(sv)
                top = [np.array([x0 + a, y + h / 2, 0]) for a, y in zip(sv, yc)]
                bot = [np.array([x0 + a, y - h / 2, 0]) for a, y in zip(sv, yc)][::-1]
                pg = Polygon(*top, *bot, stroke_width=2, color=stroke)
                pg.set_stroke(opacity=op)
                pg.set_fill(fill, opacity=0 if outline else fop * op)
                return pg

            parts = VGroup()
            rr = red.get_value()
            parts.add(poly(0, L - Lc, 50, mix(STEEL, DANGER, rr), mix(STEEL, DANGER, rr), 0.32 + 0.58 * rr))
            parts.add(poly(L - Lc, L, 20, mix(CARBIDE, DANGER, rr), mix(CARBIDE, DANGER, rr), 0.22 + 0.68 * rr))
            if not outline:
                fl = VGroup()
                n = 5
                for j in range(n):
                    sa = L - Lc + ((j + phase) % n) * Lc / n
                    sb = sa + 0.17
                    if sb > L:
                        continue
                    fl.add(Line([x0 + sa, yc_of(sa) + h / 2, 0], [x0 + sb, yc_of(sb) - h / 2, 0],
                                stroke_width=1.6, color=CARBIDE).set_stroke(opacity=0.7 * op * (1 - rr)))
                parts.add(fl)
            return parts

        def make_beam():
            t = tnow()
            op = vis_side.get_value()
            g = VGroup()
            amp = chat_amp(t)
            if amp > 0.01:
                for j in range(5, 0, -1):
                    dt_ = j * 0.009
                    dd = dstat.get_value() + amp * np.sin(TAU * FCH * (t - dt_ - t_chat0))
                    g.add(beam_parts(Lt.get_value(), dd, op * 0.30 * (1 - j / 6), outline=True))
            g.add(beam_parts(Lt.get_value(), tip_defl(t), op, phase=(t * 2.2) % 1.0))
            return g

        beam = redraw(make_beam)

        # spindle + collet nose
        sp_body = RoundedRectangle(width=2.6, height=3.0, corner_radius=0.18, color=STEEL, stroke_width=2)
        sp_body.move_to([x0 - 0.7 - 1.3, y0, 0]).set_fill(mix(BG, STEEL, 0.12), opacity=1)
        hatch = VGroup()
        xl, xr, yl, yh = x0 - 3.3, x0 - 0.7, y0 - 1.5, y0 + 1.5
        for cst in np.arange(-12, 0, 0.32):
            # line y = x - cst  (45 deg); clip to rect
            pts = []
            for xx in (xl, xr):
                yy = xx - cst
                if yl <= yy <= yh:
                    pts.append([xx, yy, 0])
            for yy in (yl, yh):
                xx = yy + cst
                if xl <= xx <= xr:
                    pts.append([xx, yy, 0])
            if len(pts) >= 2:
                hatch.add(Line(pts[0], pts[1], stroke_width=1.2, color=FAINT))
        nose = Polygon([x0 - 0.7, y0 + 0.66, 0], [x0, y0 + 0.3, 0], [x0, y0 - 0.3, 0], [x0 - 0.7, y0 - 0.66, 0],
                       color=STEEL, stroke_width=2).set_fill(mix(BG, STEEL, 0.25), opacity=1)
        spindle = VGroup(sp_body, hatch, nose)

        def spindle_op(m):
            v = vis_side.get_value()
            m[0].set_stroke(opacity=v).set_fill(opacity=v)
            m[1].set_stroke(opacity=v)
            m[2].set_stroke(opacity=v).set_fill(opacity=v)

        spindle.add_updater(spindle_op)

        def make_center():
            v = vis_side.get_value() * (1 - chat_on.get_value() * 0.0)
            return DashedLine([x0, y0, 0], [x0 + Lt.get_value() + 0.35, y0, 0], dash_length=0.08,
                              dashed_ratio=0.5, stroke_width=1.4, color=DIM).set_stroke(opacity=0.8 * v)

        center = redraw(make_center)

        def tip_xy(t):
            L = Lt.get_value()
            return np.array([x0 + L, y0 - tip_defl(t), 0])

        def make_force():
            v = vis_force.get_value() * vis_side.get_value()
            L = Lt.get_value()
            sx = L - 0.32
            dd = dstat.get_value()
            yy = y0 - dd * sx ** 2 * (3 * L - sx) / (2 * L ** 3) + h / 2
            p_end = np.array([x0 + sx, yy + 0.04, 0])
            ar = Arrow(p_end + UP * 1.25, p_end, buff=0, color=HEAT, stroke_width=5,
                       max_tip_length_to_length_ratio=0.22, tip_length=0.22)
            ar.set_opacity(v)
            lab = T("force", size=22, color=HEAT).next_to(ar.get_start(), RIGHT, buff=0.12).shift(DOWN * 0.15)
            lab.set_opacity(v)
            return VGroup(ar, lab)

        force = redraw(make_force)

        def make_delta():
            v = vis_delta.get_value() * vis_side.get_value()
            L = Lt.get_value()
            dd = dstat.get_value()
            xb = x0 + L + 0.3
            top, bot = y0, y0 - dd
            g = VGroup(
                Line([xb, top, 0], [xb, bot, 0], stroke_width=2, color=WARN),
                Line([xb - 0.08, top, 0], [xb + 0.08, top, 0], stroke_width=2, color=WARN),
                Line([xb - 0.08, bot, 0], [xb + 0.08, bot, 0], stroke_width=2, color=WARN),
            ).set_stroke(opacity=v)
            r = dd / d1 if d1 > 0 else 1
            if r < 1.04:
                txt = "δ"
            elif r > 7.96:
                txt = "8δ"
            else:
                txt = f"{r:.1f}δ"
            lab = T(txt, size=32, color=WARN).set_opacity(v)
            lab.next_to(g[0], RIGHT, buff=0.16)
            return VGroup(g, lab)

        delta = redraw(make_delta)

        def make_Ldim():
            v = vis_Ldim.get_value() * vis_side.get_value()
            L = Lt.get_value()
            yy = y0 + 0.78
            g = VGroup(
                Line([x0, yy, 0], [x0 + L, yy, 0], stroke_width=1.8, color=INK),
                Line([x0, yy - 0.09, 0], [x0, yy + 0.09, 0], stroke_width=1.8, color=INK),
                Line([x0 + L, yy - 0.09, 0], [x0 + L, yy + 0.09, 0], stroke_width=1.8, color=INK),
            ).set_stroke(opacity=0.75 * v)
            r = L / L1
            txt = "L" if r < 1.02 else ("2L" if r > 1.98 else f"{r:.1f}L")
            lab = T(txt, size=30, color=INK).set_opacity(v).next_to(g[0], UP, buff=0.14)
            return VGroup(g, lab)

        Ldim = redraw(make_Ldim)

        law = VGroup(T("δ ∝ L", size=46, color=INK), T("3", size=28, color=INK))
        law[1].next_to(law[0], RIGHT, buff=0.04).align_to(law[0], UP).shift(UP * 0.12)
        law.move_to([-1.6, -2.35, 0])

        # chatter trace (tip displacement, scrolling right like a pen recorder)
        trace_x0, trace_x1, trace_v = x0 + 2 * L1 + 0.85, 6.9, 1.8
        hist = []

        def upd_hist(m, dt):
            t = tnow()
            if t >= t_chat0 and chat_on.get_value() > 0:
                hist.append((t, tip_defl(t) - dstat.get_value()))

        hist_rec = Mobject()
        hist_rec.add_updater(upd_hist)
        vis_trace = ValueTracker(0.0)

        def make_trace():
            t = tnow()
            v = vis_trace.get_value() * vis_side.get_value()
            yc = y0 - dstat.get_value()
            pts = []
            for (ti, di) in reversed(hist):
                x = trace_x0 + (t - ti) * trace_v
                if x > trace_x1:
                    break
                pts.append([x, yc - di, 0])
            g = VGroup()
            base = DashedLine([trace_x0, yc, 0], [trace_x1, yc, 0], dash_length=0.06, dashed_ratio=0.4,
                              stroke_width=1.2, color=FAINT).set_stroke(opacity=v)
            g.add(base)
            if len(pts) >= 2:
                ln = VMobject(stroke_width=2.6, color=DANGER).set_points_smoothly(pts) if len(pts) > 3 \
                    else VMobject(stroke_width=2.6, color=DANGER).set_points_as_corners(pts)
                ln.set_stroke(opacity=v)
                g.add(ln)
                g.add(Dot(pts[0], radius=0.05, color=DANGER).set_fill(opacity=v))
            if pts:
                tip = tip_xy(t)
                g.add(DashedLine(tip + RIGHT * 0.1, pts[0], dash_length=0.05, dashed_ratio=0.5,
                                 stroke_width=1.2, color=DANGER).set_stroke(opacity=0.35 * v))
            return g

        trace = redraw(make_trace)

        self.add(spindle, center, beam, force, delta, Ldim, hist_rec, trace)

        # ---- timeline: side view
        # cross-fade top view -> side view
        self.play(vis_top.animate.set_value(0.0), run_time=0.6, rate_func=smooth)
        self.remove(steel, grains, arc, chips, body, teeth, dim, dia, counts)
        self.play(vis_side.animate.set_value(1.0), run_time=0.9, rate_func=smooth)
        self.play(vis_Ldim.animate.set_value(1.0), run_time=0.4)
        self.wait_until(c(2) + 1.5)                     # "...into a diving board"
        self.play(vis_force.animate.set_value(1.0), run_time=0.3)

        # push down with a diving-board wobble
        def bounce(a):
            tt = a * 1.2
            return 1 - np.exp(-4.0 * tt) * np.cos(11 * tt)

        self.play(dstat.animate(rate_func=bounce).set_value(d1), run_time=1.1)
        self.play(vis_delta.animate.set_value(1.0), run_time=0.3)
        self.wait_until(c(3) + 0.05)                    # "twice as long"

        def upd_cubic(m):
            m.set_value(d1 * (Lt.get_value() / L1) ** 3)

        dstat.add_updater(upd_cubic)
        self.play(Lt.animate.set_value(2 * L1), run_time=1.6, rate_func=smooth)
        dstat.clear_updaters()
        dstat.set_value(8 * d1)
        self.wait_until(c(3) + 2.05)                    # "...eight times floppier"
        self.play(FadeIn(law, shift=UP * 0.15), run_time=0.7)
        self.wait_until(t_chat0 - 0.45)
        self.play(vis_force.animate.set_value(0.0), vis_delta.animate.set_value(0.0), run_time=0.45)
        chat_on.set_value(1.0)
        self.play(vis_trace.animate.set_value(1.0), run_time=0.5)
        self.wait_until(t_chat_end - 0.72)

        # settle and clear the stage
        self.play(chat_on.animate.set_value(0.0), dstat.animate.set_value(0.0), red.animate.set_value(1.0),
                  vis_trace.animate.set_value(0.0), FadeOut(law), FadeOut(spindle), FadeOut(center),
                  vis_Ldim.animate.set_value(0.0), run_time=0.5)
        self.remove(spindle, center, Ldim)
        hist.clear()

        # ================================================================== BAR CHART
        lives = [cdict for cdict in DATA["cutters"] if cdict["tool"] != 11]
        lives.sort(key=lambda r: r["life"])

        def col(r):
            if r["holder"] >= 160:
                return DANGER
            return HEAT if r["rdoc"] >= 8 else SIGNAL

        bx0 = -5.0
        bscale = 9.0 / 150.0
        pitch, bh = 0.42, 0.27
        ytop = 2.75
        bars = VGroup()
        for i, r in enumerate(lives):
            ln = r["life"] * bscale
            b = RoundedRectangle(width=ln, height=bh, corner_radius=0.05, stroke_width=0)
            b.set_fill(col(r), opacity=0.9)
            b.move_to([bx0 + ln / 2, ytop - i * pitch, 0])
            bars.add(b)
        axis = Line([bx0, ytop + 0.3, 0], [bx0, ytop - 12 * pitch - 0.3, 0], stroke_width=2, color=DIM)

        lab15 = N("15", size=30, color=INK).next_to(bars[0], RIGHT, buff=0.18)
        lab150 = N("150", size=30, color=INK).next_to(bars[-1], RIGHT, buff=0.18)
        cyc = T("cycles", size=24, color=DIM).next_to(lab150, RIGHT, buff=0.16).align_to(lab150, DOWN)

        def chip(colr, text):
            sw = RoundedRectangle(width=0.36, height=0.2, corner_radius=0.04, stroke_width=0).set_fill(colr, 0.9)
            tx = T(text, size=22, color=DIM)
            return VGroup(sw, tx).arrange(RIGHT, buff=0.14)

        legend = VGroup(chip(DANGER, "long holder"), chip(HEAT, "wide bite"), chip(SIGNAL, "narrow bite"))
        legend.arrange(RIGHT, buff=0.7).move_to([0.0, -3.35, 0])

        # freeze the straight beam and morph it into the shortest bar
        beam.clear_updaters()
        straight = RoundedRectangle(width=2 * L1, height=h, corner_radius=0.05, stroke_width=0)
        straight.set_fill(DANGER, opacity=0.9).move_to([x0 + L1, y0, 0])
        self.remove(beam, force, delta, trace, hist_rec)
        self.add(straight)
        bar0 = bars[0].copy()
        stubs = [b.copy().stretch_to_fit_width(0.02, about_edge=LEFT) for b in bars[1:]]
        self.play(ReplacementTransform(straight, bar0, run_time=0.8),
                  Create(axis, run_time=0.8),
                  LaggedStart(*[ReplacementTransform(sb, b) for sb, b in zip(stubs, bars[1:])], lag_ratio=0.1,
                              run_time=1.35),
                  FadeIn(legend, shift=UP * 0.1, run_time=1.35,
                         rate_func=lambda a: smooth(np.clip((a - 0.65) / 0.35, 0, 1))))
        self.add(bars[0])
        self.remove(bar0)
        self.wait_until(c(4) + 1.5)                     # "fifteen"
        self.play(FadeIn(lab15, shift=RIGHT * 0.1), Indicate(bars[0], color=DANGER, scale_factor=1.06),
                  run_time=0.5)
        self.wait_until(c(4) + 2.05)                    # "a hundred and fifty"
        self.play(FadeIn(lab150, shift=RIGHT * 0.1), Indicate(bars[-1], color=SIGNAL, scale_factor=1.04),
                  run_time=0.5)
        self.wait_until(c(4) + 3.2)                     # "cycles"
        self.play(FadeIn(cyc), run_time=0.4)

        frame.clear_updaters()
        self.remove(frame)
        self.remove(clock)
        for m in self.mobjects:      # freeze live parts so the closing fade sees fixed shapes
            m.clear_updaters()
        self.finish()
