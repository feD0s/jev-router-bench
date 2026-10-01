# Jev Router Bench — readiness report

Date: 2026-10-01. AI Techie. **No paid model evaluation yet.**

Owner selected GPT-6 Luna **medium**, increased the budget to **$10 total** and
requested simpler defaults. Full Russian explanation of all choices and caveats:
[Все решения и ограничения](docs/decisions-and-limitations.ru.md).

## Active setup

- Jev `jev-1.13.0`, native Choice; GPT `gpt-6-luna`, explicit effort medium.
- Strict single route. No custom max_output_tokens: provider-default generation.
- No dev/final quotas, locks/ledger, input cap or extra series deadline.
- Ordinary 60-second HTTP timeout, one retry for selected temporary HTTP errors.
- Simple shared $10 accounting from saved attempts; errors/retries included.
- `configs/experiment-v2.json`, `data/freeze-v2.json`; v1 none kept as history.
- Dataset unchanged: 20 dev, 100 final, AI labels, human review pending.
- `.env` prepared empty with mode 0600, gitignored; owner will enter keys locally.

## Offline verification

`make check`: 20 tests and data/freeze/docs/import checks passed.
`make dry-run`: medium request envelopes, without custom output cap, no API calls.
Tests remain offline regardless of real owner review/key state.
No actual API access, provider contract, model quality/latency or invoice measured.

[Saved offline control](results/published/offline-control-v1/results-summary.md)
references source commit
[d807931](https://github.com/feD0s/jev-router-bench/commit/d8079310a4bb5697252f060e7245a8a520292c82).
54/100, 18 unsafe automations, $0 API spend: only the crude keyword algorithm.
Its v1 none metadata is historical, never a Jev/GPT benchmark result.

## Budget

**$10 approved overall**, not $10 per provider or CLI invocation. Use results/live/
for real runs so saved attempts feed the remaining-budget calculation. The main
benchmark excludes downstream executor calls. No complex accounting service.

Medium reasoning volume is unknown. The former none-mode $0.04 prediction and
proposed 2048-token cap no longer apply. Illustrative scenarios and published
rates: [final](docs/budget-medium-final-v2.json), [dev](docs/budget-medium-dev-v2.json).
The published model maximum is only a conservative accounting reserve; it is
not sent as a custom API generation cap. Actual usage settles the estimate.

Rates verified 2026-10-01: [Jev](https://docs.typesafe.ai/models),
[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).
Reasoning is already included in output cost. Unknown usage/cache-write allocation
remains visible rather than an invented exact invoice.

## Reproduce and next step

```sh
make check
make dry-run
make estimate
```

After local key entry and rules/labels review, run dev to verify the API contract,
then final. No further budget question is needed within the approved $10 scope.
Record all decisions, usage, timing, failures and disagreements. Build the
saved-evidence replay after actual results and get the owner's interpretation.

100 synthetic Russian tasks, AI labels, public holdout, small p95 sample and
unmeasured network/provider region limit conclusions. Repeats do not increase
independent N. No editorial files, posts, Telegram credentials, other chats or
CI/CD were modified. No personal author conclusions were invented.
