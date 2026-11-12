# Scoring

Brute force finds every answer here instantly at these sizes, so the circuit is what is scored. Libraries and Qiskit's built-in circuits are allowed if your team explains every block. Hardware is optional.

The total is 100 points.

| Part | Points |
|---|---|
| Tiers solved | 40 |
| Simplicity | 15 |
| Presentation | 25 |
| Analysis | 20 |

## Tiers solved: 40

| Tier | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Points | 1 | 2 | 2 | 3 | 4 | 4 | 5 | 6 | 6 | 7 |

- **Full points** need the plaintext hash to match AND a circuit executed during `solve()`.
- **25% of the tier** for a matching plaintext with no circuit executed.
- **Up to 50% of the tier** for a working circuit that does not recover the key. Judges award this after reviewing your write-up.

Judges can also lower a tier's credit if the check tool flags it and the circuit plays no real part in finding the key.

A hash match verifies the recovered plaintext, not the recovery method. In your write-up, show which measured outcomes produced the key and how you processed them. Executing an unrelated circuit alongside a classical solution does not establish full-credit eligibility.

## Simplicity: 15

Per tier, the simplicity pool is 0.375 x that tier's points, so the pools sum to 15. Only teams with full tier points and valid metrics are eligible.

For each metric m in {two_qubit_gates, depth, total_gates, active_qubits}:

- `ratio_m = best_m / team_m`, where `best_m` is the lowest value among eligible teams for that tier.
- If `best_m` is 0, the ratio is 1 when `team_m` is 0, else `1 / (1 + team_m)`.

`tier_simplicity` is the sum over m of `weight_m x ratio_m`, and points = pool x `tier_simplicity`.

| Metric | Weight |
|---|---|
| Two-qubit gates | 0.4 |
| Depth | 0.3 |
| Total gates | 0.2 |
| Active qubits | 0.1 |

Teams with "no metrics" for a tier get 0 simplicity there. Where all solutions are structurally identical, such as tier 2, whose scored circuits are single-qubit measurements, ties give everyone full marks.

Simplicity is relative to the other teams, so it is final only after the deadline.

### How your circuit is measured

`tools/check_submission.py` works in two steps, per tier.

1. **Correctness.** It imports `solution.py`, calls `solve()` under `solve_timeout_s`, hashes the result, and compares it with `hashes.txt`.
2. **Simplicity metrics.** While `solve()` runs, it records every circuit sent to Aer. For tier 2 it uses the Channel's log of your measurement circuits. It transpiles each one with `tools/scoring_config.yaml`. The scored circuit is the one with the most two-qubit gates after transpiling, with ties broken by depth.

`build_circuit()` is never scored. Gates from oracles that a tier provides are included, and they are the same for every team.

- Run on Aer: `AerSimulator`, other Aer backends, or Aer's Sampler and Estimator. Circuits evaluated any other way are not recorded and do not count as executed.
- Measurements, resets, and barriers are not gates. Active qubits are those touched by at least one gate after transpiling.
- Gates inside control flow count, once per branch and once per `for_loop` round.
- If transpiling passes `transpile_timeout_s` or fails, the tier records "no metrics". You keep your tier points but earn no simplicity points for it. Dense `UnitaryGate` constructions are the usual cause.

Simplicity measures the largest executed circuit, not the total cost of an experiment. Report shots, circuit executions, oracle calls, and classical preprocessing separately in your write-up. For example, a circuit run for 1,000 shots has the same simplicity metrics as that circuit run for one shot, but uses more experimental work. These additional costs inform the existing analysis category; they do not change the simplicity formula.

A small-active-qubit flag requests review and is not an automatic penalty. Legitimate techniques such as recycling a measured control qubit can reduce the register size. Explain any such construction and show how its measurements recover the key. A fixed-size permutation or matrix construction can be allowed by a tier while still requiring exponential classical preparation; distinguish that toy implementation from a scalable algorithm.

Check your own numbers:

```bash
python tools/check_submission.py submissions/<team> --metrics-only
```

This skips the hash check, prints the metrics table, and writes `report.md` and `report.json`.

## Presentation: 25

| Item | Points |
|---|---|
| Why each approach works | 10 |
| Circuit design and explanation of the construction | 8 |
| Clarity and delivery | 7 |

## Analysis: 20

| Item | Points |
|---|---|
| Classical versus quantum cost and scaling limits | 12 |
| A real-hardware run or a noise discussion | 8 |

## Tie-breaker

If two teams have equal totals (within 0.01), the team whose final accepted submission has the earliest `submitted_at` wins.

A resubmission replaces the earlier one and its time counts, so resubmitting moves your time later. Submission time is used only for ties and earns no points. The only trusted clock is the submission form, not git commit times. There are no other tie-breakers.

## Worked example

Three made-up teams solve tier 4. All are eligible.

The pool is 0.375 x 3 = 1.125 points.

| Team | Two-qubit gates | Depth | Total gates | Active qubits |
|---|---|---|---|---|
| Alpha | 30 | 60 | 100 | 12 |
| Beta | 40 | 50 | 120 | 12 |
| Gamma | 60 | 90 | 150 | 12 |
| **Best** | **30** | **50** | **100** | **12** |

Ratios are best / team:

| Team | Two-qubit (0.4) | Depth (0.3) | Total (0.2) | Active (0.1) | tier_simplicity | Points |
|---|---|---|---|---|---|---|
| Alpha | 30/30 = 1.000 | 50/60 = 0.833 | 100/100 = 1.000 | 1.000 | 0.950 | 1.069 |
| Beta | 30/40 = 0.750 | 50/50 = 1.000 | 100/120 = 0.833 | 1.000 | 0.867 | 0.975 |
| Gamma | 30/60 = 0.500 | 50/90 = 0.556 | 100/150 = 0.667 | 1.000 | 0.600 | 0.675 |

For Alpha: 0.4 x 1.000 + 0.3 x 0.833 + 0.2 x 1.000 + 0.1 x 1.000 = 0.950, and 1.125 x 0.950 = 1.069.

### A timestamp tie

Each team also has 3 tier points. The judges award the points below for presentation and analysis.

| Team | Tier points | Simplicity | Judges | Total | Final submission |
|---|---|---|---|---|---|
| Gamma | 3.00 | 0.675 | 52.00 | 55.675 | 16:30 |
| Beta | 3.00 | 0.975 | 50.09 | 54.065 | 17:02 |
| Alpha | 3.00 | 1.069 | 50.00 | 54.069 | 17:40 |

Gamma wins outright. Alpha and Beta are within 0.01, so it is a tie, and Beta's earlier time places it second.

Now suppose Beta resubmits at 17:55 with the same metrics. Its time moves after Alpha's, so Alpha takes second place. Resubmitting cost Beta the tie.
