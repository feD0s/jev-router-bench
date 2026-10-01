"""Sequential paired experiment with explicit attempts and conservative spending."""
import json
import math
import os
import platform
import random
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from .adapters import request_body, parse_route, usage_and_cost, reservation_usd, SchemaError
from .core import ROOT, check_freeze, hashes, inputs, load_cases, read_json, write_json
from .transport import post_json, redact


def load_env(path):
    """Read only the two keys from this project's .env; never execute it."""
    keys = {}
    if not path.is_file():
        raise ValueError("Create local .env with both API keys first")
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, value = line.partition("=")
        if sep and name in ("OPENAI_API_KEY", "TYPESAFE_API_KEY"):
            keys[name] = value.strip().strip("\"'")
    if not all(keys.get(n) for n in ("OPENAI_API_KEY", "TYPESAFE_API_KEY")):
        raise ValueError("Both local .env API keys are required")
    return keys


def git_state():
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
        return {"commit": head, "dirty": dirty, "commit_url": f"https://github.com/feD0s/jev-router-bench/commit/{head}"}
    except subprocess.CalledProcessError:
        return {"commit": None, "dirty": True, "commit_url": None}


def pair_schedule(cases, cfg, repeats):
    shuffled = list(cases)
    random.Random(cfg["measurement"]["seed"]).shuffle(shuffled)
    for repeat in range(1, repeats+1):
        for index, case in enumerate(shuffled):
            order = ("jev", "gpt") if (index+repeat-1) % 2 == 0 else ("gpt", "jev")
            yield repeat, index, case, order


class Limits:
    def __init__(self, spend, max_requests, seconds):
        if not math.isfinite(spend) or spend <= 0:
            raise ValueError("Spend limit must be finite and positive")
        self.limit, self.max_requests = spend, max_requests
        self.accounted, self.requests = 0.0, 0
        self.deadline = time.monotonic() + seconds

    def reserve(self, amount):
        if time.monotonic() >= self.deadline:
            raise ValueError("Series deadline reached")
        if self.requests >= self.max_requests:
            raise ValueError("Request limit reached")
        if self.accounted + amount > self.limit + 1e-12:
            raise ValueError("Spend limit reached before next request")
        self.accounted += amount
        self.requests += 1

    def settle(self, reserved, known_upper):
        if known_upper is not None:
            self.accounted += known_upper - reserved
        if self.accounted > self.limit + 1e-12:
            raise ValueError("Usage exceeded conservative reservation; stop and reconcile billing")


def keyword_route(case):
    """Intentionally simple local control, not a semantic oracle."""
    msg = case["message"].lower()
    if any(s in msg for s in ("оператор", "человек", "менеджер", "отмен", "верните", "измените", "обмен", "списали")):
        return "operator"
    if any(s in msg for s in ("где", "статус", "состояни", "доставлен", "отправ")):
        numbers = set(re.findall(r"(?<!\d)\d{5}(?!\d)", msg))
        selected = next(iter(numbers)) if len(numbers) == 1 else case["context"]["selected_order_id"] if not numbers else None
        return "status" if selected in case["context"]["known_order_ids"] else "operator"
    return "answer"


def prepare_run(out, split, mode, repeats, cfg, prompt, shop):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    manifest = {"schema_version": 1, "mode": mode, "split": split, "runs": repeats,
                "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "python": platform.python_version(), "platform": platform.system(),
                "git": git_state(), "sha256": hashes(), "config": cfg,
                "prompt": prompt, "shop": shop, "status": "running",
                "client_region": "not_measured", "provider_region": "not_reported"}
    write_json(out / "manifest.json", manifest)
    write_json(out / "cases.json", load_cases(split))
    return out, manifest


def save_attempt(handle, record):
    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    handle.flush()
    os.fsync(handle.fileno())


def dry_run(split, out):
    check_freeze()
    cfg, prompt, shop = inputs()
    out, manifest = prepare_run(out, split, "offline-keyword-control", 1, cfg, prompt, shop)
    cases = load_cases(split)
    with (out / "attempts.jsonl").open("x") as log, (out / "requests-preview.jsonl").open("x") as previews:
        for case in cases:
            for provider in ("jev", "gpt"):
                previews.write(json.dumps({"id": case["id"], "provider": provider,
                    "request": request_body(provider, case, cfg, prompt, shop)}, ensure_ascii=False) + "\n")
            start = time.perf_counter()
            route = keyword_route(case)
            wall = (time.perf_counter()-start)*1000
            save_attempt(log, {"id": case["id"], "run": 1, "provider": "keyword", "attempt": 1,
                "actual_route": route, "wall_ms": wall, "decision_wall_ms": wall, "error_kind": None,
                "usage": {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0,
                    "cache_write_tokens": 0, "reasoning_tokens": 0, "cost_usd": 0.0,
                    "cost_upper_usd": 0.0, "cost_method": "offline_no_api"},
                "accounted_usd": 0.0, "raw_response": None})
    manifest.update(status="complete", finished_at_utc=datetime.now(timezone.utc).isoformat(), paid_requests=0)
    write_json(out / "manifest.json", manifest)
    return out


