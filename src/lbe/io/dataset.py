"""Schemas for eval items and eval results.

EvalItem and its subclasses define the input shape for each eval type.
EvalResult captures what comes back after running one item against one model.

Loaded from and saved to JSONL files for reproducibility -
Pydantic handles JSON parsing and validation at the disk boundary so corrupt rows fail.
"""

from typing import Literal

from pydantic import BaseModel, Field


class EvalItem(BaseModel):
    """Base class for all eval items.

    Every eval item has an ID,
    a category for slicing analyses, and free-form metadata.
    Subclasses and type-specific fields.
    """

    id: str
    category: str
    metadata: dict = Field(default_factory=dict)


class SteerabilityItem(EvalItem):
    """One steerability test case.

    The model is promoted twice: once with 'base_prompt' alone,
    once with 'base_prompt + steering_instruction'.
    We measure whether the model's behavior changed in the way
    the steering instruction asked for.
    """

    item_type: Literal["steerability"] = "steerability"
    base_prompt: str
    steering_instruction: str
    expected_behavior_change: str  # human-readable description for scoring


class ConsistencyItem(EvalItem):
    """One consistency test case.

    The model is asked the same question multiple ways -
    'base_prompt' plus 'paraphrases'.
    For factual questions there's a 'correct_answer' to score against;
    for non-factual questions we just measure response variance.
    """

    item_type: Literal["consistency"] = "consistency"
    base_prompt: str
    paraphrases: list[str]
    correct_answer: str | None = None


class FaithfulnessItem(EvalItem):
    """One CoT faithfulness test case.

    The model produces chain-of-thought reasoning, then we intervene on one
    step and see if the final answer changes. If the answer is invariant to
    the intervention, the CoT was post-hoc rather than causal.
    """

    item_type: Literal["faithfulness"] = "faithfulness"
    question: str
    correct_answer: str
    intervention_target: str  # what part of the CoT we'll intervene on


class EvalResult(BaseModel):
    """Result of running one eval item against one model.

    Captures enough to reproduce the experiment and slice the analysis later
    by model, item category, seed, etc.

    Attributes:
        item_id: The item this result is for.
        item_type: Discriminator matching the EvalItem subclass used.
        model_name: Loader identifier of the responding model.
        seed: Legacy field. NOT applied per-call by any API backend — the
            Model interface deliberately excludes sampling controls (see
            base.py) because most provider APIs reject them for reasoning
            models. Backends that do apply a seed set it internally at
            request time and document it. Retained for schema compatibility
            with existing result files; do not read it as evidence that a
            seed was applied to this generation.
        raw_completions: One entry per generation. For steerability v2 this
            is exactly [base_response, steered_response].
        finish_reasons: Provider stop-reason per entry in raw_completions,
            same order and length. None for records written before this
            field existed — absence means "not recorded", NOT "completed
            cleanly". Use this to detect responses truncated at the token
            ceiling, which would otherwise be indistinguishable from a model
            simply choosing to answer briefly.
        score: Eval-specific scalar; None if not yet scored.
        extra: Eval-specific extras (e.g. {"category": ...}).
    """

    item_id: str
    item_type: str
    model_name: str
    seed: int | None
    raw_completions: list[str]  # one per generation (multiple if multi-seed)
    finish_reasons: list[str | None] | None = None
    score: float | None  # eval-specific scalar; None if not yet scored
    extra: dict = Field(default_factory=dict)  # eval-specific extras
