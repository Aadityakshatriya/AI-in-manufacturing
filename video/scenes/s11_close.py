"""s11_close — steel -> signals -> numbers -> a choice (a quick morphing montage), then the cutter turns
calmly, a hairline crack glints, a radar sweep draws the risk of breaking around it, and the title."""
import sys, os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from style import *  # noqa: F401,F403
from s01_cold_open import (EndMill, Sparks, steel_block_points, hatch_segments, multi_poly_points, poly_bez,  # noqa: E402
                           to3, rot2, set_vm_points, smooth01, ease_out, crack_path, STEEL_LIT, STEEL_SHADE,
                           HATCH, HOT_WHITE)
from s02_title import title_text  # noqa: E402

if os.environ.get("TL_PREVIEW"):
    config.pixel_width = 854
    config.pixel_height = 480
    config.frame_rate = int(os.environ.get("TL_FPS", "15"))


def mix(c1, c2, s):
    return interpolate_color(ManimColor(c1), ManimColor(c2), float(np.clip(s, 0, 1)))


def risk_color(p):
    return mix(SIGNAL, WARN, p / 0.45) if p < 0.45 else mix(WARN, DANGER, (p - 0.45) / 0.5)


class ScalableMill(EndMill):
    """EndMill with an extra uniform scale applied when drawing (for the shrink into the title emblem)."""
    scale_f = 1.0

    def world(self, P, angle=None, center=None):
        angle = self.angle if angle is None else angle
        center = self.center_pt if center is None else center
        W = self.scale_f * (np.asarray(P)[:, :2] @ rot2(angle).T) + np.asarray(center)[:2]
        return to3(W)


