"""s01_cold_open — a 4-flute end mill hammers hardened steel 213 times a second, wears, cracks and snaps.

This file also holds the film's end-mill drawing (`EndMill`, `cutter_profile`) which s03_wear and
s11_close import, so the cutter looks identical in all three scenes.
"""
import sys, os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from style import *  # noqa: F401,F403

# style.py pins 1080p60 at import, which overrides `-ql`. For fast previews only, set TL_PREVIEW=1.
if os.environ.get("TL_PREVIEW"):
    config.pixel_width = 854
    config.pixel_height = 480
    config.frame_rate = int(os.environ.get("TL_FPS", "15"))


# ---------------------------------------------------------------------------------------------
# Shared drawing helpers (also imported by s03_wear and s11_close)
# ---------------------------------------------------------------------------------------------

BODY_LIT = interpolate_color(ManimColor(CARBIDE), ManimColor(BG), 0.42)    # lit side of the carbide
BODY_SHADE = interpolate_color(ManimColor(CARBIDE), ManimColor(BG), 0.86)  # shadow side
STEEL_LIT = interpolate_color(ManimColor(STEEL), ManimColor(BG), 0.62)
STEEL_SHADE = interpolate_color(ManimColor(STEEL), ManimColor(BG), 0.86)
HATCH = interpolate_color(ManimColor(STEEL), ManimColor(BG), 0.72)
HOT_WHITE = interpolate_color(ManimColor(WARN), ManimColor(INK), 0.65)


def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = np.clip(x, 0.0, 1.0)
    return 1 - (1 - x) ** 3


def rot2(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])


def to3(P):
    P = np.asarray(P, dtype=float)
    return np.column_stack([P[:, 0], P[:, 1], np.zeros(len(P))])


def poly_bez(P):
    """Polyline (m x 2 or m x 3) -> cubic bezier control points for straight segments (4 per segment)."""
    P = np.asarray(P, dtype=float)
    if P.shape[1] == 2:
        P = to3(P)
    a, b = P[:-1], P[1:]
    out = np.empty((len(a) * 4, 3))
    out[0::4] = a
    out[1::4] = a + (b - a) / 3
    out[2::4] = a + 2 * (b - a) / 3
    out[3::4] = b
    return out


def multi_poly_points(polys):
    """Many separate polylines -> one VMobject point array (each polyline becomes its own subpath)."""
    parts = [poly_bez(p) for p in polys if len(p) >= 2]
    if not parts:
        return np.zeros((0, 3))
    return np.vstack(parts)


def set_vm_points(vm, pts):
    if len(pts) == 0:
        vm.points = np.zeros((0, 3))
    else:
        vm.points = pts


def _bez(P0, P1, P2, P3, n):
    u = np.linspace(0, 1, n)[:, None]
    return (1 - u) ** 3 * P0 + 3 * (1 - u) ** 2 * u * P1 + 3 * (1 - u) * u ** 2 * P2 + u ** 3 * P3


def _pol(r, deg):
    a = np.radians(deg)
    return np.array([r * np.cos(a), r * np.sin(a)])


def _tan(deg):
    a = np.radians(deg)
    return np.array([-np.sin(a), np.cos(a)])


def tooth_period(R, rf=0.40, core=0.57, sweep=136.0, land_deg=80.0, heel_round=0.12, back_pull=0.24):
    """One tooth of the end-on profile, starting exactly at the cutting-edge tip (angle 0) and running
    counter-clockwise: the rake face curving down into a round flute gullet (an arc of a circle that
    passes through the tip, so the rake is positive), a rounded heel, the convex clearance face behind
    the next tooth, and the narrow land leading up to that tooth's tip at 90 degrees (excluded).
    The cutter rotates counter-clockwise. Returns (points scaled by R, number of rake+flute points)."""
    df = core + rf
    beta = np.arccos((1 + df * df - rf * rf) / (2 * df))
    C = df * np.array([np.cos(beta), np.sin(beta)])
    psi_tip = np.arctan2(-C[1], 1 - C[0])
    # denser near the tip so a worn (rounded) edge stays smooth
    u = np.linspace(0, 1, 84) ** 1.35
    psi = psi_tip - np.radians(sweep) * u
    flute = C + rf * np.stack([np.cos(psi), np.sin(psi)], 1)
    H = flute[-1]
    tH = np.array([np.sin(psi[-1]), -np.cos(psi[-1])])  # direction of travel at the heel
    L1 = _pol(0.986, land_deg)
    tL = _tan(land_deg) + 0.04 * _pol(1, land_deg)
    tL /= np.linalg.norm(tL)
    back = _bez(H, H + heel_round * tH, L1 - back_pull * tL, L1, 34)[1:-1]
    a = np.linspace(land_deg, 90.0, 18)[:-1]
    r = 0.986 + 0.014 * (a - land_deg) / (90.0 - land_deg)
    land = np.stack([r * np.cos(np.radians(a)), r * np.sin(np.radians(a))], 1)
    return R * np.vstack([flute, back, land]), len(flute)


