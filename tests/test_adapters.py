import copy
import json
import unittest
from bench.adapters import SchemaError, parse_route, request_body, usage_and_cost
from bench.core import inputs, load_cases


def jev_response(route="status", usage=None):
    return {"model": "jev-1.13.0", "answers": {"route": {"type": "choice", "choice": route,
            "confidence": 1.0, "probabilities": {r: float(r == route) for r in ("status", "operator", "answer")}}},
            "usage": usage or {"input_tokens": 1000, "output_tokens": 40}}


def gpt_response(route="status", usage=None):
    return {"model": "gpt-6-luna", "status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps({"route": route})}]}],
            "usage": usage or {"input_tokens": 1000, "output_tokens": 20,
                "input_tokens_details": {"cached_tokens": 200, "cache_write_tokens": 100},
                "output_tokens_details": {"reasoning_tokens": 5}}}


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.prompt, self.shop = inputs()

    def test_identical_semantics_without_label_leak(self):
        case = load_cases("dev")[0]
        jev = request_body("jev", case, self.cfg, self.prompt, self.shop)
        gpt = request_body("gpt", case, self.cfg, self.prompt, self.shop)
        self.assertEqual(jev["state"], json.loads(gpt["input"][1]["content"]))
        self.assertEqual(jev["questions"]["route"]["instructions"], self.prompt)
        self.assertEqual(gpt["reasoning"], {"effort": "none"})
        self.assertFalse(gpt["store"])
        for key in ("id", "expected_route", "rationale", "tags"):
            self.assertNotIn(key, jev["state"])
        self.assertTrue(gpt["text"]["format"]["strict"])
        # Adversarial text stays verbatim inside the data envelope.
        attack = load_cases("dev")[-1]
        self.assertEqual(request_body("jev", attack, self.cfg, self.prompt, self.shop)["state"]["message"], attack["message"])

    def test_native_success(self):
        for route in ("status", "operator", "answer"):
            self.assertEqual(parse_route("jev", jev_response(route), "jev-1.13.0"), route)
            self.assertEqual(parse_route("gpt", gpt_response(route), "gpt-6-luna"), route)

    def test_malformed_and_refusal(self):
        malformed = [None, [], {}, {"model": "other"}, {"model": "gpt-6-luna", "status": "completed", "output": ["bad"]}]
        for provider, model in (("jev", "jev-1.13.0"), ("gpt", "gpt-6-luna")):
            for raw in malformed:
                with self.subTest(provider=provider, raw=raw), self.assertRaises(SchemaError):
                    parse_route(provider, raw, model)
        for text in ('{"route":"status","why":"extra"}', '{"route":"bogus"}', 'status', '[]'):
            raw = gpt_response()
            raw["output"][0]["content"][0]["text"] = text
            with self.assertRaises(SchemaError):
                parse_route("gpt", raw, "gpt-6-luna")
        for status in ("incomplete", "failed"):
            raw = gpt_response()
            raw["status"] = status
            with self.assertRaises(SchemaError):
                parse_route("gpt", raw, "gpt-6-luna")
        raw = gpt_response()
        raw["output"][0]["content"] = [{"type": "refusal", "refusal": "No"}]
        with self.assertRaises(SchemaError):
            parse_route("gpt", raw, "gpt-6-luna")

    def test_bad_probabilities(self):
        for probabilities in ({"status": 1}, {"status": float("nan"), "operator": 0, "answer": 0},
                              {"status": 0.1, "operator": 0.8, "answer": 0.1}):
            raw = jev_response()
            raw["answers"]["route"]["probabilities"] = probabilities
            with self.assertRaises(SchemaError):
                parse_route("jev", raw, "jev-1.13.0")

    def test_usage_cost_cache_reasoning_not_double_billed(self):
        u = usage_and_cost("gpt", gpt_response(), self.cfg["providers"]["gpt"])
        # 700 uncached + 200 cached + 100 writes; 20 output INCLUDING 5 reasoning.
        self.assertAlmostEqual(u["cost_usd"], (700*.1 + 200*.01 + 100*.125 + 20*.5)/1e6)
        self.assertEqual(u["cost_usd"], u["cost_upper_usd"])
        self.assertEqual(u["reasoning_tokens"], 5)
        raw = gpt_response()
        del raw["usage"]["input_tokens_details"]["cache_write_tokens"]
        u = usage_and_cost("gpt", raw, self.cfg["providers"]["gpt"])
        self.assertIsNone(u["cache_write_tokens"])
        self.assertGreater(u["cost_upper_usd"], u["cost_usd"])
        self.assertAlmostEqual(usage_and_cost("jev", jev_response(), self.cfg["providers"]["jev"])["cost_usd"], .000042)
        raw["usage"]["input_tokens"] = -1
        self.assertIsNone(usage_and_cost("gpt", raw, self.cfg["providers"]["gpt"]))
        raw["usage"]["input_tokens"] = True
        self.assertIsNone(usage_and_cost("gpt", raw, self.cfg["providers"]["gpt"]))
