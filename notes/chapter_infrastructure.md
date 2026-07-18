# Chapter: Infrastructure Buildout for v2 Steerability Evaluation

**Chapter status:** Complete. Verified facts unless otherwise noted.
**Coverage:** All code and infrastructure decisions made during v2 buildout.
**Not covered:** Data collection results (see Chapter: Data Collection), judge
pipeline (see Chapter: LLM-Judge Pipeline), pending decisions (see Chapter:
Open Questions).

## Project structure at end of this phase

```
~/projects/anthropic/
├── data/
│   ├── steerability_items.jsonl                     (v1, from earlier chats)
│   └── steerability_items_v2.jsonl                  (v2, 100 items, this chat)
├── src/lbe/
│   ├── evals/
│   │   ├── steerability.py                          (v1)
│   │   └── steerability_v2.py                       (v2, this chat)
│   ├── io/
│   │   ├── dataset.py                               (unchanged, from earlier)
│   │   └── jsonl.py                                 (unchanged)
│   ├── models/
│   │   ├── base.py                                  (unchanged)
│   │   ├── local.py                                 (unchanged)
│   │   ├── loader.py                                (rewrote for API routing)
│   │   ├── api_utils.py                             (new)
│   │   ├── anthropic_backend.py                     (new)
│   │   ├── openai_backend.py                        (new)
│   │   ├── deepseek_backend.py                      (new)
│   │   ├── together_backend.py                      (new)
│   │   └── google_backend.py                        (new)
│   └── judging/                                     (new package)
│       ├── __init__.py
│       ├── rubrics.py
│       ├── judge_prompt.py
│       ├── judge_output.py
│       ├── run_judges.py
│       └── aggregate.py
├── scripts/
│   ├── run_v2_local.py                              (misleading name; runs
│   │                                                 both local and API)
│   ├── dump_readable_v2.py                          (readable txt from jsonl)
│   ├── count_empty_responses.py                     (diagnose broken runs)
│   ├── rerun_items.py                               (targeted re-runs)
│   └── run_judge_pipeline.py                        (judge orchestration)
├── results/
│   ├── steerability_v2_<8 model files>.jsonl        (data collection outputs)
│   ├── <slug>-v2-readable.txt                       (readable close-reading versions)
│   └── judgments/                                   (populated by judge pipeline)
└── notes/
    ├── setup.md                                     (from earlier chats)
    ├── decisions.md                                 (from earlier chats)
    ├── observations.md                              (from earlier chats)
    └── future_directions.md                         (from earlier chats)
```

## v2 items file: `steerability_items_v2.jsonl`

100 items across 5 categories, 20 items per category.

**Categories and their purpose (as designed):**

- `stylistic` (sty): style/register adoption. Baseline steerability check.
- `values_conflict_low` (vcl): low-stakes values-conflict instructions (write
  cheerful comfort for grief, tactless birthday message, arrogant cover
  letter, etc.). Novel category exploring values-override behavior.
- `reasoning_hint` (rh): math problems with an injected wrong-answer hint.
  Direct replication of Chen 2025 / Turpin 2023 methodology.
- `reasoning_values_elicit` (rve): values-adjacent questions with explicit
  "think step by step" prompt. Tests whether CoT elicitation surfaces
  values considerations.
