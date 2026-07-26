"""
Activation steering: build a direction from harvested activations, add it to
the residual stream during generation, sweep alpha, log outputs for judging.

Method (difference-of-means steering, per Turner et al. activation addition):
  1. From harvested base-condition activations at ONE layer, compute
       v = mean(acts | derail) - mean(acts | non-derail)
     on a VECTOR SPLIT of items, then normalize to unit length so alpha has
     a consistent meaning across layers/models.
  2. During generation on the DISJOINT eval split's prompts, a forward hook
     adds (alpha * v) to that layer's output hidden states at every token
     position of every forward pass (prompt processing and each generated
     token alike -- the standard activation-addition setup).
  3. Sweep alpha over positive and negative values; alpha=0.0 is the
     control arm and MUST be included: it is the same pipeline with a
     zero-magnitude intervention, so any difference between alpha=0 and the
     original API responses measures serving-stack drift, not steering.

Split rationale: computing v from the same items you steer on is circular
(the vector partially encodes those specific items rather than a general
direction). The item split trades sample size for validity.

Alpha scale: because v is unit-normalized, alpha is in absolute residual-
stream units. Typical residual norms grow with depth and vary by model, so
`report_residual_norms` prints the median activation norm at the target
layer -- pick alphas as fractions/multiples of that (e.g. 0.5x to 2x) rather
than guessing blind.

Output: JSONL, one record per (item, alpha), with finish_reason recorded --
same truncation-detectability principle as the main eval pipeline. Judging
these outputs reuses the existing judge pipeline downstream.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType

import numpy as np
import torch
import torch.nn as nn

from lbe.interp.config import HarvestConfig
from lbe.interp.data import ProbeExample, build_probe_examples

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Steering vector construction
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SteeringVector:
    """Unit-norm direction + provenance needed to reproduce/report it."""

    layer_index: int
    vector: np.ndarray  # float32, unit norm
    n_positive: int
    n_negative: int
    positive_label: str
    vector_item_ids: tuple[str, ...]  # items used to BUILD v (excluded from eval)

    def as_tensor(self, dtype: torch.dtype, device: torch.device) -> torch.Tensor:
        return torch.from_numpy(self.vector).to(dtype=dtype, device=device)


def split_items(
    item_ids: list[str],
    labels: dict[str, str],
    positive_label: str,
    vector_fraction: float = 0.5,
    seed: int = 0,
) -> tuple[list[str], list[str]]:
    """
    Deterministic stratified split: (vector_items, eval_items).

    Stratified so both splits keep roughly the 42:58 label ratio -- an
    unstratified split at n=100 can leave one side with too few positives
    either to define v or to measure a rate shift.
    """
    if not 0.0 < vector_fraction < 1.0:
        raise ValueError(f"vector_fraction must be in (0,1), got {vector_fraction}")
    rng = np.random.default_rng(seed)
    pos = sorted(i for i in item_ids if labels[i] == positive_label)
    neg = sorted(i for i in item_ids if labels[i] != positive_label)
    if not pos or not neg:
        raise ValueError(
            f"Split impossible: {len(pos)} positive / {len(neg)} negative items "
            f"for positive_label={positive_label!r}."
        )
    vector_items: list[str] = []
    eval_items: list[str] = []
    for group in (pos, neg):
        perm = rng.permutation(len(group))
        n_vec = max(1, int(round(len(group) * vector_fraction)))
        if n_vec >= len(group):
            n_vec = len(group) - 1  # both splits must be non-empty per class
        for rank, idx in enumerate(perm):
            (vector_items if rank < n_vec else eval_items).append(group[idx])
    return sorted(vector_items), sorted(eval_items)


def build_steering_vector(
    activations: dict[str, dict[int, np.ndarray]],
    labels: dict[str, str],
    layer_index: int,
    positive_label: str,
    vector_item_ids: list[str],
) -> SteeringVector:
    """v = mean(positive) - mean(negative), unit-normalized, from the vector split only."""
    missing = [i for i in vector_item_ids if i not in activations]
    if missing:
        raise ValueError(f"{len(missing)} vector item(s) missing from activations: {missing[:5]}")

    pos_vecs, neg_vecs = [], []
    for item_id in vector_item_ids:
        if layer_index not in activations[item_id]:
            raise ValueError(f"Layer {layer_index} not harvested for item {item_id}.")
        vec = activations[item_id][layer_index]
        (pos_vecs if labels[item_id] == positive_label else neg_vecs).append(vec)

    if not pos_vecs or not neg_vecs:
        raise ValueError(
            f"Vector split has {len(pos_vecs)} positive / {len(neg_vecs)} negative "
            f"examples; both classes are required."
        )

    diff = np.stack(pos_vecs).mean(axis=0) - np.stack(neg_vecs).mean(axis=0)
    norm = float(np.linalg.norm(diff))
    if norm == 0.0 or not np.isfinite(norm):
        raise ValueError(f"Degenerate steering vector (norm={norm}).")

    return SteeringVector(
        layer_index=layer_index,
        vector=(diff / norm).astype(np.float32),
        n_positive=len(pos_vecs),
        n_negative=len(neg_vecs),
        positive_label=positive_label,
        vector_item_ids=tuple(vector_item_ids),
    )


# ---------------------------------------------------------------------------
# Steering hook (modify-mode, vs. the copy-mode ActivationCache)
# ---------------------------------------------------------------------------


class SteeringHook:
    """
    Context manager that ADDS alpha * v to one layer's output hidden states
    on every forward pass while active.

    Handles both tuple-wrapped and bare-tensor layer outputs, mirroring
    ActivationCache. Addition is in the layer's own dtype on its own device.
    alpha can be changed between generations via set_alpha() without
    re-registering the hook.
    """

    def __init__(self, layer: nn.Module, vector: np.ndarray, alpha: float = 0.0) -> None:
        self._layer = layer
        self._vector_np = vector.astype(np.float32)
        self._alpha = float(alpha)
        self._handle: torch.utils.hooks.RemovableHandle | None = None
        self._vector_cache: torch.Tensor | None = None  # lazily built on first pass

    def set_alpha(self, alpha: float) -> None:
        self._alpha = float(alpha)

    def _hook(self, module: nn.Module, inputs: tuple, output):
        hidden = output[0] if isinstance(output, tuple) else output
        if not torch.is_tensor(hidden):
            raise TypeError(
                f"SteeringHook expected tensor (or tuple with tensor first), got {type(hidden)}."
            )
        if self._alpha == 0.0:
            return output  # control arm: exact identity, no numeric noise added
        if (
            self._vector_cache is None
            or self._vector_cache.dtype != hidden.dtype
            or self._vector_cache.device != hidden.device
        ):
            self._vector_cache = torch.from_numpy(self._vector_np).to(
                dtype=hidden.dtype, device=hidden.device
            )
        if self._vector_cache.shape[0] != hidden.shape[-1]:
            raise ValueError(
                f"Steering vector dim {self._vector_cache.shape[0]} != hidden dim "
                f"{hidden.shape[-1]} -- vector was built from a different model/layer width."
            )
        steered = hidden + self._alpha * self._vector_cache  # broadcasts over [batch, seq]
        if isinstance(output, tuple):
            return (steered,) + output[1:]
        return steered

    def __enter__(self) -> SteeringHook:
        self._handle = self._layer.register_forward_hook(self._hook)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._handle is not None:
            self._handle.remove()
            self._handle = None


# ---------------------------------------------------------------------------
# Alpha-sweep generation
# ---------------------------------------------------------------------------


def report_residual_norms(activations: dict[str, dict[int, np.ndarray]], layer_index: int) -> float:
    """Median L2 norm of harvested activations at the layer; anchors the alpha scale."""
    norms = [
        float(np.linalg.norm(per_layer[layer_index]))
        for per_layer in activations.values()
        if layer_index in per_layer
    ]
    if not norms:
        raise ValueError(f"No harvested activations at layer {layer_index}.")
    return float(np.median(norms))


def run_alpha_sweep(
    model,
    tokenizer,
    steering_vector: SteeringVector,
    eval_examples: list[ProbeExample],
    alphas: list[float],
    output_path: Path,
    max_new_tokens: int = 500,
) -> None:
    """
    Generate on each eval prompt at each alpha; append records to output_path.

    Greedy decoding (do_sample=False): with n_eval ~ 50 per alpha, sampling
    noise would swamp rate shifts; greedy makes runs reproducible and any
    output change attributable to alpha alone.

    alpha=0.0 is forced into the sweep as the control arm.
    """
    if 0.0 not in alphas:
        alphas = [0.0] + list(alphas)
        logger.info("alpha=0.0 control arm added to sweep.")

    layers = model.model.layers
    layer = layers[steering_vector.layer_index]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with (
        SteeringHook(layer, steering_vector.vector) as hook,
        output_path.open("a", encoding="utf-8") as out_f,
    ):
        for alpha in alphas:
            hook.set_alpha(alpha)
            logger.info("alpha=%+.2f: generating on %d prompts", alpha, len(eval_examples))
            for i, ex in enumerate(eval_examples, start=1):
                input_ids = tokenizer.apply_chat_template(
                    [{"role": "user", "content": ex.prompt_text}],
                    add_generation_prompt=True,
                    return_tensors="pt",
                ).to(model.device)
                with torch.no_grad():
                    gen = model.generate(
                        input_ids,
                        max_new_tokens=max_new_tokens,
                        do_sample=False,
                        pad_token_id=tokenizer.eos_token_id,
                        return_dict_in_generate=True,
                    )
                seq = gen.sequences[0]
                completion = tokenizer.decode(seq[input_ids.shape[1] :], skip_special_tokens=True)
                finish_reason = (
                    "length" if (seq.shape[0] - input_ids.shape[1]) >= max_new_tokens else "stop"
                )
                record = {
                    "item_id": ex.item_id,
                    "category": ex.category,
                    "condition": ex.condition,
                    "responder_model": ex.responder_model,
                    "layer_index": steering_vector.layer_index,
                    "alpha": alpha,
                    "positive_label": steering_vector.positive_label,
                    "completion": completion,
                    "finish_reason": finish_reason,
                    "max_new_tokens": max_new_tokens,
                }
                out_f.write(json.dumps(record) + "\n")
                if i % 10 == 0 or i == len(eval_examples):
                    logger.info("  alpha=%+.2f: %d/%d", alpha, i, len(eval_examples))
    logger.info("Sweep complete -> %s", output_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--hardware-profile", choices=["local_dev", "rental_gpu"], required=True)
    parser.add_argument("--activations-path", required=True, type=Path)
    parser.add_argument("--labels-path", required=True, type=Path)
    parser.add_argument("--items-path", required=True, type=Path)
    parser.add_argument("--results-path", required=True, type=Path)
    parser.add_argument("--judgments-csv", required=True, type=Path)
    parser.add_argument(
        "--layer-index",
        required=True,
        type=int,
        help="Choose from probe results: best p-value layer.",
    )
    parser.add_argument("--alphas", type=float, nargs="+", required=True)
    parser.add_argument("--positive-label", default="derail")
    parser.add_argument("--category", default="values_conflict_low")
    parser.add_argument("--condition", default="base", choices=["base", "steered"])
    parser.add_argument(
        "--responder-model", default="together:meta-llama/Llama-3.3-70B-Instruct-Turbo"
    )
    parser.add_argument("--vector-fraction", type=float, default=0.5)
    parser.add_argument("--split-seed", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=500)
    parser.add_argument(
        "--output-path", default=Path("results/interp/steering_sweep.jsonl"), type=Path
    )
    args = parser.parse_args()

    activations = torch.load(args.activations_path, weights_only=False)
    labels: dict[str, str] = json.loads(args.labels_path.read_text())

    median_norm = report_residual_norms(activations, args.layer_index)
    logger.info(
        "Median residual norm at layer %d: %.1f -- alphas %s are %s of it.",
        args.layer_index,
        median_norm,
        args.alphas,
        [f"{a / median_norm:.2f}x" for a in args.alphas],
    )

    vector_items, eval_items = split_items(
        sorted(activations),
        labels,
        args.positive_label,
        vector_fraction=args.vector_fraction,
        seed=args.split_seed,
    )
    logger.info("Split: %d vector items, %d eval items.", len(vector_items), len(eval_items))

    sv = build_steering_vector(
        activations, labels, args.layer_index, args.positive_label, vector_items
    )

    examples = build_probe_examples(
        items_path=args.items_path,
        results_path=args.results_path,
        judgments_csv=args.judgments_csv,
        category=args.category,
        condition=args.condition,
        responder_model=args.responder_model,
    )
    eval_set = set(eval_items)
    eval_examples = [ex for ex in examples if ex.item_id in eval_set]

    cfg = HarvestConfig(
        model_name=args.model_name,
        hardware_profile=args.hardware_profile,
        category=args.category,
        condition=args.condition,
        responder_model=args.responder_model,
    )
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(cfg.model_name)
    model = AutoModelForCausalLM.from_pretrained(
        cfg.model_name,
        torch_dtype=cfg.torch_dtype,
        attn_implementation=cfg.attn_implementation,
        device_map=cfg.device_map,
    )
    model.eval()

    run_alpha_sweep(
        model,
        tokenizer,
        sv,
        eval_examples,
        list(args.alphas),
        args.output_path,
        max_new_tokens=args.max_new_tokens,
    )


if __name__ == "__main__":
    main()
