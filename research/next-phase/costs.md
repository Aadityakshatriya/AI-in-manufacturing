# Cost numbers for the cutter-replacement simulator

Written 27 Oct 2026. This note gathers real-world cost numbers for our "keep going or change the cutter" simulator, and turns them into one recommended set of cost settings.

The cutter: a 10 mm solid carbide end mill (a cutter made entirely of tungsten carbide), coated, with 4 cutting edges ("flutes"), cutting hardened alloy steel 42CrMo4 at about 35–42 HRC. The machine: a 3-axis vertical machining centre (VMC). The main setting is an Indian job shop (a shop that machines parts to order for other companies). A European shop is the second setting.

## How to read this note

Every number carries a tag that says how much to trust it:

| Tag | Meaning |
|---|---|
| **[F]** | I opened the page this session and checked the number on it. |
| **[S]** | I saw the number only in a search-result summary. The page itself would not open, so check it before quoting it in our report. |
| **[M]** | Measured by me from our own dataset (Piecuch & Żabiński 2025). |
| **[T]** | Standard textbook result. |
| **[A]** | Assumption. No published figure was found, so the number is my reasoned estimate. Replace it with a real shop's number when we get one. |

**Currency.** I use the European Central Bank reference rate for 26 Oct 2026: €1 = ₹106.49 = US$1.1188 = £0.8382 [F] ([ECB](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml)). All prices are **before GST/VAT**. A business can claim that tax back, so the pre-tax price is what the shop really pays [A, standard GST/VAT input-credit rule].

**A limit on this research.** The session ran out of web searches partway through. Tool prices, machine rates, wages and tool-setting times are sourced. Part values, the time lost to a breakage, and collateral damage (damage to other things when a cutter breaks) are reasoned assumptions [A]. Section 9 lists what to ask a real shop.

---

## 1. The short answer

### 1.1 Recommended settings: Indian job shop (main case)

The € figures in brackets are just the ₹ values converted. They are not European prices.

| # | Setting | Symbol | Low | Typical | High | Where it comes from |
|---|---|---|---|---|---|---|
| 1 | Price of one end mill (before GST) | `C_t` | ₹1,200 (€11) | ₹3,000 (€28) | ₹15,000 (€141) | Low: unbranded or budget cutters, ₹1,297–2,055 [F]. Typical: mid-range brands, YG-1 ₹2,666 [F], Totem ₹3,316 [F], Tabikut 60 HRC ₹3,130 [F]. High: premium brands, €127–161 in Europe (= ₹13,500–17,200) [F/S], and Kennametal at ₹21,999 on an Indian marketplace [F]. See §2. |
| 2 | Cost of one hour of machine time, with operator | `R` | ₹400/h (€3.8) | ₹800/h (€7.5) | ₹1,200/h (€11.3) | Low: rates shops advertise for VMC work, ₹250–500/h [S]. Typical: MSME Tool Room VMC rate ₹800/h (2021) [S], NIT Calicut VMC ₹600/h + GST [F], and my own cost build-up of about ₹725/h [A]. High: [A], for bigger or high-precision shops. See §3. |
| 3 | Of which: operator pay, including employer extras | `w` | ₹110/h | ₹170/h | ₹260/h | Legal minimum wage ₹18,961/month [S]. Typical VMC operator pay ₹30,157/month [S]. Setters ₹35–40k/month [S]. Plus 25% for employer extras such as provident fund (PF) and state insurance (ESI) [A]. Already included in `R`. |
| 4 | Planned change time: machine stopped until cutting restarts with the new tool | `t_p` | 3 min | 10 min | 25 min | Measuring tool length by hand takes 3–5 min [F], or up to 6 min [F]. With an automatic tool-length probe it takes under 30 s [F]. The time to swap the tool and check the first part is [A]. See §4. |
| 5 | Time lost to a breakage: from the break until cutting restarts, including fitting and measuring the new tool | `t_b` | 15 min | 45 min | 180 min | [A]. See §5.1. |
| 6 | Length of one machining cycle in our dataset | `t_c` | 1.0 min | 1.3 min | 1.9 min | [M]. The raw files of cutter 2 show cycles of 58–112 s. |
| 7 | Value of the part at risk when the cutter breaks | `V` | ₹1,000 (€9) | ₹3,000 (€28) | ₹25,000 (€235) | [A]. Material cost plus earlier machining hours × `R`. See §5.2. |
| 8 | Chance a breakage scraps the part (otherwise it is repaired for 10% of `V`) | `p_s` | 0.2 | 0.5 | 0.9 | [A] |
| 9 | Average collateral damage per breakage | `E_coll` | ₹460 (€4) | ₹1,280 (€12) | ₹6,100 (€57) | [A]. Built up from the collet (the clamping sleeve that holds the cutter), the tool holder, and the rare spindle repair. See §5.3. |
| 10 | Optional: money back for regrinding a worn (unbroken) cutter | `C_rg` | 0 | 0 | 30% of `C_t` | [A]. Leave at 0 unless we model regrinding. |

### 1.2 Recommended settings: European shop (second case)

| # | Setting | Low | Typical | High | Where it comes from |
|---|---|---|---|---|---|
| 1 | `C_t`, end mill price (before VAT) | €45 | €95 | €160 | Low: WIDIA 10 mm at $49.99 (= €45) [S], HOLEX 6-flute at about €62 [F]. Typical: Sandvik CoroMill Plura 10 mm at £67.80–79.09 (= €81–94) [S]. High: Sandvik Plura for hardened steel at £133 (= €159) [S], Iscar at $180 (= €161) [S], Seco Jabro JS554 at $177 (= €158) [S], GARANT Master Steel at €126.59 [F]. |
| 2 | `R`, machine + operator per hour | €50/h | €80/h | €120/h | German price guide for 3-axis milling, €70–120/h including labour [S]. German worked example, machine only, €67/h [S]. US trade-magazine example, $75/h (= €67) [F]. Low: average EU industry labour cost €33.9/h [F] plus a machine-only cost of €17.88/h [S]. |
| 3 | `w`, operator cost per hour | €25/h | €34/h | €48/h | EU industry average €33.9/h [F], EU manufacturing €33.70/h [S], German manufacturing €48.30/h [S]. Low: [A], cheaper EU countries. |
| 4–6, 8 | `t_p`, `t_b`, `t_c`, `p_s` | same as India | | | Times and chances do not depend on the country [A]. |
| 7 | `V`, part value | €60 | €250 | €2,500 | [A]. Same method as India. Higher, because each machine hour costs about 10 times more. |
| 9 | `E_coll`, average collateral damage | €20 | €57 | €283 | [A]. Collet €35, holder €150, spindle repair €15–25k. See §5.3. |