def live_run(split, out, repeats, approved_spend, max_requests=None, transport=post_json):
    frozen = check_freeze()
    review = read_json(ROOT / "data/owner-review.json")
    if review.get("approved") is not True or review.get("sha256") != frozen["sha256"] or not review.get("reviewer"):
        raise ValueError("Owner must review business rules and labels before live evaluation")
    cfg, prompt, shop = inputs()
    if not 1 <= repeats <= cfg["measurement"]["max_runs"]:
        raise ValueError("Runs must be 1–3")
    state = git_state()
    if state["dirty"] or not state["commit"]:
        raise ValueError("Commit the reviewed inputs/code before live evaluation")
    keys = load_env(ROOT / ".env")
    m = cfg["measurement"]
    cases = load_cases(split)
    planned_attempt_cap = len(cases) * len(cfg["providers"]) * repeats * m["max_attempts"]
    request_limit = min(planned_attempt_cap, m["max_requests"])
    if max_requests is not None:
        request_limit = min(max_requests, request_limit)
    if type(request_limit) is not int or request_limit <= 0:
        raise ValueError("Invalid request limit")
    limits = Limits(approved_spend, request_limit, m["series_timeout_s"])
    # Validate all envelopes before a single paid request.
    for case in cases:
        for provider in ("jev", "gpt"):
            body = request_body(provider, case, cfg, prompt, shop)
            if len(json.dumps(body, ensure_ascii=False).encode()) + 4096 > m["input_token_ceiling"]:
                raise ValueError("Request exceeds conservative input reservation")
    out, manifest = prepare_run(out, split, "paired-live", repeats, cfg, prompt, shop)
    manifest["approval"] = {"spend_limit_usd": approved_spend, "max_requests": request_limit, "owner_review": review}
    write_json(out / "manifest.json", manifest)
    stop = None
    with (out / "attempts.jsonl").open("x") as log:
        try:
            for repeat, index, case, order in pair_schedule(cases, cfg, repeats):
                for position, provider in enumerate(order):
                    body = request_body(provider, case, cfg, prompt, shop)
                    p = cfg["providers"][provider]
                    decision_start = time.perf_counter()
                    for attempt in range(1, m["max_attempts"]+1):
                        reserved = reservation_usd(provider, cfg)
                        limits.reserve(reserved)
                        key = keys["TYPESAFE_API_KEY" if provider == "jev" else "OPENAI_API_KEY"]
                        start = time.perf_counter()
                        timeout = min(m["request_timeout_s"], max(0.001, limits.deadline-time.monotonic()))
                        try:
                            result = transport(p["endpoint"], body, key, timeout, tuple(keys.values()))
                        except Exception as exc:
                            result = {"status": None, "raw_response": None, "error": type(exc).__name__}
                        raw = result["raw_response"]
                        usage = usage_and_cost(provider, raw, p)
                        route, error, error_detail = None, None, None
                        if result.get("error") or result.get("status") is None:
                            error, error_detail = "transport", result.get("error")
                        elif result["status"] != 200:
                            error, error_detail = "http", str(result["status"])
                        else:
                            try:
                                route = parse_route(provider, raw, p["model"])
                            except SchemaError as exc:
                                error, error_detail = "schema", str(exc)
                        record = {"id": case["id"], "run": repeat, "provider": provider,
                            "pair_index": index, "pair_position": position, "attempt": attempt,
                            "request": body, "raw_response": raw, "response_model": raw.get("model") if isinstance(raw, dict) else None,
                            "http_status": result.get("status"), "request_id": result.get("request_id"),
                            "actual_route": route, "error_kind": error, "error_detail": error_detail,
                            "usage": usage, "accounted_usd": usage["cost_upper_usd"] if usage else reserved,
                            "cost_unknown": usage is None,
                            "wall_ms": (time.perf_counter()-start)*1000,
                            "decision_wall_ms": (time.perf_counter()-decision_start)*1000}
                        save_attempt(log, redact(record, tuple(keys.values())))
                        limits.settle(reserved, usage["cost_upper_usd"] if usage else None)
                        if error is None:
                            break
                        # A lost response may be billed. Stop, retain reservation, no blind retry.
                        if error == "transport":
                            raise ValueError("Transport failed with unknown billing; reconcile before another run")
                        if error == "schema" and isinstance(raw, dict) and raw.get("model") != p["model"]:
                            raise ValueError("Unexpected model version; no silent substitution")
                        if result.get("status") in (401, 403, 404, 422):
                            raise ValueError("Provider access/configuration failed; no model substitution")
                        if result.get("status") not in (429, 500, 502, 503, 504, 529):
                            break
                        if attempt < m["max_attempts"]:
                            retry = result.get("retry_after")
                            try:
                                delay = max(m["retry_backoff_s"] * 2**(attempt-1), float(retry or 0))
                            except ValueError:
                                delay = m["retry_backoff_s"] * 2**(attempt-1)
                            if not math.isfinite(delay) or delay > 60 or time.monotonic()+delay >= limits.deadline:
                                raise ValueError("Retry wait exceeds series limits")
                            time.sleep(delay)
                    time.sleep(m["spacing_s"])
        except (ValueError, KeyboardInterrupt) as exc:
            stop = str(exc) or "Interrupted"
        except Exception as exc:
            stop = "Unexpected local failure: " + type(exc).__name__
        finally:
            manifest.update(status="stopped" if stop else "complete", stop_reason=stop,
                finished_at_utc=datetime.now(timezone.utc).isoformat(), paid_requests=limits.requests,
                accounted_upper_usd=limits.accounted)
            write_json(out / "manifest.json", redact(manifest, tuple(keys.values())))
    return out
