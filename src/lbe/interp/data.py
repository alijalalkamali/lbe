"""
Data assembly for the interp probe: join items x responses x consensus labels.

Three sources, joined on item_id:
  1. data/steerability_items_v3.jsonl   (SteerabilityItem: prompt text)
  2. results/steerability_v2_{model}.jsonl (EvalResult: raw_completions =
     [base_response, steered_response] -- order fixed by steerability_v2.run_v2_item)
  3. results/judgments/aggregated_judgments.csv (consensus_loo label per
     item/responder/condition)

Prompt reconstruction rule (verified against evals/steerability_v2.py):
  - base condition    -> the prompt sent to the API was item.base_prompt, alone
  - steered condition -> the prompt sent was item.steering_instruction, alone
  No concatenation, no system prompt. The harvested input must reproduce the
  original API input byte-for-byte, so this module uses those fields verbatim.

Label rule for the derail probe (verified against aggregated_judgments.csv):
  y = 1 if consensus_loo == "derail" else 0. For Llama VCL base this yields
  42 positives / 58 negatives (57 full-compliance + 1 compliance-with-disavowal).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import torch

from lbe.io.dataset import EvalResult, SteerabilityItem
from lbe.io.jsonl import read_jsonl

if TYPE_CHECKING:
    from transformers import PreTrainedTokenizerBase

# Index into EvalResult.raw_completions, fixed by run_v2_item's construction:
# raw_completions=[base.text, steered.text]
_COMPLETION_INDEX = {"base": 0, "steered": 1}


@dataclass(frozen=True)
class ProbeExample:
    """One joined example: exact original prompt, logged response, label."""

    item_id: str
    category: str
    condition: str
    responder_model: str
    prompt_text: str
    response_text: str
    consensus_loo: str


def _load_consensus(
    judgments_csv: Path,
    category: str,
    condition: str,
    responder_model: str,
) -> dict[str, str]:
    """item_id -> consensus_loo, filtered to one category/condition/responder."""
    if not judgments_csv.exists():
        raise FileNotFoundError(f"Judgments CSV not found: {judgments_csv}")

    out: dict[str, str] = {}
    with judgments_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"item_id", "category", "condition", "responder_model", "consensus_loo"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{judgments_csv} is missing expected column(s) {sorted(missing)}; "
                f"found {reader.fieldnames}"
            )
        for row in reader:
            if (
                row["category"] == category
                and row["condition"] == condition
                and row["responder_model"] == responder_model
            ):
                if row["item_id"] in out:
                    raise ValueError(
                        f"Duplicate consensus row for item_id={row['item_id']!r} "
                        f"({category}/{condition}/{responder_model}) -- the CSV "
                        f"should have exactly one row per item/responder/condition."
                    )
                out[row["item_id"]] = row["consensus_loo"]
    if not out:
        raise ValueError(
            f"No consensus rows matched category={category!r}, condition="
            f"{condition!r}, responder_model={responder_model!r} in {judgments_csv}."
        )
    return out


def build_probe_examples(
    items_path: Path,
    results_path: Path,
    judgments_csv: Path,
    category: str,
    condition: str,
    responder_model: str,
) -> list[ProbeExample]:
    """
    Join the three sources. Fails loudly on any item that appears in the
    consensus labels but lacks an item definition or a logged response --
    a silently-shrinking n is worse than a crash at this sample size.
    """
    if condition not in _COMPLETION_INDEX:
        raise ValueError(f"condition must be one of {list(_COMPLETION_INDEX)}, got {condition!r}")

    items_by_id: dict[str, SteerabilityItem] = {}
    for item in read_jsonl(items_path, SteerabilityItem):
        if item.category == category:
            items_by_id[item.id] = item

    results_by_id: dict[str, EvalResult] = {}
    for result in read_jsonl(results_path, EvalResult):
        if result.extra.get("category") == category and result.model_name == responder_model:
            if result.item_id in results_by_id:
                raise ValueError(
                    f"Duplicate result for item_id={result.item_id!r} in {results_path} -- "
                    f"resolve (e.g. stale rows from a partial rerun) before harvesting."
                )
            results_by_id[result.item_id] = result

    consensus = _load_consensus(judgments_csv, category, condition, responder_model)

    missing_items = sorted(set(consensus) - set(items_by_id))
    missing_results = sorted(set(consensus) - set(results_by_id))
    if missing_items or missing_results:
        raise ValueError(
            f"Join incomplete: {len(missing_items)} labeled item(s) missing from "
            f"{items_path.name} {missing_items[:5]}...; {len(missing_results)} "
            f"missing from {results_path.name} {missing_results[:5]}..."
        )

    completion_idx = _COMPLETION_INDEX[condition]
    examples: list[ProbeExample] = []
    for item_id, label in sorted(consensus.items()):
        item = items_by_id[item_id]
        result = results_by_id[item_id]
        if len(result.raw_completions) <= completion_idx:
            raise ValueError(
                f"Item {item_id}: raw_completions has {len(result.raw_completions)} "
                f"entries; need index {completion_idx} for condition={condition!r}."
            )
        prompt_text = item.base_prompt if condition == "base" else item.steering_instruction
        examples.append(
            ProbeExample(
                item_id=item_id,
                category=category,
                condition=condition,
                responder_model=responder_model,
                prompt_text=prompt_text,
                response_text=result.raw_completions[completion_idx],
                consensus_loo=label,
            )
        )
    return examples


def binary_labels(examples: list[ProbeExample], positive_label: str) -> list[int]:
    """y=1 where consensus_loo == positive_label, else 0. Errors on degenerate splits."""
    labels = [1 if ex.consensus_loo == positive_label else 0 for ex in examples]
    n_pos = sum(labels)
    if n_pos == 0 or n_pos == len(labels):
        raise ValueError(
            f"Degenerate label split for positive_label={positive_label!r}: "
            f"{n_pos}/{len(labels)} positives. A probe cannot be trained or "
            f"evaluated on a single-class dataset."
        )
    return labels


def compute_boundary_index(
    tokenizer: PreTrainedTokenizerBase,
    prompt_text: str,
    response_text: str,
) -> tuple[torch.Tensor, int]:
    """
    Tokenize prompt+response once, and independently tokenize the
    generation-onset point (prompt + assistant-turn-open, no content), then
    verify the latter is an exact token-level prefix of the former.

    Returns (full_input_ids, boundary_index): boundary_index is the 0-indexed
    position of the LAST prompt-side token -- the position whose residual-
    stream activation is what we probe and (later) steer at.

    Raises ValueError if the chat template is not prefix-consistent for this
    tokenizer -- an off-by-one here corrupts every downstream result, so it
    must fail loudly rather than misindex silently.
    """
    prompt_messages = [{"role": "user", "content": prompt_text}]
    full_messages = prompt_messages + [{"role": "assistant", "content": response_text}]

    prompt_ids = tokenizer.apply_chat_template(
        prompt_messages, add_generation_prompt=True, return_tensors="pt"
    )
    full_ids = tokenizer.apply_chat_template(
        full_messages, add_generation_prompt=False, return_tensors="pt"
    )
    # Newer transformers versions return a BatchEncoding dict rather than a
    # raw tensor; normalize both to tensors.
    if not torch.is_tensor(prompt_ids):
        prompt_ids = prompt_ids["input_ids"]
    if not torch.is_tensor(full_ids):
        full_ids = full_ids["input_ids"]

    prompt_len = prompt_ids.shape[1]
    if full_ids.shape[1] < prompt_len:
        raise ValueError(
            "Full sequence is shorter than the prompt-only sequence -- chat "
            "template misconfiguration."
        )
    if not torch.equal(full_ids[0, :prompt_len], prompt_ids[0]):
        raise ValueError(
            "Tokenization prefix mismatch: prompt-only tokens are not an exact "
            "prefix of prompt+response tokens for this tokenizer/chat template. "
            "Boundary index cannot be trusted; resolve before harvesting."
        )
    return full_ids, prompt_len - 1
