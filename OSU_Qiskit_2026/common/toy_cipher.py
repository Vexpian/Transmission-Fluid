"""The toy byte cipher used by tiers 5 and 6.

Decrypting byte number i with key k has three steps:

  1. XOR the ciphertext byte with mask(k, i).
  2. Apply the 4-bit S-box to the low nibble and to the high nibble.
  3. Apply the fixed bit permutation PERM.

Bit j of a byte means the bit of value 2**j. Key bit j likewise means 2**j.

mask(k, i) rotates the w-bit key left by 3*i bits, then for each mask bit j
computes

    m[j] = k[j] XOR (k[j + 8 ...]) XOR (k[(j + 1) mod w] AND k[(j + 3) mod w])

and finally XORs ROUND_CONSTANT * i mod 256. The middle term applies only to
keys wider than 8 bits, and uses key bit 8 + (j mod (w - 8)).

SBOX_GATES and mask_gates() give the same steps as gate lists, so they can be
turned into a circuit.
"""

# In-place reversible gates on nibble bits 0..3. Applying them defines SBOX.
SBOX_GATES = [
    ("ccx", 0, 1, 2),
    ("cx", 2, 3),
    ("ccx", 3, 2, 0),
    ("x", 1),
    ("cx", 0, 1),
    ("ccx", 1, 0, 3),
]

# PERM[j] is where bit j moves to.
PERM = [3, 6, 0, 5, 1, 7, 2, 4]
ROUND_CONSTANT = 0x1D


def _apply_sbox_gates(value):
    bits = [(value >> j) & 1 for j in range(4)]
    for gate in SBOX_GATES:
        if gate[0] == "x":
            bits[gate[1]] ^= 1
        elif gate[0] == "cx":
            bits[gate[2]] ^= bits[gate[1]]
        else:
            bits[gate[3]] ^= bits[gate[1]] & bits[gate[2]]
    return sum(b << j for j, b in enumerate(bits))


SBOX = [_apply_sbox_gates(v) for v in range(16)]


def mask_gates(key_bits):
    """Gate list that XORs mask(k, 0) into data bits 0..7 from key qubits.

    Each entry is ("cx", key_bit, data_bit) or ("ccx", key_a, key_b, data_bit).
    """
    gates = []
    for j in range(8):
        gates.append(("cx", j, j))
        if key_bits > 8:
            gates.append(("cx", 8 + j % (key_bits - 8), j))
        gates.append(("ccx", (j + 1) % key_bits, (j + 3) % key_bits, j))
    return gates


def rotate_left(k, r, key_bits):
    """Rotate a key_bits wide integer left by r bits."""
    r %= key_bits
    full = (1 << key_bits) - 1
    return ((k << r) | (k >> (key_bits - r))) & full


def mask(k, i, key_bits):
    """Return the 8-bit mask for byte number i."""
    rotated = rotate_left(k, 3 * i, key_bits)
    bit = lambda n: (rotated >> n) & 1
    value = [0] * 8
    for gate in mask_gates(key_bits):
        if gate[0] == "cx":
            value[gate[2]] ^= bit(gate[1])
        else:
            value[gate[3]] ^= bit(gate[1]) & bit(gate[2])
    m = sum(b << j for j, b in enumerate(value))
    return m ^ ((ROUND_CONSTANT * i) % 256)


def permute(value):
    """Apply the bit permutation PERM to a byte."""
    return sum(((value >> j) & 1) << PERM[j] for j in range(8))


def inverse_permute(value):
    """Undo permute."""
    return sum(((value >> PERM[j]) & 1) << j for j in range(8))


def sbox_layer(value):
    """Apply SBOX to both nibbles of a byte."""
    return SBOX[value & 15] | (SBOX[value >> 4] << 4)


def inverse_sbox_layer(value):
    """Undo sbox_layer."""
    return SBOX.index(value & 15) | (SBOX.index(value >> 4) << 4)


class ToyCipher:
    """Byte cipher with a key of key_bits bits."""

    def __init__(self, key, key_bits):
        self.key = key
        self.key_bits = key_bits

    def decrypt_byte(self, c, i):
        return permute(sbox_layer(c ^ mask(self.key, i, self.key_bits)))

    def encrypt_byte(self, p, i):
        return inverse_sbox_layer(inverse_permute(p)) ^ mask(self.key, i, self.key_bits)

    def decrypt(self, data):
        return bytes(self.decrypt_byte(c, i) for i, c in enumerate(data))

    def encrypt(self, data):
        return bytes(self.encrypt_byte(p, i) for i, p in enumerate(data))
