"""s06_bits — the sound becomes numbers, the numbers become bits, one cut becomes a 5 x 4,096 grid, and one
cutter's life becomes millions of readings. Opens on the same worn waveform, in the same place, that closes
s05."""

import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from style import *  # noqa: F401,F403

from manim.utils.family import extract_mobject_family_members as _fam
from manim.utils.iterables import list_update as _list_update


def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def mix(a, b, t):
    return ManimColor(a).interpolate(ManimColor(b), float(np.clip(t, 0, 1)))


def P(x, y):
    return np.array([x, y, 0.0])


def redraw(func):
    """Like always_redraw, but swaps in freshly built children each frame (no family-alignment glitches)."""
    holder = VGroup(func())

    def upd(m):
        m.remove(*m.submobjects)
        m.add(func())

    holder.add_updater(upd)
    return holder


class LiveFamilies:
    """Scene mixin: give the camera moving top-level mobjects so swapped-in children are drawn live."""

    def get_moving_and_static_mobjects(self, animations):
        tops = _list_update(self.mobjects, self.foreground_mobjects)
        z = self.renderer.camera.use_z_index
        flat = self.get_moving_mobjects(*animations)
        if not flat:
            return [], _fam(tops, use_z_index=z, only_those_with_points=True)
        first = flat[0]
        idx = next((i for i, m in enumerate(tops) if first in m.get_family()), 0)
        return tops[idx:], _fam(tops[:idx], use_z_index=z, only_those_with_points=True)


# same strip geometry as the end of s05
WX0, WX1, WY, WA = -4.7, 6.2, 1.85, 0.42


