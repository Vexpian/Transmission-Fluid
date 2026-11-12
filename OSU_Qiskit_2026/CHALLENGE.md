
## The story

Someone has locked ten files, and each lock gives way to a different quantum algorithm. The labels on the files say how each one is encoded, but not which algorithm opens it. Working that out is part of the challenge, and each tier README has two optional hints. Each file holds one line, and the ten lines in order form a final message.

Your team's job is to open as many as you can, and then to stand up and explain how you did it.

## The ten tiers

Every plaintext is one line starting `QC-NN: `, where NN is the tier. Tier 1 masks its line with a repeating XOR. Tiers 3, 4, and 7 to 10 use `keystream(key_bits, n_bytes)` from `common/`, a SHA-256 counter-mode stream, so short keys can mask a message of any length. Tier 2 uses a key rebuilt from qubits sent over a quantum link, and tiers 5 and 6 use a toy byte cipher.

| Tier | Level | What you do |
|---|---|---|
| 1. The Parity Vault | Warm-up | Recover a hidden 24-bit string with one oracle call. |
| 2. Two Links | Easy | Spot the tapped link among two and rebuild the key from the clean one. |
| 3. Twenty-Four Seals | Easy | Sort 24 oracles into constant and balanced, one call each. |
| 4. The Echo | Medium | Find the hidden XOR repeat of a 2-to-1 function on 10 bits. |
| 5. The Small Safe | Medium | Build a toy cipher as a reversible oracle and find its 10-bit key. |
| 6. The Bigger Safe | Medium to hard | Find a 14-bit key when many keys pass, then filter with a checksum. |
| 7. The Hidden Angle | Hard | Read a 14-bit angle out of a one-qubit gate. |
| 8. The Wrapped Key, N = 35 | Hard | Factor an RSA modulus and unwrap the key. |
| 9. The Wrapped Key, N = 77 | Very hard | The same with N = 77 and harder modular arithmetic. |
| 10. The Handshake | Boss | Recover a Diffie-Hellman exponent and rebuild the shared secret. |

Each tier folder has the exact rules, what is provided, and what is not.

## What you deliver

1. Your `submissions/<team_name>/` folder with a `solution.py` per tier.
2. A write-up, `WRITEUP.md`, with a section per tier and a scaling section.
3. A short presentation.

## Presentation

For each tier attempted:

- What the file hid, and how you worked out which approach fits.
- Why that approach works.
- The circuit diagram with qubit and gate counts.
- The measurement result and how the key was extracted.
- The classical cost.

For unfinished tiers, give one slide on the attempt and where it got stuck. End with a scaling slide: what changes between these toy sizes and real key sizes, and what hardware would be needed.

## Rules

1. No sharing keys or answers across teams.
2. Do not edit `hashes.txt` or anything under `tools/`.
3. A tier needs a quantum circuit executed in `solve()` to earn credit. A matching answer with no circuit earns 25% of the tier.
4. Classical post-processing of measurement results is fine.
5. Libraries and Qiskit's built-in circuits are allowed if your team explains every block.
6. These keys are small on purpose, and the tier data is simple to pick apart by inspection. Reading a key out of an oracle's gates or `channels.dat`, or running a circuit that plays no part in finding the key, is against the spirit of the challenge. Judges can reduce a tier's credit for it.
7. Hardware is optional.
8. Team size: 3 to 5 people.