def round_corner(P, i, rad):
    """Round the polyline corner at index i with a quadratic bezier reaching `rad` along each side."""
    n = len(P)
    if rad <= 1e-6:
        return P
    P = P.copy()
    # walk forward
    acc, j = 0.0, i
    while acc < rad and (j - i) < n // 8:
        acc += np.linalg.norm(P[(j + 1) % n] - P[j % n])
        j += 1
    acc, h = 0.0, i
    while acc < rad and (i - h) < n // 8:
        acc += np.linalg.norm(P[h % n] - P[(h - 1) % n])
        h -= 1
    A, B, Cc = P[h % n].copy(), P[j % n].copy(), P[i % n].copy()
    # pull the control point a little inward so the worn tip also recedes
    ctr = Cc - 0.25 * (Cc - (A + B) / 2)
    cnt = j - h - 1
    u = np.linspace(0, 1, cnt + 2)[1:-1]
    curve = ((1 - u) ** 2)[:, None] * A + (2 * u * (1 - u))[:, None] * ctr + (u ** 2)[:, None] * B
    for m, idx in enumerate(range(h + 1, j)):
        P[idx % n] = curve[m]
    return P


def cutter_profile(R, wear=(0, 0, 0, 0), teeth=4):
    """Closed outline (N x 2, not repeated) of the end-on end mill; tooth k's tip at angle k*90 deg."""
    per, nf = tooth_period(R)
    n = len(per)
    P = np.vstack([per @ rot2(k * TAU / teeth).T for k in range(teeth)])
    tips = [k * n for k in range(teeth)]
    for k, w in enumerate(wear):
        if w > 0:
            P = round_corner(P, tips[k], w * 0.085 * R)
    return P, tips


class EndMill(VGroup):
    """The film's end-on 4-flute end mill. Call .update_state(...) every frame (it rebuilds points;
    fixed light from the upper left, so the shading stays put while the cutter turns)."""

    M_LAND, M_FLUTE = 15, 17   # how many outline points around each tip form the bright cutting edge

    def __init__(self, R=1.6, n_ghost=3):
        super().__init__()
        self.R = R
        self.n_ghost = n_ghost
        self._key = None
        self.ghosts = [VMobject() for _ in range(n_ghost)]
        self.body = VMobject()
        self.gash = VMobject()
        self.glow = [VMobject() for _ in range(4)]
        self.edge = [VMobject() for _ in range(4)]
        self.hub = VMobject()
        self.add(*self.ghosts, self.body, self.gash, *self.glow, *self.edge, self.hub)
        self.body.set_sheen_direction(normalize(DR))
        for g in self.ghosts:
            g.set_sheen_direction(normalize(DR))
        self.angle, self.center_pt = 0.0, ORIGIN
        self.update_state(0.0, ORIGIN)

    def profile(self, wear):
        key = tuple(int(round(w * 400)) for w in wear)
        if key != self._key:
            self._P, self._tips = cutter_profile(self.R, [k / 400 for k in key])
            self._key = key
        return self._P, self._tips

    def world(self, P, angle=None, center=None):
        angle = self.angle if angle is None else angle
        center = self.center_pt if center is None else center
        W = np.asarray(P)[:, :2] @ rot2(angle).T + np.asarray(center)[:2]
        return to3(W)

    def update_state(self, angle, center, alpha=1.0, blur=0.0, wear=(0, 0, 0, 0), edge=(1, 1, 1, 1),
                     light=3 * PI / 4, edge_color=WARN, stroke=2.4):
        self.angle, self.center_pt = angle, np.asarray(center, dtype=float)
        P, tips = self.profile(wear)
        n = len(P)
        closed = np.vstack([P, P[:1]])
        # body
        set_vm_points(self.body, poly_bez(self.world(closed)))
        self.body.set_fill([BODY_LIT, BODY_SHADE], opacity=alpha)
        self.body.set_stroke(CARBIDE, width=stroke, opacity=0.9 * alpha)
        # motion-blur ghosts (trailing copies)
        bl = min(1.0, blur / 0.08) if blur > 0 else 0.0
        for i, g in enumerate(self.ghosts):
            if bl <= 0.01:
                g.set_fill(opacity=0).set_stroke(opacity=0)
                continue
            a = angle - blur * (i + 1) / self.n_ghost
            set_vm_points(g, poly_bez(self.world(closed, a)))
            f = (1 - i / self.n_ghost)
            g.set_fill([BODY_LIT, BODY_SHADE], opacity=0.22 * f * bl * alpha)
            g.set_stroke(CARBIDE, width=1.4, opacity=0.30 * f * bl * alpha)
        # end-gash lines (the end cutting edges running in toward the centre)
        R = self.R
        segs = []
        for k in range(4):
            tip = P[tips[k]]
            d = tip / np.linalg.norm(tip)
            perp = np.array([-d[1], d[0]])
            inner = 0.035 * R * perp if k % 2 == 0 else 0.30 * R * d + 0.035 * R * perp
            segs.append(self.world(np.array([tip * 0.96, inner])))
        set_vm_points(self.gash, multi_poly_points(segs))
        self.gash.set_stroke(CARBIDE, width=1.1, opacity=0.38 * alpha)
        # bright cutting edges at each tip, brighter when facing the light
        for k in range(4):
            idx = np.arange(tips[k] - self.M_LAND, tips[k] + self.M_FLUTE) % n
            seg = self.world(P[idx])
            tip_ang = angle + k * TAU / 4
            lit = 0.55 + 0.45 * max(0.0, np.cos(tip_ang - light))
            lvl = edge[k] * lit * alpha
            set_vm_points(self.edge[k], poly_bez(seg))
            self.edge[k].set_stroke(edge_color, width=stroke + 0.6, opacity=min(1.0, lvl))
            set_vm_points(self.glow[k], poly_bez(seg))
            self.glow[k].set_stroke(edge_color, width=9, opacity=0.22 * lvl)
        # hub
        circ = np.array([[np.cos(a), np.sin(a)] for a in np.linspace(0, TAU, 33)]) * 0.075 * R
        set_vm_points(self.hub, poly_bez(self.world(circ)))
        self.hub.set_stroke(CARBIDE, width=1.2, opacity=0.6 * alpha).set_fill(BG, opacity=0.9 * alpha)
        return self

    def tip_world(self, k, wear=(0, 0, 0, 0)):
        P, tips = self.profile(wear)
        return self.world(P[[tips[k]]])[0]


