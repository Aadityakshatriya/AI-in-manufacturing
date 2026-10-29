# Review 2 video script: final deck

**Length:** 818 spoken words, about 6½–7 minutes at a calm presenting pace (about 120 words a minute) with slide changes.
**Deck:** 10 main slides and 3 backup slides (ToolLife Policy Review 2 Final). The same words are in each slide's speaker notes.
**Speakers:** 5. Yadukrishna opens; each speaker thanks the last and hands over to the next by name.
**Rule for every speaker:** say the numbers exactly as written. Every number is a measured result from our code, on cutters the model never saw. Errors are in cycles; costs are rupees per good cycle.

---

## Yadukrishna: the problem in one slide, and the data (about 85 seconds)

**Slide 1: ToolLife Policy**

> Hello everyone, I'm Yadukrishna, and this is ToolLife Policy, our Review 2: predicting how many cycles a milling cutter has left, and deciding when to change it. Today we'll cover pre-processing, features, the model, how we tested it, and the working system.

**Slide 2: Problem Statement**

> First, the problem. A milling cutter wears a little on every cut until it snaps; these fourteen did. A breakage costs about six and a half thousand rupees; a planned change, about three thousand. So every cycle, our system reads the sensors, the TCN turns them into a risk curve, and a cost rule decides: keep cutting, or change the cutter now.

**Slide 3: Dataset**

> Now the dataset, from Piecuch and Żabiński, 2025: fourteen cutters on one Haas milling machine, each run until it broke. Nine hundred and sixty-eight cycles, twenty sensors, a hundred and twelve gigabytes. Cutter eleven broke on its first cycle, so we leave it out. That leaves thirteen lives, our real sample size, because each life gives just one breaking point. Over to Bhuwan now.

## Bhuwan: data pre-processing and feature engineering (about 90 seconds)

**Slide 4: Data Pre-processing**

> Thanks, Yadukrishna. Data pre-processing happens in six steps. One: each cycle is a raw recording, about two minutes long. Two, segmentation: the spindle current shows when the tool is really cutting, here twenty-seven seconds, and we keep only that. Three, spectral analysis: the blue lines mark the teeth hitting the metal. Four: from this we extract twenty-two physics numbers. Five, normalisation: we divide each by the cutter's own first three cycles, because what matters is change since new. Six: one row per cycle; darker means more change. Nothing ever uses the future.

**Slide 5: Feature Engineering**

> Next, feature engineering. The twenty-two numbers come in four families: load, how hard the motors work; vibration, how strongly it shakes; rhythm, the beat of the teeth, where a chipped tooth shows; and impacts, sharp spikes. On the right, two of them across every cutter's life: both climb towards the end. We checked that this is wear, not position in the block. Add five cutting settings, the cycle count and a first-ring flag, and the model gets twenty-nine inputs per cycle. Amal, over to you.

## Amal: model selection and architecture (about 50 seconds)

**Slide 6: Model Architecture: Causal TCN**

> Thanks, Bhuwan. So, which model? We tried five kinds. LightGBM has no memory of past cycles, so it became our yardstick. An autoencoder health score did worse than our physics numbers. LSTM, GRU and Transformer were no more accurate. We chose a causal TCN, a temporal convolutional network: it only looks back, never at the future. Four layers with gaps of one, two, four and eight let it see about sixty cycles with a hundred and nine thousand weights. It outputs the chance of breaking on each coming cycle: the risk curve our cost rule needs. Rafiq will now show how we tested it.

## Rafiq: training and evaluation (about 75 seconds)

**Slide 7: Training and Evaluation: Leave-One-Cutter-Out**

> Thanks, Amal. To test honestly, we hide one whole cutter, train on the other twelve with five random starts, and predict the hidden one. We repeat that thirteen times, so every cutter is tested by a model that never saw it. You might ask, why not seventy-thirty? A random split puts the same cutter on both sides: the error drops to about six, but that is a leak. Splitting by whole cutters is honest, but swings from nine to thirty-eight depending on which cutters land in the test.

**Slide 8: Results: Remaining Useful Life Prediction**

> Here are the results: average error in cycles left, on cutters the model never saw. A TCN that knows only the cutter's age is off by twenty-eight; with our physics features, twenty-two. That six-cycle gain from the sensors is real. Between network types it is a tie: they are closer together than one model re-run with new random starts. Over to Aaditya for the working system.

## Aaditya: model implementation: the working system and its decisions (about 110 seconds)

**Slide 9: Model Implementation**

