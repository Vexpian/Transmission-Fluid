# Helper reference

These files provide public interfaces, not completed solutions. This reference describes their inputs, outputs, and constraints without naming the algorithms needed for the tiers. Read each tier's README for the exact key format and rules.

In submitted `solution.py` files, import from the repo root, for example `from common import load_locked` and `from tier01 import helper`. Starter notebooks use their own local import setup.

## Shared helpers

### `common/__init__.py`

Makes the shared helpers available through `from common import ...`. It re-exports the data-loading, answer-checking, keystream, and XOR functions below. The toy cipher is imported separately from `common.toy_cipher` or through the tier-5/6 helpers.

### `common/check.py`

Loads public challenge data and checks recovered answers:

| Name | Purpose |
|---|---|
| `REPO_ROOT` | Absolute path of this challenge checkout. |
| `tier_dir(tier)` | Returns the `Path` for a tier number; raises an error if that folder is missing. |
| `load_locked(tier)` | Returns that tier's `locked.json` as a dictionary, including `public_parameters` and `ciphertext_hex`. |
| `load_hashes()` | Returns `{tier_number: expected_SHA256_hex_digest}` from `hashes.txt`. |
| `hash_line(text)` | Returns the SHA-256 hex digest of the string's UTF-8 bytes, without trimming it. |
| `is_correct(tier, text)` | Returns a boolean for a string answer, ignoring trailing carriage returns/newlines. Other whitespace remains significant. Non-string input returns `False`. |
| `check(tier, text)` | Prints PASS/FAIL and returns a boolean. Also accepts bytes, which it decodes, or `None` for an unfinished answer. |

### Checking an answer

A hash is a digital fingerprint of text. The checker computes SHA-256 of your decrypted line and compares it with the published fingerprint. A matching hash checks that the plaintext is correct; it does not establish that your circuit found the key. Keep the required prefix, punctuation, spaces, and capitalization. Do not edit `hashes.txt`.

For a recovered string, use `check(tier_number, plaintext)`. You do not need to calculate or compare hashes yourself.

### `common/crypto.py`

Applies the public masking schemes after you have recovered a key:

| Function | Purpose |
|---|---|
| `keystream(key_bits, n_bytes)` | Expands a nonempty string of binary digits into exactly `n_bytes` bytes using SHA-256 with a four-byte counter. Preserve leading zeros and use the key width/order specified by the tier. It does not recover the key. |
| `xor_bytes(data, stream)` | XORs two equal-length byte strings; raises `ValueError` for unequal lengths. |
| `xor_repeating(data, key)` | XORs each data byte with a repeating, nonempty byte key. Used by tier 1. |

Convert a ciphertext with `bytes.fromhex(locked["ciphertext_hex"])`. These functions return bytes; decode the decrypted bytes to return a string from `solve()`.

### `common/toy_cipher.py`

Defines the public classical byte cipher for tiers 5 and 6 and the gate descriptions needed to construct your own reversible check. It contains no completed quantum oracle.

| Name | Purpose |
|---|---|
| `ToyCipher(key, key_bits)` | Creates a classical cipher for an integer key of the given width. `encrypt(data)` / `decrypt(data)` process bytes; `encrypt_byte(p, i)` / `decrypt_byte(c, i)` process byte position `i`, starting at zero. |
| `mask(k, i, key_bits)` | Computes the byte mask for a key and byte position, including key rotation and the round constant. |
| `mask_gates(key_bits)` | Returns CX/CCX tuples describing how to XOR the position-zero mask into eight data wires. Indices for key wires and data wires refer to separate registers. You turn these tuples into gates. |
| `SBOX_GATES` | Ordered X/CX/CCX tuples defining a reversible four-bit substitution. Apply to each nibble separately. |
| `SBOX` | The corresponding classical 16-entry substitution table. |
| `PERM` | Bit-position mapping: input bit `j` moves to `PERM[j]`. |
| `ROUND_CONSTANT` | Public constant used for position-dependent masks. |
| `rotate_left(k, r, key_bits)` | Rotates an integer within the specified key width. |
| `permute(value)` / `inverse_permute(value)` | Applies or reverses the byte's public bit permutation. |
| `sbox_layer(value)` / `inverse_sbox_layer(value)` | Applies or reverses substitution on both nibbles of a byte. |

`_apply_sbox_gates` is an internal utility that constructs the classical table. Bit `j` of a key or byte has value `2**j`. For nonzero byte positions, follow the tier README's key rotation and round-constant instructions; `mask_gates` alone describes position zero.

## Tier helpers

### `tier01/helper.py`

- `build_oracle()` loads `oracle.qpy` as a 25-qubit circuit. Qubits 0–23 hold the input and qubit 24 is the target. The oracle XORs the hidden parity into that target.
- `count_oracle_calls(circuit)` recursively counts named oracle applications. Call it before transpiling/decomposing; the tier requires exactly one application.
- `ORACLE_NAME` identifies that block; `HERE` locates the tier folder. Neither is a key.

Use the supplied oracle as a block. Do not inspect its gates to extract the hidden string. Transpile your completed circuit for Aer before executing it.

### `tier02/helper.py`

Provides the simulated links and public information reconciliation:

