# Quality status

Updated 2026-10-01.

| Area | Status | Evidence / gap |
|---|---|---|
| Rules and labels | AI-authored, awaiting owner | business-rules and owner-review |
| Dataset structure | locally checked | 20/100, 60/30/10, labels, uniqueness, context |
| API adapters | offline contract tests | live provider contract still unverified |
| Cost/limits | local tests | real usage/cache-write allocation/invoice unverified |
| Metrics/report | deterministic tests + dry-run | no vendor benchmark data yet |
| Documentation/architecture | locally enforced | make check |
| GitHub | public requested | repository URL in README; verify after push |
| UI/replay | awaiting real evidence | implement after paid results, per scope |
| Editorial results | pending real eval | personal owner conclusions absent |

Known debt: Python HTTP worker startup adds client overhead; explicitly included
for both models. Account availability and token estimates require dev verification.
Public holdout is unsuitable for future prompt optimization. Rates need refresh
before future runs. Incomplete runs preserve artifacts but require a fresh run
directory and budget reconciliation; there is no automatic paid resume.
