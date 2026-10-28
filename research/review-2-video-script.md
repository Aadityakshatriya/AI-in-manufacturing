# Review 2 video script: final deck

**Length:** about 7½ minutes (1007 spoken words at about 135 words a minute, plus slide changes).
**Deck:** 10 main slides and 3 backup slides (ToolLife Policy Review 2 Final). The same words are in each slide's speaker notes.
**Speakers:** 5. Nobody introduces themselves; each speaker hands over by name.
**Rule for every speaker:** say the numbers exactly as written. Every number is a measured result from our code, on cutters the model never saw. Errors are in cycles; costs are rupees per good cycle.

---

## Yadu: the problem in one slide, and the data (about 85 seconds)

**Slide 1: ToolLife Policy**

> This is ToolLife Policy, our Review 2. Review 1 set out the problem and the data. Today: how we prepared the data, the model we chose, how we tested it, and the working system.

**Slide 2: A breakage costs ₹6,530; a planned change ₹3,133**

> A quick reminder of the problem. A milling cutter wears a little on every cut, until it snaps; these fourteen did. A breakage costs about six and a half thousand rupees, twice a planned change. So on every cycle our system reads the sensors, the TCN turns them into a risk curve, and a cost rule decides: keep cutting and check again next cycle, or change the cutter now. Everything we promised at Review 1 is built.

**Slide 3: Fourteen cutters, each run until it broke**

> The data is from Piecuch and Żabiński, 2025: one Haas milling machine, and fourteen cutters run until they broke. Nine hundred and sixty-eight cycles, eight vibration sensors, twelve motor currents, a hundred and twelve gigabytes. The lives range from fifteen cycles to a hundred and fifty. Cutter eleven, in grey, broke on its first cycle, so we leave it out. Thirteen lives is our real sample size, because each life gives exactly one breaking point. Over to Bhuwan.

## Bhuwan: data pre-processing and feature engineering (about 95 seconds)

**Slide 4: From a raw recording to one row per cycle**

> Each cycle arrives as a raw recording, about two minutes long. We keep only the actual cutting: the spindle current shows when the cutter is in the steel, here twenty-seven seconds out of a hundred and fifteen. We take each sensor's spectrum; the blue lines are the tooth hits, two hundred and thirteen a second. From that we compute twenty-two physics numbers, and divide each by the same cutter's first three clean cycles, because what matters is change since new. We only ever use cycles already seen, never the future. The result is one row per cycle; darker means more change.

**Slide 5: 22 physics numbers, plus 7 for context**

> The twenty-two numbers come in four families. Load: how hard the motors work, since a blunt cutter rubs and the steel pushes back. Vibration: how loud, and how high-pitched. Rhythms: the beat of the four teeth, and the once-per-turn beat a chipped tooth adds. And impacts: sharp spikes. On the right are two of them over every cutter's life, and both climb towards the end. We checked that this is wear, not the cutter's position in the block: with position removed, table current still tracks life at zero point nine four. With five settings, the cycle count and a first-ring flag, the model gets twenty-nine inputs per cycle. Amal.

## Amal: model selection and architecture (about 55 seconds)

**Slide 6: A causal TCN that looks back about 60 cycles**

> We tried five kinds of model. LightGBM looks at one cycle at a time, with no memory, so it became our yardstick. A one-D CNN on raw vibration could not learn from only thirteen lives. An autoencoder health score did worse than our physics numbers. LSTM, GRU and Transformer were no more accurate. We chose a TCN, a temporal convolutional network. It is causal: as the picture shows, every output looks only backwards, never at the future, just like a real machine. Four blocks with gaps of one, two, four and eight let it see about sixty cycles back with only a hundred and nine thousand weights. Its head gives the chance of breaking on each coming cycle: the risk curve our cost rule needs. Rafiq.

## Rafiq: training and evaluation (about 100 seconds)

**Slide 7: Every test cutter is one the model never saw**

> To test honestly with thirteen cutters, we hide one whole cutter, train on the other twelve with five random starts, average them, and predict the hidden one. We repeat that thirteen times, so every cutter is tested by a model that never saw it. Training uses a survival loss, the AdamW optimiser and four hundred passes. Why not a normal seventy-thirty split? Shuffling cycles puts the same cutter on both sides: the error drops to about six, and that is a leak, not skill. Splitting by whole cutters is honest, but the answer swings from nine to thirty-eight depending on which four cutters land in the test.

**Slide 8: Sensors help; the network type barely matters**

