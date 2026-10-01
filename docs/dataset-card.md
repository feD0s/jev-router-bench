# Dataset card — synthetic-ru-v1

Created 2026-10-01 by an AI coding agent for the fictional «Лист» shop.
All examples and labels are AI-authored. Human label review: pending.
No customer, employer, CRM, Telegram or third-party benchmark data.

| Split | Tasks | status | operator | answer |
|---|---:|---:|---:|---:|
| Dev | 20 | 7 | 7 | 6 |
| Final | 100 | 33 | 34 | 33 |

Final difficulty buckets: 60 ordinary (20 per route), 30 hard (10 per route),
10 adversarial (3 status, 4 operator, 3 answer). Each row is JSON with id, message,
context, expected_route, rationale and tags. First tag specifies difficulty.
IDs and expected labels never reach the models. Variable context specifies known
IDs, selected order and prior conversation. `shop-v1.json` is attached identically
to both requests; it includes the full fictional order snapshot and FAQ.

Dev was authored separately before the final set; final cases are not generated
by templated paraphrases of dev. Categories naturally overlap because there are
only three routes. `validate` checks uniqueness across splits and flags string
similarity >= 0.82 after number normalization. This heuristic cannot establish
semantic independence; owner should also review conceptual overlap.

Final is public and frozen before model testing. No model calls were used for
tuning. Viewing/authoring the final labels is not evidence of blinded human
evaluation. Future agents must avoid using final failures to improve v1.
For future prompt/model development create a new final set and new version.

Labeling follows [business rules](business-rules.md). Disputed boundary cases are
listed in [owner review](owner-review.md); all 120 rows remain available for review.
Freeze manifest records SHA-256 of rules, prompt, config, shop and both splits.
Label corrections require a new freeze/version and repeated review before any eval.

Limits: artificial language style, small sample, equal class frequencies, shared
AI authorship of rules/labels, no real distribution, no inter-annotator agreement,
no privacy/ownership validation, no guaranteed resistance to dataset contamination.
An accuracy interval cannot correct these sources of bias.
