# Architecture

Python 3.11+, standard library only. No SDK retry defaults, services or infrastructure.

`data + prompts + config → core → adapters/metrics → runner → report/CLI`

- `core.py`: reads/validates data, config and SHA-256 freeze; no network.
- `adapters.py`: builds native API envelopes from identical semantic inputs,
  validates responses, normalizes usage and computes cost. Never reads labels.
- `transport.py`: the sole HTTP boundary; strict hosts, bounded full-body timeout,
  no redirects or hidden retries, secrets removed before persistence.
- `metrics.py`: deterministic exact match, confusion matrix, macro-F1 and uncertainty.
- `runner.py`: one outstanding request; alternating provider order, limits,
  append-only attempts and immutable run manifest. Offline path cannot reach HTTP.
- `report.py`: JSON/CSV/Markdown + SVG from saved evidence. No model calls.
- `__main__.py`: explicit commands. `live` is the only paid entry point.

The router sees `message` + `context`, the common shop snapshot and frozen rules.
`expected_route`, `rationale`, `tags`, and case IDs are excluded from API input.
The GPT system instructions include the same rules and route criteria as Jev Choice.
Native serialization differs, semantic content does not. No requested explanation.

Main timing covers HTTP + full response parsing and route validation. Retry/backoff
time is also reported per logical decision. Executors are absent from the main runner.
After actual evaluation, a separate replay UI may render the local fake-order lookup,
screen-only operator queue, and a separately identified FAQ answering role. It must
consume saved decisions and never silently trigger a paid request.
