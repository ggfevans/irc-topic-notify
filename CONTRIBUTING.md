# Contributing

Thanks for your interest in contributing!

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=irc_topic_notify --cov-report=term-missing 

## Bug Reports

Open an issue with:
- What you expected to happen
- What actually happened
- Your Python version and OS
- Relevant config settings (redact tokens!)

## Pull Requests

1. Fork the repo
2. Create a feature branch (`git checkout -b my-feature`)
3. Make your changes
4. Test locally with `--test` and `--test-trigger` flags
5. Submit a PR with a clear description

## Code Style

- Keep it simple — this is a small utility
- Follow existing patterns in the codebase
- Add type hints for new functions
- Update README if adding config options

## Scope

This project intentionally stays minimal. Features that might be out of scope:
- Alternative notification backends (Discord, Telegram, etc.) — consider forking
- Complex trigger logic (regex, multiple phrases) — keep it simple
- GUI or web interface

When in doubt, open an issue to discuss before writing code.
