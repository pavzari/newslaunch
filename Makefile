fmt:
	ruff check --fix-only .
	black ./newslaunch ./tests

test:
	ruff check .
	black --check ./newslaunch ./tests
	pytest
