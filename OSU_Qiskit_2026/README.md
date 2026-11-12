# Qiskit Fall Fest 2026 @ Ohio State: Quantum Cryptography Challenge

Ten encrypted files, each opened by a quantum algorithm. Your team works out which one fits, builds the circuits, runs them on a simulator, recovers each key, and decrypts each file. Then you show how you did it. The ten decrypted lines, read in order, form a final message. Hosted by The Quantum Club at Ohio State.

| Tier | Folder | Title | Level |
|---|---|---|---|
| 1 | `tier01` | The Parity Vault | Warm-up |
| 2 | `tier02` | Two Links | Easy |
| 3 | `tier03` | Twenty-Four Seals | Easy |
| 4 | `tier04` | The Echo | Medium |
| 5 | `tier05` | The Small Safe | Medium |
| 6 | `tier06` | The Bigger Safe | Medium to hard |
| 7 | `tier07` | The Hidden Angle | Hard |
| 8 | `tier08` | The Wrapped Key, N = 35 | Hard |
| 9 | `tier09` | The Wrapped Key, N = 77 | Very hard |
| 10 | `tier10` | The Handshake | Boss |

The quantum algorithm behind each tier is not named anywhere. Each tier README says how its file is encoded and gives two optional hints, and working out which algorithm fits is part of the challenge.

## Contents

| Path | Purpose |
|---|---|
| `README.md` | Setup, workflow, submission, and a scoring summary |
| `CHALLENGE.md` | The challenge statement: story, the ten tiers, rules |
| `SCORING.md` | The full rubric with worked examples |
| `HELPERS.md` | What each supplied helper does and how to use its public interface |
| `requirements.txt` | Pinned Qiskit, Aer, and tool versions |
| `hashes.txt` | SHA-256 of each tier's plaintext, one line per tier |
| `common/` | Shared helpers: keystream, hash checker, toy cipher |
| `tier01/` to `tier10/` | One folder per tier: README, `locked.json`, helpers, starter notebook |
| `references/` | Textbook and documentation links |
| `submissions/TEAM_TEMPLATE/` | What your team copies and fills in |
| `tools/` | The scoring settings and scripts, so you can see exactly how you are scored |
| `.github/workflows/ci.yml` | Checks that the challenge files are intact |

## Getting started

Python 3.12 is the tested version.

