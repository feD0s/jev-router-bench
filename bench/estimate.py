"""Planning estimate, not a tokenizer or permission to spend."""
import json
from .adapters import request_body, reservation_usd
from .core import inputs, load_cases


def estimate(split, repeats):
    cfg, prompt, shop = inputs()
    if not 1 <= repeats <= cfg["measurement"]["max_runs"]:
        raise ValueError("Runs must be 1–3")
    cases = load_cases(split)
    estimates = {}
    for provider in ("jev", "gpt"):
        p = cfg["providers"][provider]
        sizes = [len(json.dumps(request_body(provider, c, cfg, prompt, shop), ensure_ascii=False).encode()) for c in cases]
        # Russian text tokenization and envelope overhead differ across providers.
        inp = sum(sizes)/3
        output_tokens = len(cases)*12 if provider == "gpt" else 0
        expected = (inp*p["input_per_million_usd"] + output_tokens*p["output_per_million_usd"])/1e6*repeats
        estimates[provider] = {"request_count_no_retries": len(cases)*repeats,
            "serialized_utf8_bytes": sum(sizes), "heuristic_input_tokens": inp*repeats,
            "heuristic_expected_usd": expected,
            "conservative_one_attempt_per_task_usd": reservation_usd(provider, cfg)*len(cases)*repeats,
            "all_tasks_max_attempts_usd": reservation_usd(provider, cfg)*len(cases)*repeats*cfg["measurement"]["max_attempts"],
            "largest_envelope_bytes_plus_overhead": max(sizes)+4096}
    return {"status": "proposal_only_no_paid_requests", "split": split, "runs": repeats,
        "prices_verified_on": cfg["pricing_verified_on"], "sources": cfg["pricing_sources"], "providers": estimates,
        "heuristic_total_usd": sum(x["heuristic_expected_usd"] for x in estimates.values()),
        "conservative_no_retries_usd": sum(x["conservative_one_attempt_per_task_usd"] for x in estimates.values()),
        "conservative_all_retries_usd": sum(x["all_tasks_max_attempts_usd"] for x in estimates.values()),
        "proposed_limit_usd": 1.0,
        "note": "UTF-8 bytes / 3 is a planning heuristic, not measured token usage. No cache savings assumed; GPT output estimate 12 tokens, cap 32. Conservative reservations use 16000 input tokens and cache-write premium. Repeats multiply the bound; a $1 limit can stop a multi-repeat series. Dev is separately estimated/authorized. This proposal is not spending permission."}
