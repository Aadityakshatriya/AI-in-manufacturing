# Review 2 video script: final deck

**Length:** 788 spoken words, about 6½–7 minutes at a calm presenting pace (about 120 words a minute) with slide changes.
**Deck:** 10 main slides and 3 backup slides (ToolLife Policy Review 2 Final). The same words are in each slide's speaker notes.
**Speakers:** 5. Nobody introduces themselves; each speaker hands over by name.
**Rule for every speaker:** say the numbers exactly as written. Every number is a measured result from our code, on cutters the model never saw. Errors are in cycles; costs are rupees per good cycle.

---

## Yadu: the problem in one slide, and the data (about 75 seconds)

**Slide 1: ToolLife Policy**

> This is ToolLife Policy, our Review 2. Review 1 set out the problem and the data. Today: how we prepared the data, the model we chose, how we tested it, and the working system.

**Slide 2: Problem Statement**

> A milling cutter wears a little on every cut until it snaps; these fourteen did. A breakage costs about twice a planned change. So every cycle, our system reads the sensors, the TCN turns them into a risk curve, and a cost rule decides: keep cutting, or change the cutter now. Everything we promised at Review 1 is built.

**Slide 3: Dataset**

> The data is from Piecuch and Żabiński, 2025: fourteen cutters on one machine, run until they broke. Nine hundred and sixty-eight cycles, twenty sensors, a hundred and twelve gigabytes. Cutter eleven, in grey, broke on its first cycle, so we leave it out. That makes thirteen lives, our real sample size, since each life gives one breaking point. Over to Bhuwan.

## Bhuwan: data pre-processing and feature engineering (about 70 seconds)

**Slide 4: Data Pre-processing**

> Each cycle is a raw recording, about two minutes long. We keep only the cutting, which the spindle current shows: here, twenty-seven seconds. We take each sensor's spectrum; the blue lines are the tooth hits. From that we compute twenty-two physics numbers, and divide each by the cutter's first three cycles, because what matters is change since new. We never use the future. The result is one row per cycle; darker means more change.

**Slide 5: Feature Engineering**

> The twenty-two numbers come in four families: load, meaning how hard the motors work; vibration; rhythms, the beat of the teeth, where a chipped tooth shows; and impacts. On the right, two of them over every cutter's life: both climb towards the end. We checked it is wear, not position in the block. With the settings, the cycle count and a first-ring flag, the model gets twenty-nine inputs per cycle. Amal.

## Amal: model selection and architecture (about 55 seconds)

**Slide 6: Model Architecture: Causal TCN**

> We tried five kinds of model. LightGBM has no memory of past cycles, so it became our yardstick. A CNN on raw vibration could not learn from thirteen lives. An autoencoder health score did worse than our physics numbers. LSTM, GRU and Transformer were no more accurate. We chose a TCN, a temporal convolutional network. It is causal: it only looks back, never at the future, like a real machine. Four blocks with growing gaps let it see about sixty cycles with a hundred and nine thousand weights. It outputs the chance of breaking on each coming cycle: the risk curve our cost rule needs. Rafiq.

## Rafiq: training and evaluation (about 85 seconds)

**Slide 7: Training and Evaluation: Leave-One-Cutter-Out**

> To test honestly, we hide one whole cutter, train on the other twelve with five random starts, and predict the hidden one. We repeat that thirteen times, so every cutter is tested by a model that never saw it. Why not seventy-thirty? A random split puts the same cutter on both sides: the error drops to about six, but that is a leak. Splitting by whole cutters is honest, but swings from nine to thirty-eight depending on which cutters land in the test.

**Slide 8: Results: Remaining Useful Life Prediction**

> Here is every main model on unseen cutters, in cycles of error. A TCN that knows only the cutter's age is off by twenty-eight; with our physics features, twenty-two. That six-cycle gain from sensors is real. Settings alone are hard to beat on ordinary cutters, but on cutter ten, the only one on a long holder, they were off by over a hundred cycles; the TCN, seeing it shake, by twenty-eight. Between models it is a tie: they are closer together than one model re-run. Aaditya.

## Aaditya: model implementation: the working system and its decisions (about 105 seconds)

**Slide 9: Model Implementation**

> This is the system as running code: four scripts in a chain. The first cleans the raw signal and keeps only the cutting. The second computes the physics numbers. The third trains the TCN in PyTorch, thirteen folds with five random starts each; over thirteen hundred networks across the whole comparison. The fourth turns each risk curve into keep or change. On the left is cutter one-oh-three, never seen in training. Black is the truth, blue our prediction. Early on it is too hopeful, but as wear builds it closes in and meets the truth near cycle forty. At forty-seven the rule changes the cutter. It would have broken at sixty.

