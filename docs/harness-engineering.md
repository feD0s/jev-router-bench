# Harness engineering in this experiment

This small project applies practices from [OpenAI's article](https://openai.com/index/harness-engineering/).
This is a scoped interpretation, not an official compliance certification.

| Principle | Concrete implementation | Local check |
|---|---|---|
| Map rather than giant manual | AGENTS.md links to repository knowledge | docs link/size checker |
| Repository is source of truth | data, config, rules, plan, source references, run manifests | SHA-256 freeze |
| Plans as artifacts | active plan with progress, decisions and remaining work | manually maintained on changes |
| Parse shapes at boundaries | strict Choice/Structured Output parsers, input validator | malformed/refusal/usage tests |
| Enforce architecture | no network outside transport, allowed Python imports | AST structural check |
| Make behavior legible | immutable raw attempts, explicit errors, deterministic reports | offline end-to-end tests |
| Resource-aware autonomy | ordinary HTTP timeout, saved usage, total budget | limit/retry/error-accounting tests |
| Small maintenance scope | zero dependencies, no production infrastructure | stdlib-only imports |

No CI/CD, GitHub Actions, scheduled maintenance agents or observability service.
The owner explicitly requested local checks only. `make check` validates datasets,
freeze, local documentation links, dependency boundaries and regression tests.
