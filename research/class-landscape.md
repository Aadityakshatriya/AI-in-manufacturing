# Class-project landscape audit

## Source and audit result

The provided Google Sheet was downloaded as an XLSX workbook and inspected across
its used range (A1:E197). It lists 40 batches, but only three rows or row-groups
contain substantive project proposals at the time of the audit:

| Batch | Existing proposal | What it appears to contain | Consequence for us |
|---:|---|---|---|
| 4 | Simulating supply-chain shocks with LLM agents | Agent-based shock scenarios and LLM reasoning | Avoid a generic “LLM agents simulate suppliers” project; a graph-predictive mitigation system must be clearly differentiated |
| 21/22 | AI-based sound anomaly detection for predictive maintenance | MIMII audio, spectrogram CNN, MFCC + SVM baseline | Avoid plain sound anomaly detection or a standard predictive-maintenance classifier |
| 24 | Reinforcement learning on job-shop scheduling | RL dispatching/scheduling | Technically valid, but both crowded and already claimed; not a good selection for this team |
| 25 | Aaditya Kshatriya’s group | No project title yet | The manufacturing landscape remains almost entirely open |

## Interpretation

The class sheet does **not** show a crowded field of mature ideas. It shows three
familiar themes. This gives us freedom to choose a deeper mechanical process or a
less common factory decision problem.

The useful strategic exclusions are therefore:

- plain acoustic anomaly detection;
- generic predictive maintenance;
- generic job-shop RL;
- conversational supply-chain-agent theater without a validated network model,
  simulator, optimizer, or operational metric.

The strongest differentiation comes from an end-to-end system that senses or
predicts a manufacturing condition and then recommends or evaluates a feasible
action.

## Note on the job-shop RL proposal

“RL on job-shop scheduling” is not meaningless. A job shop can be represented as
a state containing unfinished operations and machine availability; actions choose
the next dispatch; reward penalizes makespan or tardiness. GNN + PPO approaches
and public Gym-style environments exist. The problem is that it is a mature
benchmark, reward design and generalization are easy to get wrong, and a
constraint-programming or heuristic baseline can be extremely strong. Since the
idea is already taken, the research payoff for repeating it is poor.
