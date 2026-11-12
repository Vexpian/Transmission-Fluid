"""Check dependencies, supplied circuit loading, and Aer without solving a tier.

Run from the repo root: python tools/check_setup.py
"""
import importlib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent


def main():
    sys.path.insert(0, str(REPO_ROOT))
    required = {}
    for line in (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        if "==" in line:
            name, pinned = line.strip().split("==", 1)
            if name in ("qiskit", "qiskit-aer"):
                required[name] = pinned

    problems = []
    for name, pinned in required.items():
        try:
            installed = version(name)
        except PackageNotFoundError:
            problems.append(f"{name} is not installed; expected {pinned}")
            continue
        if installed != pinned:
            problems.append(f"{name} is {installed}; expected {pinned}")
        else:
            print(f"PASS: {name} {installed}")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        print("Use your challenge environment and run: python -m pip install -r requirements.txt")
        return 1

    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator

        # Loading checks QPY compatibility; it does not inspect oracle gates.
        supplied = [
            ("tier01.helper", "build_oracle", (), 25),
            *[("tier03.helper", "build_oracle", (i,), 7) for i in range(24)],
            ("tier04.helper", "build_oracle", (), 20),
            ("tier07.helper", "build_unitary", (), 1),
            ("tier07.helper", "build_eigenstate", (), 1),
        ]
        for module, function, args, qubits in supplied:
            circuit = getattr(importlib.import_module(module), function)(*args)
            if circuit.num_qubits != qubits:
                raise ValueError(f"{module}.{function}{args}: expected {qubits} qubits")
        # Import the remaining public interfaces without receiving hidden states.
        for module in ("common", "common.toy_cipher", "tier02.helper", "tier05.helper", "tier06.helper"):
            importlib.import_module(module)
        print(f"PASS: loaded all {len(supplied)} supplied circuits and helper modules")

        circuit = QuantumCircuit(1, 1)
        circuit.h(0)
        circuit.measure(0, 0)
        simulator = AerSimulator()
        result = simulator.run(transpile(circuit, simulator), shots=8, seed_simulator=12345).result()
        if not result.success or sum(result.get_counts().values()) != 8:
            raise RuntimeError("Aer did not return eight successful measurements")
        print("PASS: Aer simulation")
    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}")
        print("Check that your files are intact and your Python/Jupyter environment uses requirements.txt.")
        return 1

    print("Setup is ready. No tier keys or plaintexts were recovered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
