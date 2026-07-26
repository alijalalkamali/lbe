"""
Activation harvesting entry point (lbe.interp).

Joins items x logged responses x consensus labels, teacher-forces each
(exact original prompt + exact logged response) through the locally loaded
model, and records the residual-stream activation at the last prompt token
for every sampled layer.

Runs one item at a time (batch size 1): at n~100 the simplicity is worth
it -- batching requires padding, which reintroduces exactly the left/right-
pad and attention-mask indexing bugs that silently corrupt which token's
activation gets read.

Output layout:
    {output_dir}/{responder_model_slug}/{category}_{condition}/
        activations.pt  -- dict[item_id -> dict[layer_idx -> np.ndarray float32]]
        labels.json     -- dict[item_id -> consensus_loo string]
        metadata.csv    -- one row per harvested item

Usage (rental GPU, real run):
    python -m lbe.interp.harvest \
        --model-name meta-llama/Llama-3.3-70B-Instruct \
        --hardware-profile rental_gpu \
        --items-path data/steerability_items_v3.jsonl \
        --results-path \
          results/steerability_v2_together_meta-llama_Llama-3.3-70B-Instruct-Turbo.jsonl \
        --judgments-csv results/judgments/aggregated_judgments.csv \
        --category values_conflict_low --condition base
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from pathlib import Path

import numpy as np
import torch

from lbe.interp.config import HarvestConfig
from lbe.interp.data import build_probe_examples, compute_boundary_index
from lbe.interp.hooks import ActivationCache

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


def run_harvest(
    config: HarvestConfig,
    items_path: Path,
    results_path: Path,
    judgments_csv: Path,
) -> Path:
    # Join FIRST: if the data doesn't line up, fail before paying for model load.
    examples = build_probe_examples(
        items_path=items_path,
        results_path=results_path,
        judgments_csv=judgments_csv,
        category=config.category,
        condition=config.condition,
        responder_model=config.responder_model,
    )
    logger.info(
        "Joined %d examples for %s/%s/%s",
        len(examples),
        config.category,
        config.condition,
        config.responder_model,
    )

    from transformers import AutoModelForCausalLM, AutoTokenizer

    logger.info("Loading tokenizer/model: %s (%s)", config.model_name, config.hardware_profile)
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        torch_dtype=config.torch_dtype,
        attn_implementation=config.attn_implementation,
        device_map=config.device_map,
    )
    model.eval()

    layers = model.model.layers
    n_layers = len(layers)
    layer_indices = config.resolve_layer_indices(n_layers)
    logger.info("Model has %d layers; harvesting layers: %s", n_layers, layer_indices)

    out_dir = (
        config.output_dir / _slug(config.responder_model) / f"{config.category}_{config.condition}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    activations: dict[str, dict[int, np.ndarray]] = {}
    labels: dict[str, str] = {}
    metadata_rows: list[dict] = []
    failures: list[tuple[str, str]] = []

    with ActivationCache(layers, layer_indices) as cache:
        for i, ex in enumerate(examples, start=1):
            try:
                full_ids, boundary_idx = compute_boundary_index(
                    tokenizer, ex.prompt_text, ex.response_text
                )
            except ValueError as e:
                logger.error("Item %s: boundary computation failed: %s", ex.item_id, e)
                failures.append((ex.item_id, str(e)))
                continue

            full_ids = full_ids.to(model.device)
            cache.clear()
            with torch.no_grad():
                model(input_ids=full_ids)

            per_layer: dict[int, np.ndarray] = {}
            for layer_idx in layer_indices:
                hidden = cache.get(layer_idx)  # [1, seq_len, hidden_dim]
                if boundary_idx >= hidden.shape[1]:
                    raise RuntimeError(
                        f"Item {ex.item_id}: boundary_idx {boundary_idx} >= seq_len "
                        f"{hidden.shape[1]} at layer {layer_idx}. Should be impossible "
                        f"given compute_boundary_index's checks -- investigate, do not "
                        f"truncate silently."
                    )
                per_layer[layer_idx] = hidden[0, boundary_idx, :].to(torch.float32).cpu().numpy()

            activations[ex.item_id] = per_layer
            labels[ex.item_id] = ex.consensus_loo
            metadata_rows.append(
                {
                    "item_id": ex.item_id,
                    "category": ex.category,
                    "condition": ex.condition,
                    "responder_model": ex.responder_model,
                    "consensus_loo": ex.consensus_loo,
                    "seq_len": int(full_ids.shape[1]),
                    "boundary_index": boundary_idx,
                }
            )
            if i % 10 == 0 or i == len(examples):
                logger.info("Harvested %d/%d (%d failed)", i, len(examples), len(failures))

    if failures:
        logger.warning(
            "%d item(s) failed and were EXCLUDED -- the probe's effective n is %d, "
            "not %d. Resolve failures or document the exclusion: %s",
            len(failures),
            len(activations),
            len(examples),
            [f[0] for f in failures],
        )

    torch.save(activations, out_dir / "activations.pt")
    (out_dir / "labels.json").write_text(json.dumps(labels, indent=2, sort_keys=True))
    with (out_dir / "metadata.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(metadata_rows[0].keys()))
        writer.writeheader()
        writer.writerows(metadata_rows)

    logger.info("Saved %d items under %s", len(activations), out_dir)
    return out_dir / "activations.pt"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--hardware-profile", choices=["local_dev", "rental_gpu"], required=True)
    parser.add_argument("--items-path", required=True, type=Path)
    parser.add_argument("--results-path", required=True, type=Path)
    parser.add_argument("--judgments-csv", required=True, type=Path)
    parser.add_argument("--category", default="values_conflict_low")
    parser.add_argument("--condition", default="base", choices=["base", "steered"])
    parser.add_argument(
        "--responder-model", default="together:meta-llama/Llama-3.3-70B-Instruct-Turbo"
    )
    parser.add_argument("--layer-stride", type=int, default=4)
    parser.add_argument("--output-dir", default=Path("results/interp/activations"), type=Path)
    args = parser.parse_args()

    cfg = HarvestConfig(
        model_name=args.model_name,
        hardware_profile=args.hardware_profile,
        category=args.category,
        condition=args.condition,
        responder_model=args.responder_model,
        layer_stride=args.layer_stride,
        output_dir=args.output_dir,
    )
    run_harvest(cfg, args.items_path, args.results_path, args.judgments_csv)


if __name__ == "__main__":
    main()
