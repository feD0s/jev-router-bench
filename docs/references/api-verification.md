# API verification — 2026-10-01

Official pages read immediately before offline adapter integration. No paid call,
account-access verification or live contract validation has occurred; local `.env`
does not exist. Documentation examples are not benchmark results.

| Item | Verified in published docs | Source |
|---|---|---|
| Jev fixed ID | jev-1.13.0; aliases may move, pinned ID accepted | [Models](https://docs.typesafe.ai/models) |
| Jev price | $0.042 / million input; output free | [Models](https://docs.typesafe.ai/models) |
| Jev API | POST https://api.typesafe.ai/v1/systemone, Bearer auth, state/model/questions | [API](https://docs.typesafe.ai/api) |
| Choice | criteria map, choice + confidence + probabilities under answers | [Choice](https://docs.typesafe.ai/primitives/choice) |
| Intent router pattern | deterministic handler / LLM / human | [Routing](https://docs.typesafe.ai/patterns/intent-routing) |
| Confidence | distribution-derived; no comparable GPT measure added | [Confidence](https://docs.typesafe.ai/confidence) |
| Jev quick start | native request/response and usage input/output tokens | [Quick start](https://docs.typesafe.ai/introduction/quickstart) |
| GPT fixed requested ID | gpt-6-luna, Responses supported; official page has no dated snapshot | [Model](https://developers.openai.com/api/docs/models/gpt-6-luna) |
| GPT effort | none/low/medium(default)/high/xhigh/max; explicitly choose none | [Model](https://developers.openai.com/api/docs/models/gpt-6-luna) |
| GPT Standard USD / Mtok | input .10, cached .01, write .125, output .50 | [Model](https://developers.openai.com/api/docs/models/gpt-6-luna) |
| GPT Structured Output | strict text.format json_schema; handle refusal/incomplete | [Guide](https://developers.openai.com/api/docs/guides/structured-outputs) |
| Evals | explicit success criteria, representative and adversarial tasks, held-out evaluation | [Best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) |
| Harness | repository knowledge, small map, versioned plans and mechanical boundaries | [Article](https://openai.com/index/harness-engineering/) |

Rates have no Batch/Flex/Fast or regional multipliers here. GPT cache-write pricing
is published, but allocation in normal Responses usage is not established by this
review; calculations therefore retain uncertainty rather than silently ignoring it.

Before a real run: re-open model/rate pages, verify account access with supplied
keys without logging them, record date/evidence and request configuration. Jev
GET /v1/models lists aliases; pinned IDs can be accepted even if absent there.
An initial dev call verifies contract/model response, charged against the approved
budget. No silent fallback to another model or effort. Exact returned IDs saved;
mismatch halts run. Re-check rates whenever dates change.
