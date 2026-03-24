"""Output formatting utilities."""

import json
import sys
from typing import Any, Dict


def output_json(data: Any):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def output_text(text: str):
    """Print plain text."""
    print(text)


def output_error(message: str):
    """Print error to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def output_stream_chunk(chunk: str, end: str = ""):
    """Print a streaming chunk without newline."""
    sys.stdout.write(chunk)
    if end:
        sys.stdout.write(end)
    sys.stdout.flush()


def output_progress(status: str, percent: float):
    """Print task progress."""
    bar_len = 30
    filled = int(bar_len * percent / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    sys.stderr.write(f"\r[{bar}] {percent:.0f}% - {status}")
    sys.stderr.flush()
    if percent >= 100:
        sys.stderr.write("\n")


def format_balance(raw: str) -> str:
    """Convert balance from 0.0001 USD units to dollars."""
    try:
        cents = int(raw)
        return f"${cents / 10000:.4f}"
    except (ValueError, TypeError):
        return raw


def format_table(rows: list, headers: list) -> str:
    """Format data as a simple ASCII table."""
    if not rows:
        return "(no data)"
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(val)))

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_row = "|" + "|".join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)) + "|"

    lines = [sep, header_row, sep]
    for row in rows:
        line = "|" + "|".join(
            f" {str(row[i]) if i < len(row) else '':<{col_widths[i]}} "
            for i in range(len(headers))
        ) + "|"
        lines.append(line)
    lines.append(sep)
    return "\n".join(lines)