| Interface | Purpose |
|---|---|
| `LINKS` | The supported link names. |
| `Channel(name)` | Creates your receiver for one link. Use one instance per link in the final solution. |
| `channel.n_qubits` | Number of incoming qubits for which you must supply measurement circuits. |
| `channel.receive_all(circuits)` | Takes one 1-qubit/1-classical-bit circuit per incoming index, performs the measurements on Aer, and returns a list of measured bits. Can be called once per link. |
| `channel.finish()` | After reception, closes the channel and returns `alice_bases`, `check_bits`, and `reconcile` data. Choose your bases before calling it. |
| `reconcile(key_bits_by_index, reconcile_data)` | Solves the public binary equations using your sifted, non-check bits; returns the shared key as bytes. The first argument maps original qubit indices to your measured bits. Raises an error if there are too few independent equations. |
| `Channel.log` | Shared record of measurement circuits used by the checker. Do not clear or edit it. |

Select the clean link using the public check positions, then exclude those positions from reconciliation. Noisy input bits can produce the wrong key; the routine is not a guarantee that any chosen link or input is valid. This reconciliation mechanism is specific to the exercise, not a complete production key-distribution protocol.

`_load_link`, `_row`, and the channel's underscore-prefixed fields are implementation details. In particular, do not call `_load_link`, open `channels.dat`, or read private state to obtain hidden preparations. Recreating a channel to measure a link twice violates the tier rules.

### `tier03/helper.py`

- `build_oracle(i)` loads oracle `i`, from 0 through 23, as a seven-qubit circuit. Qubits 0–5 are inputs; qubit 6 is the target.
- `count_oracle_calls(circuit)` counts named oracle applications recursively. Each oracle's circuit must contain one application, checked before transpilation.
- `ORACLE_NAME` and `HERE` identify the block and tier folder.

Keep oracle index order when forming the key. Do not determine the oracle's class by inspecting gates or simulating its matrix. Transpile the circuit for Aer.

### `tier04/helper.py`

`build_oracle()` loads the 20-qubit `oracle.qpy`. Qubits 0–9 are inputs and 10–19 are the output register, which must start in zero. It computes the promised function on that initialized output register; do not assume arbitrary target initialization is supported. `HERE` locates its data file.

It supplies neither the recovery circuit nor a binary linear-equation solver. Recover the hidden repeat from measurements, without reading the oracle's gates. Transpile for Aer before running.

### `tier05/helper.py`

Re-exports `ToyCipher`, `SBOX`, `SBOX_GATES`, `PERM`, `ROUND_CONSTANT`, and `mask_gates` from `common/toy_cipher.py`, and sets `KEY_BITS = 10`. These have the same meanings as in the shared-helper table. It also sets up the repo import path for the notebook.

You build the reversible oracle yourself. The first two known bytes must both be checked, as specified by the tier README. The classical cipher can check measured candidates and decrypt the final message.

### `tier06/helper.py`

Re-exports the same cipher tools as tier 5, sets `KEY_BITS = 14`, and adds `checksum(data)`, which returns `sum(data) % 256` for plaintext bytes. It also sets up the repo import path for the notebook.

Build the oracle using only the first known byte. Use the checksum to filter measured candidates after decrypting their messages. This byte sum is an exercise filter, not a cryptographic authentication mechanism.

### `tier07/helper.py`

- `build_unitary()` loads the supplied one-qubit `unitary.qpy` circuit. Its global phase matters when making a controlled version.
- `build_eigenstate()` loads the one-qubit `eigenstate.qpy` preparation circuit.
- `HERE` locates those files.

You supply the controlled operations and readout circuit. The tier permits using the unitary matrix to construct powers, but not classically extracting its eigenvalues as the solution.

### Tiers 8–10

No tier-specific helper is supplied. Use the public parameters in `locked.json` and the shared loading, keystream, XOR, and answer-checking functions. Construct the required quantum operations yourself within the tier rules.

## Supporting files and tools

| File | Purpose |
|---|---|
| `tierNN/locked.json` | Public parameters and ciphertext, not executable helper code. |
| Supplied `.qpy` files | Serialized circuits loaded by the tier helpers. Treat hidden oracles as blocks under the tier's inspection rules. |
| `tier02/channels.dat` | Hidden channel data accessed only through the supported `Channel` interface. |
| `hashes.txt` | Expected plaintext fingerprints used for answer checks. |
| `tierNN/starter.ipynb` | Notebook scaffold for your circuit, key extraction, and answer check. |
| `submissions/TEAM_TEMPLATE/tierNN/solution.py` | Submission scaffold: implement `solve()` for execution and `build_circuit()` for diagrams. |
| `tools/check_setup.py` | Checks pinned quantum-library versions, loads supplied circuits, and runs a small Aer smoke test without solving tiers. |
| `tools/check_submission.py` | Runs submitted solutions, checks plaintext hashes, records executed circuits, and writes resource reports. `--metrics-only` skips answer verification. |
| `tools/scoring_config.yaml` | Official basis gates, compilation settings, time limits, weights, tier points, and advisory review thresholds. |
| `tools/rank.py` | Organizer tool that combines checker reports, submission timestamps, and judging decisions into rankings. |

Students should not edit the scoring tools, configuration, or expected hashes. See [SCORING.md](SCORING.md) for what the checker measures and what judges review.
