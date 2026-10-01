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
- [x] Estimate a concrete one-pass budget; paid calls still unauthorized.
- [x] Confirm local checks: 19 tests, data/freeze/docs/import boundaries; dev/final offline reports.
- [x] Push and verify GitHub publication: PUBLIC, main, remote SHA matches local.
- [ ] Owner reviews rules/labels, resolves disputed cases and approves budget.
- [ ] Verify actual account/API contract on dev within approved budget.
- [ ] Run final series (up to three only if separately affordable/authorized).
- [ ] Publish checked safe results with exact source commit and dates.
- [ ] Build two-column replay UI with status/operator/answer and measured errors/time/cost.
- [ ] Get owner's personal conclusions; deliver editorial handoff in this chat.

## Decisions

- Latest direct owner request makes GitHub public, overriding attached private default.
- Python stdlib keeps offline reproduction installation-free; HTTP isolated from report.
- Primary paired requests are sequential; no UI, executor, race or Batch overhead.
- Unknown order/insufficient context → operator for clarification, pending owner review.
- No paid requests or invented Jev/GPT results before approval.
- API usage and published rates calculate cost; missing usage/cache-write allocation
  remains explicit uncertainty with conservative accounting.
- Preserve original editorial repo unchanged. Do not publish posts or message other chats.

## Validation and completion evidence

`make check`: 19 tests passed; dataset/freeze/docs/import boundaries passed.
Dev 20 and final 100 offline runs completed without network or API keys.
Verified implementation commit: d8079310a4bb5697252f060e7245a8a520292c82.
Clean-commit offline evidence: `results/published/offline-control-v1/`; fixed keyword
control scored 54/100, unsafe automation 18, API cost $0. Never vendor measurements.
GitHub repository created public: https://github.com/feD0s/jev-router-bench.
GitHub verification 2026-10-01: PUBLIC, default branch main; published source/evidence
commit 9c322977f9c67b33d78f5b0275f2b09b5201908d matched local HEAD. Working tree clean.
Paid model evaluation remains unapproved.
Paid results and UI depend on human review/budget, not on elapsed time or assumed permission.
