import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bench.core import ROOT, hashes, inputs, load_cases, read_json, validate_config, validate_dataset
from bench.report import generate_report
from bench.runner import Limits, dry_run, live_run, pair_schedule
from bench.transport import NoRedirect, redact
from test_adapters import gpt_response, jev_response


class RunnerTests(unittest.TestCase):
    def test_dataset_and_fixed_pairing(self):
        result = validate_dataset()
        self.assertEqual(result["counts"]["final"], {"status": 33, "operator": 34, "answer": 33})
        cfg, _, _ = inputs()
        cases = load_cases("dev")
        schedule = list(pair_schedule(cases, cfg, 2))
        self.assertEqual(schedule, list(pair_schedule(cases, cfg, 2)))
        self.assertNotEqual(schedule[0][3], schedule[1][3])
        self.assertNotEqual(schedule[0][3], schedule[20][3])

    def test_budget_reservations_and_unknown_charges(self):
        budget = Limits(.1, 2, 30)
        budget.reserve(.06)
        budget.settle(.06, None)  # Lost usage: reservation remains, not zero.
        with self.assertRaises(ValueError):
            budget.reserve(.06)
        budget.reserve(.03)
        with self.assertRaises(ValueError):
            budget.reserve(.001)
        with self.assertRaises(ValueError):
            Limits(float("nan"), 1, 30)

    def test_default_live_denied_before_transport(self):
        with tempfile.TemporaryDirectory() as d:
            with patch("bench.runner.post_json") as network, self.assertRaises(ValueError):
                live_run("final", Path(d)/"denied", 1, 1)
            network.assert_not_called()

    def test_dry_run_never_network_and_immutable_output(self):
        with tempfile.TemporaryDirectory() as d, patch("bench.transport.urllib.request.build_opener", side_effect=AssertionError("offline must not call HTTP")):
            out = Path(d)/"offline"
            dry_run("dev", out)
            report = generate_report(out)
            self.assertEqual(report["mode"], "offline-keyword-control")
            self.assertEqual(report["unique_tasks"], 20)
            self.assertNotIn("jev", report["runs"]["1"])
            self.assertEqual(read_json(out/"manifest.json")["paid_requests"], 0)
            with self.assertRaises(FileExistsError):
                dry_run("dev", out)

    def test_mocked_live_retry_accounting_and_stopping(self):
        cfg, prompt, shop = inputs()
        cfg = copy.deepcopy(cfg)
        cfg["measurement"]["spacing_s"] = cfg["measurement"]["retry_backoff_s"] = 0
        calls = []
        def fixture_transport(endpoint, body, key, timeout, secrets):
            calls.append(body)
            if len(calls) == 1:
                return {"status": 429, "raw_response": {"error": "fixture rate limit"}, "error": None}
            raw = jev_response() if "systemone" in endpoint else gpt_response()
            return {"status": 200, "raw_response": raw, "error": None}
        cases = load_cases("dev")[:1]
        with tempfile.TemporaryDirectory() as d, \
             patch("bench.runner.check_freeze", return_value={"sha256": hashes()}), \
             patch("bench.runner.read_json", return_value={"approved": True, "sha256": hashes(), "reviewer": "fixture"}), \
             patch("bench.runner.inputs", return_value=(cfg, prompt, shop)), \
             patch("bench.runner.git_state", return_value={"commit": "fixture", "dirty": False}), \
             patch("bench.runner.load_env", return_value={"OPENAI_API_KEY": "fixture-gpt", "TYPESAFE_API_KEY": "fixture-jev"}), \
             patch("bench.runner.load_cases", return_value=cases):
            out = Path(d)/"live-fixture"
            live_run("dev", out, 1, 1, transport=fixture_transport)
            report = generate_report(out)
            self.assertEqual(len(calls), 3)
            self.assertEqual(report["runs"]["1"]["jev"]["attempt_count"], 2)
            self.assertEqual(report["runs"]["1"]["jev"]["unknown_usage_attempts"], 1)
            self.assertGreater(report["runs"]["1"]["jev"]["cost_upper_accounted_usd"], .0006)
            out2 = Path(d)/"limited-fixture"
            live_run("dev", out2, 1, .0001, transport=fixture_transport)
            limited = generate_report(out2)
            self.assertEqual(read_json(out2/"manifest.json")["status"], "stopped")
            self.assertEqual(limited["runs"]["1"]["jev"]["not_run_count"], 1)
            self.assertEqual(len(calls), 3)
            def lost_response(*args):
                raise TimeoutError("echo fixture-jev")
            lost = Path(d)/"lost-fixture"
            live_run("dev", lost, 1, 1, transport=lost_response)
            lost_report = generate_report(lost)
            self.assertEqual(read_json(lost/"manifest.json")["paid_requests"], 1)
            self.assertEqual(read_json(lost/"manifest.json")["status"], "stopped")
            self.assertEqual(lost_report["runs"]["1"]["jev"]["failed_decisions"], 1)
            self.assertNotIn("fixture-jev", (lost/"attempts.jsonl").read_text())

    def test_config_rejects_hidden_defaults_and_bad_limits(self):
        original, _, _ = inputs()
        for key, value in (("reasoning_effort", "medium"), ("model", "gpt-other")):
            cfg = copy.deepcopy(original)
            cfg["providers"]["gpt"][key] = value
            with self.assertRaises(ValueError):
                validate_config(cfg)
        cfg = copy.deepcopy(original)
        cfg["measurement"]["request_timeout_s"] = float("nan")
        with self.assertRaises(ValueError):
            validate_config(cfg)

    def test_redact_credentials_and_disable_redirects(self):
        value = {"Authorization": "private", "raw": ["echo fixture-secret", "Bearer abc123"], "api_key": "key"}
        serialized = json.dumps(redact(value, ["fixture-secret"]))
        self.assertNotIn("fixture-secret", serialized)
        self.assertNotIn("abc123", serialized)
        self.assertNotIn("private", serialized)
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, None, {}, "https://evil.example"))
