"""Native request envelopes, strict route parsers, usage and prices."""
import json
import math
from .core import ROUTES, semantic_input


class SchemaError(ValueError):
    pass


def request_body(provider, case, cfg, prompt, shop):
    p = cfg["providers"][provider]
    state = semantic_input(case, shop)
    if provider == "jev":
        return {"model": p["model"], "state": state, "questions": {
            "route": {"type": "choice", "instructions": prompt, "criteria": cfg["criteria"]}}}
    return {"model": p["model"], "store": False, "service_tier": "default",
            "reasoning": {"effort": p["reasoning_effort"]},
            "input": [{"role": "system", "content": prompt + "\n" + json.dumps(cfg["criteria"], ensure_ascii=False)},
                      {"role": "user", "content": json.dumps(state, ensure_ascii=False)}],
            "text": {"format": {"type": "json_schema", "name": "route", "strict": True,
                "schema": {"type": "object", "properties": {"route": {"type": "string", "enum": list(ROUTES)}},
                           "required": ["route"], "additionalProperties": False}}}}


def unit_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and 0 <= value <= 1


def parse_route(provider, raw, requested_model):
    try:
        if not isinstance(raw, dict) or raw["model"] != requested_model:
            raise SchemaError("Missing or unexpected response model; no substitution")
        if provider == "jev":
            answer = raw["answers"]["route"]
            route = answer["choice"]
            if answer["type"] != "choice" or route not in ROUTES or not unit_number(answer["confidence"]):
                raise SchemaError("Invalid Choice result")
            probs = answer["probabilities"]
            if set(probs) != set(ROUTES) or not all(unit_number(x) for x in probs.values()):
                raise SchemaError("Invalid probability map")
            if abs(sum(probs.values()) - 1) > 0.01 or probs[route] < max(probs.values()):
                raise SchemaError("Invalid Choice distribution")
            return route
        if raw["status"] != "completed":
            raise SchemaError("Incomplete response")
        texts = []
        for item in raw["output"]:
            if item.get("type") != "message":
                continue
            for content in item["content"]:
                if content["type"] == "refusal":
                    raise SchemaError("Model refusal")
                if content["type"] == "output_text":
                    texts.append(content["text"])
        if len(texts) != 1:
            raise SchemaError("Expected exactly one text result")
        answer = json.loads(texts[0])
        if not isinstance(answer, dict) or set(answer) != {"route"} or answer["route"] not in ROUTES:
            raise SchemaError("Expected only route enum")
        return answer["route"]
    except (KeyError, TypeError, ValueError, AttributeError, IndexError) as exc:
        if isinstance(exc, SchemaError):
            raise
        raise SchemaError("Malformed response") from None


def token_count(value):
    if type(value) is not int or value < 0:
        raise SchemaError("Invalid usage count")
    return value


def usage_and_cost(provider, raw, settings):
    try:
        u = raw["usage"]
        inp, out = token_count(u["input_tokens"]), token_count(u["output_tokens"])
        cached = reasoning = cache_write = None
        if provider == "gpt":
            details = u.get("input_tokens_details", {})
            cached = token_count(details.get("cached_tokens", 0))
            # Some APIs expose cache writes; if absent their billing allocation is unknown.
            value = details.get("cache_write_tokens", details.get("cache_creation_tokens"))
            cache_write = token_count(value) if value is not None else None
            reasoning = token_count(u.get("output_tokens_details", {}).get("reasoning_tokens", 0))
            if cached + (cache_write or 0) > inp or reasoning > out:
                raise SchemaError("Inconsistent usage")
        if provider == "jev":
            cost = inp * settings["input_per_million_usd"] / 1e6
            upper = cost
        else:
            uncached = inp - cached - (cache_write or 0)
            cost = (uncached * settings["input_per_million_usd"] + cached * settings["cached_input_per_million_usd"]
                    + (cache_write or 0) * settings["cache_write_per_million_usd"]
                    + out * settings["output_per_million_usd"]) / 1e6
            # If writes are unreported, reserve the premium on all uncached input.
            upper = cost if cache_write is not None else cost + uncached * max(
                0, settings["cache_write_per_million_usd"] - settings["input_per_million_usd"]) / 1e6
        return {"input_tokens": inp, "output_tokens": out, "cached_tokens": cached,
                "cache_write_tokens": cache_write, "reasoning_tokens": reasoning,
                "cost_usd": cost, "cost_upper_usd": upper,
                "cost_method": "usage_x_rates" if upper == cost else "usage_x_rates_cache_write_uncertain"}
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        return None


def reservation_usd(provider, cfg, body=None):
    p = cfg["providers"][provider]
    rate = max(p[f"{key}_per_million_usd"] for key in ("input", "cached_input", "cache_write"))
    # An accounting estimate, not an input/output limit sent to the API.
    input_reserve = len(json.dumps(body, ensure_ascii=False).encode()) + 4096 if body else 16000
    return (input_reserve * rate
            + p.get("model_max_output_tokens", 0) * p["output_per_million_usd"]) / 1e6