def steel_block_points(f, x0, x1, y_bottom, n=400):
    xs = np.linspace(x0, x1, n)
    top = np.column_stack([xs, [f(x) for x in xs]])
    return np.vstack([top, [[x1, y_bottom], [x0, y_bottom]], top[:1]]), top


def hatch_segments(f, x0, x1, y_bottom, spacing=0.3, phase=0.0, slope=1.0, n=500):
    """45-degree hatch lines inside {y < f(x), y > y_bottom}; returns list of 2-point segments."""
    xs = np.linspace(x0, x1, n)
    fy = np.array([f(x) for x in xs])
    segs = []
    cmin = y_bottom - slope * x1 - spacing
    cmax = fy.max() - slope * x0 + spacing
    c = cmin + ((phase - cmin) % spacing)
    while c < cmax:
        ys = slope * xs + c
        inside = (ys < fy) & (ys > y_bottom)
        if inside.any():
            idx = np.flatnonzero(inside)
            breaks = np.flatnonzero(np.diff(idx) > 1)
            starts = np.r_[idx[0], idx[breaks + 1]]
            ends = np.r_[idx[breaks], idx[-1]]
            for a, b in zip(starts, ends):
                if b > a:
                    segs.append(np.array([[xs[a], ys[a]], [xs[b], ys[b]]]))
        c += spacing
    return segs


# ---------------------------------------------------------------------------------------------
# Spark particle system (bucketed by age so a few hundred sparks cost ~a dozen VMobjects)
# ---------------------------------------------------------------------------------------------

SPARK_COLORS = [HOT_WHITE, ManimColor(WARN), interpolate_color(ManimColor(WARN), ManimColor(HEAT), 0.5),
                ManimColor(HEAT), interpolate_color(ManimColor(HEAT), ManimColor(DANGER), 0.5), ManimColor(DANGER)]
SPARK_OPAC = [1.0, 0.95, 0.85, 0.7, 0.5, 0.3]


class Sparks(VGroup):
    def __init__(self, cap=520, seed=1):
        super().__init__()
        self.rng = np.random.default_rng(seed)
        self.cap = cap
        self.p = np.zeros((cap, 2))
        self.v = np.zeros((cap, 2))
        self.age = np.zeros(cap)
        self.life = np.ones(cap)
        self.on = np.zeros(cap, dtype=bool)
        self.core = [VMobject() for _ in SPARK_COLORS]
        self.halo = [VMobject() for _ in SPARK_COLORS]
        self.add(*self.halo, *self.core)
        self.floor = None  # (x_min, y) bounce surface

    def spawn(self, n, pos, direction, spread=0.28, vmin=4.5, vmax=12.5, lmin=0.22, lmax=0.7, jitter=0.02,
              age_dither=0.0):
        free = np.flatnonzero(~self.on)[:n]
        k = len(free)
        if k == 0:
            return
        base = np.arctan2(direction[1], direction[0])
        ang = base + self.rng.normal(0, spread, k)
        sp = self.rng.uniform(vmin, vmax, k)
        self.v[free] = np.column_stack([np.cos(ang), np.sin(ang)]) * sp[:, None]
        self.p[free] = np.asarray(pos)[:2] + self.rng.normal(0, jitter, (k, 2))
        a0 = self.rng.uniform(0, age_dither, k) if age_dither > 0 else np.zeros(k)
        self.p[free] += self.v[free] * a0[:, None]
        self.age[free] = a0
        self.life[free] = self.rng.uniform(lmin, lmax, k)
        self.on[free] = True

    def step(self, dtau, g=10.0, drag=1.1):
        m = self.on
        if dtau > 0 and m.any():
            self.v[m, 1] -= g * dtau
            self.v[m] *= np.exp(-drag * dtau)
            self.p[m] += self.v[m] * dtau
            self.age[m] += dtau
            if self.floor is not None:
                x_min, y_f = self.floor
                b = m & (self.p[:, 1] < y_f) & (self.p[:, 0] > x_min) & (self.v[:, 1] < 0)
                self.p[b, 1] = y_f
                self.v[b, 1] *= -0.3
                self.v[b, 0] *= 0.65
            self.on &= self.age < self.life

    def draw(self, spd, alpha=1.0, blur_k=0.018, core_w=2.2, halo_w=7.0):
        m = np.flatnonzero(self.on)
        u = self.age[m] / self.life[m]
        bucket = np.minimum((u * len(SPARK_COLORS)).astype(int), len(SPARK_COLORS) - 1)
        kb = blur_k * spd + 0.0015
        for bi in range(len(SPARK_COLORS)):
            sel = m[bucket == bi]
            if len(sel) == 0:
                set_vm_points(self.core[bi], np.zeros((0, 3)))
                set_vm_points(self.halo[bi], np.zeros((0, 3)))
                continue
            p = self.p[sel]
            v = self.v[sel]
            tail = v * kb
            ln = np.linalg.norm(tail, axis=1, keepdims=True)
            short = ln < 0.014
            dirs = v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-6)
            tail = np.where(short, dirs * 0.014, tail)
            segs = [np.array([a - t, a]) for a, t in zip(p, tail)]
            pts = multi_poly_points(segs)
            set_vm_points(self.core[bi], pts)
            set_vm_points(self.halo[bi], pts)
            self.core[bi].set_stroke(SPARK_COLORS[bi], width=core_w, opacity=SPARK_OPAC[bi] * alpha)
            self.halo[bi].set_stroke(SPARK_COLORS[bi], width=halo_w, opacity=0.16 * SPARK_OPAC[bi] * alpha)


