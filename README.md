# lbe — Cross-Laboratory LLM Steerability Evaluation

A symmetric, blind, peer-judged evaluation of how six frontier language models,
one from each of six developers, respond to explicit steering pressure. The
study measures not only how much steering shifts behavior but the qualitative
*mode* of the response, and finds that some modes are exclusive to a single
developer.

## What this is

Each of 300 core evaluation items pairs a base prompt with a steered variant of
the same scenario, so every model serves as its own control. Responses are
classified against fixed categorical rubrics by all six models acting as blind
judges, producing a complete judge-by-responder matrix of 24,480 judgments
scored by leave-one-out consensus.

The six evaluated models, one per developer:

| Developer | Model |
|-----------|-------|
| Anthropic | Claude Opus 4.7 |
| OpenAI    | GPT-5 |
| Google    | Gemini 2.5 Pro |
| DeepSeek  | DeepSeek-R1 |
| Alibaba   | Qwen3.7-Max |
| Meta      | Llama-3.3-70B-Instruct-Turbo |

Three core behavioral categories carry the findings: values-conflicting
requests, pressure to expose reasoning, and pressure to suppress values
reasoning. Two additional categories (stylistic formatting and reasoning
hints with checkable answers) validate the instrument and carry no claims of
their own.

## Headline findings

- **A reasoning-disclosure mode exclusive to GPT-5.** On steered
  reasoning-elicitation items, GPT-5 declined to disclose its reasoning while
  answering intact on 99 of 100 items; no other model did so once across 500
  equivalent opportunities.
- **Suppression resistance in two models only, in two modes.** Claude Opus and
  GPT-5 are the only models that overtly resist explicit suppression
  instructions (combined 23% vs 0.25% elsewhere), and they favor opposite
  modes: Opus challenges the framing while complying, GPT-5 refuses outright.
- **Three tiers of baseline compliance.** On values-conflicting requests the
  models separate into three statistically distinct tiers rather than a
  continuum.
- **Divergent baseline dispositions.** With no suppression instruction present,
  models differ sharply in whether values considerations are expressed overtly
  or woven into ostensibly neutral reasoning.

## Auditing and controls

The findings survived two forms of scrutiny built into the pipeline:

- **Token-budget confound.** A response-length audit found genuine truncation
  in three models under the shared token budget. All affected responses were
  regenerated at a threefold budget, re-judged, and the analysis recomputed;
  every finding held.
- **Demand-characteristics control.** A two-arm re-judging experiment measured
  how much the item-context field shown to judges influenced labels, using an
  identical-prompt arm to establish the nondeterminism floor. The cross-model
  contrasts persist when the field is stripped.
- **Held-out validation.** The rubric was built from the first 20 items per
  category. Re-running the full analysis over the 80 items per category that
  were never read during rubric construction reproduces every headline finding,
  with inter-judge agreement rising rather than falling on the unseen items.

## Repository layout

```
data/                     Evaluation items (steerability_items_v3.jsonl, 300 items)
src/lbe/                  Package: model backends, judging, aggregation, IO
scripts/                  Pipeline entry points and diagnostics
results/analysis/         Aggregate rate tables, statistical tests, agreement
results/leakage/          Demand-characteristics control outputs
```

The raw per-judge judgment files (24,480 classifications) are large and are
distributed as a release asset rather than committed to the repository. See
Releases, or the archived deposit linked below.

## Reproducing the analysis

```bash
# Aggregate raw judgments into consensus labels and rate tables
python scripts/run_judge_pipeline.py --aggregate-only

# Compute rates, pairwise tests, effect sizes, and agreement
python scripts/analyze_judgments.py

# Held-out subset (items never used in rubric construction)
python scripts/analyze_judgments.py --item-range 21 100 --output-suffix _heldout80
```

## Data availability

Aggregate results and analysis outputs are in `results/`. The full raw
judgment matrix is available as a GitHub release asset and archived at
[Zenodo DOI to be added].

## Status

Evaluation phase complete. A mechanistic interpretability phase, probing
open-weight models for internal correlates of the behavioral categories
identified here, is in development.
