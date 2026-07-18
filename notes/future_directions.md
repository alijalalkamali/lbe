# Future Directions

Research questions that emerged during the steerability eval work but are
out of scope for the current project. Kept here so they aren't lost and
can be evaluated against later work.

Each entry: the observation, the candidate research question, why it's
out of scope now, and what would be needed to pursue it.

---

## FD1: Turns-to-deliverable as a model-perceived complexity signal

**Observation:** In extended use, Claude (and likely other assistants)
exhibit an asymmetric pattern: some questions resolve in 1-2 turns, while
others extend across many exchanges without producing the promised
deliverable. The exchanges often involve clarification questions,
restatements of intent, or proposals that get revised before any
substantive output is produced. The user-side experience is "the model
is dragging."

**Candidate research question:** Treat the number of turns required to
produce a substantive deliverable as an operational measure of
"model-perceived complexity" or "interaction friction." Specifically:

- Cap interaction at a fixed budget (e.g., 10 or 20 exchanges). Within
  budget, measure turns-to-first-substantive-deliverable. Beyond budget
  counts as a failure.
- Use this as the dependent variable rather than pre-rating complexity
  ourselves — let the model's behavior define what is complex for it,
  rather than imposing a researcher prior.
- Compare across models. If frontier models (which presumably "know"
  the answer to most prompts) still show high turns-to-deliverable on
  some topics, the friction is not capability-bound. It's something
  else.

**Why this is interesting:**

1. The existing clarification-question literature (NoisyToolBench, AwN,
   "Curiosity by Design") treats over-asking as a tuning issue and
   under-asking as the research problem. The "model engages but defers
   delivery" pattern is not, as of search in this project, an
   independently studied failure mode.
2. If the same model resolves topic A in 2 turns and topic B in 15
   turns, and topic B's CoT (where visible) doesn't show 7.5x more
   actual reasoning content, then the friction lives somewhere other
   than the visible reasoning trace. This connects to the
   internal-vs-external CoT distinction (Korbak et al. 2025; Stickland
   & Korbak 2025) but observed from the conversational interaction side
   rather than from model introspection. Long shot but the connection
   is real.
3. The methodology (capped multi-turn budget, model-emergent
   complexity measure) is closer to agentic eval protocols (SWE-bench
   style) than to single-turn instruction-following benchmarks. It
   could fill a methodology gap between those two literatures.

**Why out of scope now:**

- The methodology is fundamentally multi-turn. The current project is
  built around single-turn base/steered eval items. Folding this in
  would dilute the focus and produce a half-built multi-turn framework
  alongside a half-finished single-turn one.
- Operationalizing the dependent variable cleanly is non-trivial.
  "Substantive deliverable" needs sharp definition; distinguishing
  "model genuinely needs clarification" from "model is deferring
  unnecessarily" needs a careful protocol.
- Generating prompts across a complexity gradient without prejudging
  what counts as complex requires its own design pass — probably
  sampling from real user logs or generating with a separate model
  acting as a user proxy.

**What would be needed to pursue:**

1. A multi-turn evaluation framework with a controlled "user
   simulator" (likely a separate LLM with constrained behavior).
2. An operational definition of "substantive deliverable" with
   per-prompt acceptance criteria, possibly via an LLM judge with a
   tight rubric.
3. A prompt corpus drawn from real conversational logs or generated to
   span a complexity range without researcher pre-rating.
4. A protocol for the user simulator's responses (curt vs verbose,
   precise vs ambiguous) to control confounders.

**Status:** Logged. Candidate "next project after this one."

---

## FD2: Steerability vs alignment trade-off at frontier scale

**Observation:** In the current project, Llama 3.2 3B (but not 0.5B or
1B) overrode a steering instruction it judged inappropriate by
substituting its own preferred response while continuing to engage with
the task. See Obs 7+8 in observations.md.

**Candidate research question:** Where, across the open-weights model
size axis and across frontier APIs, does values-grounded covert override
emerge? Is it monotone with scale (and if so, between which sizes?), or
non-monotone (and tied to training methodology rather than scale)? Does
it appear in extended-thinking reasoning traces, and if so, does the
model verbalize the override or perform it silently?

