"""Tier 2 solution for your team.

The checker runs this file from the repo root. Keep these imports; they work
there, while the notebook's `import helper` does not.
"""
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from common import load_locked, xor_bytes
from tier02 import helper


def build_circuit():
    """Return your main circuit. Used for diagrams only, never for scoring."""
    qlist = list()
    blist = list()

    for i in range(1024):
        qc = QuantumCircuit(1, 1)
        if (random.randint(0,1))==1:
            qc.h(0)
            blist.append(1)
        else:
            blist.append(0)
        qc.measure([0], [0])
        qlist.append(qc)

    channel =  helper.Channel("link_A")

    mb = channel.receive_all(qlist)
    mf = channel.finish()
    print(mb)
    print(mf)

    ab = mf['alice_bases']
    cb = mf['check_bits']
    kb = {}

    for j in range(1024):
        if blist[j] == ab[j]:
            if j in cb:
                if mb[j] != cb[j]:
                    print("No match")
            else:
                kb[j] = mb[j]

    print(kb)

    rr = mf['reconcile']
    bk = helper.reconcile(kb, rr)
    print(bk)
    raise NotImplementedError


def solve():
    """Run your circuit on Aer and return the decrypted line as a string."""
    key = bk  # the bytes returned by helper.reconcile

    plaintext = None
    if key is not None:
        plaintext = xor_bytes(ciphertext, key).decode("utf-8", errors="replace")

    check(2, plaintext)
    print(plaintext)
    raise NotImplementedError
