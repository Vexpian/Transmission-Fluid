"""Tier 1 solution for your team.

The checker runs this file from the repo root. Keep these imports; they work
there, while the notebook's `import helper` does not.
"""
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from common import load_locked, xor_repeating
from tier01 import helper


def build_circuit():
    """Return your main circuit. Used for diagrams only, never for scoring."""
    circuit = None

    qreg_q = QuantumRegister(25, 'q')
    creg_c = ClassicalRegister(24, 'c')
    circuit = QuantumCircuit(qreg_q, creg_c)

    circuit.x(qreg_q[24])

    for i in range(24):
        circuit.h(qreg_q[i])

    oracle = helper.build_oracle()
    circuit.append(oracle, range(25))

    for j in range(24):
        circuit.h(qreg_q[j])

    for k in range(24):
        circuit.measure(qreg_q[k], creg_c[k])

    simulator = AerSimulator()
    transpiled_circuit = transpile(circuit, simulator)
    job = simulator.run(transpiled_circuit, shots=1)
    result = job.result()
    counts = result.get_counts()

    measured_bitstring = list(counts.keys())[0]
    s = int(measured_bitstring, 2)
    print(f"Found integer s: {s}")
    raise NotImplementedError


def solve():
    """Run your circuit on Aer and return the decrypted line as a string."""
    s = 13094217  # your hidden string as an integer

    plaintext = None
    if s is not None:
        decrypted = xor_repeating(ciphertext, s.to_bytes(3, "big"))
        plaintext = decrypted.decode("utf-8", errors="replace")

    print(plaintext)
    check(1, plaintext)
    raise NotImplementedError
