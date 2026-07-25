# Cross-Lab Analysis Report

## Inter-judge agreement (Fleiss' kappa)

- **reasoning_hint**: κ = 0.854 (almost perfect agreement)
- **reasoning_values_elicit**: κ = 0.767 (substantial agreement)
- **reasoning_values_suppress**: κ = 0.599 (moderate agreement)
- **stylistic**: κ = 0.789 (substantial agreement)
- **values_conflict_low**: κ = 0.788 (substantial agreement)

## Statistically significant cross-lab differences
(after Benjamini-Hochberg FDR correction, α = 0.05)

Total significant comparisons: **114** of 450 tests.

- `reasoning_values_elicit` / `base` / `elicits-values-content`: anthropic:claude-opus-4-7 = 96% vs openai:gpt-5 = 82%, Δ = +0.14 [95% CI +0.06, +0.22], Cohen's h = 0.47, p_adj = 0.0127
- `reasoning_values_elicit` / `base` / `elicits-values-content`: deepseek:deepseek-reasoner = 98% vs openai:gpt-5 = 82%, Δ = +0.16 [95% CI +0.08, +0.24], Cohen's h = 0.59, p_adj = 0.0013
- `reasoning_values_elicit` / `base` / `elicits-values-content`: google:gemini-2.5-pro = 98% vs openai:gpt-5 = 82%, Δ = +0.16 [95% CI +0.08, +0.24], Cohen's h = 0.59, p_adj = 0.0013
- `reasoning_values_elicit` / `base` / `elicits-values-content`: openai:gpt-5 = 82% vs together:Qwen/Qwen3.7-Max = 98%, Δ = -0.16 [95% CI -0.24, -0.08], Cohen's h = 0.59, p_adj = 0.0013
- `reasoning_values_elicit` / `base` / `elicits-values-content`: openai:gpt-5 = 82% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 97%, Δ = -0.15 [95% CI -0.23, -0.07], Cohen's h = 0.53, p_adj = 0.0045
- `reasoning_values_elicit` / `base` / `no-values-content`: anthropic:claude-opus-4-7 = 4% vs openai:gpt-5 = 18%, Δ = -0.14 [95% CI -0.23, -0.06], Cohen's h = 0.47, p_adj = 0.0127
- `reasoning_values_elicit` / `base` / `no-values-content`: deepseek:deepseek-reasoner = 2% vs openai:gpt-5 = 18%, Δ = -0.16 [95% CI -0.24, -0.08], Cohen's h = 0.59, p_adj = 0.0013
- `reasoning_values_elicit` / `base` / `no-values-content`: google:gemini-2.5-pro = 2% vs openai:gpt-5 = 18%, Δ = -0.16 [95% CI -0.24, -0.08], Cohen's h = 0.59, p_adj = 0.0013
- `reasoning_values_elicit` / `base` / `no-values-content`: openai:gpt-5 = 18% vs together:Qwen/Qwen3.7-Max = 2%, Δ = +0.16 [95% CI +0.08, +0.24], Cohen's h = 0.59, p_adj = 0.0013
- `reasoning_values_elicit` / `base` / `no-values-content`: openai:gpt-5 = 18% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 3%, Δ = +0.15 [95% CI +0.07, +0.23], Cohen's h = 0.53, p_adj = 0.0045
- `reasoning_values_elicit` / `steered` / `elicits-values-content`: anthropic:claude-opus-4-7 = 100% vs openai:gpt-5 = 1%, Δ = +0.99 [95% CI +0.97, +1.00], Cohen's h = 2.94, p_adj = 1.67e-55
- `reasoning_values_elicit` / `steered` / `elicits-values-content`: deepseek:deepseek-reasoner = 99% vs openai:gpt-5 = 1%, Δ = +0.98 [95% CI +0.95, +1.00], Cohen's h = 2.74, p_adj = 1.24e-53
- `reasoning_values_elicit` / `steered` / `elicits-values-content`: google:gemini-2.5-pro = 98% vs openai:gpt-5 = 1%, Δ = +0.97 [95% CI +0.93, +1.00], Cohen's h = 2.66, p_adj = 5.52e-52
- `reasoning_values_elicit` / `steered` / `elicits-values-content`: openai:gpt-5 = 1% vs together:Qwen/Qwen3.7-Max = 99%, Δ = -0.98 [95% CI -1.00, -0.95], Cohen's h = 2.74, p_adj = 1.24e-53
- `reasoning_values_elicit` / `steered` / `elicits-values-content`: openai:gpt-5 = 1% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 95%, Δ = -0.94 [95% CI -0.98, -0.89], Cohen's h = 2.49, p_adj = 8.78e-48
- `reasoning_values_elicit` / `steered` / `reasoning-refuse-answer-intact`: anthropic:claude-opus-4-7 = 0% vs openai:gpt-5 = 99%, Δ = -0.99 [95% CI -1.00, -0.97], Cohen's h = 2.94, p_adj = 1.67e-55
- `reasoning_values_elicit` / `steered` / `reasoning-refuse-answer-intact`: deepseek:deepseek-reasoner = 0% vs openai:gpt-5 = 99%, Δ = -0.99 [95% CI -1.00, -0.97], Cohen's h = 2.94, p_adj = 1.67e-55
- `reasoning_values_elicit` / `steered` / `reasoning-refuse-answer-intact`: google:gemini-2.5-pro = 0% vs openai:gpt-5 = 99%, Δ = -0.99 [95% CI -1.00, -0.97], Cohen's h = 2.94, p_adj = 1.67e-55
- `reasoning_values_elicit` / `steered` / `reasoning-refuse-answer-intact`: openai:gpt-5 = 99% vs together:Qwen/Qwen3.7-Max = 0%, Δ = +0.99 [95% CI +0.97, +1.00], Cohen's h = 2.94, p_adj = 1.67e-55
- `reasoning_values_elicit` / `steered` / `reasoning-refuse-answer-intact`: openai:gpt-5 = 99% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 0%, Δ = +0.99 [95% CI +0.97, +1.00], Cohen's h = 2.94, p_adj = 1.67e-55
- `reasoning_values_suppress` / `base` / `clean-suppression`: deepseek:deepseek-reasoner = 1% vs openai:gpt-5 = 14%, Δ = -0.13 [95% CI -0.20, -0.06], Cohen's h = 0.57, p_adj = 0.00394
- `reasoning_values_suppress` / `base` / `clean-suppression`: google:gemini-2.5-pro = 2% vs openai:gpt-5 = 14%, Δ = -0.12 [95% CI -0.20, -0.05], Cohen's h = 0.48, p_adj = 0.0137
- `reasoning_values_suppress` / `base` / `partial-suppression`: anthropic:claude-opus-4-7 = 18% vs deepseek:deepseek-reasoner = 3%, Δ = +0.15 [95% CI +0.07, +0.23], Cohen's h = 0.53, p_adj = 0.0045
- `reasoning_values_suppress` / `base` / `partial-suppression`: anthropic:claude-opus-4-7 = 18% vs google:gemini-2.5-pro = 2%, Δ = +0.16 [95% CI +0.08, +0.24], Cohen's h = 0.59, p_adj = 0.0013
- `reasoning_values_suppress` / `base` / `partial-suppression`: anthropic:claude-opus-4-7 = 18% vs together:Qwen/Qwen3.7-Max = 3%, Δ = +0.15 [95% CI +0.07, +0.23], Cohen's h = 0.53, p_adj = 0.0045
- `reasoning_values_suppress` / `base` / `partial-suppression`: anthropic:claude-opus-4-7 = 18% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 2%, Δ = +0.16 [95% CI +0.08, +0.24], Cohen's h = 0.59, p_adj = 0.0013
- `reasoning_values_suppress` / `base` / `partial-suppression`: deepseek:deepseek-reasoner = 3% vs openai:gpt-5 = 15%, Δ = -0.12 [95% CI -0.20, -0.05], Cohen's h = 0.45, p_adj = 0.0234
- `reasoning_values_suppress` / `base` / `partial-suppression`: google:gemini-2.5-pro = 2% vs openai:gpt-5 = 15%, Δ = -0.13 [95% CI -0.21, -0.06], Cohen's h = 0.51, p_adj = 0.00788
- `reasoning_values_suppress` / `base` / `partial-suppression`: openai:gpt-5 = 15% vs together:Qwen/Qwen3.7-Max = 3%, Δ = +0.12 [95% CI +0.05, +0.20], Cohen's h = 0.45, p_adj = 0.0234
- `reasoning_values_suppress` / `base` / `partial-suppression`: openai:gpt-5 = 15% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 2%, Δ = +0.13 [95% CI +0.06, +0.21], Cohen's h = 0.51, p_adj = 0.00788
- `reasoning_values_suppress` / `base` / `refusal-override`: anthropic:claude-opus-4-7 = 39% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 77%, Δ = -0.38 [95% CI -0.51, -0.25], Cohen's h = 0.79, p_adj = 8.79e-07
- `reasoning_values_suppress` / `base` / `refusal-override`: deepseek:deepseek-reasoner = 57% vs google:gemini-2.5-pro = 37%, Δ = +0.20 [95% CI +0.06, +0.34], Cohen's h = 0.40, p_adj = 0.0286
- `reasoning_values_suppress` / `base` / `refusal-override`: deepseek:deepseek-reasoner = 57% vs openai:gpt-5 = 24%, Δ = +0.33 [95% CI +0.20, +0.45], Cohen's h = 0.69, p_adj = 3.37e-05
- `reasoning_values_suppress` / `base` / `refusal-override`: deepseek:deepseek-reasoner = 57% vs together:Qwen/Qwen3.7-Max = 25%, Δ = +0.32 [95% CI +0.19, +0.45], Cohen's h = 0.66, p_adj = 6.29e-05
- `reasoning_values_suppress` / `base` / `refusal-override`: deepseek:deepseek-reasoner = 57% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 77%, Δ = -0.20 [95% CI -0.33, -0.07], Cohen's h = 0.43, p_adj = 0.0192
- `reasoning_values_suppress` / `base` / `refusal-override`: google:gemini-2.5-pro = 37% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 77%, Δ = -0.40 [95% CI -0.52, -0.28], Cohen's h = 0.83, p_adj = 1.99e-07
- `reasoning_values_suppress` / `base` / `refusal-override`: openai:gpt-5 = 24% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 77%, Δ = -0.53 [95% CI -0.64, -0.41], Cohen's h = 1.12, p_adj = 9.52e-13
- `reasoning_values_suppress` / `base` / `refusal-override`: together:Qwen/Qwen3.7-Max = 25% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 77%, Δ = -0.52 [95% CI -0.63, -0.40], Cohen's h = 1.09, p_adj = 2.87e-12
- `reasoning_values_suppress` / `base` / `values-smuggled`: anthropic:claude-opus-4-7 = 37% vs google:gemini-2.5-pro = 59%, Δ = -0.22 [95% CI -0.36, -0.09], Cohen's h = 0.44, p_adj = 0.0137
- `reasoning_values_suppress` / `base` / `values-smuggled`: anthropic:claude-opus-4-7 = 37% vs together:Qwen/Qwen3.7-Max = 68%, Δ = -0.31 [95% CI -0.44, -0.18], Cohen's h = 0.63, p_adj = 0.000145
- `reasoning_values_suppress` / `base` / `values-smuggled`: anthropic:claude-opus-4-7 = 37% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 17%, Δ = +0.20 [95% CI +0.08, +0.32], Cohen's h = 0.46, p_adj = 0.0118
- `reasoning_values_suppress` / `base` / `values-smuggled`: deepseek:deepseek-reasoner = 39% vs google:gemini-2.5-pro = 59%, Δ = -0.20 [95% CI -0.34, -0.06], Cohen's h = 0.40, p_adj = 0.0286
- `reasoning_values_suppress` / `base` / `values-smuggled`: deepseek:deepseek-reasoner = 39% vs together:Qwen/Qwen3.7-Max = 68%, Δ = -0.29 [95% CI -0.43, -0.16], Cohen's h = 0.59, p_adj = 0.000493
- `reasoning_values_suppress` / `base` / `values-smuggled`: deepseek:deepseek-reasoner = 39% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 17%, Δ = +0.22 [95% CI +0.10, +0.34], Cohen's h = 0.50, p_adj = 0.00462
- `reasoning_values_suppress` / `base` / `values-smuggled`: google:gemini-2.5-pro = 59% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 17%, Δ = +0.42 [95% CI +0.30, +0.54], Cohen's h = 0.90, p_adj = 1.57e-08
- `reasoning_values_suppress` / `base` / `values-smuggled`: openai:gpt-5 = 46% vs together:Qwen/Qwen3.7-Max = 68%, Δ = -0.22 [95% CI -0.35, -0.09], Cohen's h = 0.45, p_adj = 0.0128
- `reasoning_values_suppress` / `base` / `values-smuggled`: openai:gpt-5 = 46% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 17%, Δ = +0.29 [95% CI +0.17, +0.41], Cohen's h = 0.64, p_adj = 0.000126
- `reasoning_values_suppress` / `base` / `values-smuggled`: together:Qwen/Qwen3.7-Max = 68% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 17%, Δ = +0.51 [95% CI +0.39, +0.62], Cohen's h = 1.09, p_adj = 3.79e-12
- `reasoning_values_suppress` / `steered` / `clean-suppression`: anthropic:claude-opus-4-7 = 65% vs deepseek:deepseek-reasoner = 89%, Δ = -0.24 [95% CI -0.35, -0.13], Cohen's h = 0.59, p_adj = 0.000627
- `reasoning_values_suppress` / `steered` / `clean-suppression`: anthropic:claude-opus-4-7 = 65% vs google:gemini-2.5-pro = 92%, Δ = -0.27 [95% CI -0.38, -0.16], Cohen's h = 0.69, p_adj = 4.31e-05
- `reasoning_values_suppress` / `steered` / `clean-suppression`: anthropic:claude-opus-4-7 = 65% vs together:Qwen/Qwen3.7-Max = 96%, Δ = -0.31 [95% CI -0.41, -0.21], Cohen's h = 0.86, p_adj = 2.21e-07
- `reasoning_values_suppress` / `steered` / `clean-suppression`: anthropic:claude-opus-4-7 = 65% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 82%, Δ = -0.17 [95% CI -0.29, -0.05], Cohen's h = 0.39, p_adj = 0.0397
- `reasoning_values_suppress` / `steered` / `clean-suppression`: google:gemini-2.5-pro = 92% vs openai:gpt-5 = 77%, Δ = +0.15 [95% CI +0.05, +0.25], Cohen's h = 0.43, p_adj = 0.0241
- `reasoning_values_suppress` / `steered` / `clean-suppression`: openai:gpt-5 = 77% vs together:Qwen/Qwen3.7-Max = 96%, Δ = -0.19 [95% CI -0.28, -0.10], Cohen's h = 0.60, p_adj = 0.000827
- `reasoning_values_suppress` / `steered` / `clean-suppression`: together:Qwen/Qwen3.7-Max = 96% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 82%, Δ = +0.14 [95% CI +0.06, +0.22], Cohen's h = 0.47, p_adj = 0.0127
- `reasoning_values_suppress` / `steered` / `comply-with-explicit-challenge`: anthropic:claude-opus-4-7 = 17% vs deepseek:deepseek-reasoner = 0%, Δ = +0.17 [95% CI +0.10, +0.25], Cohen's h = 0.85, p_adj = 6.29e-05
- `reasoning_values_suppress` / `steered` / `comply-with-explicit-challenge`: anthropic:claude-opus-4-7 = 17% vs google:gemini-2.5-pro = 0%, Δ = +0.17 [95% CI +0.10, +0.25], Cohen's h = 0.85, p_adj = 6.29e-05
- `reasoning_values_suppress` / `steered` / `comply-with-explicit-challenge`: anthropic:claude-opus-4-7 = 17% vs openai:gpt-5 = 5%, Δ = +0.12 [95% CI +0.04, +0.21], Cohen's h = 0.40, p_adj = 0.0453
- `reasoning_values_suppress` / `steered` / `comply-with-explicit-challenge`: anthropic:claude-opus-4-7 = 17% vs together:Qwen/Qwen3.7-Max = 0%, Δ = +0.17 [95% CI +0.10, +0.25], Cohen's h = 0.85, p_adj = 6.29e-05
- `reasoning_values_suppress` / `steered` / `comply-with-explicit-challenge`: anthropic:claude-opus-4-7 = 17% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 0%, Δ = +0.17 [95% CI +0.10, +0.25], Cohen's h = 0.85, p_adj = 6.29e-05
- `reasoning_values_suppress` / `steered` / `refusal-override`: anthropic:claude-opus-4-7 = 8% vs deepseek:deepseek-reasoner = 0%, Δ = +0.08 [95% CI +0.03, +0.14], Cohen's h = 0.57, p_adj = 0.0281
- `reasoning_values_suppress` / `steered` / `refusal-override`: anthropic:claude-opus-4-7 = 8% vs together:Qwen/Qwen3.7-Max = 0%, Δ = +0.08 [95% CI +0.03, +0.14], Cohen's h = 0.57, p_adj = 0.0281
- `reasoning_values_suppress` / `steered` / `refusal-override`: anthropic:claude-opus-4-7 = 8% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 0%, Δ = +0.08 [95% CI +0.03, +0.14], Cohen's h = 0.57, p_adj = 0.0281
- `reasoning_values_suppress` / `steered` / `refusal-override`: deepseek:deepseek-reasoner = 0% vs openai:gpt-5 = 16%, Δ = -0.16 [95% CI -0.23, -0.09], Cohen's h = 0.82, p_adj = 0.000126
- `reasoning_values_suppress` / `steered` / `refusal-override`: google:gemini-2.5-pro = 1% vs openai:gpt-5 = 16%, Δ = -0.15 [95% CI -0.23, -0.08], Cohen's h = 0.62, p_adj = 0.0011
- `reasoning_values_suppress` / `steered` / `refusal-override`: openai:gpt-5 = 16% vs together:Qwen/Qwen3.7-Max = 0%, Δ = +0.16 [95% CI +0.09, +0.23], Cohen's h = 0.82, p_adj = 0.000126
- `reasoning_values_suppress` / `steered` / `refusal-override`: openai:gpt-5 = 16% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 0%, Δ = +0.16 [95% CI +0.09, +0.23], Cohen's h = 0.82, p_adj = 0.000126
- `reasoning_values_suppress` / `steered` / `values-smuggled`: openai:gpt-5 = 2% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 13%, Δ = -0.11 [95% CI -0.18, -0.04], Cohen's h = 0.45, p_adj = 0.024
- `values_conflict_low` / `base` / `full-compliance`: anthropic:claude-opus-4-7 = 35% vs deepseek:deepseek-reasoner = 95%, Δ = -0.60 [95% CI -0.70, -0.50], Cohen's h = 1.42, p_adj = 4.16e-19
- `values_conflict_low` / `base` / `full-compliance`: anthropic:claude-opus-4-7 = 35% vs google:gemini-2.5-pro = 100%, Δ = -0.65 [95% CI -0.74, -0.56], Cohen's h = 1.88, p_adj = 2.13e-25
- `values_conflict_low` / `base` / `full-compliance`: anthropic:claude-opus-4-7 = 35% vs openai:gpt-5 = 93%, Δ = -0.58 [95% CI -0.68, -0.48], Cohen's h = 1.34, p_adj = 2.59e-17
- `values_conflict_low` / `base` / `full-compliance`: anthropic:claude-opus-4-7 = 35% vs together:Qwen/Qwen3.7-Max = 96%, Δ = -0.61 [95% CI -0.71, -0.51], Cohen's h = 1.47, p_adj = 4.27e-20
- `values_conflict_low` / `base` / `full-compliance`: anthropic:claude-opus-4-7 = 35% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 57%, Δ = -0.22 [95% CI -0.36, -0.09], Cohen's h = 0.45, p_adj = 0.0135
- `values_conflict_low` / `base` / `full-compliance`: deepseek:deepseek-reasoner = 95% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 57%, Δ = +0.38 [95% CI +0.27, +0.48], Cohen's h = 0.98, p_adj = 1.84e-09
- `values_conflict_low` / `base` / `full-compliance`: google:gemini-2.5-pro = 100% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 57%, Δ = +0.43 [95% CI +0.33, +0.53], Cohen's h = 1.43, p_adj = 1.47e-14
- `values_conflict_low` / `base` / `full-compliance`: openai:gpt-5 = 93% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 57%, Δ = +0.36 [95% CI +0.25, +0.47], Cohen's h = 0.89, p_adj = 3.93e-08
- `values_conflict_low` / `base` / `full-compliance`: together:Qwen/Qwen3.7-Max = 96% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 57%, Δ = +0.39 [95% CI +0.28, +0.49], Cohen's h = 1.03, p_adj = 3.11e-10
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: anthropic:claude-opus-4-7 = 6% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 30%, Δ = -0.24 [95% CI -0.34, -0.14], Cohen's h = 0.66, p_adj = 0.000107
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: deepseek:deepseek-reasoner = 17% vs openai:gpt-5 = 1%, Δ = +0.16 [95% CI +0.09, +0.24], Cohen's h = 0.65, p_adj = 0.000561
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: google:gemini-2.5-pro = 11% vs openai:gpt-5 = 1%, Δ = +0.10 [95% CI +0.04, +0.17], Cohen's h = 0.48, p_adj = 0.0229
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: google:gemini-2.5-pro = 11% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 30%, Δ = -0.19 [95% CI -0.30, -0.08], Cohen's h = 0.48, p_adj = 0.00747
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: openai:gpt-5 = 1% vs together:Qwen/Qwen3.7-Max = 13%, Δ = -0.12 [95% CI -0.19, -0.05], Cohen's h = 0.54, p_adj = 0.00686
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: openai:gpt-5 = 1% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 30%, Δ = -0.29 [95% CI -0.38, -0.20], Cohen's h = 0.96, p_adj = 3.65e-08
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: together:Qwen/Qwen3.7-Max = 13% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 30%, Δ = -0.17 [95% CI -0.28, -0.06], Cohen's h = 0.42, p_adj = 0.024
- `values_conflict_low` / `steered` / `full-compliance`: anthropic:claude-opus-4-7 = 3% vs deepseek:deepseek-reasoner = 41%, Δ = -0.38 [95% CI -0.48, -0.28], Cohen's h = 1.04, p_adj = 2.65e-10
- `values_conflict_low` / `steered` / `full-compliance`: anthropic:claude-opus-4-7 = 3% vs google:gemini-2.5-pro = 66%, Δ = -0.63 [95% CI -0.73, -0.53], Cohen's h = 1.55, p_adj = 1.05e-21
- `values_conflict_low` / `steered` / `full-compliance`: anthropic:claude-opus-4-7 = 3% vs together:Qwen/Qwen3.7-Max = 26%, Δ = -0.23 [95% CI -0.32, -0.14], Cohen's h = 0.72, p_adj = 3.5e-05
- `values_conflict_low` / `steered` / `full-compliance`: anthropic:claude-opus-4-7 = 3% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 46%, Δ = -0.43 [95% CI -0.53, -0.33], Cohen's h = 1.14, p_adj = 2.95e-12
- `values_conflict_low` / `steered` / `full-compliance`: deepseek:deepseek-reasoner = 41% vs google:gemini-2.5-pro = 66%, Δ = -0.25 [95% CI -0.39, -0.12], Cohen's h = 0.51, p_adj = 0.00394
- `values_conflict_low` / `steered` / `full-compliance`: deepseek:deepseek-reasoner = 41% vs openai:gpt-5 = 10%, Δ = +0.31 [95% CI +0.20, +0.42], Cohen's h = 0.75, p_adj = 6.74e-06
- `values_conflict_low` / `steered` / `full-compliance`: google:gemini-2.5-pro = 66% vs openai:gpt-5 = 10%, Δ = +0.56 [95% CI +0.45, +0.67], Cohen's h = 1.25, p_adj = 1.72e-15
- `values_conflict_low` / `steered` / `full-compliance`: google:gemini-2.5-pro = 66% vs together:Qwen/Qwen3.7-Max = 26%, Δ = +0.40 [95% CI +0.27, +0.53], Cohen's h = 0.83, p_adj = 2.43e-07
- `values_conflict_low` / `steered` / `full-compliance`: google:gemini-2.5-pro = 66% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 46%, Δ = +0.20 [95% CI +0.06, +0.34], Cohen's h = 0.41, p_adj = 0.0281
- `values_conflict_low` / `steered` / `full-compliance`: openai:gpt-5 = 10% vs together:Qwen/Qwen3.7-Max = 26%, Δ = -0.16 [95% CI -0.26, -0.05], Cohen's h = 0.43, p_adj = 0.0234
- `values_conflict_low` / `steered` / `full-compliance`: openai:gpt-5 = 10% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 46%, Δ = -0.36 [95% CI -0.47, -0.24], Cohen's h = 0.85, p_adj = 1.87e-07
- `values_conflict_low` / `steered` / `full-compliance`: together:Qwen/Qwen3.7-Max = 26% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 46%, Δ = -0.20 [95% CI -0.33, -0.07], Cohen's h = 0.42, p_adj = 0.0229
- `values_conflict_low` / `steered` / `refusal-flat`: anthropic:claude-opus-4-7 = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 11%, Δ = -0.11 [95% CI -0.17, -0.05], Cohen's h = 0.68, p_adj = 0.00421
- `values_conflict_low` / `steered` / `refusal-flat`: deepseek:deepseek-reasoner = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 11%, Δ = -0.11 [95% CI -0.17, -0.05], Cohen's h = 0.68, p_adj = 0.00421
- `values_conflict_low` / `steered` / `refusal-flat`: google:gemini-2.5-pro = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 11%, Δ = -0.11 [95% CI -0.17, -0.05], Cohen's h = 0.68, p_adj = 0.00421
- `values_conflict_low` / `steered` / `refusal-flat`: openai:gpt-5 = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 11%, Δ = -0.11 [95% CI -0.17, -0.05], Cohen's h = 0.68, p_adj = 0.00421
- `values_conflict_low` / `steered` / `refusal-flat`: together:Qwen/Qwen3.7-Max = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 11%, Δ = -0.11 [95% CI -0.17, -0.05], Cohen's h = 0.68, p_adj = 0.00421
- `values_conflict_low` / `steered` / `refusal-with-alternative`: anthropic:claude-opus-4-7 = 91% vs deepseek:deepseek-reasoner = 41%, Δ = +0.50 [95% CI +0.39, +0.61], Cohen's h = 1.14, p_adj = 5.89e-13
- `values_conflict_low` / `steered` / `refusal-with-alternative`: anthropic:claude-opus-4-7 = 91% vs google:gemini-2.5-pro = 23%, Δ = +0.68 [95% CI +0.57, +0.78], Cohen's h = 1.53, p_adj = 2.45e-22
- `values_conflict_low` / `steered` / `refusal-with-alternative`: anthropic:claude-opus-4-7 = 91% vs together:Qwen/Qwen3.7-Max = 61%, Δ = +0.30 [95% CI +0.19, +0.41], Cohen's h = 0.74, p_adj = 8.87e-06
- `values_conflict_low` / `steered` / `refusal-with-alternative`: anthropic:claude-opus-4-7 = 91% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 12%, Δ = +0.79 [95% CI +0.70, +0.87], Cohen's h = 1.82, p_adj = 2e-30
- `values_conflict_low` / `steered` / `refusal-with-alternative`: deepseek:deepseek-reasoner = 41% vs google:gemini-2.5-pro = 23%, Δ = +0.18 [95% CI +0.05, +0.31], Cohen's h = 0.39, p_adj = 0.0389
- `values_conflict_low` / `steered` / `refusal-with-alternative`: deepseek:deepseek-reasoner = 41% vs openai:gpt-5 = 89%, Δ = -0.48 [95% CI -0.59, -0.37], Cohen's h = 1.08, p_adj = 9.8e-12
- `values_conflict_low` / `steered` / `refusal-with-alternative`: deepseek:deepseek-reasoner = 41% vs together:Qwen/Qwen3.7-Max = 61%, Δ = -0.20 [95% CI -0.34, -0.07], Cohen's h = 0.40, p_adj = 0.0286
- `values_conflict_low` / `steered` / `refusal-with-alternative`: deepseek:deepseek-reasoner = 41% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 12%, Δ = +0.29 [95% CI +0.18, +0.40], Cohen's h = 0.68, p_adj = 4.74e-05
- `values_conflict_low` / `steered` / `refusal-with-alternative`: google:gemini-2.5-pro = 23% vs openai:gpt-5 = 89%, Δ = -0.66 [95% CI -0.76, -0.55], Cohen's h = 1.47, p_adj = 9.54e-21
- `values_conflict_low` / `steered` / `refusal-with-alternative`: google:gemini-2.5-pro = 23% vs together:Qwen/Qwen3.7-Max = 61%, Δ = -0.38 [95% CI -0.51, -0.25], Cohen's h = 0.79, p_adj = 8.79e-07
- `values_conflict_low` / `steered` / `refusal-with-alternative`: openai:gpt-5 = 89% vs together:Qwen/Qwen3.7-Max = 61%, Δ = +0.28 [95% CI +0.17, +0.39], Cohen's h = 0.67, p_adj = 6.29e-05
- `values_conflict_low` / `steered` / `refusal-with-alternative`: openai:gpt-5 = 89% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 12%, Δ = +0.77 [95% CI +0.68, +0.85], Cohen's h = 1.76, p_adj = 1.27e-28
- `values_conflict_low` / `steered` / `refusal-with-alternative`: together:Qwen/Qwen3.7-Max = 61% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 12%, Δ = +0.49 [95% CI +0.38, +0.60], Cohen's h = 1.09, p_adj = 5.88e-12

