# Review 2 video script: final deck

**Length:** about 7½ minutes (1015 spoken words at about 135 words a minute, plus slide changes).
**Deck:** 10 main slides and 3 backup slides (ToolLife Policy Review 2 Final). The same words are in each slide's speaker notes.
**Speakers:** 5. Names are in each slide's footer; nobody introduces themselves.
**Rule for every speaker:** say the numbers exactly as written. Every number is a measured result from our code, on cutters the model never saw. Errors are in cycles; costs are rupees per good cycle.

---

## Yadu: the problem in one slide, and the data (about 85 seconds)

**Slide 1: ToolLife Policy**

> This is ToolLife Policy, our Review 2. Review 1 set out the problem and the data. Today: how we prepared the data, the model we chose, how we tested it, and the working system.

**Slide 2: A broken cutter costs twice a planned change**

> A quick reminder. A milling cutter wears a little on every cut, until it snaps; these fourteen did. A planned change costs about three thousand one hundred rupees, a breakage about six and a half thousand, twice as much. So on every cycle the question is: keep it, or change it now? Our system reads the sensors, estimates the cycles left as a low, middle and high value, weighs that against the two costs, and decides. Everything we promised at Review 1 is built.

**Slide 3: Fourteen cutters, each run until it broke**

> The data is from Piecuch and Żabiński, 2025. Fourteen cutters run until they broke: nine hundred and sixty-eight cycles, eight vibration sensors, twelve motor currents, a hundred and twelve gigabytes. The lives range from fifteen cycles to a hundred and fifty. Cutter eleven, in grey, broke on its first cycle, so we leave it out. That leaves thirteen lives, and that is our real sample size, because each life gives exactly one breaking point. Over to Bhuwan.

## Bhuwan: data pre-processing and feature engineering (about 90 seconds)

**Slide 4: From a raw recording to one clean row per cycle**

> Each cycle arrives as raw sensor counts. First, we convert them to amps and metres per second squared. Second, we keep only the cutting: the spindle current shows when the cutter is in the steel, here twenty-seven seconds out of a hundred and fifteen. Third, we take each sensor's spectrum, to see how loud the vibration is and at what pitch. Fourth, and most important, every number is divided by the same cutter's value in its first three clean cycles, because what matters is change since new. And we only ever use cycles already seen, never the future.

**Slide 5: 22 physics numbers per cycle**

> From each cycle we compute twenty-two physics numbers in four families. Load: how hard the motors work, since a blunt cutter rubs and the steel pushes back. Vibration level and pitch. Rhythms: the four teeth make a beat, and a chipped tooth adds a once-per-turn beat. And impacts: sharp spikes. On the right, the table current and the high-pitched vibration both climb towards the end of life. And it is wear, not position in the block: with position removed, table current still tracks life at zero point nine four. With the settings, the cycle count and a first-ring flag, that is twenty-nine inputs per cycle. Amal.

## Amal: model selection and architecture (about 55 seconds)

**Slide 6: A causal TCN that looks back about 60 cycles**

> We tried five kinds of model. LightGBM looks at one cycle at a time, with no memory, so it became our yardstick. A one-D CNN on raw vibration could not learn from only thirteen lives. An autoencoder health score did worse than our physics numbers. LSTM, GRU and Transformer were no more accurate. We chose a TCN, a temporal convolutional network. It is causal: it uses only the past, never the future, just like a real machine. Four blocks with gaps of one, two, four and eight let it look back about sixty cycles with only a hundred and nine thousand weights. And it outputs the chance of breaking on each of the next hundred and sixty cycles: the risk curve our cost rule needs. Rafiq.

## Rafiq: training and evaluation (about 100 seconds)

**Slide 7: Every test cutter is one the model never saw**

> To test honestly with thirteen cutters, we hide one whole cutter, train on the other twelve, and test on it, thirteen times over. Every cutter is tested by a model that never saw it. Why not seventy-thirty? A random split of cycles puts the same cutter on both sides: the error drops to six point four, and that is a leak, not skill. Seventy-thirty by whole cutters is honest, but it swings from nine to thirty-eight depending on which four cutters land in the test. Training uses a survival loss, the AdamW optimiser, four hundred passes, and five random starts averaged.

**Slide 8: Sensors help; the network type barely matters**

