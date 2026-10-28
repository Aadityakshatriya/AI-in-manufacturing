# ToolLife Policy — the film: production brief for scene builders

A ~3.8-minute cinematic explainer in the style of 3Blue1Brown, made with Manim Community 0.22 (Python).
It tells our IIT course project's story: a CNC milling cutter wears and snaps → why (physics) → what the
machine's sensors feel → how that becomes numbers and bits → the two neural networks (CNN autoencoder,
TCN) → how we tested honestly (30 other models, learning curve) → the keep-or-change decision. A female
narrator (Sarvam Bulbul TTS, voice "tanya") speaks over it; her audio already exists per scene.

**Bar:** this should feel like a 3Blue1Brown video: near-black ground, elegant thin strokes, smooth
transforms where one idea *morphs* into the next, a slowly moving camera, purposeful colour, very few
on-screen words (labels of 1–4 words, a few key numbers). The narration carries the story; the picture
shows it. Never put the narration on screen as sentences. Motion should be continuous: something is
always gently alive (rotating, drifting, pulsing), but never busy. Go for "wow", within that taste.

## Where things are

- Project root: `/Users/aaditya/Documents/ChatGPT/AI in Manufacturing/video/`
- `style.py` — shared palette, fonts, helpers and the `TLScene` base class. Read it first; use it.
- `cues.json` — per scene: narration duration and each phrase's start/end time (seconds from narration start).
- `narration.json` — the narration text per scene.
- `data.json` — real numbers from the project (see "Data" below). Use real data wherever a plot appears.
- `audio/<sid>.wav` — the narration audio, to listen to timing if useful (do not put audio in renders).
- Your scene files go in `scenes/<sid>.py` (e.g. `scenes/s03_wear.py`), one `TLScene` subclass each.
- Python env: `source .venv/bin/activate` inside `video/` (has manim, numpy, and `ffmpeg` on PATH;
  do NOT use /opt/homebrew/bin/ffmpeg, it is broken). There is no `ffprobe`; use `ffmpeg -i file 2>&1 | grep Duration`.

## Hard technical rules

1. **No LaTeX on this machine.** `MathTex`, `Tex`, `DecimalNumber`, `Integer`, `Variable`, `BarChart`,
   `Brace.get_text/BraceLabel`, `NumberLine(include_numbers=True)`, `Axes.add_coordinates`,
   `axes.get_axis_labels` all need LaTeX and will crash. Use `T(...)`/`N(...)` from style.py (Pango `Text`)
   for every label and number. For a counting number use a `ValueTracker` + `always_redraw(lambda: N(...))`.
   `Axes(...)` itself is fine if you don't ask it for numbers.
2. Each scene class sets `SID = "<sid>"` and subclasses `TLScene` (a `MovingCameraScene`; zoom with
   `self.camera.frame`). Begin with `import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))`
   then `from style import *`.
3. **Exact length.** A scene lasts `self.total` = 0.5 s lead + narration + 0.9 s tail. Narration phrase i
   starts at `self.cue(i)` and ends at `self.cue_end(i)` (scene clock). Time visual beats to the phrases with
   `self.wait_until(t)` and `run_time`s. The last line of `construct` must be `self.finish()` (fades out and pads
   to the exact length). Start each scene from black (fade/draw things in); the film is hard cuts between scenes.
4. Render previews fast: `manim -ql --media_dir media scenes/<sid>.py <ClassName>` (480p15).
   Final render: `manim -qh --media_dir media scenes/<sid>.py <ClassName>` (1080p60) → `media/videos/<sid>/1080p60/<ClassName>.mp4`.
   Keep it renderable in reasonable time (a 20 s scene should render at 1080p60 in under ~10 minutes): prefer
   updaters over thousands of separate animations; cap particle counts (a few hundred dots max).
5. **Verify your own work by looking at it.** After the final render, extract stills at the key beats with
   `ffmpeg -loglevel error -y -ss <t> -i <mp4> -frames:v 1 /tmp/..png` (use your own scratch folder) and
   open them (Read tool on the PNG). Check: nothing overlaps or runs off-frame, text is legible, the beat
   matches the narration at that time, colours follow the palette. Fix and re-render until it is right.
   Check the duration equals `self.total` (±1 frame).
