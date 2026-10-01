"""Deterministic route evaluation. Repeated runs are reported separately."""
import math
import statistics
from collections import Counter
from .core import ROUTES


def wilson(correct, total):
    if not total:
        return None
    z = 1.959963984540054
    p, d = correct / total, 1 + z*z / total
    center = (p + z*z / (2*total)) / d
    delta = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / d
    return [max(0, center-delta), min(1, center+delta)]


def latency(values):
    if not values:
        return {"n": 0, "median_ms": None, "p95_ms": None, "p95_method": "nearest_rank"}
    values = sorted(values)
    return {"n": len(values), "median_ms": statistics.median(values),
            "p95_ms": values[math.ceil(0.95*len(values))-1], "p95_method": "nearest_rank"}


def evaluate(rows):
    n = len(rows)
    matrix = {r: {p: 0 for p in (*ROUTES, "error", "not_run")} for r in ROUTES}
    correct = automated = wrong_auto = unsafe = operator = 0
    attempts = [a for row in rows for a in row["attempts"]]
    error_counts = Counter(a["error_kind"] for a in attempts if a.get("error_kind"))
    for row in rows:
        expected, actual = row["expected_route"], row["actual_route"]
        column = actual or ("error" if row["attempts"] else "not_run")
        matrix[expected][column] += 1
        correct += actual == expected
        operator += actual == "operator"
        if actual in ("status", "answer"):
            automated += 1
            wrong_auto += actual != expected
            unsafe += expected == "operator"
    per_class = {}
    for r in ROUTES:
        tp = matrix[r][r]
        fp = sum(matrix[x][r] for x in ROUTES if x != r)
        fn = sum(matrix[r][x] for x in matrix[r] if x != r)
        per_class[r] = {"precision": tp / (tp+fp) if tp+fp else 0,
                        "recall": tp / (tp+fn) if tp+fn else 0,
                        "f1": 2*tp / (2*tp+fp+fn) if 2*tp+fp+fn else 0}
    priced = [a for a in attempts if a.get("usage") is not None]
    unknown = [a for a in attempts if a.get("usage") is None]
    return {"n_tasks": n, "correct": correct, "accuracy": correct/n if n else None,
            "accuracy_wilson_95": wilson(correct, n),
            "macro_f1": statistics.mean(x["f1"] for x in per_class.values()),
            "per_class": per_class, "confusion_matrix": matrix,
            "operator_count": operator, "operator_fraction": operator/n if n else None,
            "automation_fraction": automated/n if n else None,
            "wrong_automation_count": wrong_auto,
            "wrong_automation_fraction_of_automated": wrong_auto/automated if automated else None,
            "unsafe_automation_count": unsafe, "unsafe_automation_fraction": unsafe/n if n else None,
            "operator_miss_rate": unsafe/sum(x["expected_route"] == "operator" for x in rows)
                if any(x["expected_route"] == "operator" for x in rows) else None,
            "attempt_errors": dict(error_counts), "attempt_count": len(attempts),
            "failed_decisions": sum(x["actual_route"] is None and bool(x["attempts"]) for x in rows),
            "not_run_count": sum(not x["attempts"] for x in rows),
            "latency_all_attempts": latency([a["wall_ms"] for a in attempts]),
            "latency_valid_attempts": latency([a["wall_ms"] for a in attempts if a["actual_route"]]),
            "latency_decisions_with_retries": latency([r["decision_wall_ms"] for r in rows if r["attempts"]]),
            "usage_totals": {key: sum(a["usage"][key] or 0 for a in priced)
                for key in ("input_tokens", "output_tokens", "cached_tokens", "cache_write_tokens", "reasoning_tokens")},
            "unknown_usage_attempts": len(unknown),
            "cache_write_unknown_attempts": sum(a["usage"]["cache_write_tokens"] is None for a in priced),
            "cost_usage_usd": sum(a["usage"]["cost_usd"] for a in priced),
            "cost_upper_accounted_usd": sum(a["accounted_usd"] for a in attempts),
            "cost_complete": not unknown and all(a["usage"]["cost_usd"] == a["usage"]["cost_upper_usd"] for a in priced),
            "errors": [{"id": r["id"], "message": r["message"], "context": r["context"],
                        "expected_route": r["expected_route"], "actual_route": r["actual_route"],
                        "rationale": r["rationale"], "tags": r["tags"]}
                       for r in rows if r["actual_route"] != r["expected_route"]]}


def paired_comparison(left, right):
    a, b = {r["id"]: r for r in left}, {r["id"]: r for r in right}
    if a.keys() != b.keys():
        raise ValueError("Paired task IDs differ")
    differences, a_only, b_only = [], 0, 0
    for key, x in a.items():
        y = b[key]
        if x["expected_route"] != y["expected_route"]:
            raise ValueError("Paired labels differ")
        ac = x["actual_route"] == x["expected_route"]
        bc = y["actual_route"] == y["expected_route"]
        a_only += ac and not bc
        b_only += bc and not ac
        if x["actual_route"] != y["actual_route"]:
            differences.append({"id": key, "message": x["message"], "context": x["context"],
                "expected_route": x["expected_route"], "jev_route": x["actual_route"],
                "gpt_route": y["actual_route"], "rationale": x["rationale"], "tags": x["tags"]})
    discordant = a_only + b_only
    p = min(1.0, 2*sum(math.comb(discordant, k) for k in range(min(a_only, b_only)+1)) / 2**discordant) if discordant else 1.0
    return {"jev_only_correct": a_only, "gpt_only_correct": b_only,
            "mcnemar_exact_two_sided_p": p, "disagreements": differences,
            "note": "Exploratory paired test on synthetic tasks; no claim of general superiority."}
