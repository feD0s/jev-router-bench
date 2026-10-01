import io
import json
import time
import unittest
from unittest.mock import patch
from bench.transport import _worker, post_json


def silent_fixture_worker(pipe, *args):
    """A deliberately stalled local worker, with no HTTP request."""
    time.sleep(10)


class PipeFixture:
    def send(self, value):
        self.value = value

    def close(self):
        pass


class ResponseFixture(io.BytesIO):
    code = 200
    headers = {"x-request-id": "fixture-request"}


class TransportTests(unittest.TestCase):
    def test_full_response_deadline_kills_stalled_worker(self):
        start = time.monotonic()
        with patch("bench.transport._worker", silent_fixture_worker):
            result = post_json("https://api.typesafe.ai/v1/systemone", {}, "fixture-key", .2)
        self.assertEqual(result["error"], "DeadlineExceeded")
        self.assertIsNone(result["raw_response"])
        self.assertLess(time.monotonic()-start, 3)

    def test_full_safe_body_saved_and_no_authorization_header(self):
        pipe = PipeFixture()
        class OpenerFixture:
            def open(self, request, timeout):
                self.authorization = request.get_header("Authorization")
                return ResponseFixture(json.dumps({"model": "fixture", "echo": "fixture-key", "extra": [1,2,3]}).encode())
        opener = OpenerFixture()
        with patch("bench.transport.urllib.request.build_opener", return_value=opener):
            _worker(pipe, "https://api.typesafe.ai/v1/systemone", {}, "fixture-key", 1, ("fixture-key",))
        self.assertEqual(opener.authorization, "Bearer fixture-key")
        self.assertEqual(pipe.value["raw_response"]["extra"], [1,2,3])
        self.assertNotIn("fixture-key", json.dumps(pipe.value))
        self.assertNotIn("Authorization", pipe.value)

    def test_untrusted_endpoint_rejected_before_worker(self):
        with self.assertRaises(ValueError):
            post_json("https://evil.example", {}, "fixture-key", 1)
