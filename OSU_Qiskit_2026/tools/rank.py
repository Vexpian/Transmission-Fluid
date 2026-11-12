#!/usr/bin/env python
"""Combine team reports into the final ranking (organizers).

  python tools/rank.py reports/ --log submissions_log.csv
         [--judging judging.csv] [--partial partial.csv] [--out ranking.json]

--log       team, submitted_at, from the submission form. Other columns, such
            as the uploaded zip's link, are ignored. The latest row per team
            is that team's final submission.
--judging   team, presentation_why, presentation_circuit, presentation_clarity,
            analysis_cost, analysis_hardware. Points from the judges.
--partial   team, tier, fraction. A judge's decision on a tier: up to 0.5 for a
            working circuit that did not recover the key, or a lower fraction
            for a flagged tier. It replaces the automatic fraction.

reports/, the log, and the judging files stay with organizers. They are not
committed to the public repo.
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "tools" / "scoring_config.yaml"
METRICS = ("two_qubit_gates", "depth", "total_gates", "active_qubits")
TIE_MARGIN = 0.01
JUDGING_LIMITS = {
    "presentation_why": 10,
    "presentation_circuit": 8,
    "presentation_clarity": 7,
    "analysis_cost": 12,
    "analysis_hardware": 8,
}
AUTOMATIC_FRACTION = {"full": 1.0, "no_circuit": 0.25}


def parse_time(text):
    moment = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def load_reports(folder):
    reports = {}
    for path in sorted(Path(folder).rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "team" in data and "tiers" in data:
            reports[data["team"]] = data
    return reports


def load_log(path):
    """Return {team: latest log row}. A later row replaces an earlier one."""
    latest = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row["time"] = parse_time(row["submitted_at"])
            if row["team"] not in latest or row["time"] >= latest[row["team"]]["time"]:
                latest[row["team"]] = row
    return latest


def load_judging(path):
    if not path:
        return {}
    with open(path, newline="", encoding="utf-8") as handle:
        return {row["team"]: row for row in csv.DictReader(handle)}


def load_partial(path):
    if not path:
        return {}
    with open(path, newline="", encoding="utf-8") as handle:
        return {(row["team"], int(row["tier"])): float(row["fraction"]) for row in csv.DictReader(handle)}


def metric_ratio(best, value):
    if best == 0:
        return 1.0 if value == 0 else 1.0 / (1 + value)
    return best / value


def tier_fractions(team, report, partial, tiers):
    fractions = {}
    for tier in tiers:
        entry = report["tiers"].get(str(tier), {})
        fraction = AUTOMATIC_FRACTION.get(entry.get("status"), 0.0)
        fractions[tier] = partial.get((team, tier), fraction)
    return fractions


def score_teams(reports, log, judging, partial, config):
    """Return one result dict per team in the log, unsorted."""
    tiers = sorted(config["tier_points"])
    weights = config["weights"]
    teams = sorted(set(reports) & set(log))
    fractions = {team: tier_fractions(team, reports[team], partial, tiers) for team in teams}

    results = {}
    for team in teams:
        row = judging.get(team, {})
        human = {
            name: min(float(row.get(name) or 0), limit)
            for name, limit in JUDGING_LIMITS.items()
        }
        results[team] = {
            "team": team,
            "submitted_at": log[team]["submitted_at"],
            "time": log[team]["time"],
            "tier_points": {},
            "simplicity": {},
            "human": human,
            "warnings": [],
        }
        if reports[team].get("sha") and reports[team]["sha"] != log[team]["commit_sha"]:
            results[team]["warnings"].append("report sha differs from the latest log row")

    for tier in tiers:
        points = config["tier_points"][tier]
        pool = config["simplicity_share"] * points
        eligible = {}
        for team in teams:
            results[team]["tier_points"][tier] = points * fractions[team][tier]
            results[team]["simplicity"][tier] = 0.0
            metrics = reports[team]["tiers"].get(str(tier), {}).get("metrics")
            if fractions[team][tier] >= 1.0 and metrics:
                eligible[team] = metrics
        if not eligible:
            continue
        best = {m: min(metrics[m] for metrics in eligible.values()) for m in METRICS}
        for team, metrics in eligible.items():
            share = sum(weights[m] * metric_ratio(best[m], metrics[m]) for m in METRICS)
            results[team]["simplicity"][tier] = pool * share

    for result in results.values():
        result["tiers_total"] = sum(result["tier_points"].values())
        result["simplicity_total"] = sum(result["simplicity"].values())
        result["human_total"] = sum(result["human"].values())
        result["total"] = result["tiers_total"] + result["simplicity_total"] + result["human_total"]
    return list(results.values())


def rank_results(results):
    """Sort by total. Teams within TIE_MARGIN of each other go by earliest time."""
    ordered = sorted(results, key=lambda r: (-r["total"], r["team"]))
    final = []
    while ordered:
        anchor = ordered[0]["total"]
        group = [r for r in ordered if anchor - r["total"] <= TIE_MARGIN + 1e-9]
        ordered = ordered[len(group):]
        final.extend(sorted(group, key=lambda r: (r["time"], r["team"])))
    place = 0
    previous = None
    for index, result in enumerate(final, start=1):
        shared = (
            previous is not None
            and abs(previous["total"] - result["total"]) <= TIE_MARGIN + 1e-9
            and previous["time"] == result["time"]
        )
        place = place if shared else index
        result["place"] = place
        previous = result
    return final


def print_ranking(final):
    print("| Place | Team | Total | Tiers | Simplicity | Presentation + Analysis | Final submission |")
    print("|---|---|---|---|---|---|---|")
    for r in final:
        print(
            f"| {r['place']} | {r['team']} | {r['total']:.2f} | {r['tiers_total']:.2f} "
            f"| {r['simplicity_total']:.2f} | {r['human_total']:.2f} | {r['submitted_at']} |"
        )
    for r in final:
        print(f"\n{r['team']}")
        for tier in sorted(r["tier_points"]):
            print(f"  tier {tier:2d}: points {r['tier_points'][tier]:.2f}, simplicity {r['simplicity'][tier]:.3f}")
        for name, value in r["human"].items():
            print(f"  {name}: {value:.2f}")
        for warning in r["warnings"]:
            print(f"  WARNING: {warning}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("reports", help="folder of team report.json files")
    parser.add_argument("--log", required=True, help="submissions_log.csv")
    parser.add_argument("--judging", help="judges' presentation and analysis points")
    parser.add_argument("--partial", help="judges' decisions on partial credit")
    parser.add_argument("--out", help="also write the ranking to this JSON file")
    args = parser.parse_args()

    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    reports = load_reports(args.reports)
    log = load_log(args.log)
    for team in sorted(set(reports) - set(log)):
        print(f"WARNING: {team} has a report but no log row, so it is not ranked", file=sys.stderr)
    for team in sorted(set(log) - set(reports)):
        print(f"WARNING: {team} has a log row but no report, so it is not ranked", file=sys.stderr)

    final = rank_results(score_teams(reports, log, load_judging(args.judging), load_partial(args.partial), config))
    print_ranking(final)
    if args.out:
        rows = [{key: value for key, value in r.items() if key != "time"} for r in final]
        Path(args.out).write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