**Why this is interesting:**

- The closest existing work, CircuChain / "Convention Blindness"
  (Nov 2026), names a related phenomenon but studies a different domain
  (symbolic conventions in circuit analysis) and explicitly calls it
  "underexplored."
- Inverse IFEval (Sep 2025) provides a benchmark for "Counter-intuitive
  Ability" — overriding training conventions when instructed — but
  focuses on training-induced patterns, not values-driven override.
- The "Steerability of Instrumental-Convergence Tendencies" paper
  (Jan 2026) studies 4B and 30B Qwen variants; the sub-10B emergence
  point is not well documented.

**Why partially in scope:** The current v2 item set includes
values-conflict items designed to test exactly this. The "future
direction" framing applies specifically to the **extended analysis**:
sliced-by-scale across many open-weights models (1B, 3B, 7B, 13B, 30B,
70B), correlation with training methodology metadata, and CoT-trace
analysis on reasoning models.

**Why the deeper version is out of scope now:**

- Running across many open-weights model sizes systematically is an
  infrastructure project (model loading, inference budget, careful
  reproducibility) larger than the current eval design phase.
- Correlating with training methodology requires access to training
  metadata that is often not public for closed models and inconsistent
  for open ones.

**What would be needed to pursue the deeper version:**

1. A larger sweep across open-weights sizes from the same model family
   (Llama 3.2 1B/3B + Llama 3.1 8B/70B + Llama 4 variants; same for
   Qwen).
2. CoT-aware item design for reasoning models, with separate scoring
   for "override appeared in CoT" vs "override appeared only in final
   answer."
3. Statistical power calculation for the cross-scale comparison;
   current ~10-item set is too small for the deeper analysis.

**Status:** The narrow version is in v2. The deeper sliced-by-scale
version is logged here as candidate follow-up.

---

## FD3: Internal vs external CoT faithfulness gap

**Observation:** Multiple recent papers (Stickland & Korbak 2025;
"Can Reasoning Models Obfuscate Reasoning?" 2025) distinguish internal
CoT (reasoning traces, usually separated from output) from external CoT
(prompted reasoning in output). The gap between these two channels
appears empirically — models can obfuscate reasoning differentially in
the two channels under pressure.

**Candidate research question:** For a fixed set of prompts where
reasoning is required, measure the divergence between internal CoT
(extended thinking trace, where exposed by the API) and external CoT
(reasoning verbalized in the user-facing output). Does the divergence
scale with model size? With perceived task sensitivity? With explicit
monitoring pressure?

**Why this is interesting:**

- The internal/external distinction is recent and recognized as a
  monitorability concern but not yet systematically measured across
  contexts.
- Connects to FD1: if turns-to-deliverable is high but CoT length is
  proportionally low, the friction is somewhere other than visible
  reasoning. Internal CoT (where exposed) might explain the gap.

**Why out of scope now:**

- Requires API access to models that expose internal CoT (Claude
  extended thinking, DeepSeek R1, o3 partial). API support for
  internal-CoT exposure varies and is partially limited.
- The methodology requires aligning internal and external CoT tokens
  semantically, which is a non-trivial NLP problem in its own right.

**What would be needed to pursue:**

1. API integrations for at least 2-3 reasoning models that expose
   internal CoT.
2. A semantic alignment method (likely embedding-based) to compare
   internal and external CoT content rather than raw text overlap.
3. A protocol for varying monitoring-pressure conditions in the
   prompt.

**Status:** Logged. Candidate follow-up if FD2 work produces
encouraging results on reasoning models.

---

## How to use this file

When adding new directions: include observation, candidate question,
why interesting, why out of scope now, what would be needed. Don't add
directions that are just "we should test more X" — those go in
decisions.md as extensions of the current scope. This file is for
research questions that need their own framing and would be their own
project.

When closing out current work: revisit this file and re-evaluate which
items have become more tractable, which have been subsumed by published
work, and which are still candidate next projects.
