# word-counter

CLI tool for word frequency analysis. Reads text files (or stdin) and prints a ranked table of word frequencies.

## Install

```bash
uv sync
uv pip install -e .
```

## Usage

```bash
# Analyze files
wc-freq file1.txt file2.txt

# Pipe from stdin
echo "hello world hello" | wc-freq

# Options
wc-freq --top 5 --ignore-case file.txt
```

## Options

- `--top N` — Show top N words (default: 10)
- `--ignore-case` — Treat words case-insensitively

## Development

```bash
uv run pytest          # Run tests
uv run ruff check .    # Lint
uv run mypy .          # Typecheck
```
