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
        expected = inp*p["input_per_million_usd"]/1e6*repeats if provider == "jev" else None
        estimates[provider] = {"request_count_no_retries": len(cases)*repeats,
            "serialized_utf8_bytes": sum(sizes), "heuristic_input_tokens": inp*repeats,
            "heuristic_expected_usd": expected,
            "conservative_one_attempt_per_task_usd": reservation_usd(provider, cfg)*len(cases)*repeats,
            "all_tasks_max_attempts_usd": reservation_usd(provider, cfg)*len(cases)*repeats*cfg["measurement"]["max_attempts"],
            "largest_envelope_bytes_plus_overhead": max(sizes)+4096}
    scenarios = []
    for output_per_request in (256, 1024, 4096, 16384):
        gpt = cfg["providers"]["gpt"]
        cost = (estimates["gpt"]["heuristic_input_tokens"] * gpt["input_per_million_usd"]
                + len(cases)*repeats*output_per_request*gpt["output_per_million_usd"])/1e6
        scenarios.append({"assumed_gpt_total_output_tokens_per_request": output_per_request,
                          "combined_heuristic_cost_usd": cost+estimates["jev"]["heuristic_expected_usd"]})
    return {"status": "planning_only_no_paid_requests", "split": split, "runs": repeats,
        "model": cfg["providers"]["gpt"]["model"],
        "reasoning_effort": cfg["providers"]["gpt"]["reasoning_effort"],
        "custom_max_output_tokens": None,
        "documented_model_max_output_tokens": cfg["providers"]["gpt"]["model_max_output_tokens"],
        "prices_verified_on": cfg["pricing_verified_on"], "sources": cfg["pricing_sources"], "providers": estimates,
        "heuristic_total_usd": None, "medium_output_scenarios": scenarios,
        "conservative_no_retries_usd": sum(x["conservative_one_attempt_per_task_usd"] for x in estimates.values()),
        "conservative_all_retries_usd": sum(x["all_tasks_max_attempts_usd"] for x in estimates.values()),
        "approved_shared_limit_usd": 10.0,
        "note": "Owner approved $10 total and requested simpler defaults. No custom output cap or split quotas. Medium usage is unknown: scenarios are illustrations, not a prediction. Reservations use the published model maximum only for accounting, not as a request setting; settled actual usage is normally lower. No paid requests yet. Old none-mode $0.04 estimate does not apply."}
