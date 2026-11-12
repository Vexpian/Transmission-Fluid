"""Load tier data and compare a decrypted line with hashes.txt."""
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def tier_dir(tier):
    """Return the folder of a tier, given its number."""
    folder = REPO_ROOT / f"tier{tier:02d}"
    if not folder.is_dir():
        raise FileNotFoundError(f"could not find the folder for tier {tier}")
    return folder


def load_locked(tier):
    """Return the parsed locked.json of a tier."""
    return json.loads((tier_dir(tier) / "locked.json").read_text(encoding="utf-8"))


def load_hashes():
    """Return {tier number: expected SHA-256 hex digest} from hashes.txt."""
    hashes = {}
    for line in (REPO_ROOT / "hashes.txt").read_text(encoding="utf-8").splitlines():
        name, digest = line.split()
        hashes[int(name.removeprefix("tier"))] = digest
    return hashes


def hash_line(text):
    """Return the SHA-256 hex digest of a decrypted line."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_correct(tier, text):
    """Return True when text is the plaintext of the tier."""
    if not isinstance(text, str):
        return False
    return hash_line(text.rstrip("\r\n")) == load_hashes()[tier]


def check(tier, text):
    """Print a clear PASS or FAIL for a decrypted line and return the result."""
    if text is None:
        print(f"FAIL: tier {tier} has no answer yet. Set `plaintext` first.")
        return False
    if isinstance(text, (bytes, bytearray)):
        text = bytes(text).decode("utf-8", errors="replace")
    if is_correct(tier, text):
        print(f"PASS: tier {tier} hash matches. Well done.")
        return True
    print(f"FAIL: tier {tier} hash does not match. Check your key and bit order.")
    return False