1. Clone [this repo](https://github.com/QuantumClub-OSU/Quantum-Cryptography-Challenge). Do not fork it.

   ```bash
   git clone https://github.com/QuantumClub-OSU/Quantum-Cryptography-Challenge.git
   cd Quantum-Cryptography-Challenge
   ```

   If you don't use git, click **Code**, then **Download ZIP** on the repo page, and unzip it.

2. Create a virtual environment and install the requirements:

   ```bash
   python -m venv .venv
   ```

   Activate it with `source .venv/bin/activate` on macOS or Linux, or `.venv\Scripts\activate` on Windows. Then:

   ```bash
   pip install -r requirements.txt
   ```

3. Check your setup from the repo root:

   ```bash
   python tools/check_setup.py
   ```

   This checks the required Qiskit/Aer versions, loads every supplied circuit file, and runs a small Aer circuit without solving a tier. If it fails, use the same virtual environment to reinstall with `python -m pip install -r requirements.txt`.

4. Open `tier01/starter.ipynb` in Jupyter and run all cells. With no key set, the last cell prints `FAIL: tier 1 has no answer yet.` That is expected until you add a solution. Select the same Python environment as in step 3.

## How to work a tier

1. Read the tier's `README.md`.
2. Build your circuit in `starter.ipynb` and run it on Aer. If you are not sure which technique applies, try the tier's hints and the sources in `references/`.
3. Recover the key from your measurements.
4. Decrypt, using the check cell at the end of the notebook.
5. Move your work into `solve()` in `submissions/<team_name>/tierNN/solution.py`.

## Submission

1. Copy `submissions/TEAM_TEMPLATE` to `submissions/<team_name>/`.
2. Put your solutions and your write-up there. Each `solution.py` has `solve()`, which builds and runs your circuit on Aer and returns the decrypted line, and `build_circuit()`, which returns your main circuit for diagrams only. Keep the import lines at the top of each template: the checker runs your file from the repo root, so the helper is `from tierNN import helper`, not `import helper` as in the notebooks.
3. Link your write-up from your team README.
4. Zip your team folder, `submissions/<team_name>/`, so the zip holds that one folder with the team name. Leave out everything else in the repo, and any `.venv`, `__pycache__`, or `.ipynb_checkpoints` folders.
5. Upload the zip through the [submission form](https://docs.google.com/forms/d/e/1FAIpQLSeYZrd6v9SxdsHyUpgYfwjhpEHVlhk7JjN5nYaVMcpo3uj7FQ/viewform) before November 13, 2026 at 12:00 PM Eastern. The form asks you to sign in with a Google account to upload a file.

We check your folder inside a fresh copy of this repo, so changes you make outside `submissions/<team_name>/` have no effect.

**Keep your work private.** Do not push your solutions to GitHub or anywhere public, and do not open a pull request on this repo. Anything public can be seen by other teams.

You may resubmit as many times as you like before November 13, 2026 at 12:00 PM Eastern. Only your latest submission is judged, and its form timestamp is its submission time.

**Resubmitting resets your tiebreaker time.** See [Scoring](#scoring).

## Scoring

The total is 100 points. [SCORING.md](SCORING.md) has the full rubric.

| Part | Points | Summary |
|---|---|---|
| Tiers solved | 40 | Tiers 1 to 10 are worth 1, 2, 2, 3, 4, 4, 5, 6, 6, 7. Full points need a matching hash and a circuit run during `solve()`. |
| Simplicity | 15 | Simpler circuits score higher, compared with other teams on each tier. |
| Presentation | 25 | Why each approach works, circuit design, clarity and delivery. |
| Analysis | 20 | Classical versus quantum cost, scaling limits, and hardware or noise. |

Brute force finds these keys instantly at these sizes, so the circuit is what is scored.

Check your own numbers at any time:

```bash
python tools/check_submission.py submissions/<team> --metrics-only
```

The scored circuit is the largest one your `solve()` actually runs, not the one `build_circuit()` returns. Simplicity is relative to other teams, so it is final only after the deadline.

A matching hash means the recovered text has the same SHA-256 fingerprint as the expected plaintext. It checks the answer; your measurement evidence and explanation establish how your circuit recovered it. See [the helper reference](HELPERS.md#checking-an-answer).

**Tie-breaker:** if two totals are within 0.01, the team whose final submission has the earliest time wins. A resubmission moves your time later. Time is used only for ties and earns no points.

## Presentation

For each tier you attempted, cover:

- What the file hid, and how you worked out which approach fits.
- Why that approach works.
- The circuit diagram with qubit and gate counts.
- The measurement result and how you extracted the key.
- The classical cost.

For unfinished tiers, give one slide on your attempt and where it got stuck. End with a scaling slide: what changes between these toy sizes and real key sizes, and what hardware would be needed.

## Rules

The full rules are in [CHALLENGE.md](CHALLENGE.md). The short version:

- Do not share keys or answers across teams.
- Do not edit `hashes.txt` or anything under `tools/`.
- A tier needs a quantum circuit run in `solve()` to earn full credit.
- Libraries and Qiskit's built-in circuits are allowed if you can explain every block.

## Resources

- [references/](references/README.md): papers and notes.
- [Qiskit documentation](https://docs.quantum.ibm.com/)

## Getting help

Ask in our Discord server: https://discord.gg/4jE3w3Pjn. Mentors are available Tuesdays and Thursdays anytime after 3:30 PM, Wednesdays and Fridays anytime after 1:35 PM, and 7 to 9 AM any day by request. For anything else, write to nelakurti.2@osu.edu.

## Teams and dates

Teams have 3 to 5 members. The event runs November 6 to 13, 2026.