6. Only create/modify your own `scenes/<sid>.py` files (and scratch files). Don't edit style.py, cues.json,
   data.json or other scenes; if you need a shared helper, put it in your own file.
7. The Mac is shared: render one scene at a time.

## Data (data.json)

- `cutters`: list of {tool, life (cycles incl. the breaking one), rdoc (sideways bite mm: 8 = wide, 4.5 = narrow),
  holder (mm: 80 normal, 160 long), hrc (steel hardness)}. Tool 11 broke on cycle 1 (life 1); 13 others are "usable".
- `table_current_rel`, `once_per_turn_rel`, `health_rel`: per tool (string key) a list of [fraction of life used, value
  relative to that cutter's own first cycles]. Table current rises to 1.3–2.7× by the last 10% of life in all 13.
  Cutter 10 (long holder) behaves differently (shook from the start; its health score stays flat).
- `vibration`: real table-sensor vibration of cutter 8, 1,200 samples at 25 kHz (48 ms ≈ 2.6 turns), `new` (cycle 4) and `worn` (cycle 115 of 116).
- `spectrum`: `freq_hz` (0–1100 Hz), magnitudes `new` and `worn` for the same windows; `tooth_hz` 213.3 (4 teeth × 53.3 turns/s), `turn_hz` 53.3.
- `five_channels_new`: 5 sensors × 256 values (a 4,096-sample window, every 16th) for a heat-map of one cut.
- `tcn_cutter103`: real TCN output for hidden cutter 103 (life 60): per cycle `true_rul` and `pred_q50` (predicted cycles left), and
  `hazard_at` {cycle: 60 probabilities = chance of breaking on each of the next 60 cycles, given survival until then}.
- `zoo`: 31 models' average error in cycles (whole_life, last20) with `group`; ours is "TCN: physics features" (21.9).
  The one-random-start spread of our TCN is 21.7–24.1 ("the noise"). Best: "Zoo: TCN on the 120 summaries" 19.2.
- `learning_curve`: n_train 4/6/9/12 → whole_life_mean 34.8/34.4/29.3/21.8 (still falling).
- `decisions`: costs (planned change ₹3,133, breakage ₹6,530); `per_cutter` rows for policy "fixed" (change every N cycles),
  "dp" (our rule) and "oracle": tool, L (good cycles), good (cycles used before changing), broke (True = it broke).
  Every N: 10 of 13 broke; our rule: 5 of 13 broke.
- `facts`: teeth 4, 3,200 rpm, 53.3 turns/s, 213 hits/s, 25 kHz, window 4,096, AE: 5 sensors, 3,994,341 parameters,
  bottleneck 64; TCN: 109,447 parameters, dilations 1/2/4/8, sees ~61 cycles back, predicts 60 cycles ahead.

## The film, scene by scene (all scenes, so you know what comes before and after yours)

Times below are narration-relative; add 0.5 s (use `self.cue(i)`). Narration text is in narration.json.

**s01_cold_open (13.2 s)** — Black. A 4-flute end mill seen end-on (`end_mill()` in style.py, or your own better one)
spinning fast against the edge of a steel block (a hatched/gradient slab). Every tooth passing the contact point throws
a spark (short-lived yellow/orange particles) — make the 213 hits/s feel violent (motion blur trails, a faint shockwave ring).
A tiny counter "213 / s". At "Each hit steals a little of its edge" (7.0): a slow push-in to one tooth tip; a flake detaches,
the bright edge dims/rounds. At "And one day, without any warning" (9.85): time slows (rotation decelerates, sparks hang),
a hairline crack creeps across a tooth (DANGER red). At "it snaps" (12.2): the cutter shatters — fragments fly outward
with rotation, a white flash, then darkness by the end.

**s02_title (14.5 s)** — From darkness the title "ToolLife Policy" builds (large, light weight, letter-spaced; a thin line
draws under it). At "The story of teaching a machine to feel that moment coming" (2.0): title lifts up and shrinks.
At "From steel, to signals, to ones and zeros, and back to one simple decision" (5.7–11.8): a chain of four glyphs appears
left→right, each on its word: a steel block with a cutter → a waveform → "0110" bits → a fork. Thin arrows/flow lines
connect them; a travelling pulse runs along the chain. At "keep cutting, or change the tool" (12.0): the fork splits into
two options "keep" (GOOD) and "change" (WARN), each lighting on its word.

**s03_wear (21.7 s)** — Macro side view of ONE tooth (a sharp wedge: rake face, flank face) moving through steel, a chip
curling off cleanly (2.2 "fresh edge slices cleanly"). At 4.7 ("every hit rubs the face beneath it a little flatter"):
hit counter racing; a flat **wear land** grows on the flank (highlight HEAT), the tip rounds; the chip gets ragged; at
"starts pushing" the steel surface is ploughed/smeared rather than cut. Then the runaway loop (12.4–18.4): three nodes on a
circle — "force" (12.4) → "heat" (14.3) → "wear" (16.6) — each lights on its word, curved arrows between, a glowing
particle orbiting the loop faster and faster, the colour heating from orange to red. At "ends in fracture" (~20.5) the
tooth cracks and a chunk breaks away.

**s04_settings (21.3 s)** — "how hard we push it" (0–4.2): the cutter top-view in steel, the engaged arc of the cut shown.
"A wider bite puts more teeth into the steel at once" (4.4): engagement arc widens from narrow (4.5 mm of the 10 mm) to wide
(8 mm); the teeth inside the steel light up (count them). "A longer holder turns the cutter into a diving board" (7.9): side
view, the cutter in its holder sticking out of the spindle like a cantilever; a force arrow bends it (deflection grows with
length cubed: show δ for L, then 2L bends ~8×; label "δ ∝ L³" in plain text). "until it starts to shake on its own" (~14):
the long one starts to oscillate with growing amplitude (chatter), blur trail. "Our cutters lived anywhere from fifteen to a
hundred and fifty cycles" (17.2): morph into a horizontal bar chart of the 13 cutters' real lives (sorted), bars colour-coded by
setting (wide bite HEAT, narrow SIGNAL, long holder DANGER); labels "15" and "150" at the extremes.

**s05_signals (22.6 s)** — "We cannot see the edge" (0): the cutter hidden in a cloud/fog of chips and coolant (dim).
"But the machine can feel it" (1.6): a schematic machine — spindle motor, table motor, sensor dots — with little meter needles
waking up. "The motor that drives the table works harder…" (3.9): a plot of table current (× its value when new) vs fraction
of life, the 12 normal cutters' real lines drawn left→right (thin SIGNAL), rising at the end; "near the end, up to 2.7 times"
(8.8): highlight the top line and label "×2.7". "And the vibration sensors, listening twenty-five thousand times a second" (13.6):
the real vibration waveform (new) streams across; then "hear a new beat" → morph to the spectrum: tooth peaks at 213 Hz
multiples; switch new→worn and a peak at 53 Hz (once per turn) rises (19.6 "Once per turn" — WARN highlight with a pulse);
20.2 "The sound of a chipped tooth": a small four-tooth icon with one chipped tooth beating in time.

**s06_bits (17.0 s)** — "To a computer, that sound is only numbers" (0): the waveform from s05 (real `vibration.new`, ~150
samples) zooms in. "Sample the wave" (3.2): vertical sample stems drop onto the curve, dots at the samples; "every instant becomes
a number" — numbers (e.g. "0.42", MONO, DATA_C) pop above the dots, then the curve fades and only numbers remain. "Every number
becomes bits" (6.8): each number flips into 8-bit binary that cascades/streams. "One cut becomes five sensors, times four
thousand and ninety-six readings" (8.8): bits rush into a 5-row heat-map strip (real `five_channels_new`), label "5 × 4,096".
"One cutter's life becomes millions of them" (14.1): the strip duplicates into a deep stack receding into space (one per
cycle), a counter racing to "2.4 million" (5 × 4,096 × 116 cycles of cutter 8).

**s07_autoencoder (20.6 s)** — "Our first network is an autoencoder" (0): an hourglass network draws itself: wide input column of
nodes → narrowing layers → a glowing bottleneck of 64 → widening → output column (layered nodes with thin connections, 3b1b
neural-net look). "squeezes twenty thousand numbers through a bottleneck of just sixty-four, then tries to rebuild the original"
(3.3): a healthy waveform (SIGNAL) flows in on the left, compresses into the bottleneck (labels "20,480" and "64"), and is
rebuilt on the right, overlaid on the original — they match. "We trained it only on healthy cutting" (8.3): label "healthy only"
with a GOOD tick. "So when a worn tool sounds different, the rebuild fails" (13.5): feed the real worn waveform (HEAT); the rebuilt
curve no longer matches; the gap is filled DANGER. "the size of that failure becomes a health score" (16.0): the red gap area
collapses into a single number/bar, which then becomes a point on a rising curve: real `health_rel` lines of several cutters vs
life (log-scale feel), rising to several times their start.

**s08_tcn (20.5 s)** — "reads the cutter's history like a sentence" (0): a row of cycle "tokens" (small rounded squares, each
holding a tiny column of feature dots) slides in from the left like words in a sentence, newest on the right.
"A temporal convolutional network" (4.2): above them, layers of nodes. "Each layer looks twice as far into the past" (6.5) /
"one, two, four, eight cycles back" (9.6): the dilated causal connections draw layer by layer, each lighting on its number word
(1, 2, 4, 8), forming the receptive-field cone of the newest output (it reaches ~61 cycles back). "Never into the future" (11.1):
the tokens to the right of "now" are greyed behind a vertical barrier; a connection tries to reach them and is blocked.
"After every cycle, it draws a risk curve" (13.9): the top node emits a bar chart over the next 60 cycles (real `hazard_at` for
cutter 103); "the chance of breaking on each cycle still to come" (17.2): step the cycle forward and the curve morphs (cycle 6 →
31 → 51), its mass sliding closer to "now", danger rising.

**s09_honesty (25.5 s)** — "Then we tried to fool ourselves, and caught it" (0): a small magnifying-glass sweep over a "leak"
(a thin line from test into train) that gets cut. "We hid one whole cutter at a time…" (2.9): 13 cutter dots in a ring; one is
pulled out and veiled ("hidden"), the other 12 flow into a model box, the box guesses the hidden one; repeat quickly round the
ring. "We raced our network against thirty others" (12.1) / "trees, recurrent nets, transformers, convolutions on raw sound"
(14.0): a bar race of the 31 real models' whole-life errors (from `zoo`, sorted, shorter is better), ours highlighted SIGNAL,
the family name flashing on its word. "The good ones finished within the noise of each other" (17.1): a translucent band at
21.7–24.1 sweeps over; the cluster of good models inside it glows. "With thirteen cutters, the limit is not the model" (20.2):
morph into the learning curve (4/6/9/12 cutters → 34.8/34.4/29.3/21.8), still falling. "It is the data" (24.3): a dashed arrow
continues the descent beyond 12, labelled "more cutters" (no number).

**s10_decision (19.2 s)** — "And then, the decision" (0): a balance scale draws. "weigh the chance of breaking, times the cost of
a breakage, against the cost of changing the tool right now" (1.9): left pan "risk × ₹6,530", right pan "₹3,133"; as cycles tick
(counter), the risk grows and the left pan sinks. "When the risk outweighs the cost, change it" (10.4): the beam tips past level,
a "change" flash (WARN). "Replayed on thirteen real cutters, that rule let five break, instead of ten" (13.6): 13 horizontal life
lines (real `decisions.per_cutter`), two passes: "every N" — red ✕ where it broke (10); then "our rule" — green markers where it
changed in time, red where it broke (5); big counters "10" → "5".

**s11_close (10.9 s)** — "Steel, to signals, to numbers, to a choice" (0): a fast reverse montage of the film's motifs, each on its
word (spinning cutter, waveform, bits, fork). "The tool will always break" (4.1): the cutter spins calmly; a faint crack glints.
"The only question is whether you see it coming" (6.2): a risk curve wraps around it like a halo/radar sweep. "ToolLife Policy"
(9.4): title, and underneath in small DIM text "Bhuwan · Yadu · Amal · Aaditya · Rafiq — AI in Manufacturing".

## What to report back

For each of your scenes: the final 1080p60 mp4 path, its exact duration vs `self.total`, the class name, and 2–3 stills (paths)
you checked. Mention anything you could not do as briefed.
