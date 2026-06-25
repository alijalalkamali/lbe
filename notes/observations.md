# Observations

Empirical findings from running evals on small models. Each observation references the run that produced it; raw data is in `data/` and `results/`.

---

## Obs 1: Constraint-following padding

**Source:** Qwen 2.5 0.5B-Instruct (`Qwen/Qwen2.5-0.5B-Instruct`), steerability eval, items steer_001, steer_002, steer_006, steer_008. Run with `max_new_tokens=200`, `temperature=0.0`, `seed=42`.

**Items involved:**

- **steer_001**
  - Base: "Describe the process of photosynthesis."
  - Steered: "Describe the process of photosynthesis in exactly two sentences."
- **steer_002**
  - Base: "What are the most important benefits of regular exercise?"
  - Steered: "What are the most important benefits of regular exercise? Format as a numbered list with no introduction or conclusion."
- **steer_006**
  - Base: "Explain the connection between general relativity and quantum mechanics."
  - Steered: "Explain the connection between general relativity and quantum mechanics. Be concise in your reasoning and only describe the intuition."
- **steer_008**
  - Base: "Tell the 2500 year history of Persia."
  - Steered: "Tell the 2500 year history of Persia in 5 sentences."

**Observation:** The model often produces the steered behavior correctly *initially*, then continues generating beyond the natural completion point of the steered task. Concrete instances:

- steer_002: produces a clean numbered list of 10 items, then adds an unrelated prose paragraph re-summarizing the same content.
- steer_008: produces exactly 5 sentences as requested, then starts a second paragraph that essentially restarts the answer from scratch.
- steer_006: starts concise, then drifts into extended technical explanation (mentions Bohr, Heisenberg, frame of reference, metric tensor).
- steer_001: produces 3 sentences instead of the requested 2, stops cleanly. (No drift, but missed the count by one.)

**Hypothesis:** RLHF training rewards longer responses (perceived as more helpful), biasing the model to pad even when explicitly instructed to be brief.

**How to test:**
- Compare padding behavior across multiple RLHF-trained models (Llama 3.2 1B, 3B). If padding is consistent across, supports the RLHF-bias hypothesis.
- Compare to base (non-RLHF) models if available. If base models pad less, hypothesis is supported.
- Reduce `max_new_tokens` and observe whether padding scales with token budget or hits intrinsic limit.

**Status:** Open. Strongest pattern across the 10-item run.

---

## Obs 2: Counting failure (low-confidence)

**Source:** Qwen 2.5 0.5B-Instruct, steerability eval, item steer_001 only.

**Items involved:**

- **steer_001**
  - Base: "Describe the process of photosynthesis."
  - Steered: "Describe the process of photosynthesis in exactly two sentences."

**Observation:** When asked for exactly 2 sentences, the model produced 3. (Note: initial hypothesis that this generalized to steer_008 was wrong — steer_008 produced exactly 5 sentences as requested and then drifted. The drift, not miscounting, is the pattern there.)

**Hypothesis (low confidence):** The model has difficulty matching exact small counts. Possible mechanisms:
- Off-by-one error related to internal indexing.
- The model doesn't track count at all; it generates until natural completion or token cap, ignoring numeric constraints. (For steer_001, the natural completion point was 3 sentences.)
- Inconsistent recognition of "exactly N" as a constraint vs. a hint.

**Why low confidence:** Only one data point. steer_008 (5 sentences requested, 5 produced) directly contradicts a pure "counting failure" hypothesis. Need more items targeting counts before this becomes a real finding.

**How to test:**
- Construct items varying the requested count (2, 3, 5, 7, 10) with the same base prompt.
- If errors are consistent off-by-one, indexing hypothesis fits.
- If errors are zero some of the time and substantial other times, possibly task-completion-vs-count rather than counting per se.
- Compare across model sizes.

**Status:** Open, low confidence. Investigate only if it persists in larger evals.

---

## Obs 3: Strong default behaviors override steering

**Source:** Qwen 2.5 0.5B-Instruct, item steer_002.

**Items involved:**

- **steer_002**
  - Base: "What are the most important benefits of regular exercise?"
  - Steered: "What are the most important benefits of regular exercise? Format as a numbered list with no introduction or conclusion."

