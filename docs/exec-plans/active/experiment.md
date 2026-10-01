# Jev routing experiment

Created 2026-10-01. Owner: AI Techie author. Implementation: AI coding agent.

## Objective

Reviewable experiment and public portfolio repository. Compare Jev and GPT-6 Luna
as routers on 100 synthetic Russian messages; reproducible quality/latency/cost,
then saved-evidence replay and editorial handoff. No CI/CD and no production support service.

## Progress

- [x] Read owner prompt and editorial research context (read-only).
- [x] Check published API IDs/rates/shapes; preserve requested gpt-6-luna.
- [x] Write rules and prompt before evaluation; pin Jev 1.13.0 and effort none.
- [x] Author 20 dev and 100 final examples, explicit AI provenance and review list.
- [x] Implement validator, offline control, native adapters and bounded runner.
- [x] Implement deterministic metrics, reports, CSV/JSON and confusion SVG.
- [x] Add local checks and useful tests, short AGENTS map, architecture, references.
- [x] Estimate a concrete one-pass budget; initial $1 proposal later replaced by approved $10.
- [x] Confirm local checks: 19 tests, data/freeze/docs/import boundaries; dev/final offline reports.
- [x] Push and verify GitHub publication: PUBLIC, main, remote SHA matches local.
- [x] Owner chose medium and increased the total budget from $1 to $10 (2026-10-01).
- [x] Prepared local .env with empty key fields and mode 0600; never print contents.
- [x] Versioned medium config/freeze; kept none configuration and old evidence as history.
- [ ] Owner reviews rules/labels and resolves disputed cases; budget approval is separate.
- [ ] Verify actual account/API contract on dev within approved budget.
- [ ] Run the final series; up to three stability repeats if useful within the $10 budget.
- [ ] Publish checked safe results with exact source commit and dates.
- [ ] Build two-column replay UI with status/operator/answer and measured errors/time/cost.
- [ ] Get owner's personal conclusions; deliver editorial handoff in this chat.

## Decisions

- Latest direct owner request makes GitHub public, overriding attached private default.
- Python stdlib keeps offline reproduction installation-free; HTTP isolated from report.
- Primary paired requests are sequential; no UI, executor, race or Batch overhead.
- Unknown order/insufficient context → operator for clarification, pending owner review.
- No invented Jev/GPT results; budget is approved, keys and labels review still pending.
- API usage and published rates calculate cost; missing usage/cache-write allocation
  remains explicit uncertainty with conservative accounting.
- Preserve original editorial repo unchanged. Do not publish posts or message other chats.
- Owner update: gpt-6-luna effort=medium, provider-default generation. Proposed 2048
  cap removed before any paid request; no hidden fallback to none.
- Owner requested simpler defaults and $10 total: removed split quotas, lock/ledger,
  custom output/input caps and series deadline. Keep ordinary HTTP timeout and
  simple costs from recorded attempts. Goal: complete the comparison, not build infrastructure.
- Full Russian decision audit: docs/decisions-and-limitations.ru.md; business choices
  remain AI proposals until owner review. The new approval does not approve labels.

## Validation and completion evidence

`make check`: latest 20 tests passed; dataset/freeze/docs/import boundaries passed.
Dev 20 and final 100 offline runs completed without network or API keys.
Verified implementation commit: d8079310a4bb5697252f060e7245a8a520292c82.
Clean-commit offline evidence: `results/published/offline-control-v1/`; fixed keyword
control scored 54/100, unsafe automation 18, API cost $0. Never vendor measurements.
GitHub repository created public: https://github.com/feD0s/jev-router-bench.
GitHub verification 2026-10-01: PUBLIC, default branch main; published source/evidence
commit 9c322977f9c67b33d78f5b0275f2b09b5201908d matched local HEAD. Working tree clean.
Paid budget/model now approved; execution awaits keys and business-rules/labels review.
Paid results and UI depend on human review/keys, not on elapsed time or assumed label approval.
