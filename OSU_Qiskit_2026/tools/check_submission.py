#!/usr/bin/env python
"""Check one team's submission, in two steps per tier.

  python tools/check_submission.py submissions/<team>
         [--metrics-only] [--sha <commit>] [--submitted-at <iso>] [--out <dir>]

Step 1, correctness: run solve() under a time limit and compare the hash.
Step 2, simplicity: every circuit solve() sent to Aer is recorded and
transpiled with scoring_config.yaml. The one with the most two-qubit gates
(ties broken by depth) is the scored circuit. build_circuit() is not scored.

solve() and transpiling each run in a subprocess, so a slow one can be killed.
"""
import argparse
import hashlib
import importlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "tools" / "scoring_config.yaml"
TIERS = range(1, 11)
METRICS = ("two_qubit_gates", "depth", "total_gates", "active_qubits")
NOT_GATES = {"measure", "reset", "barrier", "delay"}
# Time allowed for imports, on top of solve_timeout_s.
STARTUP_GRACE_S = 60


def load_config():
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# Worker side: runs team code.


def strip_simulator_instructions(circuit):
    """Remove Aer save_* style instructions, which are not gates."""
    clean = circuit.copy_empty_like()
    for instruction in circuit.data:
        name = instruction.operation.name
        if name.startswith("save_") or name.startswith("set_"):
            continue
        clean.append(instruction)
    return clean


def install_recorder(recorded):
    """Patch every Aer entry point to record the circuits it receives."""
    from qiskit import QuantumCircuit
    from qiskit_aer import primitives
    from qiskit_aer.backends.aerbackend import AerBackend

    def record(value):
        if isinstance(value, QuantumCircuit):
            recorded.append(value.copy())
        elif isinstance(value, (list, tuple)):
            for item in value:
                record(item)
        elif hasattr(value, "circuit"):
            record(value.circuit)

    def wrap(owner):
        original = owner.run

        def run(self, circuits, *args, **kwargs):
            record(circuits)
            return original(self, circuits, *args, **kwargs)

        owner.run = run

    wrap(AerBackend)
    for name in ("Sampler", "SamplerV2", "Estimator", "EstimatorV2"):
        owner = getattr(primitives, name, None)
        if owner is not None:
            wrap(owner)


def load_solution(path):
    spec = importlib.util.spec_from_file_location("team_solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def channel_log():
    """Return tier 2's measurement log, however the team imported the helper."""
    logs = []
    for module in list(sys.modules.values()):
        channel = getattr(module, "Channel", None)
        log = getattr(channel, "log", None)
        if isinstance(log, list) and not any(log is other for other in logs):
            logs.append(log)
    return [entry for log in logs for entry in log]


def oracle_calls(tier, module):
    """Report oracle calls in build_circuit() for tiers with a call limit."""
    folders = {1: "tier01", 3: "tier03"}
    if tier not in folders or not hasattr(module, "build_circuit"):
        return None
    try:
        helper = importlib.import_module(f"{folders[tier]}.helper")
        return helper.count_oracle_calls(module.build_circuit())
    except Exception:
        return None


def worker_solve(tier, solution_path, out_prefix):
    """Run solve() and write its outcome and the recorded circuits."""
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(Path(solution_path).parent))
    os.chdir(REPO_ROOT)
    from qiskit import qpy

    from common import hash_line

    recorded = []
    install_recorder(recorded)
    outcome = {"answer_hash": None, "error": None, "not_implemented": False}
    module = None
    started = time.perf_counter()
    try:
        module = load_solution(solution_path)
        answer = module.solve()
        if isinstance(answer, str):
            outcome["answer_hash"] = hash_line(answer.rstrip("\r\n"))
        else:
            outcome["error"] = "solve() did not return a string"
    except NotImplementedError:
        outcome["not_implemented"] = True
    except BaseException as error:
        outcome["error"] = f"{type(error).__name__}: {error}"[:300]
    outcome["solve_seconds"] = round(time.perf_counter() - started, 3)

    if tier == 2:
        log = channel_log()
        circuits = [entry[2] for entry in log]
        seen = {}
        for link, index, _ in log:
            seen[(link, index)] = seen.get((link, index), 0) + 1
        outcome["repeat_measurements"] = sum(1 for n in seen.values() if n > 1)
    else:
        circuits = [strip_simulator_instructions(c) for c in recorded]

    outcome["circuits_executed"] = len(circuits)
    unique = {}
    for circuit in circuits:
        circuit.metadata = {}
        circuit.name = "scored"
        buffer = io.BytesIO()
        try:
            qpy.dump(circuit, buffer)
        except Exception as error:
            outcome["serialize_error"] = f"{type(error).__name__}: {error}"[:300]
            continue
        data = buffer.getvalue()
        unique[hashlib.sha256(data).digest()] = data
    outcome["unique_circuits"] = len(unique)
    outcome["oracle_calls"] = oracle_calls(tier, module) if module else None

    blob = Path(out_prefix + ".circuits")
    with open(blob, "wb") as handle:
        handle.write(json.dumps([len(d) for d in unique.values()]).encode("ascii") + b"\n")
        for data in unique.values():
            handle.write(data)
    Path(out_prefix + ".json").write_text(json.dumps(outcome), encoding="utf-8")