> Thanks, Rafiq. Here's the model implementation: the system runs as four scripts in a chain. Data ingestion cleans the raw signal and keeps the cutting. Feature extraction computes the physics numbers. Model training fits the TCN in PyTorch: thirteen folds, five random starts each. The decision policy turns each risk curve into keep or change. On the left is cutter one-oh-three, never seen in training. Black is the truth, blue our prediction. Early on it is too hopeful, but as wear builds it closes in. At cycle forty-seven the rule changes the cutter; it would have broken at sixty. Our first backup slide walks this cutter through every step.

**Slide 10: Results: Tool-Change Decisions**

> And finally, the decisions. We replay all thirteen cutters cycle by cycle at Indian shop costs. Run to failure, and all thirteen break. Change every N cycles, the usual practice, and ten still break. Our rule with the TCN: five break, and the cost per good cycle falls from ninety-nine rupees to ninety-three. That six percent is promising, not proven, with thirteen cutters. What does hold up is the sensors: the same rule without them costs a hundred and eleven. Perfect knowledge would cost fifty-nine, and our error is still falling as cutters are added, so the next step is more data. Thank you for listening.

---

## The three backup questions: answers if a reviewer asks

Each answer goes with its backup slide. Its first sentence is the direct answer.

**Q: Can you show the system working on one cutter, end to end?** (slide 11, Aaditya)

> Sure. Here is one cutter the model never saw, cutter one-oh-three, at cycle forty-seven, through every step. One, the raw recording: eight vibration and twelve current signals. Two, segmentation: we keep the twenty-five seconds of real cutting. Three, spectral analysis: the teeth hit two hundred and thirteen times a second, thirty-two hundred rpm times four teeth over sixty. Four, feature extraction: twenty-two numbers for how strong the signals are, how spiky the vibration is, and how much power sits at the tooth-hit frequency. Five, normalisation: each is divided by this cutter's first three cycles; the spindle's high-pitched vibration is now twenty-two percent above new. Six: with seven context inputs, cycles one to forty-seven become a table of twenty-nine columns. Seven: the causal TCN reads the last sixty or so cycles, never the future. Eight: it gives the chance of breaking on each coming cycle; the most likely is five cycles away. Nine, the decision rule: keeping the cutter carries the risk of a breakage, so its expected cost is three thousand two hundred and twenty-nine rupees, after crediting each extra good cycle at a hundred and three, our long-run cost per cycle. A planned change now costs three thousand one hundred and thirty-three. Ten: keeping costs more, so the cutter is changed at cycle forty-seven. It really broke at sixty, thirteen cycles later.

**Q: Why did you choose this model?** (slide 12, Amal or Aaditya)

> Short answer: it fits the job, and we chose it before comparing, not after. The job needs three things. It must look only at past cycles, because a real machine cannot see the future. It must be small enough to learn from thirteen cutter lives. And it must give the chance of breaking on each coming cycle, because our cost rule needs that whole curve, not one number. A causal TCN does all three with a hundred and nine thousand weights. Then we tested it against thirty-two other models in exactly the same way, hiding one cutter at a time. The best four, the Transformer, LightGBM, the LSTM and our TCN, are within one cycle of each other, closer than one model re-run with new random starts. So none is clearly better, and switching to the top score would just be picking the luckiest of thirty-three. One honest note: the same TCN on the dataset's own hundred and twenty summaries scored nineteen point two. That could be luck, but it hints our features miss something, so we report it rather than hide it.

**Q: Why didn't you use the other datasets?** (slide 13, Yadukrishna or Aaditya)

> Short answer: our question is when a cutter breaks, and only this dataset records that cleanly. Every cutter here runs until it actually breaks, with both vibration and motor current. The others stop somewhere else: NASA, Hannover and MSTW at a wear limit, the Indian VMC 650 shop when the operator decides, and PHM 2010 never. MATWI does run to failure, but its labels are noisy and it has one slow sensor. A wear limit is not a breakage, so those lives cannot teach the breaking point. We did not ignore them: we pretrained our TCN on seventy-three cutter lives from those machines, then fine-tuned it on ours. The error was twenty-two point zero, against twenty-one point nine without it, so no gain. What would really help is more cutters run to breakage, since each life gives exactly one breaking point.

## Notes for whoever edits the video

- Keep each speaker's slide on screen while they talk; the deck uses only fades.
- If a speaker runs long, cut a sentence before cutting any number.
- The broken-cutter and machine photos and the data are from Piecuch & Żabiński (2025), CC BY 4.0.
- Charts and the small plots inside the flowcharts are drawn by `scripts/28_review2_charts.py` into `results/figures/review2/`.
