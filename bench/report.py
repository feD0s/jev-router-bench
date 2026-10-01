"""Regenerate reports from saved evidence. No network and no LLM judge."""
import csv
import html
import json
from collections import defaultdict
from pathlib import Path
from .core import ROUTES, read_json, write_json
from .metrics import evaluate, paired_comparison


def csv_write(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items() if k in fields})


def confusion_svg(path, matrix, label):
    columns = (*ROUTES, "error", "not_run")
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="680" height="300" role="img">',
           '<rect width="680" height="300" fill="#f8fafc"/>',
           f'<text x="20" y="30" font-family="sans-serif" font-size="17">{html.escape(label)}</text>',
           '<text x="20" y="55" font-family="sans-serif" font-size="12">Rows: expected · columns: actual · saved evidence</text>']
    maximum = max((v for row in matrix.values() for v in row.values()), default=1) or 1
    for j, col in enumerate(columns):
        svg.append(f'<text x="{140+j*100}" y="90" font-family="sans-serif" font-size="13">{col}</text>')
    for i, row in enumerate(ROUTES):
        y = 110+i*58
        svg.append(f'<text x="20" y="{y+32}" font-family="sans-serif" font-size="14">{row}</text>')
        for j, col in enumerate(columns):
            value, x = matrix[row][col], 128+j*100
            opacity = 0.08+0.7*value/maximum
            svg.append(f'<rect x="{x}" y="{y}" width="94" height="50" rx="5" fill="#38bdf8" opacity="{opacity}"/>')
            svg.append(f'<text x="{x+40}" y="{y+32}" font-family="sans-serif" font-size="18">{value}</text>')
    svg.append('</svg>')
    path.write_text('\n'.join(svg), encoding="utf-8")


