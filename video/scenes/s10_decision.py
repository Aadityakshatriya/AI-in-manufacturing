import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from style import *

DEC = DATA["decisions"]
C_BREAK = DEC["costs_inr"]["breakage"]           # 6530
C_CHANGE = DEC["costs_inr"]["planned_change"]    # 3133
PC = {(r["policy"], r["tool"]): r for r in DEC["per_cutter"]}
TOOLS = sorted({r["tool"] for r in DEC["per_cutter"]}, key=lambda t: PC[("dp", t)]["L"])
T103 = DATA["tcn_cutter103"]
CHANGE_AT = PC[("dp", 103)]["good"]              # our rule changed cutter 103 after this many cycles (47)
N_FIXED = max(PC[("fixed", t)]["good"] for t in TOOLS if not PC[("fixed", t)]["broke"])   # the "every N" interval


def inr(v):
    return "₹" + f"{v:,}"


def _ss(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def _camera_path(keys):
    def f(t):
        if t <= keys[0][0]:
            return keys[0][1:]
        for a, b in zip(keys, keys[1:]):
            if t <= b[0]:
                u = _ss((t - a[0]) / (b[0] - a[0]))
                return tuple(a[i] + (b[i] - a[i]) * u for i in (1, 2, 3))
        return keys[-1][1:]
    return f


def risk_weight(c):
    """Visual weight of 'risk x breakage' relative to the change cost, for cutter 103 at cycle c.
    Driven by the TCN's real predicted cycles-left (pred_q50); it crosses 1 exactly at the cycle where
    our rule changed this cutter. Only the picture uses it; no number from it is shown."""
    pred = np.interp(c, T103["cycle"], T103["pred_q50"])
    p0 = np.interp(CHANGE_AT, T103["cycle"], T103["pred_q50"])
    return 1.12 * np.exp(-(pred - p0) / 20.0)


def cross(size=0.12, color=DANGER, width=4):
    return VGroup(Line(UL * size, DR * size), Line(UR * size, DL * size)).set_stroke(color, width)


class S10Decision(TLScene):
    SID = "s10_decision"

    def construct(self):
        frame = self.camera.frame
        cam = _camera_path([
            (0.0, 0.0, 0.3, 13.6), (13.9, 0.0, 0.35, 12.9),
            (14.8, 0.2, 0.1, 14.3), (20.7, 0.2, 0.1, 13.9),
        ])
        cyc_keys = [(2.4, 1), (4.0, 12), (6.6, 35), (9.0, 42), (10.9, 45), (12.1, CHANGE_AT)]
        cyc = ValueTracker(1.0)
        clock = ValueTracker(0.0)

        def tick(m, dt):
            t = self.renderer.time
            m.set_value(t)
            cyc.set_value(float(np.interp(t, [k[0] for k in cyc_keys], [k[1] for k in cyc_keys])))
            cx, cy, w = cam(t)
            frame.set_width(w)
            frame.move_to([cx, cy, 0])
        clock.add_updater(tick)
        self.add(clock)

        # ================= the balance =================
        P = np.array([0.0, 0.75, 0.0])
        LB, TH = 3.0, 15 * DEGREES
        boost = ValueTracker(0.0)

        def theta():
            return TH * np.tanh(2 * (risk_weight(cyc.get_value()) - 1)) + boost.get_value()

        def ends():
            a = theta()
            u = np.array([np.cos(a), np.sin(a), 0.0])
            return P - LB * u, P + LB * u          # left end goes down when theta > 0

        HANG, RIM = 1.3, 0.56
        S0 = 0.62                                    # side of the "change cost" block

        post = Line(P + DOWN * 0.3, np.array([0, -2.35, 0])).set_stroke(STEEL, 3)
        foot = Polygon([-0.75, -2.45, 0], [0.75, -2.45, 0], [0.42, -2.25, 0], [-0.42, -2.25, 0])
        foot.set_stroke(STEEL, 2.5).set_fill(STEEL, 0.12)
        hub_bg = Circle(radius=0.33).move_to(P).set_stroke(width=0).set_fill(BG, 1).set_z_index(2)
        cutter = end_mill(radius=0.3).move_to(P).set_z_index(3)
        beam = Line(*ends()).set_stroke(INK, 3.5).set_z_index(1)

        def make_pan():
            s1, s2 = Line(ORIGIN, DL), Line(ORIGIN, DR)
            bowl = ArcBetweenPoints(LEFT * RIM, RIGHT * RIM, angle=PI / 2)
            g = VGroup(s1, s2, bowl).set_stroke(STEEL, 2)
            bowl.set_stroke(CARBIDE, 3)
            return g

        panL, panR = make_pan(), make_pan()

        def place_pan(g, H):
            s1, s2, bowl = g
            rim = H + DOWN * HANG
            s1.put_start_and_end_on(H, rim + LEFT * RIM)
            s2.put_start_and_end_on(H, rim + RIGHT * RIM)
            ref = (bowl.get_start() + bowl.get_end()) / 2
            bowl.shift(rim - ref)

        eL, eR = ends()
        place_pan(panL, eL)
        place_pan(panR, eR)

        def block_at(H, side, color):
            rim_y = (H + DOWN * HANG)[1]
            sq = Square(side).set_stroke(color, 2).set_fill(color, 0.8)
            return sq.move_to([H[0], rim_y - 0.14 + side / 2, 0])

        blockL = block_at(eL, S0 * np.sqrt(risk_weight(1)), DANGER)
        blockR = block_at(eR, S0, WARN)

        labL = T("risk × " + inr(C_BREAK), 30, INK, t2c={"risk": DANGER})
        labR = T(inr(C_CHANGE), 30, INK)
        subL = T("if it breaks", 20, DIM)
        subR = T("change now", 20, DIM)
        opL1, opL2, opR = ValueTracker(0.0), ValueTracker(0.0), ValueTracker(0.0)

        def place_labels():
            eL, eR = ends()
            labL.move_to(eL + DOWN * (HANG + 0.62))
            subL.next_to(labL, DOWN, buff=0.12)
            labR.move_to(eR + DOWN * (HANG + 0.62))
            subR.next_to(labR, DOWN, buff=0.12)
            labL[:4].set_opacity(opL1.get_value())
            labL[4:].set_opacity(opL2.get_value())
            subL.set_opacity(opL2.get_value())
            labR.set_opacity(opR.get_value())
            subR.set_opacity(opR.get_value())
        place_labels()

        cyc_lab = T("cycle", 26, DIM)
        cyc_num = always_redraw(lambda: N(str(int(np.floor(cyc.get_value() + 1e-6))), 40, DATA_C)
                                .next_to(cyc_lab, RIGHT, buff=0.18, aligned_edge=DOWN).shift(DOWN * 0.03))
        cyc_lab.move_to([-0.5, 2.95, 0])
        counter = VGroup(cyc_lab, cyc_num)

        self.add(labL, labR, subL, subR)
        self.wait_until(0.6)
        self.play(Create(post), Create(foot), run_time=0.6)
        self.play(Create(beam), FadeIn(hub_bg), GrowFromCenter(cutter), run_time=0.5)
        self.play(Create(panL), Create(panR), run_time=0.5)
        self.play(GrowFromEdge(blockR, DOWN), GrowFromEdge(blockL, DOWN), run_time=0.35)

        # from here the balance follows the cycle count
        beam.add_updater(lambda m: m.put_start_and_end_on(*ends()))
        panL.add_updater(lambda m: place_pan(m, ends()[0]))
        panR.add_updater(lambda m: place_pan(m, ends()[1]))
        blockL.add_updater(lambda m: m.become(block_at(ends()[0], S0 * np.sqrt(risk_weight(cyc.get_value())), DANGER)))
        blockR.add_updater(lambda m: m.move_to(block_at(ends()[1], S0, WARN)))
        labL.add_updater(lambda m: place_labels())
        cutter.add_updater(lambda m, dt: m.rotate(-dt * 0.9, about_point=P))

        self.wait_until(2.2)
        self.play(FadeIn(counter, shift=DOWN * 0.1), run_time=0.3)
        # "weigh the chance of breaking, times the cost of a breakage"
        self.wait_until(4.1)
        self.play(opL1.animate.set_value(1.0), run_time=0.4)
        self.wait_until(6.0)
        self.play(opL2.animate.set_value(1.0), run_time=0.4)
        # "against the cost of changing the tool right now"
        self.wait_until(8.1)
        self.play(opR.animate.set_value(1.0), run_time=0.4)
        # "When the risk outweighs the cost" -> the beam tips past level
        self.wait_until(12.12)
        self.play(boost.animate(rate_func=rate_functions.ease_out_back).set_value(8 * DEGREES), run_time=0.7)
        # "change it."
        change_w = T("change", 46, WARN).move_to(P + UP * 1.2)
        ring = Circle(radius=0.36).move_to(P).set_stroke(WARN, 4).set_z_index(4)
        fresh = end_mill(radius=0.3).move_to(P).set_z_index(3)
        self.wait_until(13.24)
        cutter.clear_updaters()
        self.play(FadeIn(change_w, scale=1.4), ring.animate.scale(5).set_stroke(opacity=0),
                  Indicate(blockR, color=WARN, scale_factor=1.25),
                  FadeOut(cutter, scale=0.2), FadeIn(fresh, scale=0.2), run_time=0.55)
        self.remove(ring)
        fresh.add_updater(lambda m, dt: m.rotate(-dt * 0.9, about_point=P))
        self.wait_until(14.02)

        # ================= replay on 13 real cutters =================
        x0, sx = -6.2, 8.2 / 150
        ys = [2.45 - i * 0.4 for i in range(len(TOOLS))]

        def X(v):
            return x0 + sx * v

        Ls = [PC[("dp", t)]["L"] for t in TOOLS]
        lines = VGroup(*[Line([x0, y, 0], [X(L), y, 0]).set_stroke(DIM, 2, 0.6) for y, L in zip(ys, Ls)])
        ends_t = VGroup(*[Line([X(L), y - 0.09, 0], [X(L), y + 0.09, 0]).set_stroke(DIM, 2, 0.8)
                          for y, L in zip(ys, Ls)])

        for m in [beam, panL, panR, blockL, blockR, labL, fresh, cyc_num]:
            m.clear_updaters()
        scale_parts = VGroup(post, foot, hub_bg, fresh, panL, panR, blockL, blockR, labL, labR, subL, subR,
                             counter, change_w)
        self.play(*[ReplacementTransform(beam.copy(), ln) for ln in lines], FadeOut(beam),
                  FadeOut(scale_parts, shift=DOWN * 0.3), FadeIn(ends_t, run_time=0.3, rate_func=lambda a: _ss(a * 3 - 2)),
                  run_time=0.75)

        def pass_layer(policy, color, ph, pop_units):
            """Fill lines, markers and a break counter that follow the playhead ph (cycles)."""
            fills, marks, dimtr = VGroup(), VGroup(), ValueTracker(1.0)
            broke_at = []
            for y, t in zip(ys, TOOLS):
                r = PC[(policy, t)]
                stop = r["L"] if r["broke"] else r["good"]
                fl = Line([x0, y, 0], [x0 + 0.01, y, 0]).set_stroke(color, 5, 0.0)

                def fupd(m, y=y, stop=stop):
                    x = X(min(ph.get_value(), stop))
                    if x - x0 < 0.01:
                        m.set_stroke(opacity=0.0)
                        return
                    m.put_start_and_end_on([x0, y, 0], [x, y, 0])
                    m.set_stroke(opacity=0.9 * dimtr.get_value())
                fl.add_updater(fupd)
                fills.add(fl)
                if r["broke"]:
                    base = cross(0.13, DANGER, 4)
                    broke_at.append(stop)
                else:
                    base = Line(UP * 0.17, DOWN * 0.17).set_stroke(GOOD, 5)
                mk = base.copy().set_stroke(opacity=0.0)

                def mupd(m, base=base, pos=np.array([X(stop), y, 0]), stop=stop):
                    v = ph.get_value()
                    if v < stop:
                        m.set_stroke(opacity=0.0)
                        return
                    k = rate_functions.ease_out_back(min((v - stop) / pop_units, 1.0))
                    m.become(base.copy().scale(max(k, 1e-3)).move_to(pos))
                    m.set_stroke(opacity=dimtr.get_value())
                mk.add_updater(mupd)
                marks.add(mk)
            return fills, marks, dimtr, broke_at

        # counters on the right
        cx0 = 3.3
        labA = T("every N", 28, DIM).move_to([cx0, 1.6, 0], aligned_edge=LEFT)
        labB = T("our rule", 28, SIGNAL).move_to([cx0, -0.8, 0], aligned_edge=LEFT)
        brA = T("broke", 30, DANGER).move_to([cx0 + 1.42, 0.74, 0], aligned_edge=LEFT)
        brB = T("broke", 30, DANGER).move_to([cx0 + 1.42, -1.66, 0], aligned_edge=LEFT)

        def big_num(n, y, color=INK):
            return N(str(n), 72, color).move_to([cx0 + 1.22, y, 0], aligned_edge=RIGHT)

        # pass 1: change every N cycles
        ph1 = ValueTracker(0.0)
        fills1, marks1, dim1, broke1 = pass_layer("fixed", CARBIDE, ph1, 16)
        numA = always_redraw(lambda: big_num(sum(1 for s in broke1 if ph1.get_value() >= s), 0.85))
        nline = DashedLine([X(N_FIXED), ys[0] + 0.32, 0], [X(N_FIXED), ys[-1] - 0.25, 0], dash_length=0.08)
        nline.set_stroke(WARN, 2, 0.75)
        nlab = T("N", 26, WARN).next_to(nline, UP, buff=0.08)
        self.add(fills1, marks1)
        self.play(FadeIn(labA, shift=LEFT * 0.1), FadeIn(brA), FadeIn(numA),
                  Create(nline), FadeIn(nlab), run_time=0.3)
        self.play(ph1.animate.set_value(150.0), run_time=1.1, rate_func=linear)
        numA.clear_updaters()
        self.remove(numA)
        numA = big_num(len(broke1), 0.85)
        self.add(numA)

        # pass 2: our rule
        ph2 = ValueTracker(0.0)
        fills2, marks2, dim2, broke2 = pass_layer("dp", SIGNAL, ph2, 26)
        numB = always_redraw(lambda: big_num(sum(1 for s in broke2 if ph2.get_value() >= s), -1.55))
        self.add(fills2, marks2)
        self.play(dim1.animate.set_value(0.28), nline.animate.set_stroke(opacity=0.0), nlab.animate.set_opacity(0),
                  FadeIn(labB, shift=LEFT * 0.1), FadeIn(brB), FadeIn(numB), run_time=0.2)
        self.play(ph2.animate.set_value(150.0), run_time=0.7, rate_func=linear)
        numB.clear_updaters()
        self.remove(numB)
        numB = big_num(len(broke2), -1.55)
        self.add(numB)

        # "instead of ten"
        self.wait_until(18.72)
        self.play(dim1.animate(rate_func=there_and_back).set_value(1.0),
                  numA.animate(rate_func=there_and_back).scale(1.18, about_edge=RIGHT).set_color(DANGER), run_time=0.7)
        under = Line(numB.get_corner(DL) + DOWN * 0.14, numB.get_corner(DR) + DOWN * 0.14).set_stroke(SIGNAL, 4)
        self.play(numA.animate.set_color(DIM), brA.animate.set_opacity(0.45),
                  Create(under), numB.animate.scale(1.08, about_edge=LEFT), run_time=0.45)

        for m in [*fills1, *marks1, *fills2, *marks2]:
            m.clear_updaters()
        self.remove(*[m for m in self.mobjects if isinstance(m, ValueTracker)])
        self.finish()