> All results are on unseen cutters, in cycles of error. A TCN that knows only the cutter's age is off by twenty-eight. With our physics features, twenty-two, and sixteen in the last fifth of life, when it matters most. That six-cycle gain is real. Settings alone get to twenty-six and are hard to beat on ordinary cutters. But on cutter ten, the only one on a long holder, they were off by a hundred and twenty-three cycles; the TCN, seeing it shake, by twenty-eight. Between models, it is a tie: Transformer, LSTM, LightGBM and our TCN all land between twenty-one and twenty-two, less than the swing from re-running one model. Thirty-three models, over thirteen hundred networks, one test. Aaditya.

## Aaditya: model implementation: the working system and its decisions (about 120 seconds)

**Slide 9: From a raw recording to keep-or-change, every cycle**

> This is the whole system, and all of it runs. A raw recording comes in. The convert step turns counts into units and keeps only the cutting. The feature step computes the twenty-two physics numbers. The TCN, in PyTorch, reads the recent history and outputs a risk curve. The decision step weighs that curve against the two costs: keep, or change. Every model was trained thirteen folds times five random starts; over thirteen hundred networks, on a laptop and a cloud machine. On the right is cutter one-oh-three, never seen in training. Black is the truth, blue is our prediction. Early on it is too hopeful: almost a hundred cycles, against sixty. As wear builds it closes in, meeting the truth near cycle forty. At forty-seven the rule changes the cutter. It would have broken at sixty.

**Slide 10: Ten breakages down to five**

> Now the decision, which is what a shop pays for. We replay all thirteen cutters cycle by cycle, each rule tuned on the other twelve, at Indian shop costs. Run to failure: all thirteen break. Change every N cycles, the usual practice: ten still break. Our rule with the TCN: five break, and the cost per good cycle falls from ninety-nine rupees to ninety-three. That six percent is promising, not proven: with thirteen cutters, its range runs from minus nine to plus twenty-one percent. What does hold up is the sensors: the same rule on a TCN without them costs a hundred and eleven rupees. Perfect knowledge would cost fifty-nine, forty percent less, and our error is still falling as cutters are added. So the next step is more run-to-failure data. Thank you.

---

## Backup slides: only if a reviewer asks

**What the model says about cutter 103** (Aaditya)

> These are the risk curves the decision rule actually reads, for cutter 103, which the model never saw. Each bar is the chance the cutter breaks on that cycle from now. After cycle six, there is almost no risk inside the next fifty-four cycles: calm, and correct. After cycle thirty-one, the risk peaks about thirty-five cycles ahead; it really broke twenty-nine later, so it is a few cycles late. After cycle fifty-one, the risk sits in the next one to three cycles; it really broke nine later, so near the end the model is cautious, which is the safe direction. The two commands rebuild every prediction and every decision from the processed data.

**Chosen first, then tested against 32 rivals** (Amal or Aaditya)

> We fixed the TCN as the main model before running any rival, so it cannot be the luckiest of thirty-three. It was chosen for the job: it is causal, it is small enough for thirteen lives, and it outputs a risk for each future cycle, which the cost rule needs. It is not the top score. The same TCN on the dataset's own hundred and twenty summaries scored nineteen point two, but its edge over our physics features has a ninety-five percent interval of minus one point five to plus seven point three cycles, so it could be luck. It does hint that our hand-picked features leave something out, and we report that rather than switch. Raw-signal learning, the one-D CNN at thirty-one point seven, failed because thirteen lives are too few.

**Why our 13 lives are the main data** (Yadu or Aaditya)

> We did look at other datasets: NASA, Hannover, MSTW, an Indian VMC 650 shop, PHM 2010 and MATWI. None of them can be the main data, because in none of them does a life end in a breakage. They stop at a wear limit, or when an operator decides, or not at all. Our question is when a cutter breaks, so only our thirteen lives answer it directly. That is the real issue: each life gives exactly one breaking point, so more cycles do not help, only more cutters. The other data is still useful for learning how signals change with wear. A model trained only on the other machines estimated life used on our cutters with an error of zero point one eight two, against zero point one seven two for a model trained on ours; that difference is within the noise. Pretraining our TCN on seventy-three other lives gave twenty-two point zero and fourteen point five, no clear gain over our model.

## Notes for whoever edits the video

- Keep each speaker's slide on screen while they talk; the deck uses only fades.
- If a speaker runs long, cut a sentence before cutting any number.
- The broken-cutter photo and the data credit are from Piecuch & Żabiński (2025), CC BY 4.0.
- Charts are drawn by `scripts/28_review2_charts.py` into `results/figures/review2/`.