class S06Bits(LiveFamilies, TLScene):
    SID = "s06_bits"

    def construct(self):
        clock = ValueTracker(0.0)
        clock.add_updater(lambda m, dt: m.set_value(self.renderer.time))
        self.add(clock)
        c = self.cue
        TOTAL = self.total

        vib = np.array(DATA["vibration"]["worn"])
        n = len(vib)

        # ------------------------------------------------------------ zoom states
        W1 = (301, 451)          # ~150 samples around the once-per-turn hit
        W2 = (373, 379)          # 6 samples on the falling edge (crosses zero)
        states = [
            dict(sx=(WX1 - WX0) / (n - 1), ic=(n - 1) / 2, xc=(WX0 + WX1) / 2, yc=WY, A=WA),
            dict(sx=12.6 / (W1[1] - W1[0] - 1), ic=(W1[0] + W1[1] - 1) / 2, xc=0.0, yc=0.35, A=1.15),
            dict(sx=11.0 / (W2[1] - W2[0] - 1), ic=(W2[0] + W2[1] - 1) / 2, xc=0.0, yc=0.2, A=2.6),
        ]
        zt = ValueTracker(0.0)

        def zstate():
            u = float(np.clip(zt.get_value(), 0, 2 - 1e-9))
            k = int(u)
            f = u - k
            a, b = states[k], states[k + 1]
            return dict(sx=a["sx"] ** (1 - f) * b["sx"] ** f,
                        ic=a["ic"] * (1 - f) + b["ic"] * f,
                        xc=a["xc"] * (1 - f) + b["xc"] * f,
                        yc=a["yc"] * (1 - f) + b["yc"] * f,
                        A=a["A"] ** (1 - f) * b["A"] ** f)

        def sample_xy(i, st):
            return P(st["xc"] + (i - st["ic"]) * st["sx"], st["yc"] + st["A"] * vib[i])

        vis_curve = ValueTracker(0.0)
        vis_win = ValueTracker(0.0)
        stem_prog = ValueTracker(0.0)

        def make_wave():
            st = zstate()
            v = vis_curve.get_value()
            g = VGroup()
            if v < 0.003:
                return g
            xs = st["xc"] + (np.arange(n) - st["ic"]) * st["sx"]
            m = (xs > -7.6) & (xs < 7.6)
            idx = np.nonzero(m)[0]
            if len(idx) > 1:
                lo, hi = max(idx[0] - 1, 0), min(idx[-1] + 1, n - 1)
                pts = [sample_xy(i, st) for i in range(lo, hi + 1)]
                base = DashedLine(P(max(xs[lo], -7.6), st["yc"]), P(min(xs[hi], 7.6), st["yc"]), dash_length=0.06,
                                  dashed_ratio=0.4, stroke_width=1.2, color=FAINT).set_stroke(opacity=v)
                g.add(base)
                g.add(VMobject(stroke_width=2.2 + 0.8 * min(1, zt.get_value()), color=SIGNAL)
                      .set_points_as_corners(pts).set_stroke(opacity=v))
            # sample stems + dots
            sp = stem_prog.get_value()
            if sp > 0.0:
                thr = -6.9 + 13.8 * sp
                r = float(np.clip(0.33 * st["sx"], 0.026, 0.1))
                for i in idx:
                    x = xs[i]
                    k = np.clip((thr - x) / 0.9, 0, 1)
                    if k <= 0:
                        continue
                    k = smooth01(k)
                    p = sample_xy(i, st)
                    top = P(x, st["yc"] + (p[1] - st["yc"]) * k)
                    g.add(Line(P(x, st["yc"]), top, stroke_width=1.6, color=DATA_C).set_stroke(opacity=0.75 * v))
                    g.add(Dot(top, radius=r, color=DATA_C).set_fill(opacity=v * k))
            # zoom window marker (on the full strip)
            w = vis_win.get_value()
            if w > 0.003:
                a = sample_xy(W1[0], st)[0]
                b = sample_xy(W1[1] - 1, st)[0]
                h = st["A"] * 2.6
                rect = Rectangle(width=b - a, height=h, stroke_width=1.6, color=INK)
                rect.move_to(P((a + b) / 2, st["yc"] - 0.25 * st["A"])).set_stroke(opacity=0.7 * w)
                g.add(rect)
            return g

        wave = redraw(make_wave)
        self.add(wave)

        # ---- "To a computer, that sound is only numbers."
        self.play(vis_curve.animate.set_value(1.0), run_time=0.45)
        self.wait_until(c(0) + 0.15)
        self.play(vis_win.animate.set_value(1.0), run_time=0.5)
        self.wait_until(c(0) + 0.95)
        self.play(zt.animate(rate_func=smooth).set_value(1.0), vis_win.animate(rate_func=lambda a: smooth01(a / 0.45)).set_value(0.0),
                  run_time=2.0)
        # ---- "Sample the wave,"
        self.wait_until(c(1))
        self.play(stem_prog.animate(rate_func=linear).set_value(1.0), run_time=0.95)
        # ---- "and every instant becomes a number."
        self.wait_until(c(1) + 0.95)
        self.play(zt.animate(rate_func=smooth).set_value(2.0), run_time=0.9)

        st2 = states[2]
        vals = vib[W2[0]:W2[1]]
        xs2 = [st2["xc"] + (i - st2["ic"]) * st2["sx"] for i in range(W2[0], W2[1])]
        nums = VGroup()
        for x, v in zip(xs2, vals):
            y = st2["yc"] + st2["A"] * v
            lab = N(f"{v:.2f}", size=46, color=DATA_C)
            lab.move_to(P(x, y + (0.62 if v >= 0 else -0.62)))
            nums.add(lab)
        self.play(LaggedStart(*[FadeIn(m, scale=0.5) for m in nums], lag_ratio=0.1), run_time=0.42)
        self.wait_until(c(2) - 0.6)

        # only the numbers remain, in a row across the frame
        ROW_Y = 1.95
        self.play(vis_curve.animate.set_value(0.0),
                  *[m.animate.move_to(P(x, ROW_Y)) for m, x in zip(nums, xs2)], run_time=0.55)
        self.remove(wave)

        # ---------------------------------------------------------------- heat-map strip (built early)
        fc = np.array(DATA["five_channels_new"])
        rows, ncol = fc.shape
        norm = fc / np.abs(fc).max(axis=1, keepdims=True)
        base_c = np.array(ManimColor(mix(BG, FAINT, 0.55)).to_rgb())
        pos_c = np.array(ManimColor(HEAT).to_rgb())
        neg_c = np.array(ManimColor(SIGNAL).to_rgb())
        img_arr = np.zeros((rows, ncol, 4), dtype=np.uint8)
        for r in range(rows):
            for k in range(ncol):
                v = norm[r, k]
                tgt = pos_c if v >= 0 else neg_c
                w_ = abs(v) ** 0.75
                rgb = base_c * (1 - w_) + tgt * w_
                img_arr[r, k, :3] = (rgb * 255).astype(np.uint8)
                img_arr[r, k, 3] = 255
        HM_W, HM_H = 12.0, 2.2
        HM_C = P(0.0, -0.75)
        RH = HM_H / rows
        PX = HM_W / ncol

        def make_image():
            im = ImageMobject(img_arr)
            im.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
            im.stretch_to_fit_width(HM_W)
            im.stretch_to_fit_height(HM_H)
            im.move_to(HM_C)
            return im

        heat = make_image()
        frame_hm = Rectangle(width=HM_W, height=HM_H, stroke_width=1.6, color=DIM).move_to(HM_C)
        x_left = HM_C[0] - HM_W / 2
        y_top = HM_C[1] + HM_H / 2
        MID = 2

        def row_y(r):
            return y_top - (r + 0.5) * RH

        # ---------------------------------------------------------------- bit rain (real bits of the waveform)
        allq = np.clip(np.round(vib / 2.2 * 127), -128, 127).astype(int)
        bitstream = "".join(format(int(x) & 0xFF, "08b") for x in allq[:120])
        gap = xs2[1] - xs2[0]
        rx = []
        for x in xs2[:-1]:
            rx += [x + gap * j / 4 for j in (1, 2, 3)]
        rx = [xs2[0] - 1.1, xs2[0] - 0.55] + rx + [xs2[-1] + 0.55, xs2[-1] + 1.1]
        RY = [3.85 - 0.375 * r for r in range(21)]
        t0g, t1g = N("0", size=24, color=DATA_C), N("1", size=24, color=DATA_C)
        glyphs = VGroup()
        gx, gy, gb, gc = [], [], [], []
        kk = 0
        for ci, x in enumerate(rx):
            for y in RY:
                ch = bitstream[kk % len(bitstream)]
                kk += 1
                g = (t1g if ch == "1" else t0g).copy().move_to(P(x, y))
                g.set_fill(opacity=0)
                glyphs.add(g)
                gx.append(x); gy.append(y); gb.append(ch == "1"); gc.append(ci)
        gy = np.array(gy); gb = np.array(gb); gc = np.array(gc)
        NC = len(rx)
        rr_ = np.random.default_rng(6)
        NH = 3
        spd = rr_.uniform(3.2, 6.0, (NC, NH))
        trl = rr_.uniform(1.8, 3.2, (NC, NH))
        phs = rr_.uniform(0, 12, (NC, NH))
        SPAN_TOP, SPAN_BOT = 4.4, -4.4
        rain_on = ValueTracker(0.0)
        rain_floor = ValueTracker(-4.5)
        HEADC = mix(DATA_C, INK, 0.65)

        def upd_rain(m):
            t = self.renderer.time
            on = rain_on.get_value()
            if on < 0.002:
                for g in m:
                    g.set_fill(opacity=0)
                return
            fl = rain_floor.get_value()
            best = np.zeros(len(gy))
            head = np.zeros(len(gy), dtype=bool)
            for hk in range(NH):
                span = (SPAN_TOP - SPAN_BOT) + trl[:, hk]
                hy = SPAN_TOP - ((t * spd[:, hk] + phs[:, hk]) % span)
                d = gy - hy[gc]
                L = trl[gc, hk]
                isH = np.abs(d) <= 0.17
                tr = np.where((d > 0.17) & (d <= L), (1 - d / L) ** 1.4, 0.0)
                val = np.where(isH, 1.0, tr * 0.85)
                head |= isH & (val >= best)
                best = np.maximum(best, val)
            best = best * np.where(gb, 1.0, 0.5) * on
            best[gy < fl] = 0.0
            for i, g in enumerate(m):
                o = float(best[i])
                if o < 0.01:
                    g.set_fill(opacity=0)
                else:
                    g.set_fill(HEADC if head[i] else DATA_C, opacity=o)

        glyphs.add_updater(upd_rain)

        # ---- "Every number becomes bits."
        q = np.clip(np.round(vals / 2.2 * 127), -128, 127).astype(int)
        codes = [format(int(x) & 0xFF, "08b") for x in q]
        BIT_DY = 0.43
        ONE_C = mix(DATA_C, INK, 0.2)
        cols = VGroup()
        for x, code in zip(xs2, codes):
            col = VGroup()
            for j, ch in enumerate(code):
                b = N(ch, size=40, color=ONE_C if ch == "1" else DIM)
                b.move_to(P(x, ROW_Y - j * BIT_DY))
                col.add(b)
            cols.add(col)
        anims = []
        for m, col in zip(nums, cols):
            anims.append(Succession(
                m.animate(run_time=0.14, rate_func=rush_into).stretch(0.02, 1),
                LaggedStart(*[FadeIn(b, shift=DOWN * 0.28, run_time=0.24) for b in col], lag_ratio=0.3),
            ))
        self.add(glyphs)
        self.play(LaggedStart(*anims, lag_ratio=0.085), run_time=1.05)
        self.remove(*nums)
        # the rain: many more bits, streaming down the whole frame
        self.play(rain_on.animate.set_value(1.0), run_time=0.5)
        self.wait_until(c(3) - 0.05)

        # ---- "One cut becomes five sensors, times four thousand and ninety-six readings."
        # the bit columns pour into the first readings of the middle row; the rain now falls into the strip
        NSEED = W2[1] - W2[0]
        pix = VGroup()
        for k in range(NSEED):
            v = norm[MID, k]
            tgt = HEAT if v >= 0 else SIGNAL
            rq = Rectangle(width=PX, height=RH, stroke_width=0)
            rq.set_fill(mix(mix(BG, FAINT, 0.55), tgt, abs(v) ** 0.75), opacity=1)
            rq.move_to(P(x_left + (k + 0.5) * PX, row_y(MID)))
            pix.add(rq)

        reveal = ValueTracker(float(NSEED))  # columns revealed
        rows_on = ValueTracker(0.0)          # other rows' first chunk

        def make_covers():
            g = VGroup()
            colsv = reveal.get_value()
            xr = x_left + colsv * PX
            if colsv < ncol - 0.01:
                g.add(Rectangle(width=x_left + HM_W - xr + 0.02, height=HM_H + 0.04, stroke_width=0)
                      .set_fill(BG, opacity=1).move_to(P((xr + x_left + HM_W) / 2 + 0.01, HM_C[1])))
            ro = rows_on.get_value()
            if ro < 0.999:
                for r in range(rows):
                    if r == MID:
                        continue
                    w = min(colsv, NSEED) * PX
                    g.add(Rectangle(width=w + 0.02, height=RH + 0.01, stroke_width=0)
                          .set_fill(BG, opacity=1 - smooth01(ro * 1.6 - abs(r - MID) * 0.3))
                          .move_to(P(x_left + w / 2, row_y(r))))
            return g

        covers = redraw(make_covers)

        # the sweep head glows where the rain lands
        def make_head():
            g = VGroup()
            colsv = reveal.get_value()
            if colsv <= NSEED + 0.5 or colsv >= ncol - 0.5:
                return g
            xh = x_left + colsv * PX
            g.add(Line(P(xh, y_top + 0.02), P(xh, y_top - HM_H - 0.02), stroke_width=3, color=DATA_C))
            g.add(Rectangle(width=0.5, height=HM_H, stroke_width=0).set_fill(DATA_C, opacity=0.10)
                  .move_to(P(xh - 0.25, HM_C[1])))
            return g

        head_glow = redraw(make_head)

        sens = VGroup(*[Dot(P(x_left - 0.32, row_y(r)), radius=0.08, color=SIGNAL) for r in range(rows)])

        LAB_Y = HM_C[1] - HM_H / 2 - 0.62

        def make_label():
            g = VGroup()
            colsv = reveal.get_value()
            ro = smooth01((colsv - NSEED) / 30.0)       # appears once the sweep is under way
            if ro < 0.01:
                return g
            count = int(round(colsv * 16)) if colsv < ncol - 0.01 else 4096
            a = N("5", size=50, color=INK)
            x_ = N("×", size=50, color=DIM)
            b = N(f"{count:,}", size=50, color=DATA_C)
            grp = VGroup(a, x_, b).arrange(RIGHT, buff=0.2)
            grp.move_to(P(-1.25, LAB_Y), aligned_edge=LEFT)
            grp.set_opacity(ro)
            return VGroup(grp)

        label = redraw(make_label)

        self.add(heat, covers, head_glow)
        self.bring_to_front(glyphs, cols)
        self.play(LaggedStart(*[ReplacementTransform(col, px) for col, px in zip(cols, pix)], lag_ratio=0.05),
                  Create(frame_hm), rain_floor.animate.set_value(y_top + 0.2), run_time=0.95)
        self.remove(*pix)
        self.add(label)                                       # "...five sensors"
        self.play(rows_on.animate.set_value(1.0), LaggedStart(*[FadeIn(d, scale=0.5) for d in sens], lag_ratio=0.15),
                  run_time=0.6)
        # "times four thousand and ninety-six readings"
        self.play(reveal.animate(rate_func=lambda a: 1 - (1 - a) ** 2.2).set_value(float(ncol)),
                  rain_on.animate(rate_func=lambda a: smooth01((a - 0.8) / 0.2)).set_value(0.0),
                  run_time=c(3) + 4.65 - self.now)
        glyphs.clear_updaters()
        self.remove(covers, glyphs, head_glow)
        self.wait_until(c(4) - 0.05)

        # ---- "One cutter's life becomes millions of them."
        label.clear_updaters()
        self.play(FadeOut(label), FadeOut(sens), run_time=0.35)
        FRONT_S, FRONT_C = 0.78, P(-1.05, -1.25)
        K = 30
        DX, DY, SC = 0.155, 0.122, 0.986
        stack = Group()
        for k in range(K, 0, -1):
            im = make_image()
            im.scale(FRONT_S * SC ** k)
            im.move_to(FRONT_C + P(DX * k, DY * k))
            stack.add(im)
        front = Group(heat, frame_hm)
        t_s0 = self.now + 0.15
        t_s1 = c(4) + 1.9

        def upd_stack(g):
            t = self.renderer.time
            for j, im in enumerate(g):
                k = K - j                       # depth index (1 = right behind the front)
                tk = t_s0 + (k - 1) / (K - 1) * (t_s1 - t_s0)
                a = smooth01((t - tk) / 0.18)
                im.set_opacity(a * (0.9 * (1 - (k - 1) / K) ** 1.3 + 0.06))

        stack.add_updater(upd_stack)
        upd_stack(stack)
        self.add(stack)
        self.bring_to_front(heat, frame_hm)

        total_n = 5 * 4096 * 116
        cnt = ValueTracker(5 * 4096)

        def make_counter():
            v = int(round(cnt.get_value()))
            a = N(f"{v:,}", size=46, color=DATA_C)
            a.move_to(FRONT_C + P(0, -1.35))
            return VGroup(a)

        counter = redraw(make_counter)
        cyc = T("116 cycles", size=24, color=DIM).move_to(FRONT_C + P(DX * K, DY * K) + P(1.2, 0.95))

        self.play(front.animate.scale(FRONT_S).move_to(FRONT_C), run_time=0.6)
        self.add(counter)
        self.play(cnt.animate(rate_func=lambda a: smooth01(a) ** 1.6).set_value(total_n),
                  run_time=t_s1 - self.now + 0.2)
        self.play(FadeIn(cyc, shift=UP * 0.1), run_time=0.4)

        self.remove(clock)
        for m in self.mobjects:
            m.clear_updaters()
        self.finish()