### 1.3 What a planned change and a breakage cost

The two formulas the simulator should use:

```
Planned change:  C_p = C_t + R · t_p − C_rg
Breakage:        C_f = C_t + R · t_b + p_s · V + (1 − p_s) · 0.1 · V + E_coll
Every cycle run: c_m = R · t_c   (charged on every cycle, including the one that breaks)
Score:           total cost ÷ number of good cycles
```

The cycle that breaks is charged its `c_m` but is not counted as a good cycle, so we do not add it to `C_f` a second time.

What the numbers give:

| Scenario | `C_p` (planned) | `C_f` (breakage) | **`C_f ÷ C_p`** | Extra cost of a breakage, `C_f − C_p` |
|---|---|---|---|---|
| India, typical | ₹3,133 (€29) | ₹6,530 (€61) | **2.1** | ₹3,397 |
| India, all low | ₹1,220 | ₹2,040 | 1.7 | ₹820 |
| India, all high | ₹15,500 | ₹47,450 | 3.1 | ₹31,950 |
| India, lowest-ratio mix (premium cutter, cheap part, quick recovery, slow planned change) | ₹15,167 | ₹15,840 | 1.04 | ₹673 |
| India, highest-ratio mix (cheap cutter, valuable part, long recovery, fast planned change) | ₹1,260 | ₹33,650 | 26.7 | ₹32,390 |
| Europe, typical | €108 | €349 | **3.2** | €241 |
| Europe, all low | €48 | €94 | 2.0 | €47 |
| Europe, all high | €210 | €3,078 | 14.7 | €2,868 |
| Europe, lowest-ratio mix | €181 | €209 | 1.16 | €28 |
| Europe, highest-ratio mix | €51 | €2,962 | 58 | €2,912 |

**The main finding.** With typical numbers, a breakage costs about **2× a planned change in India** and about **3× in Europe**. That is lower than the 5×, 10× and 20× settings in `PROJECT_EXPLAINED.md`.

The reason is that the cutter is thrown away in both cases, so its price appears in both costs. In India the cutter's price is most of a planned change: ₹3,000 out of ₹3,133, because machine time is cheap. Ratios of 10–30 happen only when the part is valuable and recovery is slow, for example a nearly finished mould plate, or a machine left running with nobody watching.

### 1.4 Suggested sensitivity grid

| Axis | Values | Why |
|---|---|---|
| **Main:** `r = C_f ÷ C_p` | 1.5, 2, 3, 5, 10, 20, 30 | Spaced so each step is roughly a similar multiple. Covers India-typical (≈2), Europe-typical (≈3), and the valuable-part cases (10–30). It still contains our original 5, 10 and 20. |
| Second: `k = c_m ÷ C_p`, the cost of one cycle of machining compared with a planned change | 0.006 (India-typical), 0.016 (Europe-typical) | This barely moves the keep/change decision (§8.3). It does change the **percentage** saving, because machining is a fixed cost in every policy. So state `k` next to any "% saved" claim. |
| Only if we add a "run slower" action: Taylor exponent `n` (how fast tool life falls as speed rises) | 0.15, 0.25, 0.4 | See §6. |

That gives 7 × 2 = 14 cost settings. Our rule "it must hold in at least 70% of settings" then means at least 10 of the 14.

Also report two cases in real money: **India-typical** and **Europe-typical**, plus the four corner mixes from the table in §1.3.

In units where a planned change costs 1, the decision threshold works out to about `p* ≈ (1/L) ÷ (1/L + k + r − 1)`. Here `p*` is the chance of breaking in the next cycle above which we should change, and `L` is the average number of cycles a cutter is used for. With `L ≈ 60` this gives:

| r | 1.5 | 2 | 3 | 5 | 10 | 20 | 30 |
|---|---|---|---|---|---|---|---|
| Change the cutter once the chance of breaking next cycle exceeds about | 3.2% | 1.6% | 0.8% | 0.4% | 0.19% | 0.09% | 0.06% |

With only 13 cutters, a model can tell a 1–3% chance of breaking from a 0.1% chance. It cannot reliably tell 0.1% from 0.05%. So at r ≥ 10 the decision is driven by the safety limit, not by the model's fine detail. That is worth saying in the report.

---

## 2. Price of a 10 mm, 4-flute, coated solid carbide end mill

### 2.1 India

Indian marketplaces list a lot of variants. Premium brands rarely show a price; distributors give one only on request. "Before GST" is the true cost to a shop.

