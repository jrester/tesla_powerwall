test:
    uv run --group test python -m unittest discover tests/unit

test-unit:
    uv run --group test python -m unittest discover tests/unit

test-integration:
    uv run --group test python -m unittest discover tests/integration

example:
    uv run python examples/example.py