def generate_report(directory):
    directory = Path(directory)
    manifest, cases = read_json(directory / "manifest.json"), read_json(directory / "cases.json")
    attempts = [json.loads(x) for x in (directory / "attempts.jsonl").read_text().splitlines()]
    providers = ("keyword",) if manifest["mode"] == "offline-keyword-control" else ("jev", "gpt")
    indexed = defaultdict(list)
    for a in attempts:
        if a["provider"] not in providers or a["id"] not in {c["id"] for c in cases} or not 1 <= a["run"] <= manifest["runs"]:
            raise ValueError("Attempt does not match manifest/cases")
        indexed[(a["run"], a["provider"], a["id"])].append(a)
    groups, aggregates, flat = {}, {}, []
    for run in range(1, manifest["runs"]+1):
        aggregates[str(run)] = {}
        for provider in providers:
            rows = []
            for case in cases:
                trial = indexed[(run, provider, case["id"])]
                trial.sort(key=lambda a: a["attempt"])
                if len({a["attempt"] for a in trial}) != len(trial):
                    raise ValueError("Duplicate attempt")
                last = trial[-1] if trial else {}
                row = dict(case, run=run, provider=provider, attempts=trial,
                           actual_route=last.get("actual_route"), decision_wall_ms=last.get("decision_wall_ms"))
                rows.append(row)
                flat.append({**row, "attempt_count": len(trial), "error_kind": last.get("error_kind")})
            groups[(run, provider)] = rows
            metrics = evaluate(rows)
            metrics["by_difficulty"] = {bucket: evaluate([r for r in rows if r["tags"][0] == bucket])
                                       for bucket in sorted({r["tags"][0] for r in rows})}
            aggregates[str(run)][provider] = metrics
            confusion_svg(directory / f"confusion-run{run}-{provider}.svg", metrics["confusion_matrix"],
                          f"{manifest['mode']} · run {run} · {provider}")
    pairs = {str(r): paired_comparison(groups[(r, "jev")], groups[(r, "gpt")])
             for r in range(1, manifest["runs"]+1)} if "jev" in providers else {}
    output = {"schema_version": 1, "mode": manifest["mode"], "split": manifest["split"],
              "unique_tasks": len(cases), "repeats_are_not_independent_tasks": True,
              "runs": aggregates, "paired": pairs}
    write_json(directory / "aggregates.json", output)
    csv_write(directory / "decisions.csv", flat, ["run", "provider", "id", "message", "context", "expected_route",
              "actual_route", "rationale", "tags", "attempt_count", "error_kind", "decision_wall_ms"])
    summary_rows = [{"run": r, "provider": p, **m} for r, providers_data in aggregates.items() for p, m in providers_data.items()]
    csv_write(directory / "aggregates.csv", summary_rows, ["run", "provider", "n_tasks", "correct", "accuracy", "macro_f1",
              "operator_fraction", "wrong_automation_count", "unsafe_automation_count", "attempt_count",
              "failed_decisions", "not_run_count", "cost_usage_usd", "cost_upper_accounted_usd", "cost_complete"])
    errors = [{"run": r, "provider": p, **e} for r, ps in aggregates.items() for p, m in ps.items() for e in m["errors"]]
    csv_write(directory / "errors.csv", errors, ["run", "provider", "id", "message", "context", "expected_route", "actual_route", "rationale", "tags"])
    csv_write(directory / "disagreements.csv", [{"run": r, **x} for r, data in pairs.items() for x in data["disagreements"]],
              ["run", "id", "message", "context", "expected_route", "jev_route", "gpt_route", "rationale", "tags"])
    lines = ["# Results summary", "", f"Mode: **{manifest['mode']}**. Split: `{manifest['split']}`. Status: `{manifest['status']}`.",
             f"Date (UTC): {manifest['started_at_utc']}. Unique tasks: {len(cases)}. Runs: {manifest['runs']}.", "",
             "Offline control contains no Jev/GPT measurements." if "keyword" in providers else "Router only; no executor timing/cost. Standard live requests, one outstanding request.", "",
             f"Source commit: {manifest['git'].get('commit_url') or 'not committed'}; dirty: {manifest['git']['dirty']}.",
             "Exact prompts, config, shop, hashes and environment are in manifest.json; cases in cases.json; every attempt in attempts.jsonl.", "",
             "| Run | Provider | Correct / tasks | Accuracy | Macro-F1 | Operator share | Unsafe automation | Cost from usage, USD | Conservative accounted upper, USD |",
             "|---|---|---|---|---|---|---|---|---|"]
    for row in summary_rows:
        lines.append(f"| {row['run']} | {row['provider']} | {row['correct']}/{row['n_tasks']} | {row['accuracy']:.3f} | {row['macro_f1']:.3f} | {row['operator_fraction']:.3f} | {row['unsafe_automation_count']} | {row['cost_usage_usd']:.6f} | {row['cost_upper_accounted_usd']:.6f} |")
    lines += ["", "## Latency and uncertainty", "",
              ("Offline timing measures only the local keyword function. No HTTP, model inference, or comparison with Jev/GPT latency." if "keyword" in providers else
               "Wall-clock includes full response, parsing/validation and local HTTP worker startup/cleanup. End-to-end decision time also includes retry backoff. p95 uses nearest rank; the tail is unstable on 100 observations."),
              "95% Wilson intervals describe binomial sampling uncertainty only; synthetic selection/AI label bias is not captured. Repeated runs reuse the same tasks, so do not pool them as a larger independent sample.", ""]
    for row in summary_rows:
        m = aggregates[row["run"]][row["provider"]]
        lines.append(f"- Run {row['run']} {row['provider']}: Wilson 95% {m['accuracy_wilson_95']}; valid attempts {m['latency_valid_attempts']}; all attempts {m['latency_all_attempts']}; decisions with retries {m['latency_decisions_with_retries']}.")
    lines += ["", "## Cost method", "",
              "USD = uncached input × input rate + cached input × cached rate + reported cache-write tokens × write rate + all output × output rate (rates per million). Reasoning is already included in output; never bill twice. Jev bills only input.",
              "Unknown-usage errors retain the pre-request reservation; retries are included. Unreported GPT cache writes yield a cost range using the write premium on uncached input for the upper bound. These are calculations, not a provider invoice. Null cache/reasoning fields mean unreported, not measured zero.", "",
              "## Original error examples", ""]
    for e in errors:
        lines += [f"- Run {e['run']} {e['provider']} `{e['id']}`: {json.dumps(e['message'], ensure_ascii=False)} — expected `{e['expected_route']}`, actual `{e['actual_route']}`. Rule: {e['rationale']}",
                  f"  Context: `{json.dumps(e['context'], ensure_ascii=False)}`"]
    if not errors:
        lines.append("No route errors in this saved series. This does not establish general superiority.")
    lines += ["", "## Paired disagreements", "", "All disagreements, original messages and contexts: disagreements.csv and aggregates.json.",
              json.dumps(pairs, ensure_ascii=False, indent=2) if pairs else "Not applicable to the offline control.", "",
              "## Reproduce", "", "From the repository root (replace the path with this saved directory):", "",
              "```sh", f"python3 -m bench report --dir {directory.as_posix()}", "```", "",
              "A public synthetic holdout can enter training/context of future agents. Do not use final errors for tuning this version. No real customer traffic, human label agreement, multi-language results or production conclusions. Owner's personal conclusions remain pending review."]
    (directory / "results-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output
