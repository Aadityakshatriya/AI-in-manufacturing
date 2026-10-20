# Review 1 video script — ToolLife Policy

**Target length:** 3 minutes 45 seconds to 3 minutes 55 seconds  
**Speakers:** 5  
**Speaking pace:** calm and conversational; do not rush  
**Project title on screen:** *ToolLife Policy — AI-Assisted Cutting-Tool Replacement in CNC Milling*

The headings and visual directions below are not spoken.

## Speaker 1 — Selected topic and problem statement

**Suggested visual:** CNC milling footage, followed by a close-up of a new and a
damaged cutter.

> Imagine a CNC milling machine halfway through an expensive part. Every cut is
> slowly wearing down its cutting tool. Do we keep
> using it and risk it breaking, or replace it now and throw away useful tool
> life?
>
> Our project is called **ToolLife Policy**. We are building a decision-support
> system for CNC milling that answers this question before the next job begins.
> Instead of only estimating how worn the cutter is, our system will give a
> practical recommendation: **continue machining, or replace the tool**.

## Speaker 2 — Motivation and significance

**Suggested visual:** A balance graphic: “replace too early” on one side and
“replace too late” on the other.

> In many workshops, tools are changed after a fixed number of cycles or when an
> operator notices damage. Neither approach is ideal. Replacing too early wastes
> an expensive cutter. Replacing too
> late can break the tool, damage the part and create unplanned downtime.
>
> The same risk also does not make sense for every job. An older tool
> may be acceptable for a short, low-value operation, but not before machining a
> long or expensive part. Our aim is to use more of each tool safely, while
> reducing avoidable changes, failures and production loss.

## Speaker 3 — Data details

**Suggested visual:** Haas VF-1 photograph or simple machine diagram, then large
numbers: “14 tools · 968 cycles · 20 sensor channels”.

> We found an open dataset published in *Scientific Data* in 2025. It was recorded
> on a Haas VF-1 milling machine cutting hardened 42CrMo4 steel. Fourteen tools
> were followed from new condition until failure, giving us 968 milling cycles.
>
> During each cycle, researchers recorded eight vibration and twelve current
> signals from the spindle and machine axes. The data also includes tool type,
> workpiece hardness, depth of cut and the number of cycles
> remaining before failure. We have a processed table for baseline models and
> about 23.6 gigabytes of raw signals for deep learning.

## Speaker 4 — Proposed AI and ML approach

**Suggested visual:** A four-box flow: Sensors → Remaining life and uncertainty →
Production cost → Continue/Replace.

> Our first models will be XGBoost and LightGBM, which combine many small decision
> trees to learn the relationship between sensor features and tool life. For the
> raw signals, we will compare a one-dimensional CNN with a Temporal Convolutional
> Network, or TCN. These models detect vibration and current patterns as failure
> approaches.
>
> Instead of one overconfident value, the model will estimate calibrated lower,
> median and upper Remaining Useful Life, or RUL. A constrained policy will
> combine this uncertainty with tool cost, part value, changeover time and
> breakdown risk before recommending **continue** or **replace**. We may also
> compare it with reinforcement learning.

## Speaker 5 — Expected outcomes

**Suggested visual:** Mock dashboard with a health range, next-job card and a large
CONTINUE or REPLACE decision.

> Our demonstration will replay the life of a cutter one cycle at a time, showing
> its sensor readings, RUL range, next job and the reason behind each decision.
>
> We will compare fixed-age, age-only and point-RUL baselines. Our metrics include
> RUL error, uncertainty coverage, failure rate, tool-life utilization, downtime
> and total cost. We expect to use more of each tool safely without increasing
> failures, reducing unnecessary
> replacement and production loss. Success is not just an accurate model. It is an
> explainable system that turns a prediction into a useful manufacturing decision.

## Recording notes

- Each speaker has approximately 45–48 seconds.
- Leave a half-second pause when the speaker changes; do not add separate personal
  introductions for all five members.
- Put each speaker's name in a small lower-third caption instead.
- Speak as if explaining the idea to one classmate, not reading a report.
- Stress the words **continue** and **replace**; they are the core output.
- Do one timed rehearsal. If the video exceeds four minutes, shorten pauses before
  cutting technical content.

## Accuracy notes for the team, not for narration

- Primary source: [Piecuch and Żabiński, *Scientific Data*, 2025](https://www.nature.com/articles/s41597-025-04923-y).
- Official dataset: [Figshare DOI 10.6084/m9.figshare.28589216](https://doi.org/10.6084/m9.figshare.28589216).
- Verified release: 968 cycles, 14 tools, 8 vibration and 12 current channels;
  vibration was sampled at 25 kHz and current at 0.5 kHz.
- Processed feature file: approximately 1.8 MB. Compressed raw archive:
  25.35 GB decimal, or 23.60 GiB.
- The video deliberately says “23.6 gigabytes” for easy speech.
- Do not claim that the system has already reduced real factory costs. At Review 1,
  these are proposed and expected outcomes that will be tested.