- `reasoning_values_suppress` (rvs): values-adjacent questions with explicit
  instruction to suppress values reasoning ("give me the strategic answer,
  don't lecture me about ethics"). Novel category.

**Schema (verified, matches `SteerabilityItem` in `dataset.py`):**

```
{
  "id": "sty_001",
  "category": "stylistic",
  "item_type": "steerability",
  "base_prompt": "...",
  "steering_instruction": "...",
  "expected_behavior_change": "...",
  "metadata": {}
}
```

## Backend architecture: `provider:model` routing

**Verified fact:** the loader routes on `:` prefix. Format is `provider:model`.

**Supported providers and example model strings:**

- `anthropic:claude-haiku-4-5`
- `anthropic:claude-opus-4-7`
- `anthropic:claude-sonnet-4-6` (available, not yet run)
- `openai:gpt-5`
- `openai:o4-mini` (available via reasoning-model routing, not yet run)
- `deepseek:deepseek-reasoner` (R1)
- `deepseek:deepseek-chat` (V3, available, not yet run)
- `together:meta-llama/Llama-3.3-70B-Instruct-Turbo`
- `together:Qwen/Qwen3.7-Max`
- `google:gemini-2.5-pro`
- `google:gemini-3.1-pro-preview` (available; 250/day quota)

Local models (no prefix) continue to work via the HuggingFace ID form
`org/model` (e.g., `Qwen/Qwen2.5-0.5B-Instruct`).

## Per-provider quirks encountered and resolved

**Anthropic (`anthropic_backend.py`):**
- Opus 4.7 rejects the old `thinking={"type":"enabled", "budget_tokens":N}`
  API. Requires new adaptive API: `thinking={"type":"adaptive", "display":
  "summarized"}` plus `output_config={"effort":"high"}`.
- Opus 4.7 and newer models reject `temperature`, `top_p`, `top_k` — request
  parameters must omit these.
- `display: "summarized"` is required to get visible thinking traces —
  4.7+ defaults to `"omitted"` which returns empty thinking blocks.
- Haiku 4.5 does not support extended thinking; uses standard temperature=0.0.
- Reasoning tokens count against `max_tokens`. Buffer of 4000 added.
- Response format when thinking is enabled: `<thinking>...</thinking>\n\n<answer>`
- Thinking traces are visible on some rh, rvs items; not on all vcl items
  (adaptive thinking selective by complexity).

**OpenAI (`openai_backend.py`):**
- GPT-5 rejects `max_tokens`, requires `max_completion_tokens`.
- GPT-5 rejects `temperature`, `top_p`, `seed`.
- GPT-5 is in `REASONING_MODEL_PREFIXES = ("o1", "o3", "o4", "gpt-5")`.
- Reasoning tokens consume `max_completion_tokens` budget silently.
- Without a reasoning buffer, ~50% of responses came back empty.
- With buffer of 4000, 98/100 items complete; 2 items still needed
  targeted rerun (sty_002 base, rvs_014 steered).
- Reasoning content is NOT exposed in the response.
- Total run cost: ~$3 for 100 items × 2 conditions after fixes.

**DeepSeek (`deepseek_backend.py`):**
- Uses OpenAI SDK with `base_url="https://api.deepseek.com"`.
- `deepseek-reasoner` rejects `temperature`.
- `deepseek-reasoner` exposes reasoning trace as `reasoning_content` field
  on the message. Backend prepends as `<thinking>...</thinking>`.
- Verbose responses across all items; every response has thinking block.
- Total run cost: ~$0.02 for 100 items × 2 conditions. Cheapest by far.

**Together AI (`together_backend.py`):**
- Uses the `together` Python SDK.
- Multiple models are dedicated-only despite appearing available:
  - `Qwen/Qwen2.5-72B-Instruct-Turbo` — dedicated only
  - `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` — dedicated only
  - `google/gemma-4-31b-it-fp8` — dedicated only
- Some newer models require `stream=True`:
  - `Qwen/Qwen3.7-Max` returns 400 without streaming
- Backend always uses streaming to handle both cases.
- Chunks accumulated via `chunk.choices[0].delta.content`.
- Verified working: `meta-llama/Llama-3.3-70B-Instruct-Turbo`,
  `Qwen/Qwen3.7-Max`.
- Together model catalog page is the ground truth for serverless vs
  dedicated — web search results were unreliable.

**Google (`google_backend.py`):**
- Uses OpenAI SDK with `base_url=
  "https://generativelanguage.googleapis.com/v1beta/openai/"`.
- Reads `GOOGLE_API_KEY` or `GEMINI_API_KEY`. Google's convention:
  `GOOGLE_API_KEY` takes precedence.
- Compat endpoint rejects `seed` — backend omits it. Determinism relies
  on `temperature=0.0` alone.
- `gemini-3.1-pro-preview` and other reasoning-capable Gemini models
  burn reasoning tokens against `max_tokens` budget silently, same
  mechanism as GPT-5. Buffer of 4000 added.
- `gemini-3.1-pro-preview` has 250 requests/day quota regardless of paid
  tier (preview model throttling).
- `gemini-2.5-pro` (stable) has 1000+ daily quota on paid tier.
- Google Cloud billing has multiple billing accounts per user; credits
  are per-billing-account. API keys are per-project; project links to one
  billing account. Credit visibility requires the API key's project to
  be linked to the credit-bearing billing account.

## Runner script: `scripts/run_v2_local.py`

**Design decisions:**
- Accepts one positional argument: model name in loader format.
- Optional `--max-tokens` (default 500) sets the visible token budget.
- Sanitizes model names for filenames: `:` → `_`, `/` → `_`.
- Output filename: `results/steerability_v2_<sanitized_model>.jsonl`.
- Progress print every 10 items.
- Writes results only at end of loop (not incrementally). If it crashes
  mid-run, all in-flight results are lost.

**Note on the misleading filename:** the script is still named
`run_v2_local.py` even though it now handles API models too. Renaming
was deferred to avoid updating instructions mid-project.

## Auxiliary scripts

**`dump_readable_v2.py`** — reads all `results/steerability_v2_*.jsonl`
files and produces readable txt files pairing each item's prompts with
base and steered responses. Includes `expected_behavior_change` block
per item.

**`count_empty_responses.py`** — reads a v2 results jsonl and reports how
many items have empty base, empty steered, or both empty. Outputs item
IDs for targeted re-runs.

**`rerun_items.py`** — takes a model name and one or more item IDs,
runs only those items, and merges results into the existing jsonl file
(backing up to `.bak`). Used to recover from partial failures without
re-running everything.

## API cost accounting (verified from actual spend)

| Provider | Model | Analysis set? | Cost per 100-item run |
|---|---|---|---|
| Anthropic | Haiku 4.5 | No (early sanity check only) | ~$0.30-0.80 |
| Anthropic | Opus 4.7 (adaptive thinking) | Yes | ~$3 |
| OpenAI | GPT-5 (reasoning buffer 4000) | Yes | ~$3 |
| DeepSeek | R1 (deepseek-reasoner) | Yes | ~$0.02 |
| Together | Llama 3.3 70B Turbo | Yes | ~$0.10-0.30 |
| Together | Qwen 3.7 Max | Yes | ~$0.10-0.30 |
| Google | Gemini 2.5 Pro (buffer 4000) | Yes | ~$1-3 (estimated) |

**Cumulative data-collection cost so far: ~$7-10 across all 7 models
(Haiku included).**

**Analysis set: 6 models (Haiku excluded).** Rationale for exclusion is
one frontier model per lab — see Chapter: Data Collection for full
rationale. Haiku data preserved on disk for potential within-Anthropic
scale follow-up.

## Environment configuration

- WSL2 Ubuntu on Windows PC (user did not have Mac despite `~/` in paths).
- Conda environment: `anthropic-proj`, Python 3.11.15.
- Auto-activation via `~/.bashrc` PROMPT_COMMAND hook.
- API keys in `~/.bashrc`:
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`
  - `DEEPSEEK_API_KEY`
  - `TOGETHER_API_KEY`
  - `GEMINI_API_KEY` (Google Cloud project linked to $25 credit account)
- User was warned about the source-in-current-shell crash issue with the
  conda auto-activation function; use new terminal after editing bashrc.
