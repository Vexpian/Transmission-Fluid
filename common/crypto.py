"""Keystream and XOR helpers shared by every tier."""
import hashlib


def keystream(key_bits, n_bytes):
    """Return n_bytes derived from key_bits with SHA-256 in counter mode.

    key_bits is a string of '0' and '1', written most significant bit first.
    Each tier README says exactly how to write its key as this string.
    """
    if not key_bits or set(key_bits) - {"0", "1"}:
        raise ValueError("key_bits must be a non-empty string of 0s and 1s")
    out = b""
    counter = 0
    while len(out) < n_bytes:
        block = key_bits.encode("ascii") + counter.to_bytes(4, "big")
        out += hashlib.sha256(block).digest()
        counter += 1
    return out[:n_bytes]


def xor_bytes(data, stream):
    """XOR two byte strings of equal length."""
    if len(data) != len(stream):
        raise ValueError("xor_bytes needs two inputs of equal length")
    return bytes(a ^ b for a, b in zip(data, stream))


def xor_repeating(data, key):
    """XOR data with key repeated to the length of data (used by tier 1)."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
