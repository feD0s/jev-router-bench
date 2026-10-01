# Evidence directories

`local/` and `live/` are gitignored working artifacts. No Jev/GPT results exist yet.
After a real run and secret review, publish exact safe artifacts under
`published/<run-id>/` with source commit and hashes. Do not overwrite a prior run.

Report generator is `python3 -m bench report --dir <saved-run>`; it never calls an API.
SVG source generation lives in `bench/report.py`, so figures can be regenerated.