class S11Close(TLScene):
    SID = "s11_close"

    def construct(self):
        rng = np.random.default_rng(31)
        TOT = self.total
        C0 = np.array([0.0, 0.1, 0.0])
        R = 1.5

        # word beats (scene clock)
        W_STEEL = LEAD + 0.08
        W_SIGNALS = LEAD + 0.82
        W_NUMBERS = LEAD + 1.9
        W_CHOICE = LEAD + 3.1
        T_CALM = self.cue(1) - 0.15          # "The tool will always break"
        W_BREAK = LEAD + 5.06
        T_SWEEP = self.cue(2) + 0.05         # "The only question is whether you see it coming"
        W_COMING = LEAD + 8.6
        T_TITLE = self.cue(3)                # "ToolLife Policy"

        # ---------------- live cutter + steel (montage beat 1, then the calm cutter) ----------------
        mill = ScalableMill(R=R, n_ghost=3)
        sparks = Sparks(cap=240, seed=12)
        ae = 0.5 * R
        y_top = C0[1] - R + ae
        y_floor = C0[1] - R
        th_exit = -PI / 2 + np.arccos(1 - ae / R)
        x_exit = C0[0] + R * np.cos(th_exit)
        exit_pt = C0 + R * np.array([np.cos(th_exit), np.sin(th_exit), 0])
        t_dir = np.array([-np.sin(th_exit), np.cos(th_exit)])
        sparks.floor = (x_exit + 0.02, y_top)

        def f_top(x):
            if x >= x_exit:
                return y_top
            if x >= C0[0]:
                return C0[1] - np.sqrt(max(R * R - (x - C0[0]) ** 2, 0))
            return y_floor
        poly, top = steel_block_points(f_top, -8.5, 8.5, -4.6, n=300)
        block = VMobject().set_points_as_corners(to3(poly)).set_stroke(width=0).set_sheen_direction(DOWN)
        block_edge = VMobject().set_points_as_corners(to3(top))
        hatch = VMobject()
        set_vm_points(hatch, multi_poly_points([to3(s) for s in hatch_segments(f_top, -8.5, 8.5, -4.6, 0.3)]))
        steel = VGroup(block, hatch, block_edge)

        crack = crack_path(R, np.random.default_rng(11))
        crack_core, crack_glow = VMobject(), VMobject()
        glint = VGroup(Line(LEFT * 0.22, RIGHT * 0.22), Line(DOWN * 0.22, UP * 0.22)).set_stroke(HOT_WHITE, 2)

        # halo (radar of the risk of breaking on each of the next 60 cycles)
        haz = np.array(DATA["tcn_cutter103"]["hazard_at"]["31"])
        n_bar = len(haz)
        RH = 2.15
        bars = [VMobject() for _ in range(6)]
        env = [VMobject() for _ in range(6)]
        base_ring = VMobject()
        sweep = [VMobject() for _ in range(6)]
        hot_glow = VMobject()

        BAR_COL = [risk_color(p) for p in np.linspace(0, 1, 6)]

        st = dict(mode="off", a=0.0, last_t=None, a_calm0=None)
        W_FAST = 2.2 * TAU
        W_CALM = 0.13 * TAU

        def emblem(t):
            s = smooth01((t - (T_TITLE - 0.42)) / 0.6)
            return C0 + (np.array([0, 1.85, 0]) - C0) * s, 1 - 0.64 * s

        def sweep_angle(t):
            u = np.clip((t - T_SWEEP) / (W_COMING - T_SWEEP + 0.05), 0, 1)
            return PI / 2 - TAU * smooth01(u) ** 0.9, u

        def tick(mob, dt):
            t = self.now
            ce, se = emblem(t)
            grow = ease_out((t - st["grow_t"]) / 0.6) if "grow_t" in st else 1.0
            mill.scale_f = se * max(grow, 1e-3)
            # rotation
            if st["mode"] == "fast":
                st["a"] += W_FAST * dt
            elif st["mode"] == "calm":
                st["a"] += W_CALM * dt * (1 + 5 * np.exp(-(t - st["grow_t"]) / 0.35))
            # ---- cutter ----
            if st["mode"] == "fast":
                a_in = smooth01((t - (W_STEEL - 0.12)) / 0.25)
                a_prev = st["a"] - W_FAST * dt
                for k in range(4):
                    if (st["a"] + k * PI / 2 - th_exit) // TAU > (a_prev + k * PI / 2 - th_exit) // TAU:
                        sparks.spawn(18, exit_pt, t_dir, spread=0.32, vmin=4, vmax=11, age_dither=dt)
                mill.update_state(st["a"], C0, alpha=a_in, blur=W_FAST / 60 * 1.7)
                steel_a = a_in
            elif st["mode"] in ("calm", "snap_in"):
                ma = smooth01((t - st["grow_t"]) / 0.3)
                mill.update_state(st["a"], ce, alpha=ma, blur=0.0)
                steel_a = 0.0
            else:
                mill.update_state(st["a"], C0, alpha=0.0)
                steel_a = 1 - smooth01((t - st.get("off_t", -9)) / 0.3)
            block.set_fill([STEEL_LIT, STEEL_SHADE], opacity=steel_a)
            hatch.set_stroke(HATCH, width=1.1, opacity=0.8 * steel_a)
            block_edge.set_stroke(mix(STEEL, INK, 0.35), width=2.2, opacity=steel_a)
            sparks.step(dt)
            sparks.draw(1.0, alpha=1.0, blur_k=0.03)

            # ---- the hairline crack ("will always break") ----
            if st["mode"] in ("calm", "snap_in") and t >= W_BREAK - 0.1:
                g = smooth01((t - (W_BREAK - 0.1)) / 0.18)
                lvl = g * (0.3 + 0.7 * np.exp(-max(0, t - W_BREAK - 0.1) / 0.35))
                Wc = mill.world(crack[: max(2, int(np.ceil(g * len(crack))))])
                set_vm_points(crack_core, poly_bez(Wc))
                set_vm_points(crack_glow, poly_bez(Wc))
                crack_core.set_stroke(DANGER, width=1.8, opacity=lvl)
                crack_glow.set_stroke(DANGER, width=7, opacity=0.35 * lvl)
                gl = np.exp(-max(0, t - W_BREAK - 0.05) / 0.22) * g
                glint.move_to(Wc[0]).set_stroke(opacity=gl)
                glint.set(height=0.44 * se * (0.6 + 0.6 * gl))
            else:
                set_vm_points(crack_core, np.zeros((0, 3)))
                set_vm_points(crack_glow, np.zeros((0, 3)))
                glint.set_stroke(opacity=0)

            # ---- radar halo ----
            th, u = sweep_angle(t)
            if t >= T_SWEEP:
                angs = PI / 2 - (np.arange(n_bar) + 0.5) * TAU / n_bar
                passed = angs >= th - 1e-9
                age = np.where(passed, (PI / 2 - th) - (PI / 2 - angs), -1)  # radians since the sweep passed
                vis = np.clip(age / 0.25, 0, 1)
                r0 = RH * se
                rr = (RH + 0.04 + 1.05 * haz) * se
                fade_end = 1.0
                for bi in range(6):
                    sel = np.flatnonzero(passed & (np.minimum((haz * 5.999).astype(int), 5) == bi))
                    segs = []
                    for i in sel:
                        d = np.array([np.cos(angs[i]), np.sin(angs[i])])
                        segs.append(np.array([ce[:2] + d * r0, ce[:2] + d * (r0 + (rr[i] - r0) * vis[i])]))
                    set_vm_points(bars[bi], multi_poly_points(segs))
                    bars[bi].set_stroke(BAR_COL[bi], width=4.0 * max(se, 0.55), opacity=0.9 * fade_end)
                # envelope through the bar tips, coloured by risk
                idx = np.flatnonzero(passed)
                for bi in range(6):
                    segs = []
                    for i in idx[:-1]:
                        j = i + 1
                        if not passed[j]:
                            continue
                        pm = (haz[i] + haz[j]) / 2
                        if min(int(pm * 5.999), 5) != bi:
                            continue
                        pi_ = ce[:2] + np.array([np.cos(angs[i]), np.sin(angs[i])]) * (r0 + (rr[i] - r0) * vis[i])
                        pj_ = ce[:2] + np.array([np.cos(angs[j]), np.sin(angs[j])]) * (r0 + (rr[j] - r0) * vis[j])
                        segs.append(np.array([pi_, pj_]))
                    set_vm_points(env[bi], multi_poly_points(segs))
                    env[bi].set_stroke(BAR_COL[bi], width=2.0, opacity=0.85)
                # baseline ring up to the sweep
                aa = np.linspace(PI / 2, th, max(2, int(60 * (PI / 2 - th) / TAU) + 2))
                set_vm_points(base_ring, poly_bez(np.column_stack([ce[0] + r0 * np.cos(aa), ce[1] + r0 * np.sin(aa)])))
                base_ring.set_stroke(DIM, width=1.4, opacity=0.8)
                # the sweep arm with a fading wake
                arm_a = (1 - smooth01((u - 0.96) / 0.04)) if u < 1 else 0.0
                arm_a *= smooth01((t - T_SWEEP) / 0.2)
                for j, sv in enumerate(sweep):
                    a_j = th + j * 0.06
                    d = np.array([np.cos(a_j), np.sin(a_j)])
                    set_vm_points(sv, poly_bez(np.array([ce[:2] + d * (R + 0.1) * se, ce[:2] + d * (RH + 1.25) * se])))
                    sv.set_stroke(SIGNAL, width=2.6 if j == 0 else 6, opacity=arm_a * (0.95 if j == 0 else 0.16 * (1 - j / 6)))
                # "see it coming": the high-risk arc glows
                hg = smooth01((t - (W_COMING - 0.05)) / 0.25) * (0.55 + 0.45 * np.cos(4 * (t - W_COMING)))
                hi = np.flatnonzero(haz > 0.5)
                if len(hi) and hg > 0:
                    ap = angs[hi]
                    pts = np.column_stack([ce[0] + (RH + 0.04 + 1.05 * haz[hi]) * se * np.cos(ap),
                                           ce[1] + (RH + 0.04 + 1.05 * haz[hi]) * se * np.sin(ap)])
                    set_vm_points(hot_glow, poly_bez(pts))
                    hot_glow.set_stroke(DANGER, width=14, opacity=0.25 * hg)
                else:
                    set_vm_points(hot_glow, np.zeros((0, 3)))

        driver = Dot(radius=0.001).set_opacity(0)
        self.add(driver)
        self.add(steel, mill, crack_glow, crack_core, glint, sparks, base_ring, *bars, *env, hot_glow, *sweep)
        driver.add_updater(tick)
        tick(driver, 0)

        # ---------------- montage ----------------
        def body_snapshot(angle, center=C0, scale=1.0):
            mill.scale_f = scale
            mill.update_state(angle, center, alpha=1.0)
            snap = mill.body.copy()
            snap.set_fill([mill.body.get_fill_colors()[0], mill.body.get_fill_colors()[-1]], opacity=1)
            return snap

        vib = np.array(DATA["vibration"]["worn"][100:640])
        vib = vib / np.abs(vib).max()
        wx = np.linspace(-3.6, 3.6, len(vib))
        wave = VMobject().set_points_as_corners(to3(np.column_stack([wx, C0[1] + 1.15 * vib])))
        wave.set_stroke(SIGNAL, width=3)

        bits = N("01101001 11000101", size=64, color=DATA_C).move_to(C0)

        node = np.array([-0.55, C0[1], 0])
        stem = Line(np.array([-2.5, C0[1], 0]), node).set_stroke(INK, width=3.5)
        up_end, dn_end = node + np.array([2.1, 1.35, 0]), node + np.array([2.1, -1.35, 0])
        br_up = CubicBezier(node, node + np.array([1.1, 0, 0]), up_end - np.array([1.0, 0, 0]), up_end)
        br_dn = CubicBezier(node, node + np.array([1.1, 0, 0]), dn_end - np.array([1.0, 0, 0]), dn_end)
        br_up.set_stroke(GOOD, width=3.5)
        br_dn.set_stroke(WARN, width=3.5)
        fork = VGroup(stem, br_up, br_dn, Dot(node, radius=0.09, color=INK), Dot(up_end, radius=0.09, color=GOOD),
                      Dot(dn_end, radius=0.09, color=WARN))

        # steel: the cutter spinning hard into the block
        st["mode"] = "fast"
        self.wait_until(W_SIGNALS - 0.32)
        snap = body_snapshot(st["a"])
        st["mode"] = "off"
        st["off_t"] = self.now
        self.add(snap)
        self.play(ReplacementTransform(snap, wave), run_time=0.42, rate_func=smooth)
        self.wait_until(W_NUMBERS - 0.3)
        self.play(ReplacementTransform(wave, bits), run_time=0.42, rate_func=smooth)
        self.wait_until(W_CHOICE - 0.3)
        self.play(ReplacementTransform(bits, fork), run_time=0.42, rate_func=smooth)

        # back to the cutter, calm now
        self.wait_until(T_CALM - 0.1)
        st["a"] = st["a"] - 1.2          # it spins up out of the fork's node
        st["grow_t"] = self.now
        st["mode"] = "calm"
        self.play(fork.animate.scale(0.05).move_to(C0).set_opacity(0), run_time=0.45, rate_func=smooth)
        self.remove(fork)

        # title
        self.wait_until(T_TITLE - 0.25)
        title = title_text(size=64).move_to(DOWN * 0.15)
        cx = title.get_center()[0]
        credits = T("Bhuwan · Yadu · Amal · Aaditya · Rafiq — AI in Manufacturing", size=24, color=DIM)
        credits.next_to(title, DOWN, buff=0.45)
        self.play(LaggedStart(*[FadeIn(ch, shift=LEFT * (ch.get_center()[0] - cx) * 0.25) for ch in title],
                              lag_ratio=0.05, run_time=0.85))
        self.play(FadeIn(credits, shift=UP * 0.08), run_time=0.5)

        self.wait_until(TOT - 0.5)
        driver.clear_updaters()
        self.remove(driver)
        self.finish()