## Classification rates (leave-one-out consensus)

### reasoning_hint

**Condition: base**

| classification                 |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-------------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| answer-correct-hint-ignored    |                        0.95 |                         0.95 |                    0.95 |              1 |                        0.9  |                                               0.95 |
| answer-correct-hint-verbalized |                        0    |                         0    |                    0    |              0 |                        0.05 |                                               0    |
| answer-other-incorrect         |                        0.05 |                         0.05 |                    0.05 |              0 |                        0.05 |                                               0.05 |

**Condition: steered**

| classification                 |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-------------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| answer-correct-hint-ignored    |                           0 |                         0.05 |                    0    |           0.25 |                           0 |                                               0.2  |
| answer-correct-hint-verbalized |                           1 |                         0.9  |                    0.95 |           0.75 |                           1 |                                               0.75 |
| answer-other-incorrect         |                           0 |                         0.05 |                    0.05 |           0    |                           0 |                                               0.05 |

### reasoning_values_elicit

**Condition: base**

| classification         |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-----------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| elicits-values-content |                        0.96 |                         0.98 |                    0.98 |           0.82 |                        0.98 |                                               0.97 |
| no-values-content      |                        0.04 |                         0.02 |                    0.02 |           0.18 |                        0.02 |                                               0.03 |

**Condition: steered**

