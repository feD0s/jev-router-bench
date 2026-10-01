.PHONY: check validate test dry-run estimate
check: validate test
	python3 scripts/check_repo.py

validate:
	python3 -m bench validate

test:
	python3 -m unittest discover -s tests -v

dry-run:
	python3 -m bench dry-run --split dev --out results/local/dev-dry

estimate:
	python3 -m bench estimate --split final --runs 1