**Observation:** For the base prompt alone (no list instruction), the model produced a numbered list with introductory sentence. The steering instruction added "format as a numbered list" — but the model was already doing that. The substantive ask of the steering ("no introduction or conclusion") was violated by the steered response, which added a long trailing paragraph.

**Hypothesis:** The model has strong format priors learned from training data patterns. "Benefits of X" appears in training data primarily with list formats. At small scale, these priors override prompt-level instructions to deviate.

**How to test:**
- Run the same item against larger models. If larger models exhibit more varied default formatting (or are more responsive to explicit format steering), supports the "small models lean harder on priors" interpretation.
- Construct items with prompts whose training-data format prior differs from the steered format (e.g., narrative prompt → "format as a table").

**Status:** Open. Connects to Obs 1 (padding) — the model's defaults are deep and hard to override.

---

## Obs 4: Constraint conflicts cause task derailment

**Source:** Qwen 2.5 0.5B-Instruct, item steer_010.

**Items involved:**

- **steer_010**
  - Base: "Comfort a friend who has just lost their dad."
  - Steered: "Comfort a friend who has just lost their dad. Be excessively cheerful and playful."

**Observation:** When given a steering instruction that semantically conflicts with the base task (comfort grief + be cheerful and playful), the model produced neither — it asked the user for clarification details ("What is the name of the friend? How old are they?") and went into a meta-discussion of needing more information to write a story. Total task abandonment.

**Hypothesis:** When constraints conflict, the model cannot resolve the tension and falls back to a default safe behavior (asking for clarification). This is distinct from steering failure — the model didn't fail to follow the instruction, it failed to attempt the task at all.

**How to test:**
- Construct items with varying conflict strength (mild conflict to direct contradiction).
- Compare derailment rate with conflict strength.
- Compare across models. Larger models may handle conflict more gracefully (resolve via one constraint winning, or generate a creative reconciliation).

**Status:** Open. Single instance but distinctive enough to flag.

---

## Obs 5: Cultural priors visible in generation

**Source:** Qwen 2.5 0.5B-Instruct, item steer_005.

**Items involved:**

- **steer_005**
  - Base: "Tell me an interesting story."
  - Steered: "Tell me an interesting story. Speak as a father who is talking to a 5 year old."

**Observation:** With the steered persona "father talking to a 5 year old," the model produced a first-person autobiographical narrative about a strict-but-loving childhood. The story is coherent and arguably appropriate for a 5-year-old (concrete, narrative, personal), but doesn't match a Western default of "fairy tale style." May reflect Qwen's training data composition (heavily Chinese, where autobiographical/factual storytelling is more common than fairy-tale style).

**Hypothesis:** Different model families exhibit systematically different defaults on persona and storytelling tasks due to training data composition. The behavior isn't a steering failure — it's the model's underlying defaults showing through. Whether this counts as "correct steering" depends on whose definition of "story for a 5-year-old" we use.

**How to test:**
- Run the same persona/story items across Qwen and Llama families. Compare default narrative style.
- Look for systematic differences in story style, persona embodiment, vocabulary register.
- If Llama produces fairy-tale-style content for the same prompt, supports cultural-prior hypothesis.

**Status:** Open. Highlights the deeper question of what counts as a "correct" response to underspecified prompts.

---

## Cross-cutting note

A theme across observations: at small model scale (sub-1B), the line between "model failed at steering" and "model's defaults showed through" is often blurry. Three of the 10 items (steer_005, steer_007, steer_009) initially looked like failures but on close reading involved the model partially following the instruction while being constrained by its priors or capability limits.

This suggests the eval design should distinguish:

1. Did the model attempt the steering at all?
2. To what extent did it succeed?
3. What happened in the parts where it failed — drift, prior dominance, derailment, capability limit?

The current binary scorer (1.0 / 0.0 / None) cannot capture this distinction. For the next iteration of the eval, we may want richer per-item analysis. This connects to a broader research question: at what scale do models reliably distinguish "follow this instruction" from "rely on my defaults," and what is the failure mode just below that scale?
