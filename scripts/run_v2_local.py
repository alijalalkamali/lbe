"""Run v2 steerability eval on a model (local or API).

Usage:
    python scripts/run_v2_local.py Qwen/Qwen2.5-0.5B-Instruct
    python scripts/run_v2_local.py meta-llama/Llama-3.2-1B-Instruct
    python scripts/run_v2_local.py meta-llama/Llama-3.2-3B-Instruct
    python scripts/run_v2_local.py anthropic:claude-haiku-4-5
    python scripts/run_v2_local.py deepseek:deepseek-reasoner
    python scripts/run_v2_local.py together:meta-llama/Llama-3.3-70B-Instruct-Turbo

Optional:
    python scripts/run_v2_local.py <model> --max-tokens 800

Writes to results/steerability_v2_<model>.jsonl (colons and slashes in model
names are replaced with underscores for filesystem safety).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lbe.evals.steerability_v2 import run_v2_eval
from lbe.models.loader import load_model


def sanitize_filename(name: str) -> str:
    """Replace filesystem-unfriendly characters in model names."""
    return name.replace(":", "_").replace("/", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v2 eval on a model.")
    parser.add_argument("model", help="Model identifier passed to load_model().")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=500,
        help="Max new tokens per response. Default 500.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    items_path = repo_root / "data" / args.items_file
    output_dir = repo_root / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(args.model)
    output_path = output_dir / f"steerability_v2_{safe_name}.jsonl"

    if not items_path.exists():
        sys.exit(f"Items file not found: {items_path}")

    print(f"Model: {args.model}")
    print(f"max_new_tokens: {args.max_tokens}")
    print(f"Output: {output_path}")

    model = load_model(args.model)
    run_v2_eval(
        items_path=items_path,
        model=model,
        model_name=args.model,
        output_path=output_path,
        max_new_tokens=args.max_tokens,
    )


if __name__ == "__main__":
    main()
