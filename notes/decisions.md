# Design decisions

Choices made in building the eval framework, with rationale.

## Schemas at the disk boundary

**Decision:** Pydantic for `EvalItem` (and subclasses), `EvalResult`. Dataclasses for in-memory types like `GenerationOutput`.

**Rationale:** Pydantic provides runtime validation, JSON parsing, and clear error messages when data is malformed. Worth the dependency at the boundary where untrusted input (JSONL files) becomes typed Python objects. In-memory types we control, so dataclasses are sufficient and cheaper.

## Discriminated unions via Literal types

**Decision:** Each subclass of `EvalItem` declares `item_type: Literal["steerability"] = "steerability"` etc.

**Rationale:** Allows JSON round-tripping to preserve subclass identity. Without the `item_type` discriminator, parsing a JSONL row gets you back a generic `EvalItem` and loses subclass-specific fields. Standard pattern for tagged unions.

## Model abstraction

**Decision:** Abstract `Model` base class with `LocalHFModel` subclass. Factory function `load_model(name)` dispatches by name pattern (currently: contains "/" → HuggingFace).

**Rationale:** Eval code doesn't need to know which backend it's using. Same `model.generate(...)` call works for local HF models, future API models, future vLLM, etc. When we add `AnthropicAPIModel` (Day 18), we modify the factory and nothing else.

## Hybrid scoring (rule-based + LLM-judge)

**Decision:** Rule-based scoring for structural properties (length, format). LLM-as-judge for nuanced properties (tone, persona, etc.) — to be added later. Categories without rule-based scorers explicitly return `None` and are flagged for LLM-judge.

**Rationale:**
- For structural properties, rules are more reliable and reproducible than LLM-judge. A regex matches deterministically; an LLM judge might inconsistently judge "is this a list."
- For nuanced properties, rules cannot even attempt. LLM-judge is the only option.
- Using the appropriate tool per property is more defensible than using LLM-judge for everything because it was easier.

## Greedy decoding for steerability

**Decision:** `temperature=0.0`, `seed=42` for all steerability runs.

**Rationale:** Steerability tests whether the model can shift its preferred behavior. We want the model's strongest preference, not noisy samples. Greedy decoding is fully reproducible — same prompt gives same response, every time. Seed is belt-and-suspenders.

For other evals (e.g., consistency), we will use `temperature > 0` with multiple seeds, because variation is the property being measured.

## Binary scoring (initial version)

**Decision:** Steerability score is binary — 1.0 if the metric moved in the expected direction, 0.0 if not. None if unscorable.

**Rationale:** Simple to interpret and aggregate. Easy to extend to continuous later if needed (e.g., "distance from target sentence count" instead of "did sentence count decrease"). Starting binary makes the eval pipeline working end-to-end faster.

**Known limitation:** binary scoring rewards directional improvement even when the model misses the target. E.g., asked for 2 sentences, got 3 — scores 1.0 because count decreased. Worth revising to target-accuracy scoring.

## Registry pattern for scorers

**Decision:** Scorers live in a dict `SCORERS: dict[str, Scorer]` keyed by category.

**Rationale:** Explicit (all supported categories visible at a glance), extensible (one line to add a category), testable (can iterate keys to check coverage), replaceable (mock scorers in tests by replacing dict values).

## `extra: dict` field on EvalResult

**Decision:** `EvalResult` has top-level fields for things shared across eval types (item_id, model_name, score, raw_completions) and an `extra: dict` for eval-specific data.

**Rationale:** Different evals produce different per-result data (base metric vs steered metric for steerability, paraphrase responses for consistency, intervention details for faithfulness). Putting all of those in named fields would bloat the schema with mostly-unused fields. The `extra` dict is an escape hatch.

**Known limitation:** Data inside `extra` is not type-checked. Typos in `result.extra["..."]` lookups will produce KeyErrors at runtime.

## Eval items in version control

**Decision:** `data/*.jsonl` files are tracked in git (exception in `.gitignore`). Other data is not.

**Rationale:** Hand-crafted eval items are research artifacts central to the project — they encode decisions about what to measure. Reproducibility requires them. Bulk data (large datasets, model weights, raw outputs) doesn't go in git, only eval items do.

## What's deferred

- **API backend (`AnthropicAPIModel`)**: Day 18. YAGNI until we need cross-scale validation.
- **LLM-judge scorer**: needed for tone, persona, balance, reasoning_style, audience_adaptation categories. Add when we have API access.
- **Continuous (non-binary) scoring**: revisit once we have multi-model results and see which scoring approach reveals the most.
- **More eval categories**: current 7 categories cover steerability. Consistency and faithfulness will add their own.
