# Setup

Environment, packages, and infrastructure decisions for the `lbe` (LLM Behavioral Eval) project.

## Environment

- WSL2 (Ubuntu 24.04) on Windows host. Moved from Windows-native Python after hitting recurring DLL load-order and platform-specific issues. Linux side eliminates these.
- Conda env `anthropic-proj` with Python 3.11.
- PyTorch with CUDA 12.1, GPU passthrough via WSL2 NVIDIA drivers.
- Hardware: NVIDIA GTX 1080 Ti (11 GB VRAM), 64 GB system RAM, i7-7820X.

## Key package decisions

- **transformers**: latest version. Pinning to 4.40.0 broke nnsight (which expects newer transformers). Lesson: don't pin transformers unless there's a specific reason — let it float.
- **pyarrow >= 21**, **datasets < 3**: this pairing resolved a Windows-side DLL conflict between bitsandbytes and pyarrow. Now moot on Linux but documented for reference.
- **nnsight**: for interpretability work in Week 4.
- **anthropic**: API client, planned for Day 18 (cross-scale validation).
- **pingouin, statsmodels**: stats utilities for proper statistical analysis (bootstrap CI, multiple-comparison corrections).
- **bitsandbytes**: 4-bit quantization. Optional — only needed if we add a LoRA experiment.

## Repo hygiene

- `pre-commit` configured with `ruff`, `ruff-format`, `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-toml`, `check-added-large-files`. Hooks auto-fix what they can; commit fails if hooks modified files, succeeds on retry after re-staging.
- `pyproject.toml` configures ruff with `line-length = 100` and ruleset `["E", "F", "W", "I", "N", "UP", "B", "C4"]`. Pytest config under `[tool.pytest.ini_options]`.
- Editable install via `pip install -e .` — makes `lbe` importable across the env, source edits take immediate effect.

## Repo layout

```
~/projects/anthropic/
├── src/lbe/                # package
│   ├── models/             # base, local (HF), loader factory
│   ├── evals/              # steerability and future evals
│   │   └── scorers/        # rule-based; LLM-judge to be added
│   ├── io/                 # dataset schemas (Pydantic), JSONL helpers
│   ├── stats/              # statistical utilities (placeholder)
│   └── interp/             # interpretability (placeholder)
├── tests/                  # pytest
├── data/                   # eval items (JSONL files tracked in git)
├── results/                # eval outputs (gitignored except .gitkeep)
├── notebooks/, configs/, scripts/, writeup/, _reference/
├── notes/                  # this folder (gitignored)
├── pyproject.toml
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

## Tooling

- VS Code with WSL extension. Pylance installed WSL-side for type checking.
- `.vscode/settings.json` (committed): `python.analysis.typeCheckingMode: "standard"`.
- Starship prompt + ipython for nicer terminal/REPL experience.
- Git: branch `main`, commits local, not yet pushed to GitHub (intentional — push when repo stabilizes).

## Models tested so far

- **Qwen 2.5 0.5B-Instruct**: primary local test model. HF id `Qwen/Qwen2.5-0.5B-Instruct`. Open, no gating. Loads in ~1 GB VRAM at fp16.
- **Llama 3.2 1B-Instruct, 3B-Instruct**: access granted via HuggingFace. Available for cross-scale comparison runs.
- **Frontier models**: planned for Day 18 via Anthropic API (Claude Haiku 4.5 or similar). Local 70B+ models not viable on this hardware; using API instead of Colab.
