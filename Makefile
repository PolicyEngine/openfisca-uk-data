install:
	pip install -e .
format:
	black . -l 79
test:
	black . -l 79 --check
	pytest tests