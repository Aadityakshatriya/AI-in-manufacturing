"""s03_wear — zoom from the end mill into one tooth; the fresh edge slices, a flank wear land grows until
the edge ploughs; then the runaway loop force -> heat -> wear spins up until the tooth fractures."""
import sys, os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from style import *  # noqa: F401,F403
from s01_cold_open import (EndMill, Sparks, hatch_segments, multi_poly_points, poly_bez, to3, rot2,  # noqa: E402
                           set_vm_points, smooth01, ease_out, BODY_LIT, BODY_SHADE, STEEL_LIT, STEEL_SHADE,
                           HATCH, HOT_WHITE)

if os.environ.get("TL_PREVIEW"):
    config.pixel_width = 854
    config.pixel_height = 480
    config.frame_rate = int(os.environ.get("TL_FPS", "15"))

FW = 14.222222  # full frame width in scene units


def keyed(t, keys):
    ks = np.array(keys, dtype=float)
    return float(np.interp(t, ks[:, 0], ks[:, 1]))


def lerp(a, b, s):
    return a + (b - a) * s


def lgeo(a, b, s):
    return float(np.exp(np.log(a) + (np.log(b) - np.log(a)) * s))


def mix(c1, c2, s):
    return interpolate_color(ManimColor(c1), ManimColor(c2), float(np.clip(s, 0, 1)))


# ---------------------------------------------------------------------------------------------
# clipping to the circular lens
# ---------------------------------------------------------------------------------------------

def clip_poly_circle(P, center, radius):
    """Polygon (n x 2/3, closed implicitly) ∩ circle -> VMobject points (may be empty)."""
    P = np.asarray(P)[:, :2]
    vm = VMobject().set_points_as_corners(to3(np.vstack([P, P[:1]])))
    circ = Circle(radius=radius, num_components=48).move_to([center[0], center[1], 0])
    try:
        res = Intersection(vm, circ)
        return res.points
    except Exception:
        return np.zeros((0, 3))


def clip_lines_circle(polys, center, radius, step=0.04):
    """Clip polylines to a circle by densifying and keeping inside runs."""
    out = []
    c = np.asarray(center)[:2]
    r2 = radius * radius
    for P in polys:
        P = np.asarray(P)[:, :2]
        if len(P) < 2:
            continue
        dense = [P[0]]
        for a, b in zip(P[:-1], P[1:]):
            n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
            for s in np.linspace(0, 1, n + 1)[1:]:
                dense.append(a + (b - a) * s)
        D = np.array(dense)
        inside = np.sum((D - c) ** 2, axis=1) < r2
        run = []
        for p, ins in zip(D, inside):
            if ins:
                run.append(p)
            else:
                if len(run) >= 2:
                    out.append(np.array(run))
                run = []
        if len(run) >= 2:
            out.append(np.array(run))
    return out