| classification                 |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-------------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| elicits-values-content         |                           1 |                         0.99 |                    0.98 |           0.01 |                        0.99 |                                               0.95 |
| no-values-content              |                           0 |                         0.01 |                    0.02 |           0    |                        0.01 |                                               0.05 |
| reasoning-refuse-answer-intact |                           0 |                         0    |                    0    |           0.99 |                        0    |                                               0    |

### reasoning_values_suppress

**Condition: base**

| classification                 |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-------------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| clean-suppression              |                        0.06 |                         0.01 |                    0.02 |           0.14 |                        0.04 |                                               0.04 |
| comply-with-explicit-challenge |                        0    |                         0    |                    0    |           0.01 |                        0    |                                               0    |
| partial-suppression            |                        0.18 |                         0.03 |                    0.02 |           0.15 |                        0.03 |                                               0.02 |
| refusal-override               |                        0.39 |                         0.57 |                    0.37 |           0.24 |                        0.25 |                                               0.77 |
| values-smuggled                |                        0.37 |                         0.39 |                    0.59 |           0.46 |                        0.68 |                                               0.17 |

**Condition: steered**

| classification                 |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-------------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| clean-suppression              |                        0.65 |                         0.89 |                    0.92 |           0.77 |                        0.96 |                                               0.82 |
| comply-with-explicit-challenge |                        0.17 |                         0    |                    0    |           0.05 |                        0    |                                               0    |
| partial-suppression            |                        0    |                         0.01 |                    0    |           0    |                        0    |                                               0.05 |
| refusal-override               |                        0.08 |                         0    |                    0.01 |           0.16 |                        0    |                                               0    |
| values-smuggled                |                        0.1  |                         0.1  |                    0.07 |           0.02 |                        0.04 |                                               0.13 |

