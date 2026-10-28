# Review 2 video script: what we built

**Length:** about 8 minutes (about 1,050 spoken words at a calm pace, plus slide pauses).
**Speakers:** 5. Names go on screen; nobody introduces themselves.
**Rule for every speaker:** say the numbers exactly as written. Every number here is a measured result from our code, tested on cutters the model never saw. Do not round them up.
The headings and slide notes are not spoken. The same words are in each slide's speaker notes.

---

## Speaker 1 — Bhuwan: the problem, and what changed since Review 1 (about 75 seconds)

**Slides 1–3:** title; broken cutters; what we built.

> A CNC milling cutter wears a little on every cut, until one day it snaps. Change it too early and you throw money away. Change it too late and it breaks in the middle of a part.
>
> In our data, fourteen cutters were run until they broke. One lasted fifteen cycles, another a hundred and fifty, and one broke on its very first cycle. So "change it every N cycles" cannot be right for all of them.
>
> At Review 1 we promised to predict how many cycles a cutter has left, and to turn that into a keep-or-change decision. Since then we have built the whole thing, and three things are new. We added four other factories' machines, eighty-six cutter lives in total. We tested our model against thirty others, in exactly the same way. And we put reinforcement learning in charge of a small simulated workshop. Yadu will start with what the machine actually feels.

## Speaker 2 — Yadu: what the machine feels as a cutter wears (about 80 seconds)

**Slides 4–5:** tooth hits and motor current; wear in the signals.

> The cutter has four teeth and spins fifty-three times a second, so the steel gets hit two hundred and thirteen times a second. Sensors on the table hear every one of those hits as vibration.
>
> The machine also has electricity meters on its motors. When the cutter goes blunt, it rubs instead of slicing, so the steel pushes back harder and the motor that moves the table has to work harder.
>
> We checked this on all thirteen normal cutters. The table motor's current rose in every single one: over the last tenth of its life, it was one point three to two point seven times its value when new. The once-per-turn beat in the vibration, the sign of a chipped tooth, at least doubled in ten of thirteen.
>
> We also checked that this is wear, and not just where the cutter happens to be in the steel block. It is. So the wear we cannot see shows up in signals we can measure. Amal will explain the data.

## Speaker 3 — Amal: our data, fair testing, and other factories (about 105 seconds)

**Slides 6–8:** our data and the test; four other factories; transfer between machines.

> Our main dataset is from Rzeszów University of Technology: fourteen cutters, nine hundred and sixty-eight cycles, and a hundred and twelve gigabytes of raw vibration and current.
>
> We test honestly. We hide one whole cutter, train on the rest, predict the hidden one, and repeat for every cutter. A random split would let the model peek at the cutter it is tested on. Before this review we went looking for leaks in our own work, found three, and fixed them. Every number today is after the fixes.
>
> Thirteen cutters is not much, so we added four public datasets from other machines: NASA, Hannover, MSTW, and a production shop in India. We put them on one footing: every signal is compared with the same cutter when it was new, and age becomes the fraction of its life used.
>
> Then we asked: does what other machines teach transfer to ours? A model trained only on the four other factories, which never saw our machine, estimated how much of our cutters' life was used with an error of zero point one eight. Trained on our own cutters, zero point one seven. That difference is within the noise. Aaditya will explain our models.

## Speaker 4 — Aaditya: the models, and what they tell us (about 150 seconds)

**Slides 9–13:** autoencoder; TCN; settings vs sensors; thirty other models; would more cutters help.

> We built two networks. The first is a CNN autoencoder, about four million learned numbers. It squeezes a fraction of a second of vibration into sixty-four numbers and rebuilds it, and we trained it only on healthy cutting. On cutters it never heard, its rebuild error rose with wear in twelve of thirteen. But honestly, it did not need four million numbers: PCA, a straight-line version, did as well, and a simple distance from healthy on our physics features did better.
>
> The second is a TCN, a temporal convolutional network. After every cycle it reads the cutter's history and draws a risk curve: the chance of breaking on each of the next cycles. On hidden cutters it is off by twenty-one point nine cycles on average, and by fifteen point nine in the last fifth of the cutter's life. That is level with LightGBM. Adding the autoencoder's score did not help.
>
> The most important thing we learned is this. The settings of the cut, like how wide it is and how long the holder is, already explain most of a cutter's life. On the twelve ordinary cutters, a model with no sensors at all is more accurate over the whole life. Sensors help near the end, and above all when something unexpected happens. Cutter ten was the only one on a long holder: the settings models were off by a hundred and twenty-three cycles. The TCN, reading its vibration, was off by twenty-eight.
>
> To check that we had not just picked a model we liked, we ran thirty other models through the same test: classical machine learning, LSTM, GRU, a transformer, and a CNN on the raw vibration. The good ones are all within the noise of each other. What a model is given matters more than its architecture.
>
> And when we trained the TCN on fewer cutters, its error was still falling steeply at twelve. The limit is data, not the model. Rafiq will show what this means for decisions.

## Speaker 5 — Rafiq: decisions, reinforcement learning, and what we learned (about 120 seconds)

**Slides 14–17:** replay of real cutters; decisions; the RL workshop; what we learned.

> The real question is: keep this cutter, or change it now? Our rule compares the cost of the risk of breaking with the cost of a planned change. For an Indian job shop, that is about three thousand one hundred rupees for a planned change, and six thousand five hundred for a breakage.
>
> We replayed all thirteen real cutters, cycle by cycle. Changing every N cycles let ten of thirteen break. Our rule on the TCN's risk curves let five break and was six percent cheaper, though with thirteen cutters that is not yet certain. The same network with sensors was sixteen percent cheaper than without them, and cheaper in all twenty-four cost settings we tried. But a simple survival model on the settings did about as well as the TCN, because a decision needs honest probabilities, and our network is too confident. Perfect knowledge would save forty percent, so that is where the money is.
>
> We also tried reinforcement learning, PPO and DQN, in a three-machine workshop. They did not beat well-tuned rules. They learned to slow the machines down, which cut breakages, but kept doing it even when it did not pay.
>
> What we learned: the signals carry wear on every machine we checked. Settings explain most of a cutter's life, and sensors catch the unexpected. And with thirteen cutters, the limit is data. Thank you.

---

## If a reviewer asks

The answers are in section 11 of `PROJECT_EXPLAINED.md`. The ones most likely to come up: why not a random split; is the signal rise just position in the block; why a 4-million-number autoencoder if PCA does as well; why a TCN and not an LSTM or a transformer; why not use the best model of the thirty; why sensors at all if the settings model is better on ordinary cutters; and why the decision rule is not tuned.

## Slide notes for whoever edits the video

- The deck's speaker notes hold exactly these words, slide by slide.
- Slide images are in `docs/img/` and `results/figures/`. The broken-cutter photos are from the dataset paper (CC BY 4.0); credit is on the last slide.
- Keep each speaker's slides on screen while they talk; no animations needed.
- If a speaker runs long, cut their last sentence before cutting any number.
