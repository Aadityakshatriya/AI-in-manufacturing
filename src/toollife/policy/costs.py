"""Cost settings for keep-or-change decisions (research/next-phase/costs.md).

Cost model (costs.md §1.3 and §8.1), all prices before GST/VAT:
  planned change   C_p = C_t + R·t_p − C_rg
  breakage         C_f = C_t + R·t_b + p_s·V + (1 − p_s)·0.1·V + E_coll
  every cycle run  c_m = R·t_c       (also charged on the cycle that breaks)
  score            total cost ÷ good cycles      (renewal-reward ratio over many cutters)

Defaults are the India-typical column of costs.md §1.1: end mill ₹3,000, machine + operator
₹800/h, planned change 10 min, breakage downtime 45 min, cycle 1.3 min, part at risk ₹3,000 scrapped
half the time, collateral damage ₹1,280. That gives C_p = ₹3,133, C_f = ₹6,530 (ratio 2.08) and
c_m = ₹17.3 per cycle. (costs.md §8.2 quotes c_m = ₹17.7; R·t_c with the listed 1.3 min is ₹17.3.)

Sensitivity grid (costs.md §1.4): breakage ratio r = C_f/C_p ∈ {1.5, 2, 3, 5, 10, 20, 30} ×
machining ratio k = c_m/C_p ∈ {0.006, 0.016}, with C_p held at the India-typical ₹3,133. Named
real-money scenarios: India and Europe, typical / all-low / all-high / lowest-ratio / highest-ratio
mixes (costs.md §1.3 table; each reproduces that table's C_p and C_f).

A life that ends at a wear limit instead of a breakage (other datasets) is charged as a planned change
plus one scrapped part (V) [assumption: the out-of-tolerance part is lost; no collateral damage].
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Econ:
    """Event model for one decision, used by the DP, the rules and the replay.

    The decision layer minimises the long-run ratio E[A] / E[B] over many cutter lives
    (renewal-reward theorem). After each good cycle the choice is:
      change now                → A += a_change, B += b_change, the life ends
      keep, next cycle is good  → A += a_survive, B += b_survive, decide again
      keep, the cutter fails    → A += a_break (a_wear for wear-limit lives), B += b_break, life ends
    For costs.md, A = rupees and B = good cycles, so the ratio is cost per good cycle.
    The workshop uses the same structure with A = −profit and B = machine ticks.
    """

    a_survive: float
    b_survive: float
    a_break: float
    b_break: float
    a_change: float
    b_change: float
    a_wear: float | None = None
    b_wear: float | None = None

    def end(self, end_type: str) -> tuple[float, float]:
        if end_type != "break" and self.a_wear is not None:
            return self.a_wear, self.b_wear
        return self.a_break, self.b_break


@dataclass(frozen=True)
class Costs:
    name: str = "india_typical"
    currency: str = "INR"
    tool_price: float = 3000.0        # C_t, one 10 mm solid-carbide end mill
    machine_rate_h: float = 800.0     # R, machine + operator per hour
    change_min: float = 10.0          # t_p, planned change: stop to cutting again
    break_min: float = 45.0           # t_b, breakage: break to cutting again
    cycle_min: float = 1.3            # t_c, one machining cycle of the dataset
    part_value: float = 3000.0        # V, part at risk when the cutter breaks
    p_scrap: float = 0.5              # p_s, chance a breakage scraps the part (else 10 % repair)
    collateral: float = 1280.0        # E_coll, average collet / holder / spindle damage
    regrind_credit: float = 0.0       # C_rg, money back for a worn (unbroken) cutter
    # Grid cells set the three totals directly (in the same currency).
    C_p_set: float | None = None
    C_f_set: float | None = None
    c_m_set: float | None = None

    @property
    def C_p(self) -> float:
        if self.C_p_set is not None:
            return self.C_p_set
        return self.tool_price + self.machine_rate_h * self.change_min / 60 - self.regrind_credit

    @property
    def C_f(self) -> float:
        if self.C_f_set is not None:
            return self.C_f_set
        part = self.p_scrap * self.part_value + (1 - self.p_scrap) * 0.1 * self.part_value
        return self.tool_price + self.machine_rate_h * self.break_min / 60 + part + self.collateral

    @property
    def c_m(self) -> float:
        if self.c_m_set is not None:
            return self.c_m_set
        return self.machine_rate_h * self.cycle_min / 60

    @property
    def r(self) -> float:
        return self.C_f / self.C_p

    @property
    def k(self) -> float:
        return self.c_m / self.C_p

    def econ(self) -> Econ:
        """Cost per good cycle (costs.md §8.1)."""
        return Econ(a_survive=self.c_m, b_survive=1.0, a_break=self.c_m + self.C_f, b_break=0.0,
                    a_change=self.C_p, b_change=0.0,
                    a_wear=self.c_m + self.C_p + self.part_value, b_wear=0.0)

    def one_step_threshold(self, g: float) -> float:
        """costs.md §7.3: change once P(fail next cycle) > a / (a + c_m + C_f − C_p), a = g − c_m,
        where g is the long-run cost per good cycle of the policy."""
        a = g - self.c_m
        return a / (a + self.c_m + self.C_f - self.C_p)

    def approx_threshold(self, mean_life: float = 60.0) -> float:
        """costs.md §1.4 rule of thumb, p* ≈ (1/L) / (1/L + k + r − 1)."""
        return (1 / mean_life) / (1 / mean_life + self.k + self.r - 1)


INDIA = Costs()
EUROPE = Costs(name="europe_typical", currency="EUR", tool_price=95, machine_rate_h=80,
               part_value=250, collateral=57)

# costs.md §1.3 scenario table. Fields not mentioned keep the typical value of that region.
NAMED: dict[str, Costs] = {
    "india_typical": INDIA,
    "india_all_low": replace(INDIA, name="india_all_low", tool_price=1200, machine_rate_h=400, change_min=3,
                             break_min=15, cycle_min=1.0, part_value=1000, p_scrap=0.2, collateral=460),
    "india_all_high": replace(INDIA, name="india_all_high", tool_price=15000, machine_rate_h=1200, change_min=25,
                              break_min=180, cycle_min=1.9, part_value=25000, p_scrap=0.9, collateral=6100),
    "india_lowest_ratio": replace(INDIA, name="india_lowest_ratio", tool_price=15000, machine_rate_h=400,
                                  change_min=25, break_min=15, part_value=1000, p_scrap=0.2, collateral=460),
    "india_highest_ratio": replace(INDIA, name="india_highest_ratio", tool_price=1200, machine_rate_h=1200,
                                   change_min=3, break_min=180, part_value=25000, p_scrap=0.9, collateral=6100),
    "europe_typical": EUROPE,
    "europe_all_low": replace(EUROPE, name="europe_all_low", tool_price=45, machine_rate_h=50, change_min=3,
                              break_min=15, cycle_min=1.0, part_value=60, p_scrap=0.2, collateral=20),
    "europe_all_high": replace(EUROPE, name="europe_all_high", tool_price=160, machine_rate_h=120, change_min=25,
                               break_min=180, cycle_min=1.9, part_value=2500, p_scrap=0.9, collateral=283),
    "europe_lowest_ratio": replace(EUROPE, name="europe_lowest_ratio", tool_price=160, machine_rate_h=50,
                                   change_min=25, break_min=15, part_value=60, p_scrap=0.2, collateral=20),
    "europe_highest_ratio": replace(EUROPE, name="europe_highest_ratio", tool_price=45, machine_rate_h=120,
                                    change_min=3, break_min=180, part_value=2500, p_scrap=0.9, collateral=283),
}

R_GRID = (1.5, 2, 3, 5, 10, 20, 30)
K_GRID = (0.006, 0.016)


def grid(c_p: float = INDIA.C_p) -> list[Costs]:
    """The 7 × 2 sensitivity grid of costs.md §1.4, in rupees with C_p fixed."""
    return [Costs(name=f"r{r:g}_k{k:g}", C_p_set=c_p, C_f_set=r * c_p, c_m_set=k * c_p)
            for k in K_GRID for r in R_GRID]


def all_settings() -> list[Costs]:
    """Named real-money scenarios first, then the grid."""
    return list(NAMED.values()) + grid()
