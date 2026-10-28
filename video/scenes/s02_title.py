"""s02_title — "ToolLife Policy" builds from darkness, lifts, then the story chain:
steel -> signals -> ones and zeros -> a decision that splits into keep / change."""
import sys, os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from style import *  # noqa: F401,F403
from s01_cold_open import (EndMill, Sparks, steel_block_points, hatch_segments, multi_poly_points, to3,  # noqa: E402
                           set_vm_points, smooth01, STEEL_LIT, STEEL_SHADE, HATCH)

if os.environ.get("TL_PREVIEW"):
    config.pixel_width = 854
    config.pixel_height = 480
    config.frame_rate = int(os.environ.get("TL_FPS", "15"))


def title_text(size=84, spacing=2600, color=INK):
    """The film's title: Avenir Next Ultra Light, letter-spaced. Submobjects are the letters."""
    return MarkupText(f'<span letter_spacing="{spacing}">ToolLife Policy</span>', font=FONT,
                      weight=ULTRALIGHT, font_size=size, color=color)


class GlowDot(VGroup):
    """A dot with a soft halo. Fade it through .alpha (a ValueTracker), not set_opacity."""

    def __init__(self, color, r=0.05, glow=0.22, alpha=1.0):
        super().__init__(Dot(radius=glow, color=color), Dot(radius=glow * 0.55, color=color),
                         Dot(radius=r, color=color))
        self.levels = [0.10, 0.22, 1.0]
        self.alpha = ValueTracker(alpha)
        self.add_updater(lambda m: m.apply_alpha())
        self.apply_alpha()

    def apply_alpha(self):
        a = self.alpha.get_value()
        for d, lv in zip(self, self.levels):
            d.set_opacity(lv * a)
        return self


