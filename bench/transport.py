"""Only HTTP boundary. Child process provides a full-response wall-clock deadline."""
import json
import multiprocessing
import re
import urllib.error
import urllib.request

KEY_NAMES = {"api_key", "apikey", "authorization", "access_token", "refresh_token", "secret"}


def redact(value, secrets=()):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if k.lower() in KEY_NAMES else redact(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        value = re.sub(r"(?i)bearer\s+[^\s\"']+", "Bearer [REDACTED]", value)
        return re.sub(r"\bsk-[a-zA-Z0-9_-]{12,}", "[REDACTED]", value)
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _worker(pipe, endpoint, body, key, timeout, secrets):
    try:
        request = urllib.request.Request(endpoint, json.dumps(body, ensure_ascii=False).encode(),
                    {"Content-Type": "application/json", "Authorization": "Bearer " + key}, method="POST")
        opener = urllib.request.build_opener(NoRedirect)
        try:
            response = opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as err:
            response = err
        with response:
            payload = response.read(4 * 1024 * 1024 + 1)
            if len(payload) > 4 * 1024 * 1024:
                raise ValueError("Response size limit")
            text = payload.decode("utf-8", errors="replace")
            try:
                raw = json.loads(text)
            except json.JSONDecodeError:
                raw = {"unparsed_body": text}
            pipe.send({"status": response.code, "raw_response": redact(raw, secrets),
                       "request_id": response.headers.get("x-request-id"),
                       "retry_after": response.headers.get("retry-after"), "error": None})
    except Exception as err:
        # Exception messages and request headers may contain credentials.
        pipe.send({"status": None, "raw_response": None, "error": type(err).__name__})
    finally:
        pipe.close()


def post_json(endpoint, body, key, timeout, secrets=()):
    if endpoint not in ("https://api.openai.com/v1/responses", "https://api.typesafe.ai/v1/systemone"):
        raise ValueError("Untrusted endpoint")
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(child, endpoint, body, key, timeout, secrets))
    process.start()
    child.close()
    try:
        if parent.poll(timeout):
            try:
                return parent.recv()
            except EOFError:
                return {"status": None, "raw_response": None, "error": "WorkerFailure"}
        return {"status": None, "raw_response": None, "error": "DeadlineExceeded"}
    finally:
        if process.is_alive():
            process.terminate()
        process.join(timeout=1)
        if process.is_alive():
            process.kill()
            process.join()
        parent.close()
