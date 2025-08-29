# Simple entrypoints
PY ?= python3
SRC ?= .
DST ?= ..

dry-run:
	$(PY) sync_by_rules.py --src $(SRC) --dst $(DST) --dry-run --log dry_run.txt --csv dry_run.csv

apply:
	$(PY) sync_by_rules.py --src $(SRC) --dst $(DST) --apply --log apply.txt --csv apply.csv

apply-delete:
	$(PY) sync_by_rules.py --src $(SRC) --dst $(DST) --apply --delete-older-source --log apply.txt --csv apply.csv