def compute_metrics(circuit):
    """Count gates after transpiling. Measurements and barriers are not gates.

    Gates inside control flow count too, once per block and once per loop
    round of a for_loop.
    """
    from qiskit.circuit import ControlFlowOp, ForLoopOp

    levels = {}
    tally = {"two_qubit_gates": 0, "total_gates": 0}

    def walk(block, wire_ids):
        for instruction in block.data:
            ids = [wire_ids[block.find_bit(q).index] for q in instruction.qubits]
            operation = instruction.operation
            if isinstance(operation, ControlFlowOp):
                rounds = len(operation.params[0]) if isinstance(operation, ForLoopOp) else 1
                for _ in range(rounds):
                    for inner in operation.blocks:
                        walk(inner, ids)
            elif operation.name not in NOT_GATES:
                level = max(levels.get(i, 0) for i in ids) + 1
                for i in ids:
                    levels[i] = level
                tally["total_gates"] += 1
                if len(ids) == 2:
                    tally["two_qubit_gates"] += 1

    walk(circuit, list(range(circuit.num_qubits)))
    return {
        "two_qubit_gates": tally["two_qubit_gates"],
        "depth": max(levels.values(), default=0),
        "total_gates": tally["total_gates"],
        "active_qubits": len(levels),
    }


def worker_transpile(circuits_path, out_path):
    """Transpile each recorded circuit and write the scored circuit's metrics."""
    from qiskit import qpy, transpile

    config = load_config()
    with open(circuits_path, "rb") as handle:
        sizes = json.loads(handle.readline())
        blobs = [handle.read(size) for size in sizes]
    started = time.perf_counter()
    best = None
    for data in blobs:
        circuit = qpy.load(io.BytesIO(data))[0]
        compiled = transpile(
            circuit,
            basis_gates=config["basis_gates"],
            coupling_map=config["coupling_map"],
            initial_layout=config["initial_layout"],
            optimization_level=config["optimization_level"],
            seed_transpiler=config["seed_transpiler"],
        )
        metrics = compute_metrics(compiled)
        rank = (metrics["two_qubit_gates"], metrics["depth"])
        if best is None or rank > (best["two_qubit_gates"], best["depth"]):
            best = metrics
    elapsed = time.perf_counter() - started
    Path(out_path).write_text(json.dumps({"metrics": best, "seconds": elapsed}), encoding="utf-8")


# Parent side: orchestrates the workers.


def run_worker(arguments, timeout):
    environment = dict(os.environ, PYTHONHASHSEED="0", QISKIT_PARALLEL="FALSE")
    try:
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), *arguments],
            timeout=timeout, capture_output=True, env=environment, cwd=REPO_ROOT,
        )
    except subprocess.TimeoutExpired:
        return "timeout"
    return "ok" if completed.returncode == 0 else "failed"


