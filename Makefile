.PHONY: check cli-check

check: cli-check

cli-check:
	python3 cli.py < tests/cli_regression_en.txt