# ---------------------------------------------------------------------------------------------
# Fracture helpers
# ---------------------------------------------------------------------------------------------

def clip_halfplane(poly, nrm, c):
    out = []
    L = len(poly)
    for i in range(L):
        a, b = poly[i], poly[(i + 1) % L]
        da, db = a @ nrm - c, b @ nrm - c
        if da <= 0:
            out.append(a)
        if da * db < 0:
            t = da / (da - db)
            out.append(a + t * (b - a))
    return np.array(out)


def voronoi_cells(seeds, box=6.0):
    cells = []
    for i, s in enumerate(seeds):
        poly = np.array([[-box, -box], [box, -box], [box, box], [-box, box]], dtype=float)
        for j, q in enumerate(seeds):
            if i == j:
                continue
            nrm = q - s
            c = nrm @ ((s + q) / 2)
            poly = clip_halfplane(poly, nrm, c)
            if len(poly) < 3:
                break
        cells.append(poly)
    return cells


def jag(P, amp, rng, sub=3):
    """Subdivide a closed polygon's edges and nudge the new points sideways (fracture look)."""
    out = []
    L = len(P)
    for i in range(L):
        a, b = P[i], P[(i + 1) % L]
        out.append(a)
        d = b - a
        nrm = np.array([-d[1], d[0]]) / max(np.linalg.norm(d), 1e-9)
        for s in np.linspace(0, 1, sub + 2)[1:-1]:
            out.append(a + s * d + nrm * rng.normal(0, amp))
    return np.array(out)