class S03Wear(TLScene):
    SID = "s03_wear"

    def construct(self):
        rng = np.random.default_rng(21)
        TOT = self.total

        # ---------------- timeline (scene clock) ----------------
        T_ZOOM_END = 2.2
        T_SWAP = 2.72
        T_RUB = self.cue(2)                 # "But every hit rubs..."
        T_LOOP = self.cue(3) - 0.3          # lens forms as "Pushing means more force" starts
        T_FORCE = LEAD + 13.5               # "...force"
        T_A1 = (self.cue(4), LEAD + 15.55)  # arrow force -> heat while "More force means more heat"
        T_HEAT = LEAD + 15.6
        T_A2 = (self.cue(5), LEAD + 17.85)
        T_WEAR = LEAD + 17.9
        T_A3 = (self.cue(6), self.cue(6) + 0.5)
        T_ORBIT = self.cue(6) + 0.5
        T_FRAC = LEAD + 20.95               # "...fracture"

        # ---------------- macro geometry (local coordinates, full-frame units) ----------------
        TP = np.array([-1.0, -1.25])
        y0 = TP[1]
        h = 0.34
        gam, alp = np.radians(12), np.radians(7)
        dr = np.array([-np.sin(gam), np.cos(gam)])     # rake face, from the edge upward
        df = np.array([-np.cos(alp), np.sin(alp)])     # flank face, from the edge backward
        nr = np.array([np.cos(gam), np.sin(gam)])      # rake-face normal, pointing into the chip

        VB_K = [(0, 0), (T_RUB + 0.1, 0), (LEAD + 8.2, 0.5), (LEAD + 10.8, 1.0), (T_LOOP, 1.2),
                (T_WEAR, 1.42), (T_FRAC, 2.0)]
        RE_K = [(0, 0.012), (T_RUB + 0.1, 0.012), (LEAD + 8.2, 0.07), (LEAD + 11.2, 0.17), (T_LOOP, 0.2),
                (T_FRAC, 0.25)]
        PHI_K = [(0, 31), (T_RUB, 31), (LEAD + 8.8, 27), (LEAD + 11.8, 21), (T_FRAC, 19.5)]
        RAG_K = [(0, 0), (LEAD + 7.5, 0), (LEAD + 9.4, 0.05), (LEAD + 11.8, 0.12), (T_FRAC, 0.16)]
        BUMP_K = [(0, 0), (LEAD + 10.4, 0), (LEAD + 11.9, 0.13), (T_FRAC, 0.17)]
        ROUGH_K = [(0, 0), (LEAD + 8.3, 0), (LEAD + 10.6, 0.03), (LEAD + 11.9, 0.065)]
        SMEAR_K = [(0, 0), (LEAD + 10.6, 0), (LEAD + 11.9, 0.8)]
        VCHIP_K = [(0, 1.0), (LEAD + 8.8, 0.85), (LEAD + 11.9, 0.45), (T_FRAC, 0.4)]
        HEAT_K = [(0, 0.12), (T_RUB, 0.12), (LEAD + 11.9, 0.5), (T_HEAT, 0.7), (T_FRAC, 1.0)]
        HOTCHIP_K = [(0, 0), (LEAD + 8.0, 0), (LEAD + 11.9, 0.55), (T_FRAC, 0.9)]

        st = dict(t=None, s_chip=0.0, s_work=0.0, broken=None)

        def frozen(t):
            return min(t, T_FRAC)

        def tool_poly(VB, re, n_fillet=12):
            d = VB / (1 / np.tan(alp) - np.tan(gam))
            Tp = TP + np.array([0, -d])
            x_r = Tp[0] - d * np.tan(gam)
            x_f = Tp[0] - d / np.tan(alp)
            corner = np.array([x_r, y0])
            half = (np.pi - (np.pi / 2 + gam)) / 2          # half of the interior angle (land vs rake)
            tl = re / np.tan(half)
            A = corner + np.array([-tl, 0])
            B = corner + tl * dr
            u = np.linspace(0, 1, n_fillet)[:, None]
            fil = (1 - u) ** 2 * A + 2 * u * (1 - u) * corner + u ** 2 * B
            top_r = Tp + 7.5 * dr
            far = np.array([-13.0, 9.0])
            back = Tp + 13 * df
            pts = [np.array([x_f, y0])] if x_f < A[0] - 1e-4 else []
            pts += list(fil) + [top_r, far, back]
            return np.array(pts), np.array([x_f, y0]), A, B, corner

        def surface_f(t, x_f, E, S, bump, rough, phase):
            def f(x):
                if x <= x_f:
                    return y0 + rough * (np.sin(9.0 * (x + phase)) * 0.6 + np.sin(23.0 * (x + phase) + 1.3) * 0.4)
                if x <= E[0]:
                    return y0
                if x <= S[0]:
                    s = (x - E[0]) / max(S[0] - E[0], 1e-6)
                    return y0 + h * s + bump * np.sin(np.pi * s) * s
                return y0 + h + bump * np.exp(-((x - S[0]) / 0.55) ** 2)
            return f

        def chip_geometry(t, E, S, rag, s_chip, n=90):
            hc = float((S - E) @ nr)
            L1 = 0.7
            L2 = 3.7
            L = L1 + L2
            ss = np.linspace(0, L, n)
            ang = np.zeros(n)
            # turn clockwise along the curl with tightening radius
            for i in range(1, n):
                ds = ss[i] - ss[i - 1]
                if ss[i] > L1:
                    rho = lerp(1.4, 0.95, min(1, (ss[i] - L1) / L2))
                    ang[i] = ang[i - 1] - ds / rho
                else:
                    ang[i] = ang[i - 1]
            base = np.arctan2(dr[1], dr[0])
            dirs = np.column_stack([np.cos(base + ang), np.sin(base + ang)])
            cl = np.zeros((n, 2))
            cl[0] = E + 0.5 * hc * nr
            for i in range(1, n):
                cl[i] = cl[i - 1] + dirs[i - 1] * (ss[i] - ss[i - 1])
            nrm = np.column_stack([dirs[:, 1], -dirs[:, 0]])  # right-hand normal (toward the free side)
            taper = np.clip((L - ss) / 0.3, 0.55, 1.0)
            inner = cl - nrm * (0.5 * hc)
            spacing = 0.2
            saw = ((ss - s_chip) / spacing) % 1.0
            outer = cl + nrm * (0.5 * hc * taper[:, None]) + nrm * (rag * saw)[:, None]
            outer[0] = S
            poly = np.vstack([[E], inner, outer[::-1]])
            # shear lamellae across the chip, flowing outward
            lines = []
            k0 = int(np.floor(-s_chip / spacing)) - 1
            for k in range(k0, k0 + int(L / spacing) + 3):
                sk = s_chip + k * spacing
                if 0.05 < sk < L - 0.05:
                    i = np.searchsorted(ss, sk)
                    a_ = inner[i] + nrm[i] * (0.35 * hc)
                    b_ = cl[i] + nrm[i] * (0.5 * hc * taper[i] + rag * saw[i] - 0.02)
                    lines.append(np.array([a_, b_]))
            return poly, lines, hc, cl

        # ---------------- end mill (opening) ----------------
        R = 1.6
        mill = EndMill(R=R, n_ghost=2)
        TIP_W = np.array([0.0, -R, 0.0])
        Wz = 3.0
        kz = Wz / FW
        Pc = TIP_W[:2] - kz * TP
        w0 = PI * 0.9
        a_end = -PI / 2

        def mill_angle(t):
            tt = min(t, T_ZOOM_END)
            return a_end - w0 * (T_ZOOM_END - tt) ** 2 / (2 * T_ZOOM_END)

        # ---------------- mobjects ----------------
        work = VMobject().set_sheen_direction(DOWN)
        smear = VMobject()
        hatch = VMobject()
        surf = VMobject()
        chip = VMobject().set_sheen_direction(UR)
        lam = VMobject()
        tool = VMobject().set_sheen_direction(normalize(DR))
        edge_glow, edge_line = VMobject(), VMobject()
        heat = [Circle(radius=1, num_components=24).set_stroke(width=0) for _ in range(3)]
        force = VMobject()
        crack_glow, crack_line = VMobject(), VMobject()
        chunk = VMobject().set_sheen_direction(normalize(DR))
        lens = Circle(radius=1, num_components=64).set_stroke(DIM, width=1.6, opacity=0).set_fill(opacity=0)
        flash = Circle(radius=1, num_components=48).set_stroke(width=0).set_fill(INK, 0)
        sparks = Sparks(cap=200, seed=9)

        # loop (world coordinates)
        LC = np.array([3.15, -0.2])
        LR = 1.85
        node_ang = {"force": PI / 2, "heat": PI / 2 - TAU / 3, "wear": PI / 2 - 2 * TAU / 3}
        node_pos = {k: LC + LR * np.array([np.cos(a), np.sin(a)]) for k, a in node_ang.items()}
        loop_ring = VMobject()
        arcs = [VMobject() for _ in range(3)]
        tips = [VMobject() for _ in range(3)]
        nodes = {k: Circle(radius=0.13, num_components=24).move_to([*p, 0]) for k, p in node_pos.items()}
        node_glow = {k: Circle(radius=0.34, num_components=24).move_to([*p, 0]).set_stroke(width=0)
                     for k, p in node_pos.items()}
        labels = {
            "force": T("force", size=34).next_to([*node_pos["force"], 0], UP, buff=0.3),
            "heat": T("heat", size=34).next_to([*node_pos["heat"], 0], RIGHT, buff=0.38),
            "wear": T("wear", size=34).next_to([*node_pos["wear"], 0], LEFT, buff=0.38),
        }
        comet = [VMobject() for _ in range(6)]
        head = Circle(radius=0.075, num_components=16).set_stroke(width=0)
        head_glow = Circle(radius=0.22, num_components=16).set_stroke(width=0)
        burst = VMobject()

        hits_val = {"v": 0.0, "op": 0.0}
        counter = always_redraw(lambda: VGroup(
            N(f"{int(hits_val['v']):,}", size=30, color=DATA_C),
            T("hits", size=26, color=DIM)).arrange(RIGHT, buff=0.18, aligned_edge=DOWN)
            .to_corner(UR, buff=0.55).set_opacity(hits_val["op"]))

        # text labels for the fresh tooth (world = local during this phase, the push-in is tiny)
        E0 = TP.copy()
        lab_rake = T("rake face", size=24, color=DIM).rotate(np.arctan2(dr[1], dr[0]))
        lab_rake.move_to([*(E0 + dr * 1.55 - nr * 0.28), 0])
        lab_flank = T("flank face", size=24, color=DIM).rotate(np.arctan2(-df[1], -df[0]))
        lab_flank.move_to([*(E0 + df * 1.75 + np.array([np.sin(alp), np.cos(alp)]) * 0.26), 0])
        lab_land = T("wear land", size=26, color=HEAT)
        lab_land.move_to([TP[0] - 1.75, y0 + 0.95, 0])
        land_leader = Line([TP[0] - 1.35, y0 + 0.72, 0], [TP[0] - 0.45, y0 + 0.07, 0]).set_stroke(HEAT, 1.2)

        driver = Dot(radius=0.001).set_opacity(0)
        self.add(driver)
        self.add(work, smear, hatch, surf, chip, lam, tool, edge_glow, edge_line, *heat, force, crack_glow,
                 crack_line, chunk, mill, flash, lens, sparks, loop_ring, *arcs, *tips, *node_glow.values(),
                 *nodes.values(), *labels.values(), *comet, head_glow, head, burst, counter)
        frame = self.camera.frame

        def affine(t):
            """local -> world: returns (k, C) with world = C + k * (p - TP)."""
            if t < T_SWAP:
                return kz, Pc + kz * TP
            s1 = smooth01((t - T_SWAP) / max(T_LOOP - T_SWAP, 1e-6))
            k1 = 1 + 0.04 * s1
            if t < T_LOOP:
                return k1, TP.copy()
            s = smooth01((t - T_LOOP) / 0.9)
            return lerp(1.04, 0.6, s), lerp(TP, np.array([-3.25, -0.62]), s)

        def crop(t):
            if t < T_LOOP:
                return None
            s = smooth01((t - T_LOOP) / 0.9)
            return lerp(np.array([0.0, 0.0]), np.array([-3.55, -0.2]), s), lgeo(10.0, 2.6, s), s

        def W(P, k, C):
            P = np.asarray(P)[:, :2]
            return C + k * (P - TP)

        def put_poly(vm, P, k, C, cr):
            Pw = W(P, k, C)
            if cr is None:
                set_vm_points(vm, poly_bez(np.vstack([Pw, Pw[:1]])))
            else:
                set_vm_points(vm, clip_poly_circle(Pw, cr[0], cr[1]))

        def put_lines(vm, polys, k, C, cr):
            pw = [W(p, k, C) for p in polys]
            if cr is not None:
                pw = clip_lines_circle(pw, cr[0], cr[1])
            set_vm_points(vm, multi_poly_points(pw))

        def arc_pts(a0, a1, n=40, r=LR):
            a = np.linspace(a0, a1, n)
            return np.column_stack([LC[0] + r * np.cos(a), LC[1] + r * np.sin(a)])

        GAP = 0.33  # radians of gap near each node
        arc_spans = [(node_ang["force"] - GAP, node_ang["heat"] + GAP),
                     (node_ang["heat"] - GAP, node_ang["wear"] + GAP),
                     (node_ang["wear"] - GAP, node_ang["force"] - TAU + GAP)]
        arc_times = [T_A1, T_A2, T_A3]
        node_times = {"force": T_FORCE, "heat": T_HEAT, "wear": T_WEAR}

        def tick(mob, dt):
            t = self.now   # renderer clock = the exact time of the frame being drawn
            tf = frozen(t)
            broken = t >= T_FRAC

            # ---------- opening: the end mill and the zoom ----------
            if t < T_SWAP:
                s = smooth01((t - 0.35) / (T_ZOOM_END - 0.35))
                wdt = lgeo(FW, Wz, s)
                cen = lerp(np.zeros(2), Pc, smooth01((t - 0.35) / (T_ZOOM_END - 0.35)) ** 0.85)
                frame.set(width=wdt).move_to([cen[0], cen[1], 0])
                a_m = smooth01(t / 0.6) * (1 - smooth01((t - 1.95) / 0.55))
                mill.update_state(mill_angle(t), ORIGIN, alpha=a_m, blur=0.0)
                macro_a = smooth01((t - 1.95) / 0.6)
            else:
                if mill.get_family()[0].get_fill_opacity() > 0 or True:
                    mill.set_opacity(0)
                frame.set(width=FW).move_to(ORIGIN)
                macro_a = 1.0

            # ---------- flow ----------
            if not broken:
                st["s_chip"] += keyed(t, VCHIP_K) * dt
                st["s_work"] += 1.25 * dt

            VB = keyed(tf, VB_K)
            re = keyed(tf, RE_K)
            phi = np.radians(keyed(tf, PHI_K))
            rag = keyed(tf, RAG_K)
            bump = keyed(tf, BUMP_K)
            rough = keyed(tf, ROUGH_K)
            sm = keyed(tf, SMEAR_K)
            hot = keyed(t, HEAT_K)
            hotchip = keyed(tf, HOTCHIP_K)
            # the loop makes everything run away
            if t > T_ORBIT:
                hot = min(1.0, hot + 0.25 * smooth01((t - T_ORBIT) / 1.4))

            tp, P_land, A, B, corner = tool_poly(VB, re)
            E = corner + np.array([0.02, 0])
            S = E + np.array([h / np.tan(phi), h])
            k, C = affine(t)
            cr = crop(t)
            crc = (cr[0], cr[1]) if cr is not None else None

            # ---------- workpiece ----------
            f = surface_f(t, P_land[0], E, S, bump, rough, st["s_work"])
            xs = np.linspace(-9.5, 9.5, 420)
            top = np.column_stack([xs, [f(x) for x in xs]])
            wpoly = np.vstack([top, [[9.5, -6.0], [-9.5, -6.0]]])
            put_poly(work, wpoly, k, C, crc)
            work.set_fill([STEEL_LIT, STEEL_SHADE], opacity=macro_a).set_stroke(width=0)
            hs = hatch_segments(f, -9.5, 9.5, -5.0, spacing=0.34, phase=-st["s_work"])
            put_lines(hatch, hs, k, C, crc)
            hatch.set_stroke(HATCH, width=1.1, opacity=0.85 * macro_a)
            put_lines(surf, [top], k, C, crc)
            surf.set_stroke(mix(STEEL, INK, 0.3), width=2.0, opacity=0.95 * macro_a)
            # smeared, ploughed layer behind the edge
            if sm > 0.01:
                xx = np.linspace(-9.5, P_land[0], 160)
                upper = np.column_stack([xx, [f(x) for x in xx]])
                lower = upper[::-1] + np.array([0, -0.16])
                lower[:, 1] += 0.03 * np.sin(17 * (lower[:, 0] + st["s_work"]))
                put_poly(smear, np.vstack([upper, lower]), k, C, crc)
                smear.set_fill(HEAT, opacity=0.32 * sm * macro_a).set_stroke(width=0)
            else:
                set_vm_points(smear, np.zeros((0, 3)))

            # ---------- chip ----------
            cpoly, clines, hc, cl = chip_geometry(t, E, S, rag, st["s_chip"])
            put_poly(chip, cpoly, k, C, crc)
            c_lit = mix(mix(STEEL, INK, 0.25), HEAT, hotchip)
            c_dark = mix(STEEL_LIT, DANGER, hotchip * 0.6)
            chip.set_fill([c_lit, c_dark], opacity=macro_a)
            chip.set_stroke(mix(mix(STEEL, INK, 0.45), HEAT, hotchip), width=1.6, opacity=0.9 * macro_a)
            put_lines(lam, clines, k, C, crc)
            lam.set_stroke(mix(STEEL_SHADE, BG, 0.2), width=1.1, opacity=0.32 * macro_a)

            # ---------- tool ----------
            if st["broken"] is None:
                put_poly(tool, tp, k, C, crc)
            else:
                put_poly(tool, st["broken"]["rest"], k, C, crc)
            tool.set_fill([BODY_LIT, BODY_SHADE], opacity=macro_a)
            tool.set_stroke(CARBIDE, width=2.4, opacity=0.95 * macro_a)

            # cutting edge / wear land highlight, pulsing with each hit
            if t < T_RUB + 0.1:
                pulse = 0.0
            else:
                freq_phase = 2.5 * (t - T_RUB) + 0.35 * (t - T_RUB) ** 2
                pulse = np.exp(-(freq_phase % 1.0) / 0.18) * (0 if broken else 1)
            if st["broken"] is None:
                fresh = 1 - smooth01((t - T_RUB) / 2.0)
                if VB > 0.02:
                    land = np.vstack([P_land, A])
                    fil = np.array([(1 - u) ** 2 * A + 2 * u * (1 - u) * corner + u ** 2 * B for u in np.linspace(0, 1, 8)])
                    eg = [land, np.vstack([A, fil[1:], B + dr * 0.05])]
                    col = mix(WARN, HEAT, 1 - fresh)
                else:
                    eg = [np.vstack([E + df * 0.45, E, E + dr * 0.45])]
                    col = WARN
                put_lines(edge_line, eg, k, C, crc)
                put_lines(edge_glow, eg, k, C, crc)
                lvl = (0.75 + 0.25 * pulse) * macro_a
                edge_line.set_stroke(col, width=3.2 + 1.2 * min(1, VB), opacity=lvl)
                edge_glow.set_stroke(col, width=11, opacity=(0.18 + 0.25 * pulse + 0.2 * hot) * macro_a)
            else:
                set_vm_points(edge_line, np.zeros((0, 3)))
                set_vm_points(edge_glow, np.zeros((0, 3)))

            # heat glow at the edge
            gpos = W(np.array([E + np.array([-0.15, 0.08])]), k, C)[0]
            hk = hot * (0.6 + 0.4 * pulse) * macro_a
            if broken:
                hk *= np.exp(-(t - T_FRAC) / 0.6)
            for i, (g, rr, op) in enumerate(zip(heat, (0.25, 0.55, 1.0), (0.32, 0.14, 0.06))):
                g.set(width=2 * rr * k * (0.8 + 0.6 * hot)).move_to([gpos[0], gpos[1], 0])
                g.set_fill(mix(HEAT, DANGER, max(0, hot - 0.6) / 0.4) if i < 2 else HEAT, opacity=op * hk)

            # force arrow on the edge ("pushing means more force")
            fa = smooth01((t - T_FORCE) / 0.45) * (1 - smooth01((t - T_FRAC) / 0.2))
            if fa > 0.01:
                grow = 1.0 + 0.5 * smooth01((t - T_ORBIT) / 1.5)
                base = E + np.array([-0.12, 0.22])
                d = normalize(np.array([-0.82, 0.57]))
                Lf = 1.35 * fa * grow
                wsh = 0.07 * grow
                pp = np.array([-d[1], d[0]])
                tipp = base
                tail = base + d * Lf
                neck = base + d * min(0.34 * grow, Lf)
                arrow = np.array([tipp, neck + pp * wsh * 2.4, neck + pp * wsh, tail + pp * wsh, tail - pp * wsh,
                                  neck - pp * wsh, neck - pp * wsh * 2.4])
                put_poly(force, arrow, k, C, crc)
                force.set_fill(mix(HEAT, DANGER, smooth01((t - T_ORBIT) / 1.8)), opacity=0.92).set_stroke(width=0)
            else:
                set_vm_points(force, np.zeros((0, 3)))

            # ---------- fracture ----------
            if t >= T_FRAC - 0.28:
                if "crack" not in st:
                    p1 = P_land + np.array([0.18, 0.02])
                    p2 = E + dr * 1.05 + np.array([0.0, 0.0])
                    n_c = 10
                    ss = np.linspace(0, 1, n_c)
                    bow = np.array([0, 0.32])
                    pts = p1 + ss[:, None] * (p2 - p1) + np.sin(np.pi * ss)[:, None] * bow
                    nrm_c = normalize(np.array([-(p2 - p1)[1], (p2 - p1)[0]]))
                    jit = rng.normal(0, 0.045, n_c)
                    jit[0] = jit[-1] = 0
                    pts = pts + jit[:, None] * nrm_c
                    st["crack"] = pts
                pts = st["crack"]
                g = smooth01((t - (T_FRAC - 0.28)) / 0.26)
                m = max(2, int(np.ceil(g * len(pts))))
                if st["broken"] is None:
                    put_lines(crack_line, [pts[:m]], k, C, crc)
                    put_lines(crack_glow, [pts[:m]], k, C, crc)
                    crack_line.set_stroke(DANGER, width=2.6, opacity=1)
                    crack_glow.set_stroke(DANGER, width=10, opacity=0.35)
                if broken and st["broken"] is None:
                    # split the tool along the crack, once
                    tool_vm = VMobject().set_points_as_corners(to3(np.vstack([tp, tp[:1]])))
                    below = np.vstack([pts, pts[-1] + np.array([3, -0.3]), [pts[-1][0] + 3, y0 - 2],
                                       [pts[0][0] - 1, y0 - 2], pts[0] + np.array([-1, -0.2])])
                    cut = VMobject().set_points_as_corners(to3(np.vstack([below, below[:1]])))
                    piece = Intersection(tool_vm, cut)
                    rest = Difference(tool_vm, cut)
                    # store as polygons (sample the bezier points' anchors)
                    st["broken"] = dict(rest=rest.points[::4, :2].copy() if len(rest.points) else tp,
                                        piece=piece.points[::4, :2].copy(), ctr=piece.get_center()[:2],
                                        v=np.array([1.3, -0.4]), ang=0.0, w=-2.6, off=np.zeros(2))
                    set_vm_points(crack_line, np.zeros((0, 3)))
                    set_vm_points(crack_glow, np.zeros((0, 3)))
                    bp = W(np.array([pts[len(pts) // 2]]), k, C)[0]
                    for _ in range(5):
                        dd = np.array([np.cos(rng.uniform(-1.2, 1.6)), np.sin(rng.uniform(-1.2, 1.6))])
                        sparks.spawn(14, bp, dd, spread=0.6, vmin=1.5, vmax=6.0, lmin=0.25, lmax=0.8, jitter=0.03)
                    st["burst_at"] = bp
            if st["broken"] is not None:
                b = st["broken"]
                tt = t - T_FRAC
                if dt > 0:
                    b["v"] = b["v"] + np.array([0, -5.5]) * dt
                    b["off"] = b["off"] + b["v"] * dt
                    b["ang"] += b["w"] * dt
                loc = (b["piece"] - b["ctr"]) @ rot2(b["ang"]).T + b["ctr"] + b["off"]
                put_poly(chunk, loc, k, C, crc)
                op = 1 - smooth01((tt - 0.5) / 0.5)
                chunk.set_fill([BODY_LIT, BODY_SHADE], opacity=op)
                chunk.set_stroke(mix(HOT_WHITE, CARBIDE, min(1, tt / 0.3)), width=2.4, opacity=op)
                fl = 0.55 * np.exp(-tt / 0.12)
                flash.set(width=2 * cr[1]).move_to([cr[0][0], cr[0][1], 0]).set_fill(INK, opacity=fl)

            sparks.step(dt, g=6.0, drag=1.2)
            sparks.draw(1.0, alpha=1.0, blur_k=0.02, core_w=2.0, halo_w=6)

            # ---------- lens ring ----------
            if cr is not None:
                lens.set(width=2 * cr[1]).move_to([cr[0][0], cr[0][1], 0])
                lens.set_stroke(DIM, width=1.6, opacity=0.9 * cr[2])
            # ---------- hit counter ----------
            u = np.clip((t - T_RUB) / (T_LOOP - T_RUB), 0, 1)
            hits_val["v"] = 1_022_000 * u ** 2.3  # cutter 9, the longest life: 150 cycles, 4,791 s of cutting × 213 hits/s
            hits_val["op"] = smooth01((t - T_RUB) / 0.4) * (1 - smooth01((t - T_LOOP) / 0.5))

            # ---------- the runaway loop ----------
            heat_c = smooth01((t - (T_ORBIT - 0.4)) / 2.2)
            loop_col = mix(HEAT, DANGER, heat_c)
            sk = smooth01((t - T_LOOP - 0.25) / 0.7)
            ring = arc_pts(0, TAU, 120)
            set_vm_points(loop_ring, poly_bez(ring))
            loop_ring.set_stroke(FAINT, width=1.5, opacity=0.9 * sk)
            frac_flash = np.exp(-(t - T_FRAC) / 0.25) if broken else 0.0
            for i, (vm, tvm) in enumerate(zip(arcs, tips)):
                a0, a1 = arc_spans[i]
                t0, t1 = arc_times[i]
                pr = smooth01((t - t0) / (t1 - t0))
                if pr <= 0.001:
                    set_vm_points(vm, np.zeros((0, 3)))
                    set_vm_points(tvm, np.zeros((0, 3)))
                    continue
                ae = lerp(a0, a1, pr)
                set_vm_points(vm, poly_bez(arc_pts(a0, ae, 40)))
                wdt_arc = 3.0 + 1.5 * heat_c
                col = mix(loop_col, INK, frac_flash * 0.6)
                vm.set_stroke(col, width=wdt_arc, opacity=0.95)
                # arrow tip at the current end, pointing along the clockwise tangent
                pe = LC + LR * np.array([np.cos(ae), np.sin(ae)])
                tg = np.array([np.sin(ae), -np.cos(ae)])
                pn = np.array([-tg[1], tg[0]])
                tri = np.array([pe + tg * 0.2, pe - tg * 0.02 + pn * 0.11, pe - tg * 0.02 - pn * 0.11])
                set_vm_points(tvm, poly_bez(np.vstack([tri, tri[:1]])))
                tvm.set_fill(col, opacity=1).set_stroke(width=0)

            # orbit particle
            if T_A1[0] <= t < T_A1[1]:
                pa = lerp(arc_spans[0][0], arc_spans[0][1], smooth01((t - T_A1[0]) / (T_A1[1] - T_A1[0])))
                ph_on, spd_a = 1.0, 1.0
            elif T_A2[0] <= t < T_A2[1]:
                pa = lerp(arc_spans[1][0], arc_spans[1][1], smooth01((t - T_A2[0]) / (T_A2[1] - T_A2[0])))
                ph_on, spd_a = 1.0, 1.0
            elif T_A3[0] <= t < T_ORBIT:
                pa = lerp(arc_spans[2][0], arc_spans[2][1], smooth01((t - T_A3[0]) / (T_A3[1] - T_A3[0])))
                ph_on, spd_a = 1.0, 2.0
            elif t >= T_ORBIT:
                if "orbit" not in st:
                    st["orbit"] = arc_spans[2][1]
                w_rev = 0.75 + 2.9 * smooth01((t - T_ORBIT) / 1.9)
                if not broken:
                    st["orbit"] -= TAU * w_rev * dt
                pa = st["orbit"]
                ph_on = 1.0 if not broken else max(0.0, 1 - (t - T_FRAC) / 0.15)
                spd_a = w_rev * 2.2
            else:
                pa, ph_on, spd_a = None, 0.0, 0.0
            if pa is not None and ph_on > 0:
                pp = LC + LR * np.array([np.cos(pa), np.sin(pa)])
                pc = mix(mix(WARN, HEAT, 0.3), DANGER, heat_c)
                head.move_to([pp[0], pp[1], 0]).set_fill(mix(pc, INK, 0.35), opacity=ph_on)
                head_glow.move_to([pp[0], pp[1], 0]).set_fill(pc, opacity=0.3 * ph_on)
                tail_len = min(0.25 + 0.35 * spd_a, 2.6)
                for j, cm in enumerate(comet):
                    aa = np.linspace(pa + tail_len * j / 6, pa + tail_len * (j + 1) / 6, 6)
                    set_vm_points(cm, poly_bez(arc_pts(aa[0], aa[-1], 6)))
                    cm.set_stroke(pc, width=5 - 0.6 * j, opacity=ph_on * (0.75 - 0.11 * j))
            else:
                head.set_fill(opacity=0)
                head_glow.set_fill(opacity=0)
                for cm in comet:
                    set_vm_points(cm, np.zeros((0, 3)))
            # burst ring when it all breaks
            if broken and t - T_FRAC < 0.6:
                uu = (t - T_FRAC) / 0.6
                set_vm_points(burst, poly_bez(arc_pts(0, TAU, 80, r=LR + 0.05 + 0.9 * ease_out(uu))))
                burst.set_stroke(DANGER, width=3 * (1 - uu) + 0.5, opacity=0.8 * (1 - uu) ** 2)
            else:
                set_vm_points(burst, np.zeros((0, 3)))

            # nodes and labels
            for key in ("force", "heat", "wear"):
                lt = smooth01((t - node_times[key]) / 0.35)
                pop = np.exp(-max(0, t - node_times[key]) / 0.25) if t >= node_times[key] else 0
                # pulse when the orbiting particle passes
                near = 0.0
                if t >= T_ORBIT and pa is not None and not broken:
                    dd = np.angle(np.exp(1j * (pa - node_ang[key])))
                    near = np.exp(-(dd / 0.25) ** 2)
                ncol = mix(loop_col, INK, 0.15 * near)
                nodes[key].set_stroke(mix(DIM, ncol, lt), width=2.2, opacity=sk)
                nodes[key].set_fill(ncol, opacity=lt * sk)
                node_glow[key].set_fill(ncol, opacity=(0.16 * lt + 0.25 * pop + 0.3 * near + 0.3 * frac_flash) * sk)
                labels[key].set_opacity(lt)
                labels[key].set_color(mix(INK, loop_col, 0.25 * heat_c))

        driver.add_updater(tick)
        tick(driver, 0)

        # word labels on the fresh tooth
        self.wait_until(T_SWAP + 0.35)
        self.play(FadeIn(lab_rake), FadeIn(lab_flank), run_time=0.6)
        self.wait_until(T_RUB - 0.1)
        self.play(FadeOut(lab_rake), FadeOut(lab_flank), run_time=0.5)
        self.wait_until(LEAD + 6.9)
        self.play(FadeIn(lab_land, shift=UP * 0.1), Create(land_leader), run_time=0.6)
        self.wait_until(LEAD + 10.4)
        self.play(FadeOut(lab_land), FadeOut(land_leader), run_time=0.5)

        self.wait_until(TOT - 0.5)
        driver.clear_updaters()
        counter.clear_updaters()
        self.remove(driver, counter)
        self.finish()
