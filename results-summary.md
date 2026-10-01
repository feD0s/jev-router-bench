# Jev Router Bench — readiness report

Date: 2026-10-01. Project: AI Techie. **No paid model evaluation yet.**

Prepared an offline-first, reviewable runner, synthetic dataset and public-repo
package. No Jev/GPT accuracy, latency or actual API cost has been measured.
No claim about a better model and no invented author experience.

## Frozen inputs

- `jev-1.13.0`, native Choice; `gpt-6-luna`, strict single route, explicit effort none.
- `synthetic-ru-v1`: 20 dev and 100 final (60 ordinary / 30 hard / 10 adversarial).
- Final route balance: 33 status / 34 operator / 33 answer.
- Rules, prompts, settings and both splits hashed in `data/freeze-v1.json`.
- Human review pending; concrete boundaries in [owner-review](docs/owner-review.md).

## Offline evidence

Local checks validate dataset structure, unique messages, context, freeze, document
links and module boundaries. Useful tests cover adapter/refusal/malformed parsing,
cache/reasoning pricing, exact metrics, paired disagreements, budgets/retries,
secrets and offline end-to-end reproduction. Live tests use explicit synthetic
fixtures with mocked transport, never API calls. The local keyword control is a
smoke test, not a substitute for measured Jev/GPT results.

Commands from repository root:

```sh
make check
python3 -m bench dry-run --split dev --out results/local/dev-dry
python3 -m bench dry-run --split final --out results/local/final-control-1
python3 -m bench estimate --split final --runs 1
python3 -m bench report --dir results/local/final-control-1
```

## Budget proposal, not spending permission

One final paired pass = 200 planned requests. Based on actual prepared request
sizes and UTF-8/3 input-token heuristic: **about $0.0335** combined (Jev $0.0093,
GPT $0.0242); tokenizer usage is not yet measured. No cache savings assumed.
Conservative reservations: **$0.2688 without retries**, **$0.5376 if every request
is attempted twice**. Proposal: **up to $1 for one final pass including errors/retries**.
Dev access/contract check is a separate cost and authorization decision.
Exact formulas, rates, byte sizes and limits: [budget-proposal.json](docs/budget-proposal.json).

Official rates checked 2026-10-01: [Jev models](https://docs.typesafe.ai/models) and
[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna). Recheck before
the actual run. GPT cache-write allocation in usage remains uncertain; measured
reports will show base/upper calculations rather than an invented exact invoice.

## Next evidence needed

Owner confirmation of rules and labels, explicit budget, project-local keys and
actual API access/contract check. Then final eval and real reports/figures, followed
by a two-column saved-evidence replay. UI is deliberately scheduled after real
results under the attached brief. Personal conclusions require owner review.

Synthetic balanced sample of 100 is small and not a production distribution.
Repeated runs do not increase independent sample size. Wilson intervals/p95 counts
and all errors/disagreements will accompany the actual report. Public final tasks
are not a protected holdout for future model development.

This report is for transfer to the editorial session. No editorial files, posts,
Telegram credentials or other chats were modified. [Harness mapping](docs/harness-engineering.md).
