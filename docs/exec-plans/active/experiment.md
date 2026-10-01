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
- [ ] Push and verify GitHub publication evidence.
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

Record final `make check`, dry-run and GitHub commit evidence here after verification.
Paid results and UI depend on human review/budget, not on elapsed time or assumed permission.
