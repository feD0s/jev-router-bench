"""Versioned inputs and validation; no network dependencies."""
import hashlib
import json
import math
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ("status", "operator", "answer")
CONFIG = "configs/experiment-v1.json"
FROZEN = (CONFIG, "prompts/router-v1.txt", "data/shop-v1.json",
          "data/dev-v1.jsonl", "data/final-v1.jsonl", "docs/business-rules.md")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hashes():
    return {p: digest(ROOT / p) for p in FROZEN}


def check_freeze():
    frozen = read_json(ROOT / "data/freeze-v1.json")
    if frozen["sha256"] != hashes():
        raise ValueError("Frozen inputs changed. Version them and repeat owner review.")
    return frozen


def load_cases(split):
    if split not in ("dev", "final"):
        raise ValueError("Unknown split")
    return [json.loads(line) for line in (ROOT / f"data/{split}-v1.jsonl").read_text().splitlines()]


def normalized(text):
    return re.sub(r"\W+", " ", re.sub(r"\d+", "#", text.lower())).strip()


def validate_dataset():
    shop = read_json(ROOT / "data/shop-v1.json")
    datasets = {s: load_cases(s) for s in ("dev", "final")}
    ids, messages = set(), set()
    counts = {}
    for split, rows in datasets.items():
        if len(rows) != {"dev": 20, "final": 100}[split]:
            raise ValueError(f"Wrong {split} size")
        for row in rows:
            if set(row) != {"id", "message", "context", "expected_route", "rationale", "tags"}:
                raise ValueError("Dataset schema mismatch")
            if not isinstance(row["id"], str) or row["id"] in ids:
                raise ValueError("Duplicate/invalid id")
            ids.add(row["id"])
            if not isinstance(row["message"], str) or not row["message"].strip():
                raise ValueError("Empty/invalid message")
            if row["message"].strip().lower() in messages:
                raise ValueError("Duplicate message across splits")
            messages.add(row["message"].strip().lower())
            if row["expected_route"] not in ROUTES:
                raise ValueError("Invalid label")
            if not isinstance(row["rationale"], str) or not row["rationale"].strip():
                raise ValueError("Missing rationale")
            if not isinstance(row["tags"], list) or not row["tags"] or any(
                    not isinstance(x, str) or not x for x in row["tags"]):
                raise ValueError("Invalid tags")
            ctx = row["context"]
            if not isinstance(ctx, dict) or set(ctx) != {
                    "known_order_ids", "selected_order_id", "previous_messages"}:
                raise ValueError("Invalid context schema")
            if ctx["known_order_ids"] != list(shop["orders"]):
                raise ValueError("Dataset and shop IDs drifted")
            if ctx["selected_order_id"] is not None and not isinstance(ctx["selected_order_id"], str):
                raise ValueError("Invalid selected_order_id")
            if not isinstance(ctx["previous_messages"], list) or any(
                    not isinstance(x, str) for x in ctx["previous_messages"]):
                raise ValueError("Invalid history")
        counts[split] = dict(Counter(r["expected_route"] for r in rows))
    buckets = Counter(r["tags"][0] for r in datasets["final"])
    if buckets != {"ordinary": 60, "hard": 30, "adversarial": 10}:
        raise ValueError("Final difficulty distribution changed")
    if max(counts["final"].values()) - min(counts["final"].values()) > 1:
        raise ValueError("Final routes not balanced")
    near = []
    for a in datasets["dev"]:
        for b in datasets["final"]:
            score = SequenceMatcher(None, normalized(a["message"]), normalized(b["message"])).ratio()
            if score >= 0.82:
                near.append({"dev": a["id"], "final": b["id"], "similarity": round(score, 3)})
    # A heuristic warning, not a semantic judge or automatic label rewrite.
    return {"counts": counts, "buckets": dict(buckets), "near_duplicate_review": near}


def validate_config(cfg):
    if set(cfg["providers"]) != {"jev", "gpt"}:
        raise ValueError("Exactly two providers required")
    if cfg["providers"]["jev"]["model"] != "jev-1.13.0":
        raise ValueError("Versioned Jev model required; no silent replacement")
    gpt = cfg["providers"]["gpt"]
    if gpt["model"] != "gpt-6-luna" or gpt["reasoning_effort"] != "none":
        raise ValueError("Primary mode is explicitly gpt-6-luna effort=none")
    if type(gpt["max_output_tokens"]) is not int or not 16 <= gpt["max_output_tokens"] <= 128:
        raise ValueError("Output cap must be 16–128")
    endpoints = {"jev": "https://api.typesafe.ai/v1/systemone",
                 "gpt": "https://api.openai.com/v1/responses"}
    for provider, settings in cfg["providers"].items():
        if settings["endpoint"] != endpoints[provider]:
            raise ValueError("Only official provider endpoints permitted")
        for key in ("input", "output", "cached_input", "cache_write"):
            rate = settings[f"{key}_per_million_usd"]
            if isinstance(rate, bool) or not isinstance(rate, (float, int)) or not math.isfinite(rate) or rate < 0:
                raise ValueError("Invalid price")
    m = cfg["measurement"]
    for key in ("max_attempts", "max_requests", "input_token_ceiling", "max_runs"):
        if type(m[key]) is not int or m[key] <= 0:
            raise ValueError(f"Invalid {key}")
    if m["concurrency"] != 1 or m["mode"] != "paired-live" or m["max_runs"] > 3 or m["max_attempts"] > 2:
        raise ValueError("Only serial paired runs, up to 3 repeats and 2 attempts")
    for key in ("request_timeout_s", "series_timeout_s", "spacing_s", "retry_backoff_s"):
        value = m[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid {key}")
    if not 0 < m["request_timeout_s"] <= 60 or not 0 < m["series_timeout_s"] <= 21600:
        raise ValueError("Invalid timeout")
    if set(cfg["criteria"]) != set(ROUTES):
        raise ValueError("Criteria mismatch")
    return cfg


def inputs():
    cfg = validate_config(read_json(ROOT / CONFIG))
    return cfg, (ROOT / cfg["prompt_path"]).read_text(), read_json(ROOT / cfg["shop_path"])


def semantic_input(case, shop):
    return {"message": case["message"], "context": case["context"], "shop": shop}