def check_tier(tier, solution_path, config, expected_hash, metrics_only):
    entry = {
        "status": "not_attempted", "hash_ok": None, "circuit_executed": False,
        "metrics": None, "metrics_status": "no metrics", "flags": [],
    }
    with tempfile.TemporaryDirectory() as folder:
        prefix = str(Path(folder) / f"tier{tier:02d}")
        limit = config["solve_timeout_s"]
        state = run_worker(["--_solve", str(tier), str(solution_path), prefix], limit + STARTUP_GRACE_S)
        outcome_path = Path(prefix + ".json")
        if state != "ok" or not outcome_path.exists():
            entry["status"] = "timeout" if state == "timeout" else "error"
            return entry
        outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
        if outcome["not_implemented"] and not outcome["circuits_executed"]:
            return entry

        for name in ("solve_seconds", "circuits_executed", "unique_circuits", "oracle_calls", "repeat_measurements"):
            if name in outcome:
                entry[name] = outcome[name]
        if outcome["error"]:
            entry["error"] = outcome["error"]
        entry["circuit_executed"] = outcome["circuits_executed"] > 0
        over_time = outcome["solve_seconds"] > limit
        if over_time:
            entry["flags"].append("solve() went over solve_timeout_s")

        if metrics_only:
            entry["status"] = "metrics_only"
        else:
            entry["hash_ok"] = outcome["answer_hash"] == expected_hash and not over_time
            if entry["hash_ok"]:
                entry["status"] = "full" if entry["circuit_executed"] else "no_circuit"
            else:
                entry["status"] = "circuit_only" if entry["circuit_executed"] else "incorrect"

        if outcome.get("serialize_error"):
            entry["metrics_status"] = "no metrics: a circuit could not be serialized"
        elif outcome["unique_circuits"]:
            metrics_path = prefix + ".metrics.json"
            arguments = ["--_transpile", prefix + ".circuits", metrics_path]
            state = run_worker(arguments, config["transpile_timeout_s"] + STARTUP_GRACE_S)
            result = None
            if state == "ok" and Path(metrics_path).exists():
                result = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
                if result["seconds"] > config["transpile_timeout_s"]:
                    state, result = "timeout", None
            if result:
                entry["metrics"] = result["metrics"]
                entry["metrics_status"] = "ok"
            else:
                reason = "transpile timed out" if state == "timeout" else "transpile failed"
                entry["metrics_status"] = f"no metrics: {reason}"

    if entry["metrics"]:
        minimum = config["review_min_active_qubits"][tier]
        if entry["metrics"]["active_qubits"] < minimum:
            entry["flags"].append(f"scored circuit has under {minimum} active qubits")
    if entry.get("oracle_calls") not in (None, 1):
        entry["flags"].append("build_circuit() does not show exactly one oracle call")
    if entry.get("repeat_measurements"):
        entry["flags"].append("some qubits were measured more than once")
    return entry


def write_reports(report, out_dir):
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# Report for {report['team']}", "",
        f"- Commit: {report['sha'] or 'not given'}",
        f"- Submitted at: {report['submitted_at'] or 'not given'}",
        f"- Mode: {report['mode']}", "",
        "| Tier | Status | Hash | Circuit run | 2Q gates | Depth | Gates | Active qubits | Metrics | Flags |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for tier, entry in report["tiers"].items():
        metrics = entry["metrics"] or {}
        cells = [metrics.get(name, "-") for name in METRICS]
        hash_cell = {True: "match", False: "no match", None: "-"}[entry["hash_ok"]]
        run_cell = "yes" if entry["circuit_executed"] else "no"
        row = [tier, entry["status"], hash_cell, run_cell, *cells, entry["metrics_status"], "; ".join(entry["flags"]) or "-"]
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    text = "\n".join(lines) + "\n"
    (out_dir / "report.md").write_text(text, encoding="utf-8")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("team_dir", nargs="?", help="path such as submissions/<team>")
    parser.add_argument("--metrics-only", action="store_true", help="skip the hash check")
    parser.add_argument("--sha", help="commit being checked")
    parser.add_argument("--submitted-at", help="submission time, ISO 8601")
    parser.add_argument("--out", help="folder for report.md and report.json, default team_dir")
    parser.add_argument("--_solve", nargs=3, help=argparse.SUPPRESS)
    parser.add_argument("--_transpile", nargs=2, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args._solve:
        worker_solve(int(args._solve[0]), args._solve[1], args._solve[2])
        return
    if args._transpile:
        worker_transpile(*args._transpile)
        return
    if not args.team_dir:
        parser.error("give a team folder, such as submissions/my_team")

    team_dir = Path(args.team_dir).resolve()
    if not team_dir.is_dir():
        parser.error(f"no such folder: {args.team_dir}")
    sys.path.insert(0, str(REPO_ROOT))
    import qiskit
    import qiskit_aer

    from common import load_hashes

    config = load_config()
    hashes = load_hashes()
    report = {
        "team": team_dir.name,
        "sha": args.sha,
        "submitted_at": args.submitted_at,
        "mode": "metrics-only" if args.metrics_only else "full",
        "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__,
        "config_sha256": file_hash(CONFIG_PATH),
        "hashes_sha256": file_hash(REPO_ROOT / "hashes.txt"),
        "tiers": {},
    }
    for tier in TIERS:
        solution = team_dir / f"tier{tier:02d}" / "solution.py"
        if not solution.exists():
            continue
        print(f"Checking tier {tier}...", flush=True)
        report["tiers"][str(tier)] = check_tier(tier, solution, config, hashes[tier], args.metrics_only)

    out_dir = Path(args.out).resolve() if args.out else team_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    print(write_reports(report, out_dir))


if __name__ == "__main__":
    main()