class S02Title(TLScene):
    SID = "s02_title"

    def construct(self):
        Y = -0.35
        XS = [-5.35, -2.15, 0.9, 3.7]

        frame = self.camera.frame
        frame.save_state()
        cam_t = {"t": 0.0}

        def cam_upd(m, dt):
            cam_t["t"] += dt
            s = smooth01(cam_t["t"] / self.total)
            m.set(width=config.frame_width * (1 - 0.045 * s))
            m.move_to(np.array([0.12 * s, -0.05 * s, 0]))
        frame.add_updater(cam_upd)
        self.add(frame)

        # ---------------- title ----------------
        title = title_text()
        title.move_to(UP * 0.25)
        cx = title.get_center()[0]
        rule = Line(LEFT, RIGHT).set_stroke(INK, width=1.3, opacity=0.65)
        rule.set_width(title.width * 0.92).next_to(title, DOWN, buff=0.38)
        anims = []
        for ch in title:
            dx = (ch.get_center()[0] - cx) * 0.28
            anims.append(FadeIn(ch, shift=LEFT * dx))
        self.wait_until(0.42)
        self.play(LaggedStart(*anims, lag_ratio=0.07, run_time=1.7, rate_func=smooth))
        self.play(GrowFromCenter(rule), run_time=0.6, rate_func=smooth)
        self.wait_until(self.cue(1) + 0.05)
        head = VGroup(title, rule)
        self.play(head.animate.scale(0.46).move_to(UP * 2.95), run_time=1.1, rate_func=smooth)

        # ---------------- faint chain skeleton ("feel that moment coming") ----------------
        ghosts = VGroup(*[Dot(np.array([x, Y, 0]), radius=0.045, color=DIM).set_opacity(0.6) for x in XS])
        skel = DashedLine(np.array([XS[0], Y, 0]), np.array([XS[-1] + 0.8, Y, 0]), dash_length=0.08,
                          dashed_ratio=0.45).set_stroke(FAINT, width=1.6)
        self.wait_until(3.75)
        self.play(Create(skel), LaggedStart(*[FadeIn(g, scale=0.5) for g in ghosts], lag_ratio=0.25),
                  run_time=1.2, rate_func=smooth)

        # a soft pulse runs along the skeleton
        probe = GlowDot(SIGNAL, r=0.04, glow=0.2, alpha=0.0)
        probe.move_to(skel.get_start())
        self.add(probe)
        self.play(probe.animate.move_to(np.array([XS[-1] + 0.8, Y, 0])),
                  probe.alpha.animate(rate_func=there_and_back_with_pause).set_value(1.0),
                  run_time=1.3, rate_func=smooth)
        self.remove(probe)

        # ---------------- glyph 1: steel block with the cutter ----------------
        g1x = XS[0]
        R1 = 0.5
        c1 = np.array([g1x - 0.3, Y + 0.05, 0])
        ae = 0.5 * R1
        top_y = c1[1] - R1 + ae
        floor_y = c1[1] - R1
        x_exit = c1[0] + np.sqrt(R1 * R1 - (R1 - ae) ** 2)

        def f1(x):
            if x >= x_exit:
                return top_y
            if x >= c1[0]:
                return c1[1] - np.sqrt(max(R1 * R1 - (x - c1[0]) ** 2, 0))
            return floor_y
        bx0, bx1, by = g1x - 1.0, g1x + 1.0, c1[1] - R1 - 0.5
        poly, top = steel_block_points(f1, bx0, bx1, by, n=120)
        block = VMobject().set_points_as_corners(to3(poly)).set_stroke(width=0)
        block.set_fill([STEEL_LIT, STEEL_SHADE], opacity=1).set_sheen_direction(DOWN)
        edge = VMobject().set_points_as_corners(to3(top)).set_stroke(STEEL, width=1.6)
        hatch = VMobject()
        set_vm_points(hatch, multi_poly_points([to3(s) for s in hatch_segments(f1, bx0, bx1, by, 0.14)]))
        hatch.set_stroke(HATCH, width=0.9, opacity=0.8)
        steel = VGroup(block, hatch, edge)

        mill = EndMill(R=R1, n_ghost=2)
        mill_state = {"a": 0.4, "alpha": 0.0, "on": False}
        th_exit = -PI / 2 + np.arccos(1 - ae / R1)
        exit_pt = c1 + R1 * np.array([np.cos(th_exit), np.sin(th_exit), 0])
        sparks = Sparks(cap=160, seed=5)
        sparks.floor = (x_exit + 0.01, top_y)
        t_dir = np.array([-np.sin(th_exit), np.cos(th_exit)])

        def mill_upd(m, dt):
            if mill_state["on"]:
                mill_state["alpha"] = min(1.0, mill_state["alpha"] + dt / 0.5)
            w = 1.6 * TAU
            a_prev = mill_state["a"]
            mill_state["a"] += w * dt
            for k in range(4):
                p = (a_prev + k * PI / 2 - th_exit) // TAU
                q = (mill_state["a"] + k * PI / 2 - th_exit) // TAU
                if q > p and mill_state["alpha"] > 0.3:
                    sparks.spawn(7, exit_pt, t_dir, spread=0.35, vmin=1.0, vmax=2.6, lmin=0.18, lmax=0.42,
                                 jitter=0.004)
            m.update_state(mill_state["a"], c1, alpha=mill_state["alpha"], blur=w / 60 * 1.5,
                           stroke=1.6)
            sparks.step(dt, g=4.0, drag=1.5)
            sparks.draw(1.0, alpha=mill_state["alpha"], blur_k=0.03, core_w=1.4, halo_w=4)
        mill.add_updater(mill_upd)

        # ---------------- glyph 2: the real vibration waveform ----------------
        vib = np.array(DATA["vibration"]["new"][:420])
        vib = vib / np.abs(vib).max()
        wx = np.linspace(XS[1] - 1.0, XS[1] + 1.0, len(vib))
        wave = VMobject().set_points_as_corners(to3(np.column_stack([wx, Y + 0.55 * vib])))
        wave.set_stroke(SIGNAL, width=2.2)

        # ---------------- glyph 3: bits ----------------
        bit_str = "0110"
        bits = VGroup()
        alt = VGroup()
        for i, b in enumerate(bit_str):
            d0 = N(b, size=58, color=DATA_C)
            d1 = N("1" if b == "0" else "0", size=58, color=DATA_C)
            bits.add(d0)
            alt.add(d1)
        bits.arrange(RIGHT, buff=0.12).move_to(np.array([XS[2], Y, 0]))
        for d0, d1 in zip(bits, alt):
            d1.move_to(d0)
            d1.set_opacity(0)

        # ---------------- glyph 4: the fork ----------------
        node = np.array([XS[3] - 0.1, Y, 0])
        stem = Line(np.array([XS[3] - 0.8, Y, 0]), node).set_stroke(INK, width=2.4, opacity=0.9)
        up_end = node + np.array([1.05, 0.9, 0])
        dn_end = node + np.array([1.05, -0.9, 0])
        br_up = CubicBezier(node, node + np.array([0.55, 0, 0]), up_end - np.array([0.5, 0, 0]), up_end)
        br_dn = CubicBezier(node, node + np.array([0.55, 0, 0]), dn_end - np.array([0.5, 0, 0]), dn_end)
        for b in (br_up, br_dn):
            b.set_stroke(INK, width=2.4, opacity=0.9)
        node_dot = Dot(node, radius=0.06, color=INK)
        end_up = Dot(up_end, radius=0.055, color=INK)
        end_dn = Dot(dn_end, radius=0.055, color=INK)
        fork = VGroup(stem, br_up, br_dn, node_dot, end_up, end_dn)
        lab_keep = T("keep", size=36, color=GOOD).next_to(up_end, RIGHT, buff=0.24)
        lab_change = T("change", size=36, color=WARN).next_to(dn_end, RIGHT, buff=0.24)

        # ---------------- arrows between glyphs ----------------
        def link(x0, x1):
            return Arrow(np.array([x0, Y, 0]), np.array([x1, Y, 0]), buff=0, stroke_width=1.6,
                         tip_length=0.12, max_tip_length_to_length_ratio=0.2, color=DIM)
        a12 = link(XS[0] + 1.15, XS[1] - 1.15)
        a23 = link(XS[1] + 1.15, bits.get_left()[0] - 0.2)
        a34 = link(bits.get_right()[0] + 0.2, XS[3] - 0.9)

        # ---------------- the build, word by word ----------------
        self.wait_until(LEAD + 6.05 - 0.2)                       # "steel"
        mill_state["on"] = True
        mill.set_z_index(2)
        sparks.set_z_index(3)
        self.add(sparks)
        self.add(mill)
        self.play(FadeIn(steel, shift=UP * 0.1), FadeOut(ghosts[0]), FadeOut(skel), run_time=0.55)
        self.wait_until(LEAD + 6.58 - 0.05)                      # "to signals"
        self.play(GrowArrow(a12), run_time=0.35)
        self.play(Create(wave), FadeOut(ghosts[1]), run_time=0.7, rate_func=linear)
        self.wait_until(LEAD + 7.67 - 0.05)                      # "to ones and zeros"
        self.play(GrowArrow(a23), run_time=0.3)
        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.15) for b in bits], lag_ratio=0.3),
                  FadeOut(ghosts[2]), run_time=0.7)

        # bits flicker from now on
        flick = {"t": 0.0}
        rng = np.random.default_rng(4)
        flips = np.sort(rng.uniform(0.3, 7.0, 9))     # brief blinks: a bit flips, then flips back
        flip_idx = rng.integers(0, 4, len(flips))

        def bits_upd(m, dt):
            flick["t"] += dt
            tt = flick["t"]
            for i, (d0, d1) in enumerate(zip(bits, alt)):
                on = bool(np.any((flip_idx == i) & (flips < tt) & (tt < flips + 0.28)))
                d0.set_opacity(0 if on else 1)
                d1.set_opacity(1 if on else 0)
        self.add(alt)
        alt.add_updater(bits_upd)

        # a pulse travels along the chain ("and back to one simple decision")
        pulse = GlowDot(SIGNAL, r=0.045, glow=0.22, alpha=0.0)
        self.add(pulse)
        self.wait_until(LEAD + 9.48)
        pulse.move_to(np.array([XS[0] + 0.92, Y, 0]))
        self.play(pulse.alpha.animate.set_value(1), run_time=0.15)
        self.play(pulse.animate.move_to(a23.get_end()), run_time=0.6, rate_func=smooth)
        self.play(GrowArrow(a34), pulse.animate.move_to(a34.get_end()), run_time=0.45, rate_func=smooth)
        self.wait_until(LEAD + 10.98 - 0.15)                     # "decision"
        self.play(Create(stem), pulse.animate.move_to(node), FadeOut(ghosts[3]), run_time=0.3)
        self.play(Create(br_up), Create(br_dn), FadeIn(node_dot, scale=0.5), FadeIn(end_up, scale=0.5),
                  FadeIn(end_dn, scale=0.5), pulse.alpha.animate.set_value(0), run_time=0.45)

        # "keep cutting"
        self.wait_until(LEAD + 12.01 - 0.3)
        pulse.move_to(node)
        pulse.alpha.set_value(1)
        self.play(MoveAlongPath(pulse, br_up), run_time=0.3, rate_func=smooth)
        keep_glow = GlowDot(GOOD, r=0.06, glow=0.3, alpha=0.0).move_to(up_end)
        self.add(keep_glow)
        self.play(br_up.animate.set_stroke(GOOD, width=3, opacity=1), end_up.animate.set_color(GOOD),
                  keep_glow.alpha.animate.set_value(1), FadeIn(lab_keep, shift=RIGHT * 0.12),
                  pulse.alpha.animate.set_value(0), run_time=0.4)

        # "or change the tool"
        self.wait_until(LEAD + 13.27 - 0.3)
        pulse.move_to(node)
        pulse.alpha.set_value(1)
        self.play(MoveAlongPath(pulse, br_dn), run_time=0.3, rate_func=smooth)
        change_glow = GlowDot(WARN, r=0.06, glow=0.3, alpha=0.0).move_to(dn_end)
        self.add(change_glow)
        self.play(br_dn.animate.set_stroke(WARN, width=3, opacity=1), end_dn.animate.set_color(WARN),
                  change_glow.alpha.animate.set_value(1), FadeIn(lab_change, shift=RIGHT * 0.12),
                  pulse.alpha.animate.set_value(0), run_time=0.45)

        # gentle breathing on the two choices until the end
        breathe = {"t": 0.0}

        def br_upd(m, dt):
            breathe["t"] += dt
            s = 0.5 + 0.5 * np.sin(breathe["t"] * 4.0)
            keep_glow.levels[0] = 0.07 + 0.08 * s
            change_glow.levels[0] = 0.07 + 0.08 * (1 - s)
        self.add(breathe_drv := Dot(radius=0.001).set_opacity(0))
        breathe_drv.add_updater(br_upd)

        self.wait_until(self.total - 0.5)
        for m in (mill, alt, breathe_drv, keep_glow, change_glow, pulse):
            m.clear_updaters()
        frame.clear_updaters()
        self.remove(frame)
        self.finish()