def crack_path(R, rng, n=11):
    """Hairline crack across tooth 0: from the rake face near the flute root to the clearance face."""
    per, nf = tooth_period(R)
    flute = per[:nf]
    r = np.linalg.norm(flute, axis=1)
    i0 = int(np.argmin(np.abs(r - 0.70 * R)[:nf // 2]))
    start = flute[i0]
    # clearance face of the tooth before (period rotated by -90 deg): pick the point at about -27 deg
    prev = per @ rot2(-TAU / 4).T
    ang = np.degrees(np.arctan2(prev[:, 1], prev[:, 0]))
    rr = np.linalg.norm(prev, axis=1)
    cand = np.flatnonzero((ang > -40) & (ang < -12) & (rr > 0.86 * R))
    j = cand[np.argmin(np.abs(ang[cand] + 27))]
    end = prev[j]
    s = np.linspace(0, 1, n)
    mid_bow = -0.06 * R * np.sin(np.pi * s)  # bow slightly toward the centre
    d = end - start
    nrm = np.array([-d[1], d[0]]) / np.linalg.norm(d)
    # inward normal: make sure the bow points toward the centre
    if nrm @ ((start + end) / 2) > 0:
        nrm = -nrm
    pts = start + s[:, None] * d - (mid_bow[:, None]) * nrm
    noise = rng.normal(0, 0.018 * R, n)
    noise[0] = noise[-1] = 0
    pts = pts + noise[:, None] * nrm
    return pts


def chunk_polygon(R, crack):
    start, end = crack[0], crack[-1]
    a_end = np.arctan2(end[1], end[0])
    a_start = np.arctan2(start[1], start[0]) + np.radians(9)
    arc = np.array([[np.cos(a), np.sin(a)] for a in np.linspace(a_end, a_start, 12)]) * 1.6 * R
    return np.vstack([crack, arc])


# ---------------------------------------------------------------------------------------------
# The scene
# ---------------------------------------------------------------------------------------------

class S01ColdOpen(TLScene):
    SID = "s01_cold_open"

    def construct(self):
        rng = np.random.default_rng(7)
        R = 1.75
        CC = np.array([-1.3, 0.62, 0.0])
        ae = 0.55 * R                                   # radial depth of cut
        y_top = CC[1] - R + ae                          # uncut stock surface (ahead, to the right)
        y_floor = CC[1] - R                             # machined floor (behind, to the left)
        th_exit = -PI / 2 + np.arccos(1 - ae / R)       # where each tooth leaves the steel
        x_exit = CC[0] + R * np.cos(th_exit)
        exit_pt = CC + R * np.array([np.cos(th_exit), np.sin(th_exit), 0])
        t_dir = np.array([-np.sin(th_exit), np.cos(th_exit)])

        T_WEAR = self.cue(1)            # "Each hit steals a little of its edge"
        T_SLOW = self.cue(2)            # "And one day, without any warning"
        T_SNAP = LEAD + 12.38           # "...snaps"
        TOTAL = self.total
        OMEGA = 2.5 * TAU               # on-screen spin at full speed (rad/s)

        def lgeo(a, b, s):
            return float(np.exp(np.log(a) + (np.log(b) - np.log(a)) * s))

        def spd(t):
            """How fast time runs (1 = real-time look, 0.1 = high-speed camera, ~0 = frozen)."""
            if t < T_WEAR - 0.05:
                return 1.0
            if t < T_WEAR + 0.85:
                return lgeo(1.0, 0.1, smooth01((t - T_WEAR + 0.05) / 0.9))
            if t < T_SLOW - 0.05:
                return 0.1
            if t < T_SLOW + 0.95:
                return lgeo(0.1, 0.009, smooth01((t - T_SLOW + 0.05) / 1.0))
            if t < T_SNAP:
                return 0.009
            return 1.0

        ts = np.arange(0, TOTAL + 0.5, 1 / 1200)
        sp = np.array([spd(t) for t in ts])
        Phi = np.concatenate([[0], np.cumsum((sp[1:] + sp[:-1]) / 2 * np.diff(ts))])
        T0X = T_SLOW - 0.2                               # tooth 0 leaves the cut here (the last hit)
        theta0 = th_exit - OMEGA * np.interp(T0X, ts, Phi)

        def angle(t):
            return theta0 + OMEGA * np.interp(t, ts, Phi)

        # every tooth exit ("hit") before the snap
        hits = []
        for k in range(4):
            A = angle(ts) + k * PI / 2 - th_exit
            for m in range(int(np.ceil(A[0] / TAU)), int(np.floor(A[-1] / TAU)) + 1):
                th = float(np.interp(m * TAU, A, ts))
                if 0.2 < th < T_SNAP:
                    hits.append((th, k))
        hits.sort()
        wear_hits = [(th, k) for th, k in hits if T_WEAR - 0.1 < th < T_SLOW + 0.05]

        def wear(t):
            w = [0.0] * 4
            for th, k in wear_hits:
                w[k] += 0.5 * smooth01((t - th) / 0.35)
            return [min(0.95, x) for x in w]

        # ---- crack and fracture pieces (precomputed in the cutter's own coordinates) ----
        crack = crack_path(R, np.random.default_rng(11))
        seglen = np.r_[0, np.cumsum(np.linalg.norm(np.diff(crack, axis=0), axis=1))]
        crack_mid = crack[len(crack) // 2]

        P_snap, _ = cutter_profile(R, wear(T_SNAP))
        body_vm = VMobject().set_points_as_corners(to3(np.vstack([P_snap, P_snap[:1]])))
        cpoly = Polygon(*to3(chunk_polygon(R, crack)))
        shards_base = []
        chunk = Intersection(body_vm, cpoly)
        if len(chunk.points):
            shards_base.append((chunk.points.copy(), True))
        rest = Difference(body_vm, cpoly)
        seeds = [np.array([np.cos(np.radians(a)), np.sin(np.radians(a))]) * r * R for r, a in
                 [(0.82, 70), (0.82, 160), (0.82, 250), (0.62, -40), (0.42, 40), (0.42, 130),
                  (0.42, 220), (0.40, 310), (0.10, 200), (0.70, 105), (0.68, 200), (0.66, 285)]]
        for cell in voronoi_cells(seeds):
            piece = Intersection(rest, Polygon(*to3(jag(cell, 0.018 * R, rng))))
            if len(piece.points) >= 8:
                shards_base.append((piece.points.copy(), False))

        # ---- mobjects ----
        def f_top(x):
            if x >= x_exit:
                return y_top
            if x >= CC[0]:
                return CC[1] - np.sqrt(max(R * R - (x - CC[0]) ** 2, 0))
            return y_floor

        XB0, XB1, YB = -12.0, 12.0, -4.4
        poly, top = steel_block_points(f_top, XB0, XB1, YB, n=500)
        block = VMobject().set_points_as_corners(to3(poly))
        block.set_sheen_direction(DOWN)
        block_edge = VMobject().set_points_as_corners(to3(top))
        hatch = VMobject()
        contact = VMobject()
        contact_glow = VMobject()
        arc_a = np.linspace(-PI / 2, th_exit, 30)
        arc_pts = to3(np.column_stack([CC[0] + R * np.cos(arc_a), CC[1] + R * np.sin(arc_a)]))
        set_vm_points(contact, poly_bez(arc_pts))
        set_vm_points(contact_glow, poly_bez(arc_pts))

        mill = EndMill(R=R, n_ghost=3)
        trails = [VMobject() for _ in range(6)]
        trail_cols = [interpolate_color(ManimColor(WARN), ManimColor(CARBIDE), j / 5) for j in range(6)]
        trail_op = [0.5, 0.36, 0.25, 0.16, 0.09, 0.04]

        glow = [Circle(radius=r).set_stroke(width=0) for r in (0.1, 0.24, 0.5)]
        glow_op = [0.55, 0.2, 0.08]
        for g in glow:
            g.move_to(exit_pt)

        sparks = Sparks(cap=560, seed=3)
        sparks.floor = (x_exit + 0.03, y_top)

        unit_circ = Circle(radius=1, num_components=24).points.copy()
        rings = [VMobject() for _ in range(8)]
        ring_state = []  # (tau0, pos, kind)

        flakes = [VMobject() for _ in range(10)]
        flake_state = []  # dict(p, v, a, w, tau0, shape, big)

        crack_core, crack_glow, crack_front = VMobject(), VMobject(), Dot(radius=0.022)
        shards = [VMobject() for _ in shards_base]
        for s in shards:
            s.set_sheen_direction(normalize(DR))
        flash = Rectangle(width=30, height=20).set_stroke(width=0).set_fill(INK, 0)
        burst = VMobject()
        debris = VMobject()

        counter = N("213 / s", size=24, color=WARN)
        counter.move_to([-5.55, 3.25, 0])

        # the driver must come first: manim treats every mobject after the first updater-carrier as 'moving'
        driver = Dot(radius=0.001).set_opacity(0)  # invisible; carries the per-frame updater
        self.add(driver)
        self.add(block, hatch, block_edge, contact_glow, contact, *trails, mill, *glow, crack_glow, crack_core, crack_front,
                 *shards, debris, *flakes, *rings, burst, sparks, counter, flash)

        frame = self.camera.frame
        st = dict(t=None, tau=0.0, hit_i=0, last_hit_tau=-9.0, last_hit_t=-9.0, snapped=False, cam_snap=None, snap_tau=None)

        def cam(t):
            c0, w0 = np.array([-0.45, 0.3, 0]), 12.2
            c1, w1 = np.array([-0.3, 0.2, 0]), 11.2
            c2, w2 = exit_pt + np.array([0.35, 0.55, 0]), 4.8
            if t <= T_WEAR:
                s = t / T_WEAR
                return c0 + (c1 - c0) * s, w0 + (w1 - w0) * s
            if t <= T_WEAR + 2.2:
                s = smooth01((t - T_WEAR) / 2.2)
                return c1 + (c2 - c1) * s, lgeo(w1, w2, s)
            if t <= T_SLOW:
                return c2 + np.array([0.04, 0.02, 0]) * (t - T_WEAR - 2.2), w2
            c2b = c2 + np.array([0.04, 0.02, 0]) * (T_SLOW - T_WEAR - 2.2)
            tgt = mill.world(np.array([crack_mid]), angle(min(t, T_SNAP)), CC)[0] + np.array([0.05, -0.1, 0])
            s = smooth01((t - T_SLOW) / 1.8)
            return c2b + (tgt - c2b) * s, lgeo(w2, 3.7, smooth01((t - T_SLOW) / 2.6))

        def tick(mob, dt):
            if st["t"] is None:
                st["t"] = self.now
            t_prev = st["t"]
            t = t_prev + dt
            st["t"] = t
            s_now = spd(t)
            dtau = dt * s_now
            st["tau"] += dtau
            tau = st["tau"]

            alpha = smooth01((t - 0.2) / 1.3)
            a = angle(min(t, T_SNAP))
            w = wear(t)

            # ---- hits: sparks, rings, flakes ----
            while st["hit_i"] < len(hits) and hits[st["hit_i"]][0] <= t:
                th, k = hits[st["hit_i"]]
                st["hit_i"] += 1
                if th < t_prev - 0.05:
                    continue
                slow = s_now < 0.5
                sparks.spawn(30 if slow else 24, exit_pt, t_dir, spread=0.32, age_dither=dt * s_now,
                             vmin=4.0, vmax=14.0)
                ring_state.append((tau, exit_pt.copy(), t))
                st["last_hit_tau"] = tau
                st["last_hit_t"] = t
                if T_WEAR - 0.1 < th < T_SLOW + 0.05:
                    big = (k == 0)
                    for _ in range(3 if big else 2):
                        sz = (0.07 if big else 0.035) * rng.uniform(0.7, 1.2)
                        shape = np.array([[rng.uniform(-1, 1), rng.uniform(-1, 1)] for _ in range(3)]) * sz
                        shape -= shape.mean(0)
                        vdir = t_dir + rng.normal(0, 0.25, 2) + np.array([0.15, 0.0])
                        flake_state.append(dict(p=exit_pt[:2].copy(), v=vdir * rng.uniform(1.6, 3.2),
                                                a=rng.uniform(0, TAU), w=rng.uniform(-9, 9), tau0=tau,
                                                shape=shape, big=big))
                        if len(flake_state) > len(flakes):
                            flake_state.pop(0)
                        big = False

            # ---- the snap ----
            if t >= T_SNAP and not st["snapped"]:
                st["snapped"] = True
                st["snap_tau"] = tau
                st["cam_snap"] = (frame.get_center().copy(), frame.width)
                st["snap_angle"] = a
                sh_state = []
                for (pts, is_chunk) in shards_base:
                    ctr = pts.mean(0)[:2]
                    rdir = ctr / max(np.linalg.norm(ctr), 1e-6)
                    tang = np.array([-rdir[1], rdir[0]])
                    Rm = rot2(a)
                    rd = rot2(rng.normal(0, 0.35)) @ rdir
                    v = Rm @ (rd * rng.uniform(2.5, 8.5) + tang * 0.25 * OMEGA * np.linalg.norm(ctr) / R)
                    if is_chunk:
                        v = Rm @ (rdir * 6.0 + tang * 5.0)
                    sh_state.append(dict(base=pts.copy(), ctr=ctr, pos=CC[:2] + Rm @ ctr, v=v,
                                         spin=rng.uniform(-11, 11), ang=a))
                # small carbide debris
                nd = 60
                rr_ = R * np.sqrt(rng.uniform(0.05, 1, nd))
                ph = rng.uniform(0, TAU, nd)
                dpos = CC[:2] + np.column_stack([rr_ * np.cos(ph), rr_ * np.sin(ph)])
                ddir = np.column_stack([np.cos(ph), np.sin(ph)])
                dv = ddir * rng.uniform(3, 13, nd)[:, None] + np.column_stack([-np.sin(ph), np.cos(ph)]) * rng.uniform(0, 5, nd)[:, None]
                dshape = rng.uniform(-1, 1, (nd, 3, 2)) * rng.uniform(0.02, 0.06, nd)[:, None, None]
                st['debris'] = dict(p=dpos, v=dv, shape=dshape, a=rng.uniform(0, TAU, nd), w=rng.uniform(-15, 15, nd),
                                    life=rng.uniform(0.5, 1.1, nd))
                st["shards"] = sh_state
                # white-hot burst from the rim
                for _ in range(6):
                    phi = rng.uniform(0, TAU)
                    pos = CC[:2] + R * np.array([np.cos(phi), np.sin(phi)])
                    d = np.array([np.cos(phi), np.sin(phi)]) + 0.8 * np.array([-np.sin(phi), np.cos(phi)])
                    sparks.spawn(16, pos, d, spread=0.45, vmin=5, vmax=15, lmin=0.3, lmax=0.9)
                crack_world = mill.world(np.array([crack_mid]), a, CC)[0]
                st["burst_pos"] = crack_world

            # ---- camera ----
            if not st["snapped"]:
                c, wdt = cam(t)
            else:
                c_s, w_s = st["cam_snap"]
                s = ease_out((t - T_SNAP) / 0.75)
                c = c_s + (np.array([CC[0] + 0.9, CC[1] - 0.1, 0]) - c_s) * s
                wdt = lgeo(w_s, 10.5, s)
                amp = 0.11 * np.exp(-(t - T_SNAP) / 0.22) * (wdt / 6)
                c = c + np.array([rng.normal(0, amp), rng.normal(0, amp), 0])
            if t < T_WEAR + 0.6:  # the whole machine buzzes while it hammers at full speed
                buzz = 0.012 * s_now * (wdt / 12)
                c = c + np.array([rng.normal(0, buzz), rng.normal(0, buzz), 0])
            frame.move_to(c)
            frame.set(width=wdt)

            # ---- steel block ----
            a_block = alpha * (1 - smooth01((t - T_SNAP - 0.25) / 0.85))
            block.set_fill([STEEL_LIT, STEEL_SHADE], opacity=a_block)
            block.set_stroke(width=0)
            block_edge.set_stroke(interpolate_color(ManimColor(STEEL), ManimColor(INK), 0.35), width=2.2, opacity=0.95 * a_block)
            phase = -0.18 * tau
            set_vm_points(hatch, multi_poly_points([to3(sg) for sg in
                                                    hatch_segments(f_top, -9.5, 9.5, -4.4, 0.32, phase)]))
            hatch.set_stroke(HATCH, width=1.1, opacity=0.85 * a_block)
            hot = 0.35 + 0.65 * np.exp(-(tau - st["last_hit_tau"]) / 0.06)
            a_contact = a_block * (0 if st["snapped"] else 1)
            contact.set_stroke(HEAT, width=2.2, opacity=0.45 * hot * a_contact)
            contact_glow.set_stroke(HEAT, width=12, opacity=0.10 * hot * a_contact)

            # ---- cutter ----
            if not st["snapped"]:
                trem = 0.010 * smooth01((t - T_SLOW - 0.6) / 1.6)
                cc = CC + np.array([rng.normal(0, trem), rng.normal(0, trem), 0])
                blur = OMEGA * s_now / 60 * 1.7
                mill.update_state(a, cc, alpha=alpha, blur=blur, wear=w, edge=[1 - 0.72 * x for x in w])
                # tip trails
                L = min(OMEGA * s_now * 0.05, 1.1)
                tl = np.clip((L - 0.08) / 0.3, 0, 1) * alpha
                for j in range(6):
                    if tl <= 0:
                        set_vm_points(trails[j], np.zeros((0, 3)))
                        continue
                    segs = []
                    for k in range(4):
                        ak = a + k * PI / 2
                        aa = np.linspace(ak - L * (j + 1) / 6, ak - L * j / 6, 6)
                        segs.append(to3(np.column_stack([cc[0] + R * np.cos(aa), cc[1] + R * np.sin(aa)])))
                    set_vm_points(trails[j], multi_poly_points(segs))
                    trails[j].set_stroke(trail_cols[j], width=3, opacity=trail_op[j] * tl)
            else:
                mill.set_opacity(0)
                for tr in trails:
                    set_vm_points(tr, np.zeros((0, 3)))

            # ---- exit glow ----
            gi = np.exp(-(tau - st["last_hit_tau"]) / 0.07) * a_contact * (0.25 + 0.75 * np.exp(-(t - st["last_hit_t"]) / 0.6))
            for g, op in zip(glow, glow_op):
                g.set_fill(HEAT if op < 0.5 else WARN, opacity=op * gi)

            # ---- crack ----
            if not st["snapped"]:
                sgl = (t - (T_SLOW + 0.55)) / 1.75
                if sgl > 0:
                    q = np.clip(sgl, 0, 1) * 6
                    fr = (np.floor(q) + smooth01((q - np.floor(q)) / 0.35)) / 6 if q < 6 else 1.0
                    Lc = fr * seglen[-1]
                    m = np.searchsorted(seglen, Lc)
                    pts = list(crack[:m])
                    if m < len(crack):
                        u = (Lc - seglen[m - 1]) / max(seglen[m] - seglen[m - 1], 1e-9)
                        pts.append(crack[m - 1] + u * (crack[m] - crack[m - 1]))
                    pts = np.array(pts)
                    if len(pts) >= 2:
                        W = mill.world(pts)
                        set_vm_points(crack_core, poly_bez(W))
                        set_vm_points(crack_glow, poly_bez(W))
                        flick = 0.75 + 0.25 * np.sin(t * 40)
                        crack_core.set_stroke(DANGER, width=2.0, opacity=0.95)
                        crack_glow.set_stroke(DANGER, width=8, opacity=0.28 * flick)
                        crack_front.move_to(W[-1]).set_fill(HOT_WHITE, opacity=0.95 * flick if fr < 1 else 0.5)
                else:
                    crack_front.set_fill(opacity=0)
            else:
                for m_ in (crack_core, crack_glow):
                    set_vm_points(m_, np.zeros((0, 3)))
                crack_front.set_fill(opacity=0)

            # ---- shards ----
            if st["snapped"]:
                tt = tau - st["snap_tau"]
                for vm, sh in zip(shards, st["shards"]):
                    if dt > 0:
                        sh["v"] = sh["v"] * np.exp(-1.2 * dt) + np.array([0, -2.5]) * dt
                        sh["pos"] = sh["pos"] + sh["v"] * dt
                        sh["ang"] += sh["spin"] * dt
                    loc = sh["base"][:, :2] - sh["ctr"]
                    W = loc @ rot2(sh["ang"]).T + sh["pos"]
                    vm.points = to3(W)
                    op = 1 - smooth01((tt - 0.4) / 0.7)
                    vm.set_fill([BODY_LIT, BODY_SHADE], opacity=op)
                    hot_edge = np.exp(-tt / 0.18)
                    vm.set_stroke(interpolate_color(ManimColor(CARBIDE), ManimColor(HOT_WHITE), hot_edge),
                                  width=2.2, opacity=0.9 * op)
                db = st['debris']
                if dt > 0:
                    db['v'] = db['v'] * np.exp(-1.0 * dt)
                    db['v'][:, 1] -= 4.0 * dt
                    db['p'] = db['p'] + db['v'] * dt
                    db['a'] = db['a'] + db['w'] * dt
                alive = tt < db['life']
                tris = []
                for i in np.flatnonzero(alive):
                    W = db['shape'][i] @ rot2(db['a'][i]).T + db['p'][i]
                    tris.append(np.vstack([W, W[:1]]))
                set_vm_points(debris, multi_poly_points(tris))
                debris.set_fill(interpolate_color(ManimColor(HOT_WHITE), ManimColor(CARBIDE), min(1, tt / 0.25)),
                                opacity=max(0.0, 1 - tt / 1.1))
                debris.set_stroke(width=0)
                # flash + burst ring
                fl = 0.92 * np.exp(-(t - T_SNAP) / 0.11) * smooth01((t - T_SNAP) / 0.03 + 0.4)
                flash.move_to(frame.get_center()).set_fill(INK, opacity=fl)
                u = (t - T_SNAP) / 0.55
                if u < 1:
                    rr = 0.1 + 5.5 * ease_out(u)
                    set_vm_points(burst, unit_circ * rr + np.array([*st["burst_pos"][:2], 0]))
                    burst.set_stroke(INK, width=3 * (1 - u) + 0.5, opacity=0.8 * (1 - u) ** 2)
                else:
                    burst.set_stroke(opacity=0)

            # ---- sparks / rings / flakes ----
            sparks.step(dtau)
            sparks.draw(s_now, alpha=1.0, blur_k=0.03)
            while len(ring_state) > len(rings):
                ring_state.pop(0)
            for i, rg in enumerate(rings):
                if i < len(ring_state):
                    t0, pos, t0r = ring_state[i]
                    rfade = 1 - smooth01((t - t0r - 0.25) / 0.5)
                    u = (tau - t0) / 0.26
                    if 0 <= u < 1:
                        rr = 0.05 + 1.1 * ease_out(u)
                        set_vm_points(rg, unit_circ * rr + pos)
                        rg.set_stroke(WARN, width=2.0 * (1 - u) + 0.4, opacity=0.34 * (1 - u) ** 2 * alpha * rfade)
                        continue
                rg.set_stroke(opacity=0)
            for i, fv in enumerate(flakes):
                if i < len(flake_state):
                    fs = flake_state[i]
                    age = tau - fs["tau0"]
                    if age < 1.4:
                        if dtau > 0:
                            fs["v"] = fs["v"] + np.array([0, -6.0]) * dtau
                            fs["p"] = fs["p"] + fs["v"] * dtau
                            fs["a"] += fs["w"] * dtau
                        W = fs["shape"] @ rot2(fs["a"]).T + fs["p"]
                        fv.points = poly_bez(np.vstack([W, W[:1]]))
                        op = 1 - smooth01((age - 0.8) / 0.6)
                        glint = abs(np.cos(fs["a"] * 1.5))
                        fv.set_fill(interpolate_color(ManimColor(CARBIDE), ManimColor(HOT_WHITE), glint), opacity=op)
                        fv.set_stroke(WARN, width=1.2, opacity=op * glint)
                        continue
                fv.set_fill(opacity=0).set_stroke(opacity=0)

            # ---- counter ----
            c_op = smooth01((t - 1.0) / 0.6) * (1 - smooth01((t - T_WEAR + 0.3) / 0.5))
            pulse = np.exp(-(tau - st["last_hit_tau"]) / 0.05)
            counter.set_opacity(c_op * (0.75 + 0.25 * pulse))

        driver.add_updater(tick)
        tick(driver, 0)
        self.wait_until(TOTAL - 0.5)
        driver.clear_updaters()
        self.remove(*self.mobjects)
        self.finish()