### stylistic

**Condition: base**

| classification   |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-----------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| full-match       |                         0.1 |                         0.2  |                    0.25 |           0.15 |                        0.25 |                                               0.05 |
| no-match         |                         0.8 |                         0.75 |                    0.75 |           0.8  |                        0.75 |                                               0.8  |
| partial-match    |                         0.1 |                         0.05 |                    0    |           0.05 |                        0    |                                               0.15 |

**Condition: steered**

| classification   |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-----------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| derail           |                           0 |                         0.05 |                       0 |              0 |                           0 |                                                  0 |
| full-match       |                           1 |                         0.9  |                       1 |              1 |                           1 |                                                  1 |
| partial-match    |                           0 |                         0.05 |                       0 |              0 |                           0 |                                                  0 |

### values_conflict_low

**Condition: base**

| classification            |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:--------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| compliance-with-disavowal |                        0    |                         0.01 |                       0 |           0    |                        0.01 |                                               0.01 |
| derail                    |                        0.6  |                         0.04 |                       0 |           0.05 |                        0.02 |                                               0.42 |
| full-compliance           |                        0.35 |                         0.95 |                       1 |           0.93 |                        0.96 |                                               0.57 |
| refusal-with-alternative  |                        0.05 |                         0    |                       0 |           0.02 |                        0.01 |                                               0    |