**Slide 10: Results: Tool-Change Decisions**

> Now the decision. We replay all thirteen cutters cycle by cycle at Indian shop costs. Run to failure, and all thirteen break. Change every N cycles, the usual practice, and ten still break. Our rule with the TCN: five break, and the cost per good cycle falls from ninety-nine rupees to ninety-three. That six percent is promising, not proven, with thirteen cutters. What does hold up is the sensors: the same rule without them costs a hundred and eleven. Perfect knowledge would cost fifty-nine, and our error is still falling as cutters are added. So the next step is more data. Thank you.

---

## Backup slides: only if a reviewer asks

**End-to-End Demonstration: Unseen Cutter 103** (Aaditya)

> This is the whole pipeline on one cutter the model never saw in training, cutter one-oh-three, at cycle forty-seven. One: the raw recording, eight vibration and twelve current signals. Two: we keep only the twenty-five seconds of cutting, which the spindle current shows. Three: in the vibration spectrum the teeth hit at two hundred and thirteen hertz: thirty-two hundred rpm, times four teeth, over sixty. Four: each cycle becomes twenty-two numbers: how strong the vibration and current are, how spiky the vibration is, and how much power sits at the tooth-hit frequency. Five: we divide each by this cutter's own first three cycles, so the model sees change since new; the spindle's high-pitched vibration is now twenty-two percent above new. Six: with seven context inputs, the cutting settings, the cycle count and a first-pass flag, cycles one to forty-seven become a table of twenty-nine columns. Seven: the causal TCN reads the last sixty or so cycles and never the future. Eight: it outputs the chance of breaking on each coming cycle; the most likely break is five cycles away. It really broke thirteen later, so the model is on the cautious side. Nine: the cost rule compares keeping the cutter, an expected three thousand two hundred and twenty-nine rupees, with a planned change now, three thousand one hundred and thirty-three. Every good cycle is credited a hundred and three rupees, the long-run cost per cycle learned on the other twelve cutters. Ten: keeping costs more, so it changes the cutter at cycle forty-seven, thirteen cycles before it would have broken.

**Model Selection** (Amal or Aaditya)

> We tested our TCN against thirty-two other models, each tested the same way: hide one cutter, train on the other twelve, predict the hidden one. The table shows the main ones. The best four, the Transformer, LightGBM, the LSTM and our TCN, are within one cycle of each other, closer together than one model re-run with new random starts, which moves between twenty-one point seven and twenty-four point one. So the score alone cannot choose. We fixed the TCN as the main model before running any rival, so it cannot be the luckiest of thirty-three. It was chosen for the job: it is causal, so it never uses the future; it is small enough for thirteen lives; and it outputs a risk for each coming cycle, which the cost rule needs. The same TCN on the dataset's own hundred and twenty summaries scored nineteen point two; its edge has a ninety-five percent interval of minus one point five to plus seven point three cycles, so it could be luck, but it hints our hand-picked features leave something out. We report it rather than switch. Learning from raw signal, the one-D CNN at thirty-one point seven, failed because thirteen lives are too few.

**Dataset Selection** (Yadu or Aaditya)

> We did look at other datasets: NASA, Hannover, MSTW, an Indian VMC 650 shop, PHM 2010 and MATWI. Our question is when a cutter breaks. Most of them stop at a wear limit, or when an operator decides, or never; MATWI does run to failure, but its labels are noisy and it has one slow vibration sensor. So only our thirteen lives answer the question directly. That is the real issue: each life gives exactly one breaking point, so more cycles do not help, only more cutters. The other data still teaches how signals change with wear. A model trained only on the other machines estimated life used on our cutters with an error of zero point one eight two, against zero point one seven two for one trained on ours, within the noise. Pretraining our TCN on seventy-three other lives gave twenty-two point zero against our twenty-one point nine: no gain.

## Notes for whoever edits the video

- Keep each speaker's slide on screen while they talk; the deck uses only fades.
- If a speaker runs long, cut a sentence before cutting any number.
- The broken-cutter and machine photos and the data are from Piecuch & Żabiński (2025), CC BY 4.0.
- Charts and the small plots inside the flowcharts are drawn by `scripts/28_review2_charts.py` into `results/figures/review2/`.