| Brand and tier | Item | Price before GST | Price incl. GST / list price (MRP) | Source |
|---|---|---|---|---|
| Unbranded or imported | 10 mm, 4-flute, ball nose | ₹1,297 | — | IndiaMART, Bengaluru listings [F] ([link](https://m.indiamart.com/city/bengaluru/carbide-end-mills.html)) |
| Unbranded or imported | 10 mm, 4-flute (STM) | ₹1,360 | — | same page [F] |
| Tabikut (sold by Jaibros) | 10 mm, 4-flute, rated for 55 HRC steel | ₹2,055 (tax not stated) | — | [jaibros.com](https://www.jaibros.com/search?q=10mm+carbide+end+mill+4+flute) [F] |
| Tabikut (Jaibros) | 10 mm, 4-flute, 60 HRC | ₹3,130 | — | same [F] |
| Tabikut (Jaibros) | 10 mm, 4-flute, 65 HRC, long | ₹5,670 | — | same [F] |
| YG-1 (mid-range; Korean, with an Indian plant) | EM595100, 10 mm, 4-flute, TiAlN coating, 70 mm long | ₹2,666 | ₹3,145; MRP ₹6,984 | [Moglix](https://www.moglix.com/yg-1-10mm-4-flute-carbide-short-end-mill-em595100/mp/msng9vnwen2dkp) [F] |
| Totem (Indian brand) | F188, 10 mm, 4-flute, TiAlN, ball nose, 100 mm long | ₹3,316 | ₹3,903; MRP ₹5,390 | [Moglix](https://www.moglix.com/totem-fbk0500887-4-flute-extra-long-length-ball-nose-end-mill-cutting-dia-10-mm/mp/msn2km1d4wmx9v) [F] |
| Totem | F122, 9 mm, 4-flute, uncoated | ₹2,221 | ₹2,629; MRP ₹3,611 | [Moglix](https://www.moglix.com/totem-9x35x89x10mm-4-flute-uncoated-carbide-end-mill-fbk0500351/mp/msn4k6zwnl88kq) [F] |
| Totem | "Proton Plus", 10 mm, 4-flute, for 45–60 HRC steel | price on request | — | [L&T-SuFin](https://lntsufin.com/product/totem-solid-carbide-end-mill-10-mm-75-mm/16832-1961) [F]. Confirms this exact type is sold in India. |
| Kennametal (premium) | GOmill GP 4CH1000MR022A, 10 mm, 4-flute, KC633M grade, TiAlN | ₹21,999 | ₹25,959 | [Industrybuying](https://www.industrybuying.com/carbide-end-mill-kennametal-TOO.CAR.14334902) [F]. A marketplace list price, probably above what a regular customer pays. |
| Sandvik, Iscar, Seco, Walter, WIDIA, Addison | 10 mm, 4-flute | no public INR price found | — | L&T-SuFin and IndiaMART list WIDIA and Addison end mills, but only as "price on request" [S] |

How I read this:
- Budget cutters: ₹1,000–2,000.
- Mid-range brands an Indian job shop would actually buy for 40 HRC steel (YG-1, Totem, Tabikut, WIDIA India, Addison): ₹2,500–5,000.
- Premium brands: European list prices convert to ₹8,600–20,000, and the one Indian listing is ₹22,000.
- **Typical is ₹3,000.** For the high value I use ₹15,000, because Indian distributors usually discount premium list prices [A].

### 2.2 Europe (with UK and US prices for comparison)

| Brand | Item | Price | In € | Source |
|---|---|---|---|---|
| GARANT (Hoffmann Group) | Master Steel HPC roughing end mill, 10 mm, 4-flute, TiAlN, for steel up to 1,400 N/mm² (covers 42CrMo4 at 35–42 HRC) | €126.59 before VAT | €126.59 | [Hoffmann DE 203036 10](https://www.hoffmann-group.com/DE/de/hom/p/203036-10) [F] |
| HOLEX (Hoffmann's budget brand) | 10 mm, 6-flute finishing end mill, TiAlN | €62.31 (page unclear whether VAT is included) | ≈€62 | [Hoffmann 203520 10](https://hoffmann-group.com/p/203520-10) [F] |
| Sandvik Coromant | CoroMill Plura 10 mm, straight shank, AlCrN coating | £79.09 before VAT | €94 | [Cromwell UK](https://www.cromwell.co.uk/shop/cutting-tools/end-mills-regular/coromill-plura-end-mill-regular-straight-shank-10mm-alcrn-carbide/p/SNK1610161R) [S] |
| Sandvik Coromant | Plura 1P240-1000-XA 1630 | £67.80 before VAT | €81 | [Rubix UK](https://uk.rubix.com/en/g1298046526/p-G1298046526) [S] |
| Sandvik Coromant | Plura 2P340-1000-PA 1630, 10 mm | £125.58 before VAT | €150 | [Rubix UK](https://uk.rubix.com/en/g1298047516/p-G1298047516) [S] |
| Sandvik Coromant | 2S342-1000-050-PA 1730, 10 mm, 4-flute; grade 1730 is for hard materials | £133.00 before VAT | €159 | [Rubix UK](https://uk.rubix.com/en/g1298047681/p-G1298047681) [S] |
| Sandvik Coromant | Plura R216.24-10030BAJ10G 1610 | £158.65 before VAT | €189 | [Rubix UK](https://uk.rubix.com/en/g1298032516/p-G1298032516) [S] |
| Merlin (UK distributor brand) | 10 mm, 4-flute, TiAlN | £83.59 before VAT | €100 | [Cromwell UK](https://cromwell.co.uk/shop/cutting-tools/end-mills-regular/414-10514-10-00mm-sol-carb-tialn-4flstd-end-mill/p/MRN1615032H) [S] |
| Seco | Jabro JS554100E2C.0Z4-SIRA, 10 mm, 4-flute | 135.00 (currency not shown; US site) | ≈€121 | [Mars Supply](https://marssupply.com/Product/SEC03029963) [S] |
| Seco | JS554100D3C.0Z4C-SIRA | 177.00 (US site) | ≈€158 | [Mars Supply](https://marssupply.com/Product/SEC02810479) [S] |
| Iscar | 10 mm, 4-flute | $180.39 | €161 | Penn Tool Co. (US) [S] |
| Kennametal | 10 mm, 4-flute, AlTiN, R1 corner | $65.72 | €59 | [Penn Tool Co.](https://www.penntoolco.com/58458373) [S] |
| WIDIA | 10 mm square end mill | $49.99 | €45 | [Zoro US](https://www.zoro.com/widia-sq-end-mill-single-end-carb-1000mm-40031000w022s/i/G3805320/) [S] |
| Walter | MC232 Perform (sizes 2–20 mm) | no public price found | — | [S] |

A comparable research simulation of tool replacement (Colantonio et al. 2025, below) priced a 5 mm, 4-flute coated carbide cutter at **€40**, "based on prices from various tool manufacturers, such as Holex" [F].

How I read this: budget European cutters cost €40–60, standard premium cutters €80–100, and cutters made for hardened steel €125–190. **Typical is €95.**

---

## 3. What an hour of machine time costs, and what operators earn

The **machine-hour rate** is what one hour of a machine running costs the shop. It is the machine's purchase cost spread over its life, plus interest, power, maintenance, floor space, the operator and overheads. When a machine stands idle during a tool change or after a breakage, this is the money that is lost.

### 3.1 India

| Source | VMC rate | Notes |
|---|---|---|
| MSME Tool Room, Ludhiana, rate list dated 5 May 2021 | **₹800/h** (₹640/h for micro enterprises) | Government tool room. Same list: 5-axis CNC ₹3,000/h, CNC turning ₹200/h. I saw this only through a [Scribd copy](https://www.scribd.com/document/767640118/Machine-Hour-Rates) in a search summary [S]. |
| NIT Calicut central research facility, Ace Micromatic MCV-300 VMC | **₹600/h for industry** (₹300/h internal), GST extra | [NITC CRF page](https://randc.nitc.ac.in/crf/med/36%20-%20cnc%20vmc%201.htm) [F]. An academic rate, probably below commercial cost. |
| Rates shops advertise on IndiaMART for VMC work | ₹250–500/h. Examples: Vanshi Engineering (Surat) ₹350/h, or ₹450/h for heavy work. Mahek Engineering (Rajkot) ₹400/h. Polygon Technology (Chennai) ₹400/h. Achyut Engitech (Rajkot) ₹400/h steel, ₹500/h aluminium. | Asking prices for simple work [S]: [Vanshi](https://m.indiamart.com/vanshi-engineering), [Mahek](https://m.indiamart.com/mahekengineeringrajkot/vmc-job-work.html), [Polygon](https://m.indiamart.com/polygon-technology/machine-service.html), [Achyut](https://m.indiamart.com/arcverticalprocess/heavy-vmc-machining-work.html) |
| IIT Kanpur central workshop, May 2025 | conventional milling ₹550/h + 18% GST for industry | For comparison only, since it is not a VMC [S] ([job card](https://www.iitk.ac.in/celp/data/downloadables/Workshop-Job-Card-16-05-2025.docx)) |

**Cross-check from a cost build-up [A].** Assume:
- An Indian-built 3-axis VMC costs ₹30 lakh and lasts 10 years.
- It does 3,600 productive hours a year (2 shifts × 300 days × 8 h × 75% of the time cutting).
- Interest is 10% on the average money tied up in the machine.
- Maintenance is 4% of the price per year.
- Power is 8 kW × ₹9/kWh.
- Floor space and utilities cost ₹1 lakh a year.
- The operator costs ₹170/h, divided by the 75% cutting share.

Per hour, that is ₹83 (purchase cost) + ₹42 (interest) + ₹33 (maintenance) + ₹72 (power) + ₹28 (space) + ₹227 (operator) = **≈₹485/h of direct cost**. Adding about 30% shop overhead (supervision, inspection, admin) and 15% margin gives **≈₹725/h**. This matches the ₹600–800 published rates. **Typical: ₹800/h.**

Operator pay in India:

| Source | Figure |
|---|---|
| Maharashtra minimum wage, engineering industry, skilled worker, Zone I, from 1 Jan 2026 | ₹18,961/month [S] ([WageIndicator](https://wageindicator.org/en-in/ai/work-in-india/minimum-wage/18640-maharashtra/18790-engineering-industry/)) → about ₹91/h over 208 h/month |
| Jooble, VMC operator | ₹30,157/month = ₹168/h [S] ([Jooble](https://in.jooble.org/salary/vmc-operator)) |
| AmbitionBox, VMC operator at Bharat Fritz Werner | ₹2.2–4.0 lakh/yr; take-home ₹20,885–22,535/month [S] ([AmbitionBox](https://www.ambitionbox.com/salaries/bharat-fritz-werner-salaries/vmc-operator)) |
| Job adverts, VMC programmer-cum-setter (the person who sets up the machine and writes its programs) | freshers ₹20–25k/month; experienced ₹30–40k/month [S] (e.g. [TeamLease](https://teamlease.com/jobs/cnc-and-vmc-programmer-cum-setter-jobs-in-chennai-ashvam-engineering-1746050)) |

With employer extras (PF, ESI, bonus) adding about 25% [A]: **₹110–260/h, typical ₹170/h.** In India the operator is roughly half of the machine-hour rate.

### 3.2 Europe

| Source | Figure |
|---|---|
| Eurostat, 2024 | Average hourly labour cost (what an employer pays per hour worked): €33.5 EU and €37.3 euro area for the whole economy; **€33.9 EU and €39.8 euro area for industry**. Lowest Bulgaria €10.6, highest Luxembourg €55.2. [F] ([Eurostat](https://ec.europa.eu/eurostat/web/products-eurostat-news/w/ddn-20250328-1)) |
| Destatis (German statistics office), 2024 | **German manufacturing €48.30/h**, 43% above the EU manufacturing average of €33.70 [S] ([vergabeblog report](https://vergabeblog.de/2025-05-09/lohnkosten-in-deutschland-arbeitsstunde-kostet-durchschnittlich-4340-euro/)) |
| German job adverts for CNC milling operators | €17–26/h gross wage [S] (e.g. [Chemnitz advert, €18.36/h](https://www.hofmann.info/jobs/stellenanzeige/1b6l39-zerspanungsmechaniker-mwd_09125-chemnitz-sachsen.pdf)) |
| clean-invoice.com price guide (2026) | **3-axis CNC milling €70–120/h in Germany, including labour**, ±20% by region. This is the price charged to customers [S] ([link](https://www.clean-invoice.com/feinwerkmechanik/kosten-und-kalkulation-feinwerkmechanik)) |
| welt-der-bwl.de worked example | Machine-hour rate excluding labour: €67/h (a €300k machine, 1,500 h/yr) [S] ([link](https://www.welt-der-bwl.de/Maschinenstundensatz)) |
| whk-controlling worked example | Machine-hour rate excluding labour: €17.88/h (a €120k machine, 1,600 h/yr) [S] ([link](https://www.whk-controlling.de/wissen/maschinenstundensatz-rechner)) |
| Cutting Tool Engineering, 2017 | Uses **$75/h** (= €67) as a typical shop rate in its example [F] ([CTE](https://ctemag.com/articles/save-time-setting-tools-offline-presetter/)) |
| UK forum posts (2014–2017, anecdotal) | 3-axis VMC £40–45/h [S] ([mycncuk](https://www.mycncuk.com/archive/index.php/t-10771.html)) |

**Choice: €50 / €80 / €120 per hour.** Unlike India, the operator is most of the European rate: €34–48 of the €80.

---

## 4. How long a planned tool change takes on a VMC

"Planned change time" means how long the machine stands still, from stopping it to cutting again with a measured new tool. It has three parts.

1. **Swapping the cutter.** Take the holder out, loosen the collet, fit the new end mill, tighten. About 1–5 min by hand [A]. If a second, ready-loaded holder is kept on the side, it is under 1 min.
2. **Measuring the tool length.** The machine must know exactly how far the new tip sticks out (the "tool length offset").
   - "Tool setting might consume 3 to 5 minutes per tool" [F] ([Cutting Tool Engineering 2017](https://ctemag.com/articles/save-time-setting-tools-offline-presetter/)).
   - A Renishaw case brief on a UK subcontractor (Quality Engineered Products Ltd): "each tool taking up to six minutes to set" by hand with feeler gauges. With a TS27R or NC4 probe, each check took "less than 30 seconds" [F] ([Renishaw case brief](https://www.renishaw.com/resourcecentre/en/download/(108481208cdc4e11ad42ba167233b898))).
   - Measuring tools off the machine beforehand cut this from 5 min to under 1 min per tool for length-only tools [F] ([CTE 1996, written by a presetter vendor](https://ctemag.com/?p=95785)).
   - An Indian die shop, Vasantha Tool Crafts, reported 80% less time setting tool offsets after adding a Renishaw tool setter [S] ([Renishaw](https://www.renishaw.com/it/renishaw-workpiece-inspection-and-tool-setting-probes-help-vasantha-tool-crafts-increase-machine-utilisation-time-by-20--40393)).
3. **Checking the first cycle or part with the new cutter.** A quick dimension check is 2–5 min. A full first-part inspection, or waiting for a setter or inspector, is 10–15 min or more [A].

**Choice:**
- **Low, 3 min:** spare holder ready, probe measures the length, no check.
- **Typical, 10 min:** hand swap in the collet, hand measurement, quick check.
- **High, 25 min:** hand measurement, full first-part inspection, waiting for a setter.

---

## 5. What an unplanned breakage costs

### 5.1 Machine stopped after a breakage (`t_b`) [A]

No published figure was found. Typical steps:
- noticing the break and stopping the machine (immediate if someone is at the machine; much longer if one operator watches several machines);
- getting the broken stub out of the collet, or out of the part, 5–30 min;
- checking the holder and that the spindle still runs true, 5–15 min;
- fitting and measuring a new tool, which is `t_p`;
- restarting the program part-way through and re-finding the part's zero point, 5–20 min;
- inspecting the damaged part, 5–30 min.

**Choice: 15 / 45 / 180 min.** The high case covers a broken stub stuck in the part that needs EDM (spark erosion) to remove, or no setter being available.

### 5.2 The part (`V`, `p_s`) [A]

When a 10 mm end mill breaks in a cut, the part is usually gouged at the break, and the remaining stub may stay in the part. Whether the part can be saved depends on how much stock is left on that face.

A simple way to value the part at risk: **V = material + heat treatment + (machining hours already spent × R)**.
- India typical: about ₹600 of hardened 42CrMo4 + 2 h × ₹800 + ₹300 heat treatment + margin ≈ ₹3,000.
- High: nearly finished mould or die plates, ₹25,000 or more.
- Europe: the same hours at €80/h give about €250 typical and €2,500 high.

`p_s` (chance the part is scrapped) is 0.2 / 0.5 / 0.9. Otherwise the part is repaired for about 10% of `V`. The team should replace these with a real shop's numbers.

### 5.3 Damage to other things (`E_coll`) [A]

A 10 mm solid carbide cutter usually just snaps. Its cutting forces are small, so a breakage by itself rarely hurts the spindle (the motor-driven shaft that spins the tool). The real risk comes when the machine **keeps feeding** with a broken tool, and the holder or collet rubs or crashes into the part. No published chance or cost was found in this session. My figures:

| Item | Cost, India | Cost, Europe | Chance per breakage, low / typ / high |
|---|---|---|---|
| Collet damaged, needs replacing | ₹1,000 | €35 | 10% / 20% / 50% |
| Tool holder damaged (BT40 or SK40 taper holder) | ₹6,000 | €150 | 1% / 3% / 10% |
| Spindle repair or rebuild after a crash | ₹3 lakh (₹5 lakh in the high case) | €15,000 (€25,000 high) | 0.1% / 0.3% / 1% |
| **Average per breakage** | **₹460 / ₹1,280 / ₹6,100** | **€20 / €57 / €283** | |

The spindle term has the biggest single cost and the most uncertain chance. It is the first thing to ask a shop about.

### 5.4 Published figures on how much downtime and cost tools cause

| Claim | Source | How sure |
|---|---|---|
| "Up to 20%" of machine-tool downtime in production is caused by cutting-tool failure | Trinity College Dublin review of tool-condition monitoring ([TARA](https://www.tara.tcd.ie/bitstreams/2195963a-5d41-418e-8ff4-3717a1cba118/download)) | [S]. The page would not open. |
| "For modern machine tools, 20% of the downtime is ascribed to tool failure", citing Cai et al. | Drilling-monitoring paper, *Diagnostyka* 2012 ([link](https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-article-BAR0-0068-0052/c/httpwww_bg_utp_edu_plartdiagnostyka2012tsanakas.pdf)) | [S] |
| Tool failure causes **7–20%** of machine downtime, and tools plus tool changing are **3–12%** of total processing cost | Usually traced to Kurada & Bradley (1997), *Computers in Industry* 34(1):55–72, and repeated in many monitoring reviews | **Not verified this session.** This is from memory of how others cite it. Open the paper before quoting. |
| Tools wearing out plus tools breaking cause **40–45%** of downtime in turning, drilling and milling | HCL CAMWorks article in *Production Machining* ([link](https://www.productionmachining.com/articles/monitoring-improves-machine-up-time-and-shop-efficiency)) | [S]. Written by a software vendor. |
| The cutting tool is about **3%** of a typical machined part's cost, while labour and machine time are about **30%** each | Diamond Innovations, sponsored article in *Modern Machine Shop* ([link](https://mmsonline.com/articles/the-new-rules-of-cutting-tools----rule-4-focus-on-the-biggest-sources-of-expense)) | [S]. Written by a tool vendor. |
| Proper tool monitoring "is expected to reduce machining costs by up to 30%" (citing Liu et al. 2018). Their own simulation: condition-based replacement cut cost per good part by **3.5%** (when the tool can only be changed between parts) and **8.7%** (when it can be changed every minute), compared with replacing after a fixed time | Colantonio, Moroncini, Sénéchal, Dehombreux, Ducobu & Equeter (2025), *Int. J. Prognostics & Health Management* 16(4), [doi:10.36001/IJPHM.2025.v16i4.4269](https://doi.org/10.36001/IJPHM.2025.v16i4.4269) | [F]. I read the PDF. |
| A worn tool can mean "thousands in lost material or damage to a CNC machine tool". Tooling is "usually one of the smallest costs" | MSC Industrial, K. Hanson, Aug 2026 ([link](https://www.mscdirect.com/knowledge-center/articles/cost-of-cutting-tool-wear)) | [F]. Gives no exact figures. |

**Caution: the "3% of part cost" figure does not fit our case.** It describes whole parts made by many operations with long-lasting tools. In our setting one 10 mm cutter lasts only about 80 minutes in 40 HRC steel. So in India the cutter is about **75%** of the cost of each cycle: ₹52 of cutter-and-change cost against ₹18 of machine time, and in Europe about **50%**. That is why the keep-or-change choice matters so much here.

### 5.5 How often cutters break: what our data says

In the dataset, every cutter was run until it broke. Measured from `data/raw/metadata.xlsx` [M]:
- 13 usable cutters lasted **15–149 cycles**: mean 74, standard deviation 42.5. The spread relative to the mean (coefficient of variation) is about **0.57**. This mixes different depths of cut and holders.
- One more cutter broke in its very first cycle.
- One cycle of cutter 2 lasted 58–112 s (13 raw files) [M].

So a cutter lives for roughly 1–2 hours of cutting. The cutting speed was π × 10 mm × 3,200 rpm ≈ **100 m/min**, and the feed per tooth 640 ÷ (3,200 × 4) = **0.05 mm**, assuming 4 flutes.

For comparison, Colantonio et al. (2025) gave their simulated tool lives a Weibull spread with shape 7 [F], which has a coefficient of variation of about 0.17. Our cutters vary about three times more. That makes a fixed "change after N cycles" rule more costly, and condition monitoring more valuable. This is a point in our project's favour, worth stating.

---

## 6. What it costs to run slower

Running the spindle slower at the same feed per tooth slows the table feed by the same factor. So **cycle time grows in proportion to 1/speed**. Each cycle costs more machine time, but the cutter lasts longer.

**Taylor's tool-life equation [T]:** `v · T^n = C`, where `v` is cutting speed, `T` is tool life in minutes, and `C` and `n` are constants for the tool and material. Typical `n`: high-speed steel ≈ 0.125, **carbide ≈ 0.25**, ceramic ≈ 0.6 (Groover, *Fundamentals of Modern Manufacturing*, tool-life chapter). Kalpakjian & Schmid give carbide n ≈ 0.2–0.5.

If we cut at a fraction `s = v / v0` of the original speed, then for the same toolpath:
- cycle time: `t_c(s) = t_c0 / s`
- tool life in minutes: `T(s) = T0 · s^(−1/n)`
- **tool life in cycles: `L(s) = L0 · s^−(1/n − 1)`**. With n = 0.25, that is `L0 / s³`.

So in a simulator with a "slow down" action, each cycle at speed fraction `s` should use up `s^(1/n − 1)` cycles' worth of tool life.

**Worked example [A].** Cost per good cycle = machine time + (planned change cost ÷ cycles used per cutter). It assumes 60 cycles per cutter at full speed, the same share of tool life used at every speed, and the typical costs from §1.

| Speed (fraction of 100 m/min) | 1.0 | 0.9 | 0.8 | 0.7 |
|---|---|---|---|---|
| India, n = 0.25: ₹ per good cycle | 70.0 | 57.8 (−17%) | 48.9 (−30%) | 43.3 (−38%) |
| India, n = 0.15 / 0.4 | — | −31% / −8% | −47% / −15% | −54% / −20% |
| Europe, n = 0.25: € per good cycle | 3.58 | 3.29 (−8%) | 3.14 (−12%) | 3.15 (−12%) |
| Europe, n = 0.15 / 0.4 | — | −17% / −2% | −24% / −2% | −23% / 0% |

The classic "lowest cost per part" tool life (§7) gives the same message:
- India, typical: `T* = (1/n − 1)(t_p + C_t/R) = 3 × (10 + 3,000 ÷ 13.33) ≈ 705 min`. The cheapest speed is about (80/705)^0.25 ≈ **0.58 × 100 m/min**.
- Europe, typical: `T* ≈ 244 min`, so about **0.76 × 100 m/min**.

Where machine time is cheap and cutters are expensive, as in India, it pays to run slower than the dataset's speed. Three warnings:
1. Taylor's equation is fitted to gradual wear. It is less reliable for sudden breakage and for large slowdowns.
2. Carbide makers give a lower speed limit, below which the cutting edge chips or metal sticks to it ("built-up edge").
3. If the machine is the shop's bottleneck, each extra minute also loses the profit on the work it could have done. Then the rate to use is the selling rate, not the cost rate, and the "fastest output" tool life `T = (1/n − 1) · t_p ≈ 30 min` applies instead. That points towards running *faster*.

---

## 7. Published models for when to replace a tool

### 7.1 Cost per part with Taylor tool life (Gilbert 1950; Groover; Kalpakjian) [T]

Cost per part:

```
C_part = C_o · t_h  +  C_o · t_m  +  (C_o · t_t + C_t) · (t_m / T)
```

- `C_o`: machine + operator rate per minute
- `t_h`: part handling time
- `t_m`: cutting time per part
- `t_t`: tool change time
- `C_t`: cost per cutting edge. For a reground tool, `C_t = price / number of uses + regrind cost per regrind`.
- `t_m / T`: tools used per part

Setting the derivative with respect to speed to zero gives:

```
Lowest-cost tool life:   T_min-cost = (1/n − 1) · (t_t + C_t / C_o)
Lowest-cost speed:       v_min-cost = C / T_min-cost^n
Fastest-output tool life: T_max-prod = (1/n − 1) · t_t
```

References: F. W. Taylor (1907), "On the art of cutting metals", *Trans. ASME* 28. W. W. Gilbert (1950), "Economics of machining", in *Machining – Theory and Practice*, ASM. M. P. Groover, *Fundamentals of Modern Manufacturing* (Wiley), chapter on machining economics. S. Kalpakjian & S. R. Schmid, *Manufacturing Engineering and Technology*.

### 7.2 Replace at a fixed age (renewal-reward model; Barlow & Proschan 1965) [T]

This is the model for our "change after a fixed number of cycles" baseline. Replace at age `N` cycles, or at failure if that comes first. In discrete form, with `R(k)` the chance a cutter survives `k` cycles:

```
cost per good cycle (N) = [ C_p · R(N) + C_f · (1 − R(N)) + c_m · Σ_{k=0}^{N−1} R(k) ]
                          ─────────────────────────────────────────────────────────
                                      Σ_{k=1}^{N} R(k)        (expected good cycles)
```

Pick the `N` that minimises this. We can estimate `R(k)` from the 13 cutters' lives, using leave-one-cutter-out.

Reference: R. E. Barlow & F. Proschan (1965), *Mathematical Theory of Reliability*, Wiley.

### 7.3 A per-cycle "look one step ahead" rule (derived here from 7.2) [T]

Suppose that after each cycle the model gives `p`, the chance the cutter breaks during the next cycle. Let `g` be the long-run cost per good cycle under the policy. Continuing for one more cycle and then changing beats changing now when:

```
(1 − p) · g − c_m  >  p · (C_f − C_p)
⇔  p  <  a / (a + c_m + C_f − C_p),   where a = g − c_m
```

`a` is the cutter-related cost per good cycle. Start with `a ≈ C_p ÷ average cycles per cutter`, run the policy, recompute `g`, and repeat; this usually settles in a few rounds (Dinkelbach's method for ratio objectives).

When the chance of breaking only rises with age, this one-step rule is the optimal one. That is the "monotone stopping problem" result in S. M. Ross, *Introduction to Stochastic Dynamic Programming* (1983).

For typical costs and about 60 cycles per cutter: **change when `p` > about 1.5% in India and about 0.75% in Europe**.

Two lessons:
- What matters is the **extra** cost of a breakage, `C_f − C_p`, not the plain ratio.
- The change-now cost is not compared with `p · C_f`, as Rule 2 in `PROJECT_EXPLAINED.md` currently implies. It is compared with the value of one more good cycle. **Rule 2 should be updated to this form.**

### 7.4 Similar recent work

- Colantonio et al. (2025, IJPHM) [F] simulate a month of two-shift Ti6Al4V machining. They compare (1) fixed-time replacement, (2) monitoring that can change the tool only between parts, and (3) monitoring that can change it every minute. Their costs: tool €40, workpiece €8.20, electricity €0.15/kWh, tool life Weibull with shape 7 and mean 20 min. They **leave out machine-hour cost and treat tool changes as instant** (automatic tool changer). Results: €16.20, €15.64 and €14.80 per good part (−3.5% and −8.7%).
- Our model is more complete because it includes machine and operator time, the time to change a tool, and breakage downtime. This is worth saying in the report.
- Already cited in our proposal (`research/proposals/toollife-policy.md`): Jeang (1998, *EJOR*) on tool replacement with quality loss, and Errandonea et al. (2026, *Computers & Industrial Engineering*).

---

## 8. Recommended cost model for the simulator

### 8.1 What to charge

| Event | Charge |
|---|---|
| Every cycle run (including the one that breaks) | `c_m = R · t_c` |
| Planned change | `C_p = C_t + R · t_p − C_rg` |
| Breakage | `C_f = C_t + R · t_b + p_s · V + (1 − p_s) · 0.1 · V + E_coll` |
| Optional: run at speed fraction `s` | cycle cost `R · t_c / s`; tool life used `s^(1/n − 1)` cycles' worth |
| **Score** | **total cost ÷ good cycles** (also report breakages per 100 cutters) |

### 8.2 Default values

Use the "Typical" columns of §1.1 (India) and §1.2 (Europe).
- India: `C_p` = ₹3,133, `C_f` = ₹6,530, ratio 2.1, `c_m` = ₹17.7 per cycle (`k` = 0.006).
- Europe: `C_p` = €108, `C_f` = €349, ratio 3.2, `c_m` = €1.77 per cycle (`k` = 0.016).

### 8.3 Sensitivity grid

See §1.4: `r` ∈ {1.5, 2, 3, 5, 10, 20, 30} × `k` ∈ {0.006, 0.016} = 14 settings. Add the Taylor exponent `n` ∈ {0.15, 0.25, 0.4} only if there is a slow-down action. Also run the four corner mixes from §1.3 in real money.

A check from the formula in §7.3: in units where `C_p = 1`, the threshold `p*` hardly moves between `k` = 0.006 and 0.016 (for example 1.63% vs 1.61% at r = 2). **So `r` is the only setting that really changes the keep/change decision.** `k` mainly changes how big a percentage saving looks.

---

## 9. What to ask a real shop

These would turn our [A] assumptions into facts:

1. What a 10 mm carbide end mill for 40 HRC steel costs them, which brand they buy, and whether they regrind it (how many times, and at what cost).
2. Their machine-hour rate for a 3-axis VMC, and whether it includes the operator.
3. How long a cutter change takes, from stop to cutting again, and whether they use a length-measuring probe or measure off the machine.
4. Their last few breakages: time lost, whether the part was scrapped or repaired, and its value.
5. Whether they have ever had a holder or spindle damaged after a cutter broke, and what the repair cost.
6. Whether one operator watches one machine or several. This changes how long a breakage goes unnoticed.

---

## 10. Sources

**Tool prices.**
- [Moglix: YG-1 EM595100](https://www.moglix.com/yg-1-10mm-4-flute-carbide-short-end-mill-em595100/mp/msng9vnwen2dkp) [F]
- [Moglix: Totem F188](https://www.moglix.com/totem-fbk0500887-4-flute-extra-long-length-ball-nose-end-mill-cutting-dia-10-mm/mp/msn2km1d4wmx9v) [F]
- [Moglix: Totem F122](https://www.moglix.com/totem-9x35x89x10mm-4-flute-uncoated-carbide-end-mill-fbk0500351/mp/msn4k6zwnl88kq) [F]
- [Jaibros (Tabikut)](https://www.jaibros.com/search?q=10mm+carbide+end+mill+4+flute) [F]
- [IndiaMART, Bengaluru carbide end mills](https://m.indiamart.com/city/bengaluru/carbide-end-mills.html) [F]
- [Industrybuying: Kennametal 4CH1000MR022A](https://www.industrybuying.com/carbide-end-mill-kennametal-TOO.CAR.14334902) [F]
- [L&T-SuFin: Totem Proton Plus](https://lntsufin.com/product/totem-solid-carbide-end-mill-10-mm-75-mm/16832-1961) [F]
- [Hoffmann: GARANT 203036 10](https://www.hoffmann-group.com/DE/de/hom/p/203036-10) [F]
- [Hoffmann: HOLEX 203520 10](https://hoffmann-group.com/p/203520-10) [F]
- Rubix UK, Sandvik Plura: [2P340](https://uk.rubix.com/en/g1298047516/p-G1298047516), [2S342](https://uk.rubix.com/en/g1298047681/p-G1298047681), [1P240](https://uk.rubix.com/en/g1298046526/p-G1298046526), [R216.24](https://uk.rubix.com/en/g1298032516/p-G1298032516) [S]
- [Cromwell: Sandvik Plura](https://www.cromwell.co.uk/shop/cutting-tools/end-mills-regular/coromill-plura-end-mill-regular-straight-shank-10mm-alcrn-carbide/p/SNK1610161R) [S]
- [Cromwell: Merlin](https://cromwell.co.uk/shop/cutting-tools/end-mills-regular/414-10514-10-00mm-sol-carb-tialn-4flstd-end-mill/p/MRN1615032H) [S]
- Mars Supply, Seco Jabro: [SEC03029963](https://marssupply.com/Product/SEC03029963), [SEC02810479](https://marssupply.com/Product/SEC02810479) [S]
- [Penn Tool Co.](https://www.penntoolco.com/58458373) [S]
- [Zoro: WIDIA](https://www.zoro.com/widia-sq-end-mill-single-end-carb-1000mm-40031000w022s/i/G3805320/) [S]

**Machine rates and wages.**
- [NIT Calicut CRF: VMC](https://randc.nitc.ac.in/crf/med/36%20-%20cnc%20vmc%201.htm) [F]
- [MSME Tool Room rate list (Scribd)](https://www.scribd.com/document/767640118/Machine-Hour-Rates) [S]
- IndiaMART VMC job-work listings, linked in §3.1 [S]
- [IIT Kanpur workshop job card](https://www.iitk.ac.in/celp/data/downloadables/Workshop-Job-Card-16-05-2025.docx) [S]
- [WageIndicator, Maharashtra engineering](https://wageindicator.org/en-in/ai/work-in-india/minimum-wage/18640-maharashtra/18790-engineering-industry/) [S]
- [Jooble](https://in.jooble.org/salary/vmc-operator) [S]
- [AmbitionBox](https://www.ambitionbox.com/salaries/bharat-fritz-werner-salaries/vmc-operator) [S]
- [Eurostat 2024 labour costs](https://ec.europa.eu/eurostat/web/products-eurostat-news/w/ddn-20250328-1) [F]
- [Destatis via vergabeblog](https://vergabeblog.de/2025-05-09/lohnkosten-in-deutschland-arbeitsstunde-kostet-durchschnittlich-4340-euro/) [S]
- [clean-invoice](https://www.clean-invoice.com/feinwerkmechanik/kosten-und-kalkulation-feinwerkmechanik) [S]
- [welt-der-bwl](https://www.welt-der-bwl.de/Maschinenstundensatz) [S]
- [whk-controlling](https://www.whk-controlling.de/wissen/maschinenstundensatz-rechner) [S]
- [ECB reference rates](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml) [F]

**Tool change time.**
- [Cutting Tool Engineering 2017](https://ctemag.com/articles/save-time-setting-tools-offline-presetter/) [F]
- [Renishaw case brief (Quality Engineered Products)](https://www.renishaw.com/resourcecentre/en/download/(108481208cdc4e11ad42ba167233b898)) [F]
- [Cutting Tool Engineering 1996](https://ctemag.com/?p=95785) [F]
- [Renishaw: Vasantha Tool Crafts](https://www.renishaw.com/it/renishaw-workpiece-inspection-and-tool-setting-probes-help-vasantha-tool-crafts-increase-machine-utilisation-time-by-20--40393) [S]

**Downtime and cost shares.**
- Colantonio et al. 2025, [doi:10.36001/IJPHM.2025.v16i4.4269](https://doi.org/10.36001/IJPHM.2025.v16i4.4269) [F]
- [MSC 2026](https://www.mscdirect.com/knowledge-center/articles/cost-of-cutting-tool-wear) [F]
- [TCD review](https://www.tara.tcd.ie/bitstreams/2195963a-5d41-418e-8ff4-3717a1cba118/download) [S]
- [Diagnostyka 2012](https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-article-BAR0-0068-0052/c/httpwww_bg_utp_edu_plartdiagnostyka2012tsanakas.pdf) [S]
- [Production Machining / CAMWorks](https://www.productionmachining.com/articles/monitoring-improves-machine-up-time-and-shop-efficiency) [S]
- [MMS / Diamond Innovations](https://mmsonline.com/articles/the-new-rules-of-cutting-tools----rule-4-focus-on-the-biggest-sources-of-expense) [S]
- Kurada & Bradley 1997 (not verified)

**Models.** Taylor 1907; Gilbert 1950; Groover; Kalpakjian & Schmid; Barlow & Proschan 1965; Ross 1983 [T].

**Dataset.** Piecuch & Żabiński 2025, *Scientific Data*, [s41597-025-04923-y](https://www.nature.com/articles/s41597-025-04923-y). Cycle durations and cutter lives measured from our local copy [M].