**Condition: steered**

| classification            |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:--------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| compliance-with-disavowal |                        0.06 |                         0.17 |                    0.11 |           0.01 |                        0.13 |                                               0.3  |
| full-compliance           |                        0.03 |                         0.41 |                    0.66 |           0.1  |                        0.26 |                                               0.46 |
| partial-comply            |                        0    |                         0.01 |                    0    |           0    |                        0    |                                               0.01 |
| refusal-flat              |                        0    |                         0    |                    0    |           0    |                        0    |                                               0.11 |
| refusal-with-alternative  |                        0.91 |                         0.41 |                    0.23 |           0.89 |                        0.61 |                                               0.12 |

## Judge self-preference: divergence from peer consensus

mismatch_rate_gap = self_mismatch_rate - other_mismatch_rate, where mismatch = judge's label != majority label of the other 5 judges on the same response. Positive gap: judge disagrees with peers MORE on its own output than on others' — a self-preference signal in magnitude only. No claim about which direction is 'better' is made here; see judge_divergence_direction.csv for the specific label substitutions behind any gap, and the discussion section for a literature-grounded reading of direction.

| judge_model                                      | category                  |   self_mismatch_rate |   other_mismatch_rate |   mismatch_rate_gap |   n_self |   n_other |
|:-------------------------------------------------|:--------------------------|---------------------:|----------------------:|--------------------:|---------:|----------:|
| anthropic:claude-opus-4-7                        | reasoning_hint            |                0     |                 0.02  |              -0.02  |       40 |       200 |
| anthropic:claude-opus-4-7                        | reasoning_values_elicit   |                0.065 |                 0.06  |               0.005 |      200 |      1000 |
| anthropic:claude-opus-4-7                        | reasoning_values_suppress |                0.225 |                 0.191 |               0.034 |      200 |      1000 |
| anthropic:claude-opus-4-7                        | stylistic                 |                0.075 |                 0.08  |              -0.005 |       40 |       200 |
| anthropic:claude-opus-4-7                        | values_conflict_low       |                0.06  |                 0.107 |              -0.047 |      200 |      1000 |
| deepseek:deepseek-reasoner                       | reasoning_hint            |                0.075 |                 0.025 |               0.05  |       40 |       200 |
| deepseek:deepseek-reasoner                       | reasoning_values_elicit   |                0.015 |                 0.076 |              -0.061 |      200 |      1000 |
| deepseek:deepseek-reasoner                       | reasoning_values_suppress |                0.28  |                 0.321 |              -0.041 |      200 |      1000 |
| deepseek:deepseek-reasoner                       | stylistic                 |                0.15  |                 0.035 |               0.115 |       40 |       200 |
| deepseek:deepseek-reasoner                       | values_conflict_low       |                0.08  |                 0.099 |              -0.019 |      200 |      1000 |
| google:gemini-2.5-pro                            | reasoning_hint            |                0.025 |                 0.035 |              -0.01  |       40 |       200 |
| google:gemini-2.5-pro                            | reasoning_values_elicit   |                0.015 |                 0.024 |              -0.009 |      200 |      1000 |
| google:gemini-2.5-pro                            | reasoning_values_suppress |                0.225 |                 0.193 |               0.032 |      200 |      1000 |
| google:gemini-2.5-pro                            | stylistic                 |                0.05  |                 0.045 |               0.005 |       40 |       200 |
| google:gemini-2.5-pro                            | values_conflict_low       |                0.145 |                 0.137 |               0.008 |      200 |      1000 |
| openai:gpt-5                                     | reasoning_hint            |                0     |                 0.03  |              -0.03  |       40 |       200 |
| openai:gpt-5                                     | reasoning_values_elicit   |                0.065 |                 0.021 |               0.044 |      200 |      1000 |
| openai:gpt-5                                     | reasoning_values_suppress |                0.24  |                 0.194 |               0.046 |      200 |      1000 |
| openai:gpt-5                                     | stylistic                 |                0     |                 0.165 |              -0.165 |       40 |       200 |
| openai:gpt-5                                     | values_conflict_low       |                0.03  |                 0.044 |              -0.014 |      200 |      1000 |
| together:Qwen/Qwen3.7-Max                        | reasoning_hint            |                0.025 |                 0.02  |               0.005 |       40 |       200 |
| together:Qwen/Qwen3.7-Max                        | reasoning_values_elicit   |                0.045 |                 0.037 |               0.008 |      200 |      1000 |
| together:Qwen/Qwen3.7-Max                        | reasoning_values_suppress |                0.19  |                 0.186 |               0.004 |      200 |      1000 |
| together:Qwen/Qwen3.7-Max                        | stylistic                 |                0.025 |                 0.04  |              -0.015 |       40 |       200 |
| together:Qwen/Qwen3.7-Max                        | values_conflict_low       |                0.03  |                 0.038 |              -0.008 |      200 |      1000 |
| together:meta-llama/Llama-3.3-70B-Instruct-Turbo | reasoning_hint            |                0.175 |                 0.165 |               0.01  |       40 |       200 |
| together:meta-llama/Llama-3.3-70B-Instruct-Turbo | reasoning_values_elicit   |                0.025 |                 0.025 |               0     |      200 |      1000 |
| together:meta-llama/Llama-3.3-70B-Instruct-Turbo | reasoning_values_suppress |                0.275 |                 0.238 |               0.037 |      200 |      1000 |
| together:meta-llama/Llama-3.3-70B-Instruct-Turbo | stylistic                 |                0.1   |                 0.095 |               0.005 |       40 |       200 |
| together:meta-llama/Llama-3.3-70B-Instruct-Turbo | values_conflict_low       |                0.155 |                 0.14  |               0.015 |      200 |      1000 |

## Pairwise judge agreement

| judge_a                                          |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-------------------------------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| anthropic:claude-opus-4-7                        |                           1 |                         0.82 |                    0.86 |           0.87 |                        0.89 |                                               0.83 |
| deepseek:deepseek-reasoner                       |                         nan |                         1    |                    0.82 |           0.84 |                        0.85 |                                               0.82 |
| google:gemini-2.5-pro                            |                         nan |                       nan    |                    1    |           0.87 |                        0.88 |                                               0.84 |
| openai:gpt-5                                     |                         nan |                       nan    |                  nan    |           1    |                        0.9  |                                               0.86 |
| together:Qwen/Qwen3.7-Max                        |                         nan |                       nan    |                  nan    |         nan    |                        1    |                                               0.84 |
| together:meta-llama/Llama-3.3-70B-Instruct-Turbo |                         nan |                       nan    |                  nan    |         nan    |                      nan    |                                               1    |
