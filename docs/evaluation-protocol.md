# Evaluation protocol v1

Fix rules, labels, prompt/config/model IDs before paid testing. Owner review must
be explicit and hash-matched. Use dev for integration/debugging; never choose
settings from the final 100. Primary effort is none; low would need a separately
versioned config and dev evaluation, reported separately. No confidence gate in v1.

## Requests and scheduling

Jev gets one Choice; GPT gets a strict JSON schema with only route. Both see the
same state, rules and descriptions of routes, with native envelope differences.
Neither is asked for an explanation. Jev confidence/probabilities are retained
as raw auxiliary output only. GPT confidence is never invented.

Seed 614 determines a single shuffled task order. Serial pairs alternate
Jev-first/GPT-first; next repeat reverses that order. One request outstanding;
0.1-second spacing after each decision. No warmup is silently discarded.
Any paid dev/warmup series must be separately authorized and logged. Up to three
repeats assess stability, never independence. 100 tasks remain 100 unique tasks.
Parallel race, Batch and full-cycle experiments require separate run manifests,
budgets and report rows; they are outside the primary runner.

## Measurement and errors

Monotonic client wall-clock starts before HTTP dispatch, ends after full body,
JSON parse, usage normalization and schema/route validation. The bounded HTTP
worker startup/cleanup is included and equal for both providers. This is measured
client latency, not an isolated inference-speed claim. Network/client/provider
regions are stored as unmeasured/unreported unless actually known.

Keep every attempt; request body, safe response body, returned model, status,
request ID, usage, cache, reasoning, timing and error category. Retries do not hide
earlier failures. Decision time includes retries/backoff; valid-attempt latency
and all-attempt latency are separate. Median and nearest-rank p95 always include n.
Timeout may leave a billed request; stop and reconcile, never retry it blindly.
401/403/404/422 or model-version mismatch stop the series. Only 429/5xx/529 retry
up to two attempts. Failed or not-run tasks remain in the planned denominator;
a stopped series is visibly incomplete and is not presented as a complete final eval.

## Metrics

- Exact match, correct/N; final N=100 per provider per repeat, including failures.
- Macro-F1 across the three routes. Missing/schema/transport decisions are false
  negatives of the expected class, never a successful operator fallback.
- Confusion matrix rows expected, columns actual plus error/not_run.
- Operator fraction and automation fraction out of planned tasks.
- Wrong automation: any incorrect status/answer; fraction of automated decisions.
- Unsafe automation: expected operator but actual status/answer; count/N and
  missed-operator rate. Wrong status versus answer is also visible in wrong automation.
- All paired disagreements with original messages, contexts, labels and rationale;
  discordant correctness counts and exploratory exact two-sided McNemar test.
- Wilson 95% accuracy intervals per repeat, not pooled. Small differences of a few
  cases do not establish general superiority; intervals ignore selection/label bias.

## Cost and runtime limits

Prices and sources are frozen in config, verified 2026-10-01. Recheck right before
each actual integration/run and version changes openly. Normal Standard requests,
GPT service_tier=default; Batch/Flex/Fast/regional rates are not combined here.
Jev bills input only; GPT usage cost includes output with reasoning already inside.
Cache-read and separately reported write tokens are priced at their published rates.
If GPT does not report write allocation, report base estimate and conservative
upper with write premium on all uncached input. Do not call this an exact invoice.

Accounting includes all retries/errors. Unknown usage reserves full per-request
bound (16000 input tokens, capped GPT output), rather than claiming zero cost.
Before sending, reject bodies larger than byte-based token bound plus 4096
overhead; reserve the max applicable input/cache-write rate. Published tokenization
and pricing changes can break this estimate; stop on usage exceeding it. Provider
account spending limits are complementary; client code cannot guarantee an invoice.
Request count and total series time also bound execution. Every separate CLI run
has its own budget; owner approval must specify whether dev/repeats share a total.

## Reporting and reproduction

Reports reconstruct from saved cases/manifest/attempts, so changing current code
inputs does not silently change recorded labels. Results must link exact source
commit and frozen hashes, dates, full safe responses and commands. Publish original
errors alongside successful examples and explicitly label replay. Results require
owner interpretation; do not invent personal experience or Telegram posts.
