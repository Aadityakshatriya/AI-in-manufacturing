# Review 2 video script: what we built

**Length:** about 7–7½ minutes (about 900 spoken words at a calm pace, plus slide pauses).
**Speakers:** 5. Names go on screen; nobody introduces themselves.
**Rule for every speaker:** say the numbers exactly as written. Every number here is a measured result from our code, tested on cutters the model never saw. Do not round them up.
The headings and slide notes are not spoken.

---

## Speaker 1 — Bhuwan: the problem, and what changed since Review 1 (about 80 seconds)

**Slides 1–3:** title; broken cutters photo; the system diagram.

> A CNC milling cutter wears a little on every cut, until one day it snaps. Change it too early and you throw money away. Change it too late and it breaks in the middle of a part.
>
> In our data, fourteen cutters were run until they broke. One lasted fifteen cycles, another a hundred and fifty, and one broke on its very first cycle. So "change it every N cycles" cannot be right for all of them.
>
> At Review 1 we promised to predict how many cycles a cutter has left, and to turn that into a keep-or-change decision. Since then we have built the whole thing. Two things changed. We added data from four other factories' machines, eighty-six cutter lives in total. And we put a reinforcement learning agent in charge of a small simulated workshop. Yadu will start with what the machine actually feels.

## Speaker 2 — Yadu: the physics, and what the sensors feel (about 80 seconds)

**Slides 4–5:** tooth hits and motor current; wear in the signals.

> The cutter has four teeth and spins fifty-three times a second, so the steel gets hit two hundred and thirteen times a second. Sensors on the table hear every one of those hits as vibration.
>
> The machine also has electricity meters on its motors. When the cutter goes blunt, it rubs instead of slicing, so the steel pushes back harder and the motor that moves the table has to work harder.
>
> We checked this on all thirteen normal cutters. The table motor's current rose in every single one, by one point four to two point seven times by the end of life. The vibration rose too, and a chipped tooth shows up as a once-per-turn beat that was not there before.
>
> So the wear we cannot see shows up in signals we can measure. Amal will explain the data we used.

## Speaker 3 — Amal: the data, and how we test fairly (about 80 seconds)

**Slides 6–7:** our dataset and fair testing; four other factories.

> Our main dataset is from Rzeszów University of Technology: fourteen cutters, nine hundred and sixty-eight cycles, and one hundred and twelve gigabytes of raw vibration and current.
>
> Thirteen cutters is not much, so we found four more public datasets from other machines: NASA, Hannover, a 2026 dataset called MSTW, and a production shop in India. Each measures things differently, so we put them on one common footing: every signal is compared with the same cutter when it was new, and age is measured as the fraction of its life used.
>
> We test honestly. We hide one whole cutter, train on the rest, and predict the hidden one. Then we repeat for every cutter. A random split would let the model peek at cycles from the cutter it is tested on, and make the scores look much better than they are. Aaditya will explain the models.

## Speaker 4 — Aaditya: the models and the results (about 110 seconds)

**Slides 8–10:** autoencoder; TCN and results; transfer across machines.

> We built two networks, both convolutional.
>
> The first is a CNN autoencoder, about four million learned numbers. It squeezes a fraction of a second of vibration into sixty-four numbers and rebuilds it. We trained it only on healthy cutting. So when a cutter starts to wear, its sound stops matching what the network learned, and the rebuild gets worse. On cutters it had never heard, that rebuild error rose steadily with wear in twelve of thirteen cutters, to three to seventeen times its starting level.
>
> The second is a TCN, a temporal convolutional network. After every cycle it reads the cutter's history, the physics features from the motors and the vibration, and draws a risk curve: the chance of breaking on each of the next cycles. From that curve we get a low, middle and high estimate of the cycles left.
>
> On hidden cutters, the TCN is off by twenty point nine cycles on average, and by thirteen point six in the last fifth of the cutter's life, where decisions matter. That is level with a strong LightGBM baseline overall and better near the end. Honestly, adding the autoencoder on top did not improve it: with twelve training cutters, more inputs mean more overfitting.
>
> Our favourite result: a model trained only on the four other factories, which never saw our machine, tracked wear on our cutters as well as a model trained on our own data. The physics transfers. Rafiq will show what this means for decisions.

## Speaker 5 — Rafiq: decisions, reinforcement learning, and what we learned (about 100 seconds)

**Slides 11–13:** replay of real cutters; decisions; the RL workshop; takeaways.

> The real question is: keep this cutter, or change it now? Our rule compares the cost of the risk of breaking with the cost of a planned change. We priced these for an Indian job shop: about three thousand one hundred rupees for a planned change, and about six thousand five hundred for a breakage.
>
> We replayed all thirteen real cutters, cycle by cycle, with the model never having seen the cutter. Changing every N cycles let ten of thirteen cutters break. Our rule let five break and was about five percent cheaper. With only thirteen cutters that saving is not yet statistically certain. Perfect knowledge would have saved forty percent, so better prediction is where the money is.
>
> For one cutter, the best decision can be calculated exactly, so we used that to check our reinforcement learning. PPO came within one percent of the exact best answer. Then we gave PPO and DQN a small workshop of three machines. They did not beat well-tuned rules. They learned to slow the machines down, which halved breakages, but they kept doing it even when slowing did not pay. For this problem, a clear rule is the better choice, and that is a useful thing to know.
>
> What we learned: the signals really do carry wear, the physics transfers across factories, and the decision only gets better when the prediction gets better. Thank you.

---

## Slide notes for whoever edits the video

- Slide images are in `docs/img/` and `results/figures/`. The broken-cutter photos are from the dataset paper (CC BY 4.0); credit is on the last slide.
- Keep each speaker's slides on screen while they talk; no animations needed.
- If a speaker runs long, cut their last sentence before cutting any number.
