"""Helpers for tier 1."""
from pathlib import Path

from qiskit import qpy

HERE = Path(__file__).resolve().parent
ORACLE_NAME = "tier1_oracle"


def build_oracle():
    """Return the oracle as a 25-qubit circuit.

    Qubits 0..23 hold x and qubit 24 is the target. The oracle maps
    |x>|t> to |x>|t XOR (s.x mod 2)>. Run `transpile(circuit, simulator)`
    before `simulator.run`, because Aer does not know this gate by name.
    """
    with open(HERE / "oracle.qpy", "rb") as handle:
        return qpy.load(handle)[0]


def count_oracle_calls(circuit):
    """Count how many times the oracle appears in a circuit.

    Call this on your circuit before transpiling or decomposing it. The
    tier rule is that this must return 1.
    """
    total = 0
    for instruction in circuit.data:
        operation = instruction.operation
        if operation.name == ORACLE_NAME:
            total += 1
        elif operation.definition is not None:
            total += count_oracle_calls(operation.definition)
    return total
