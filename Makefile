.PHONY: dev test coverage clean run

# Install dev dependencies
dev:
	pip install -e ".[dev]"

# Run tests
test:
	pytest

# Run tests with coverage report
coverage:
	pytest --cov=irc_topic_notify --cov-report=term-missing

# Clean up build artifacts
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov *.egg-info build dist

# Run the bot (requires config.py)
run:
	python irc_topic_notify.py
