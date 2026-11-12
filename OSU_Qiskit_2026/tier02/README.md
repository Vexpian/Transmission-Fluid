# Tier 1: The Parity Vault

**Level:** Warm-up. **Points:** see [SCORING.md](../SCORING.md).

A vault door answers parity questions about a hidden 24-bit string s. Asked classically, it would take 24 questions. You get one.

Working out which quantum method opens this file is part of the tier. The hints at the end are optional.

## How the file is locked

`locked.json` labels it as: repeating XOR, 3-byte key.

Bit j of the integer s is the value on qubit j, so bit j has value 2**j. The three key bytes are `s.to_bytes(3, "big")`. Ciphertext = plaintext XOR those three bytes, repeated. Use `xor_repeating`.

The decrypted line starts with `QC-01: `.

## What is provided

- `locked.json`: `n_bits` and the ciphertext.
- `oracle.qpy`: the oracle for f(x) = s.x mod 2.
- `helper.build_oracle()`: loads the oracle as a 25-qubit circuit. Qubits 0 to 23 hold x and qubit 24 is the target.
- `helper.count_oracle_calls(circuit)`: counts oracle applications.

## What is NOT provided

The value of s, and any circuit other than the oracle itself.

## Rules for this tier

- The oracle may be applied once. `helper.count_oracle_calls(your_circuit)` must return 1. Call it before transpiling.
- Do not read s out of `oracle.qpy` by inspecting its gates.
- A quantum circuit must run on Aer during `solve()` for full credit. See [CHALLENGE.md](../CHALLENGE.md).

## Hints

Open these only if you are stuck. They cost no points.

<details>
<summary>Hint 1: a nudge</summary>

One question is enough only if it asks about every x at once.

</details>

<details>
<summary>Hint 2: a bigger nudge</summary>

Put the target qubit in |-> before the oracle. Then the oracle flips no bit you can see. Instead it gives each x a sign, (-1)^(s.x). Which gates turn a pattern of signs back into the bits of s?

</details>

## Presentation checklist

1. What the file hid, and how you worked out which quantum approach fits.
2. Why that approach works.
3. Circuit diagram with qubit and gate counts.
4. Measurement result and key extraction.
5. Classical cost for comparison.
