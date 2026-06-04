"""JSONL reading and writing for eval items and results.

JSONL ("JSON Lines") stores one JSON object per line. Standard for ML datasets:
streamable, append-only friendly, line-oriented diffing.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def read_jsonl(path: str | Path, schema: type[T]) -> Iterator[T]:
    """Read a JSONL file and yield validated objects of the given schema.

    Streams line by line — safe for large files. Skips blank lines.
    Raises pydantic.ValidationError on malformed rows with line number context.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield schema.model_validate_json(line)
            except Exception as e:
                raise ValueError(f"Failed to parse {path}:{line_no}: {e}") from e


def write_jsonl(path: str | Path, items: list[BaseModel]) -> None:
    """Write a list of Pydantic objects to a JSONL file, one per line.

    Overwrites any existing file at the path. Creates parent directories.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(item.model_dump_json() + "\n")