> Here is every main model on unseen cutters, as the average number of cycles it is off by. A TCN that knows only the cutter's age is off by twenty-eight. With our physics features, twenty-two. That six-cycle gain from the sensors is real. Settings alone get to twenty-six and are hard to beat on ordinary cutters. But on cutter ten, the only one on a long holder, they were off by a hundred and twenty-three cycles; the TCN, seeing it shake, by twenty-eight. Between models, it is a tie: Transformer, LSTM, LightGBM and our TCN are closer together than one model re-run with new random starts. Thirty-three models, over thirteen hundred networks, one test. Aaditya.

## Aaditya: model implementation: the working system and its decisions (about 115 seconds)

**Slide 9: From a raw recording to keep-or-change**

> This is the system, as running code: four scripts in a chain. The first turns raw sensor counts into units and keeps only the cutting. The second computes the twenty-two physics numbers. The third trains the TCN in PyTorch: thirteen folds, five random starts each, four hundred passes. The fourth turns each risk curve into keep or change. Across the whole comparison that is over thirteen hundred networks, on a laptop and a cloud machine. On the left is cutter one-oh-three, never seen in training. Black is the truth, blue is our prediction. Early on it is too hopeful: almost a hundred cycles, against sixty. As wear builds it closes in, meeting the truth near cycle forty. At forty-seven the rule changes the cutter. It would have broken at sixty.

**Slide 10: Ten breakages down to five**

> Now the decision, which is what a shop pays for. We replay all thirteen cutters cycle by cycle, each rule tuned on the other twelve, at Indian shop costs. Run to failure: all thirteen break. Change every N cycles, the usual practice: ten still break. Our rule with the TCN: five break, and the cost per good cycle falls from ninety-nine rupees to ninety-three. That six percent is promising, not proven: with thirteen cutters, its range runs from minus nine to plus twenty-one percent. What does hold up is the sensors: the same rule on a TCN without them costs a hundred and eleven rupees. Perfect knowledge would cost fifty-nine, and our error is still falling as cutters are added. So the next step is more run-to-failure data. Thank you.

---

## Backup slides: only if a reviewer asks

**What the model says about cutter 103** (Aaditya)

> These are the risk curves the decision rule actually reads, for cutter 103, which the model never saw. Each bar is the chance the cutter breaks on that cycle from now. After cycle six, there is almost no risk inside the next fifty-four cycles: calm, and correct. After cycle thirty-one, the risk peaks about thirty-five cycles ahead; it really broke twenty-nine later, so it is a few cycles late. After cycle fifty-one, the risk sits in the next one to three cycles; it really broke nine later, so near the end the model is cautious, which is the safe direction. The two commands rebuild every prediction and every decision from the processed data.

**Chosen first, then tested against 32 rivals** (Amal or Aaditya)

> We fixed the TCN as the main model before running any rival, so it cannot be the luckiest of thirty-three. It was chosen for the job: it is causal, it is small enough for thirteen lives, and it outputs a risk for each coming cycle, which the cost rule needs. It is not the top score, and need not be: re-running one model with new random starts moves it between twenty-one point seven and twenty-four point one, and none of the gaps at the top is statistically certain. The same TCN on the dataset's own hundred and twenty summaries scored nineteen point two; its edge has a ninety-five percent interval of minus one point five to plus seven point three cycles, so it could be luck, but it hints our hand-picked features leave something out. We report it rather than switch. Learning from raw signal, the one-D CNN at thirty-one point seven, failed because thirteen lives are too few.

**Why our 13 lives stay the main data** (Yadu or Aaditya)

> We did look at other datasets: NASA, Hannover, MSTW, an Indian VMC 650 shop, PHM 2010 and MATWI. Our question is when a cutter breaks. Most of them stop at a wear limit, or when an operator decides, or never; MATWI does run to failure, but its labels are noisy and it has one slow vibration sensor. So only our thirteen lives answer the question directly. That is the real issue: each life gives exactly one breaking point, so more cycles do not help, only more cutters. The other data still teaches how signals change with wear. A model trained only on the other machines estimated life used on our cutters with an error of zero point one eight two, against zero point one seven two for one trained on ours, within the noise. Pretraining our TCN on seventy-three other lives gave twenty-two point zero against our twenty-one point nine: no gain.

## Notes for whoever edits the video

- Keep each speaker's slide on screen while they talk; the deck uses only fades.
- If a speaker runs long, cut a sentence before cutting any number.
- The broken-cutter and machine photos and the data are from Piecuch & Żabiński (2025), CC BY 4.0.
- Charts and the small plots inside the flowcharts are drawn by `scripts/28_review2_charts.py` into `results/figures/review2/`.
