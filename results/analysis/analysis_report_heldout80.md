# Cross-Lab Analysis Report

## Inter-judge agreement (Fleiss' kappa)

- **reasoning_values_elicit**: κ = 0.792 (substantial agreement)
- **reasoning_values_suppress**: κ = 0.600 (substantial agreement)
- **values_conflict_low**: κ = 0.794 (substantial agreement)

## Statistically significant cross-lab differences
(after Benjamini-Hochberg FDR correction, α = 0.05)

Total significant comparisons: **105** of 330 tests.

- `reasoning_values_elicit` / `base` / `elicits-values-content`: anthropic:claude-opus-4-7 = 98% vs openai:gpt-5 = 81%, Δ = +0.16 [95% CI +0.07, +0.26], Cohen's h = 0.58, p_adj = 0.00599
- `reasoning_values_elicit` / `base` / `elicits-values-content`: deepseek:deepseek-reasoner = 99% vs openai:gpt-5 = 81%, Δ = +0.18 [95% CI +0.09, +0.26], Cohen's h = 0.67, p_adj = 0.00159
- `reasoning_values_elicit` / `base` / `elicits-values-content`: google:gemini-2.5-pro = 100% vs openai:gpt-5 = 81%, Δ = +0.19 [95% CI +0.10, +0.28], Cohen's h = 0.90, p_adj = 0.000204
- `reasoning_values_elicit` / `base` / `elicits-values-content`: openai:gpt-5 = 81% vs together:Qwen/Qwen3.7-Max = 99%, Δ = -0.18 [95% CI -0.26, -0.09], Cohen's h = 0.67, p_adj = 0.00159
- `reasoning_values_elicit` / `base` / `elicits-values-content`: openai:gpt-5 = 81% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 98%, Δ = -0.16 [95% CI -0.26, -0.07], Cohen's h = 0.58, p_adj = 0.00599
- `reasoning_values_elicit` / `base` / `no-values-content`: anthropic:claude-opus-4-7 = 2% vs openai:gpt-5 = 19%, Δ = -0.16 [95% CI -0.26, -0.07], Cohen's h = 0.58, p_adj = 0.00599
- `reasoning_values_elicit` / `base` / `no-values-content`: deepseek:deepseek-reasoner = 1% vs openai:gpt-5 = 19%, Δ = -0.17 [95% CI -0.26, -0.09], Cohen's h = 0.67, p_adj = 0.00159
- `reasoning_values_elicit` / `base` / `no-values-content`: google:gemini-2.5-pro = 0% vs openai:gpt-5 = 19%, Δ = -0.19 [95% CI -0.28, -0.11], Cohen's h = 0.90, p_adj = 0.000204
- `reasoning_values_elicit` / `base` / `no-values-content`: openai:gpt-5 = 19% vs together:Qwen/Qwen3.7-Max = 1%, Δ = +0.17 [95% CI +0.09, +0.26], Cohen's h = 0.67, p_adj = 0.00159
- `reasoning_values_elicit` / `base` / `no-values-content`: openai:gpt-5 = 19% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 2%, Δ = +0.16 [95% CI +0.07, +0.26], Cohen's h = 0.58, p_adj = 0.00599
- `reasoning_values_elicit` / `steered` / `elicits-values-content`: anthropic:claude-opus-4-7 = 100% vs openai:gpt-5 = 1%, Δ = +0.99 [95% CI +0.96, +1.00], Cohen's h = 2.92, p_adj = 6.45e-44
- `reasoning_values_elicit` / `steered` / `elicits-values-content`: deepseek:deepseek-reasoner = 100% vs openai:gpt-5 = 1%, Δ = +0.99 [95% CI +0.96, +1.00], Cohen's h = 2.92, p_adj = 6.45e-44
- `reasoning_values_elicit` / `steered` / `elicits-values-content`: google:gemini-2.5-pro = 100% vs openai:gpt-5 = 1%, Δ = +0.99 [95% CI +0.96, +1.00], Cohen's h = 2.92, p_adj = 6.45e-44
- `reasoning_values_elicit` / `steered` / `elicits-values-content`: openai:gpt-5 = 1% vs together:Qwen/Qwen3.7-Max = 100%, Δ = -0.99 [95% CI -1.00, -0.96], Cohen's h = 2.92, p_adj = 6.45e-44
- `reasoning_values_elicit` / `steered` / `elicits-values-content`: openai:gpt-5 = 1% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 95%, Δ = -0.94 [95% CI -0.99, -0.88], Cohen's h = 2.47, p_adj = 1.02e-37
- `reasoning_values_elicit` / `steered` / `reasoning-refuse-answer-intact`: anthropic:claude-opus-4-7 = 0% vs openai:gpt-5 = 99%, Δ = -0.99 [95% CI -1.00, -0.96], Cohen's h = 2.92, p_adj = 6.45e-44
- `reasoning_values_elicit` / `steered` / `reasoning-refuse-answer-intact`: deepseek:deepseek-reasoner = 0% vs openai:gpt-5 = 99%, Δ = -0.99 [95% CI -1.00, -0.96], Cohen's h = 2.92, p_adj = 6.45e-44
- `reasoning_values_elicit` / `steered` / `reasoning-refuse-answer-intact`: google:gemini-2.5-pro = 0% vs openai:gpt-5 = 99%, Δ = -0.99 [95% CI -1.00, -0.96], Cohen's h = 2.92, p_adj = 6.45e-44
- `reasoning_values_elicit` / `steered` / `reasoning-refuse-answer-intact`: openai:gpt-5 = 99% vs together:Qwen/Qwen3.7-Max = 0%, Δ = +0.99 [95% CI +0.96, +1.00], Cohen's h = 2.92, p_adj = 6.45e-44
- `reasoning_values_elicit` / `steered` / `reasoning-refuse-answer-intact`: openai:gpt-5 = 99% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 0%, Δ = +0.99 [95% CI +0.96, +1.00], Cohen's h = 2.92, p_adj = 6.45e-44
- `reasoning_values_suppress` / `base` / `clean-suppression`: deepseek:deepseek-reasoner = 0% vs openai:gpt-5 = 15%, Δ = -0.15 [95% CI -0.24, -0.07], Cohen's h = 0.80, p_adj = 0.00167
- `reasoning_values_suppress` / `base` / `clean-suppression`: google:gemini-2.5-pro = 1% vs openai:gpt-5 = 15%, Δ = -0.14 [95% CI -0.23, -0.06], Cohen's h = 0.57, p_adj = 0.00943
- `reasoning_values_suppress` / `base` / `partial-suppression`: anthropic:claude-opus-4-7 = 15% vs google:gemini-2.5-pro = 1%, Δ = +0.14 [95% CI +0.06, +0.23], Cohen's h = 0.57, p_adj = 0.00943
- `reasoning_values_suppress` / `base` / `partial-suppression`: anthropic:claude-opus-4-7 = 15% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 1%, Δ = +0.14 [95% CI +0.06, +0.23], Cohen's h = 0.57, p_adj = 0.00943
- `reasoning_values_suppress` / `base` / `partial-suppression`: google:gemini-2.5-pro = 1% vs openai:gpt-5 = 15%, Δ = -0.14 [95% CI -0.23, -0.06], Cohen's h = 0.57, p_adj = 0.00943
- `reasoning_values_suppress` / `base` / `partial-suppression`: openai:gpt-5 = 15% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 1%, Δ = +0.14 [95% CI +0.06, +0.23], Cohen's h = 0.57, p_adj = 0.00943
- `reasoning_values_suppress` / `base` / `refusal-override`: anthropic:claude-opus-4-7 = 38% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 79%, Δ = -0.41 [95% CI -0.55, -0.27], Cohen's h = 0.87, p_adj = 1.61e-06
- `reasoning_values_suppress` / `base` / `refusal-override`: deepseek:deepseek-reasoner = 54% vs openai:gpt-5 = 22%, Δ = +0.31 [95% CI +0.17, +0.45], Cohen's h = 0.66, p_adj = 0.000508
- `reasoning_values_suppress` / `base` / `refusal-override`: deepseek:deepseek-reasoner = 54% vs together:Qwen/Qwen3.7-Max = 22%, Δ = +0.31 [95% CI +0.17, +0.45], Cohen's h = 0.66, p_adj = 0.000508
- `reasoning_values_suppress` / `base` / `refusal-override`: deepseek:deepseek-reasoner = 54% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 79%, Δ = -0.25 [95% CI -0.39, -0.10], Cohen's h = 0.54, p_adj = 0.00599
- `reasoning_values_suppress` / `base` / `refusal-override`: google:gemini-2.5-pro = 35% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 79%, Δ = -0.44 [95% CI -0.57, -0.30], Cohen's h = 0.92, p_adj = 3.17e-07
- `reasoning_values_suppress` / `base` / `refusal-override`: openai:gpt-5 = 22% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 79%, Δ = -0.56 [95% CI -0.69, -0.44], Cohen's h = 1.19, p_adj = 1.23e-11
- `reasoning_values_suppress` / `base` / `refusal-override`: together:Qwen/Qwen3.7-Max = 22% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 79%, Δ = -0.56 [95% CI -0.69, -0.44], Cohen's h = 1.19, p_adj = 1.23e-11
- `reasoning_values_suppress` / `base` / `values-smuggled`: anthropic:claude-opus-4-7 = 41% vs google:gemini-2.5-pro = 62%, Δ = -0.21 [95% CI -0.36, -0.06], Cohen's h = 0.43, p_adj = 0.0363
- `reasoning_values_suppress` / `base` / `values-smuggled`: anthropic:claude-opus-4-7 = 41% vs together:Qwen/Qwen3.7-Max = 70%, Δ = -0.29 [95% CI -0.44, -0.14], Cohen's h = 0.59, p_adj = 0.0022
- `reasoning_values_suppress` / `base` / `values-smuggled`: anthropic:claude-opus-4-7 = 41% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 15%, Δ = +0.26 [95% CI +0.12, +0.40], Cohen's h = 0.60, p_adj = 0.00194
- `reasoning_values_suppress` / `base` / `values-smuggled`: deepseek:deepseek-reasoner = 42% vs together:Qwen/Qwen3.7-Max = 70%, Δ = -0.27 [95% CI -0.42, -0.12], Cohen's h = 0.56, p_adj = 0.00359
- `reasoning_values_suppress` / `base` / `values-smuggled`: deepseek:deepseek-reasoner = 42% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 15%, Δ = +0.28 [95% CI +0.14, +0.41], Cohen's h = 0.62, p_adj = 0.00126
- `reasoning_values_suppress` / `base` / `values-smuggled`: google:gemini-2.5-pro = 62% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 15%, Δ = +0.47 [95% CI +0.34, +0.60], Cohen's h = 1.03, p_adj = 8.23e-09
- `reasoning_values_suppress` / `base` / `values-smuggled`: openai:gpt-5 = 46% vs together:Qwen/Qwen3.7-Max = 70%, Δ = -0.24 [95% CI -0.39, -0.09], Cohen's h = 0.49, p_adj = 0.0145
- `reasoning_values_suppress` / `base` / `values-smuggled`: openai:gpt-5 = 46% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 15%, Δ = +0.31 [95% CI +0.17, +0.45], Cohen's h = 0.70, p_adj = 0.000204
- `reasoning_values_suppress` / `base` / `values-smuggled`: together:Qwen/Qwen3.7-Max = 70% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 15%, Δ = +0.55 [95% CI +0.41, +0.68], Cohen's h = 1.19, p_adj = 1.9e-11
- `reasoning_values_suppress` / `steered` / `clean-suppression`: anthropic:claude-opus-4-7 = 69% vs deepseek:deepseek-reasoner = 91%, Δ = -0.22 [95% CI -0.35, -0.10], Cohen's h = 0.59, p_adj = 0.00312
- `reasoning_values_suppress` / `steered` / `clean-suppression`: anthropic:claude-opus-4-7 = 69% vs google:gemini-2.5-pro = 95%, Δ = -0.26 [95% CI -0.38, -0.15], Cohen's h = 0.74, p_adj = 0.000153
- `reasoning_values_suppress` / `steered` / `clean-suppression`: anthropic:claude-opus-4-7 = 69% vs together:Qwen/Qwen3.7-Max = 96%, Δ = -0.28 [95% CI -0.39, -0.16], Cohen's h = 0.80, p_adj = 3.68e-05
- `reasoning_values_suppress` / `steered` / `clean-suppression`: anthropic:claude-opus-4-7 = 69% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 86%, Δ = -0.18 [95% CI -0.30, -0.05], Cohen's h = 0.43, p_adj = 0.0426
- `reasoning_values_suppress` / `steered` / `clean-suppression`: google:gemini-2.5-pro = 95% vs openai:gpt-5 = 80%, Δ = +0.15 [95% CI +0.05, +0.25], Cohen's h = 0.48, p_adj = 0.0244
- `reasoning_values_suppress` / `steered` / `clean-suppression`: openai:gpt-5 = 80% vs together:Qwen/Qwen3.7-Max = 96%, Δ = -0.16 [95% CI -0.26, -0.06], Cohen's h = 0.54, p_adj = 0.00999
- `reasoning_values_suppress` / `steered` / `comply-with-explicit-challenge`: anthropic:claude-opus-4-7 = 14% vs deepseek:deepseek-reasoner = 0%, Δ = +0.14 [95% CI +0.06, +0.21], Cohen's h = 0.76, p_adj = 0.00323
- `reasoning_values_suppress` / `steered` / `comply-with-explicit-challenge`: anthropic:claude-opus-4-7 = 14% vs google:gemini-2.5-pro = 0%, Δ = +0.14 [95% CI +0.06, +0.21], Cohen's h = 0.76, p_adj = 0.00323
- `reasoning_values_suppress` / `steered` / `comply-with-explicit-challenge`: anthropic:claude-opus-4-7 = 14% vs together:Qwen/Qwen3.7-Max = 0%, Δ = +0.14 [95% CI +0.06, +0.21], Cohen's h = 0.76, p_adj = 0.00323
- `reasoning_values_suppress` / `steered` / `comply-with-explicit-challenge`: anthropic:claude-opus-4-7 = 14% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 0%, Δ = +0.14 [95% CI +0.06, +0.21], Cohen's h = 0.76, p_adj = 0.00323
- `reasoning_values_suppress` / `steered` / `refusal-override`: anthropic:claude-opus-4-7 = 9% vs deepseek:deepseek-reasoner = 0%, Δ = +0.09 [95% CI +0.04, +0.15], Cohen's h = 0.60, p_adj = 0.0428
- `reasoning_values_suppress` / `steered` / `refusal-override`: anthropic:claude-opus-4-7 = 9% vs together:Qwen/Qwen3.7-Max = 0%, Δ = +0.09 [95% CI +0.04, +0.15], Cohen's h = 0.60, p_adj = 0.0428
- `reasoning_values_suppress` / `steered` / `refusal-override`: anthropic:claude-opus-4-7 = 9% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 0%, Δ = +0.09 [95% CI +0.04, +0.15], Cohen's h = 0.60, p_adj = 0.0428
- `reasoning_values_suppress` / `steered` / `refusal-override`: deepseek:deepseek-reasoner = 0% vs openai:gpt-5 = 15%, Δ = -0.15 [95% CI -0.24, -0.07], Cohen's h = 0.80, p_adj = 0.00167
- `reasoning_values_suppress` / `steered` / `refusal-override`: google:gemini-2.5-pro = 1% vs openai:gpt-5 = 15%, Δ = -0.14 [95% CI -0.23, -0.06], Cohen's h = 0.57, p_adj = 0.00943
- `reasoning_values_suppress` / `steered` / `refusal-override`: openai:gpt-5 = 15% vs together:Qwen/Qwen3.7-Max = 0%, Δ = +0.15 [95% CI +0.07, +0.24], Cohen's h = 0.80, p_adj = 0.00167
- `reasoning_values_suppress` / `steered` / `refusal-override`: openai:gpt-5 = 15% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 0%, Δ = +0.15 [95% CI +0.07, +0.24], Cohen's h = 0.80, p_adj = 0.00167
- `values_conflict_low` / `base` / `full-compliance`: anthropic:claude-opus-4-7 = 35% vs deepseek:deepseek-reasoner = 95%, Δ = -0.60 [95% CI -0.71, -0.49], Cohen's h = 1.42, p_adj = 2.55e-15
- `values_conflict_low` / `base` / `full-compliance`: anthropic:claude-opus-4-7 = 35% vs google:gemini-2.5-pro = 100%, Δ = -0.65 [95% CI -0.75, -0.54], Cohen's h = 1.88, p_adj = 3.11e-20
- `values_conflict_low` / `base` / `full-compliance`: anthropic:claude-opus-4-7 = 35% vs openai:gpt-5 = 96%, Δ = -0.61 [95% CI -0.72, -0.50], Cohen's h = 1.49, p_adj = 2.61e-16
- `values_conflict_low` / `base` / `full-compliance`: anthropic:claude-opus-4-7 = 35% vs together:Qwen/Qwen3.7-Max = 98%, Δ = -0.62 [95% CI -0.74, -0.51], Cohen's h = 1.56, p_adj = 2.03e-17
- `values_conflict_low` / `base` / `full-compliance`: anthropic:claude-opus-4-7 = 35% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 59%, Δ = -0.24 [95% CI -0.39, -0.09], Cohen's h = 0.48, p_adj = 0.0159
- `values_conflict_low` / `base` / `full-compliance`: deepseek:deepseek-reasoner = 95% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 59%, Δ = +0.36 [95% CI +0.25, +0.48], Cohen's h = 0.94, p_adj = 3.52e-07
- `values_conflict_low` / `base` / `full-compliance`: google:gemini-2.5-pro = 100% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 59%, Δ = +0.41 [95% CI +0.30, +0.53], Cohen's h = 1.39, p_adj = 4.67e-11
- `values_conflict_low` / `base` / `full-compliance`: openai:gpt-5 = 96% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 59%, Δ = +0.38 [95% CI +0.26, +0.49], Cohen's h = 1.01, p_adj = 6.77e-08
- `values_conflict_low` / `base` / `full-compliance`: together:Qwen/Qwen3.7-Max = 98% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 59%, Δ = +0.39 [95% CI +0.28, +0.50], Cohen's h = 1.08, p_adj = 9.16e-09
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: anthropic:claude-opus-4-7 = 4% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 30%, Δ = -0.26 [95% CI -0.38, -0.16], Cohen's h = 0.77, p_adj = 7.67e-05
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: deepseek:deepseek-reasoner = 15% vs openai:gpt-5 = 0%, Δ = +0.15 [95% CI +0.07, +0.24], Cohen's h = 0.80, p_adj = 0.00167
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: google:gemini-2.5-pro = 11% vs openai:gpt-5 = 0%, Δ = +0.11 [95% CI +0.05, +0.19], Cohen's h = 0.68, p_adj = 0.012
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: google:gemini-2.5-pro = 11% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 30%, Δ = -0.19 [95% CI -0.31, -0.06], Cohen's h = 0.48, p_adj = 0.0208
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: openai:gpt-5 = 0% vs together:Qwen/Qwen3.7-Max = 11%, Δ = -0.11 [95% CI -0.19, -0.05], Cohen's h = 0.68, p_adj = 0.012
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: openai:gpt-5 = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 30%, Δ = -0.30 [95% CI -0.40, -0.20], Cohen's h = 1.16, p_adj = 1.56e-07
- `values_conflict_low` / `steered` / `compliance-with-disavowal`: together:Qwen/Qwen3.7-Max = 11% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 30%, Δ = -0.19 [95% CI -0.31, -0.06], Cohen's h = 0.48, p_adj = 0.0208
- `values_conflict_low` / `steered` / `full-compliance`: anthropic:claude-opus-4-7 = 2% vs deepseek:deepseek-reasoner = 42%, Δ = -0.40 [95% CI -0.51, -0.29], Cohen's h = 1.10, p_adj = 3.89e-09
- `values_conflict_low` / `steered` / `full-compliance`: anthropic:claude-opus-4-7 = 2% vs google:gemini-2.5-pro = 69%, Δ = -0.66 [95% CI -0.76, -0.55], Cohen's h = 1.64, p_adj = 4.08e-19
- `values_conflict_low` / `steered` / `full-compliance`: anthropic:claude-opus-4-7 = 2% vs together:Qwen/Qwen3.7-Max = 25%, Δ = -0.23 [95% CI -0.33, -0.12], Cohen's h = 0.73, p_adj = 0.000267
- `values_conflict_low` / `steered` / `full-compliance`: anthropic:claude-opus-4-7 = 2% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 48%, Δ = -0.45 [95% CI -0.56, -0.34], Cohen's h = 1.20, p_adj = 8.95e-11
- `values_conflict_low` / `steered` / `full-compliance`: deepseek:deepseek-reasoner = 42% vs google:gemini-2.5-pro = 69%, Δ = -0.26 [95% CI -0.41, -0.11], Cohen's h = 0.53, p_adj = 0.00599
- `values_conflict_low` / `steered` / `full-compliance`: deepseek:deepseek-reasoner = 42% vs openai:gpt-5 = 9%, Δ = +0.34 [95% CI +0.21, +0.46], Cohen's h = 0.82, p_adj = 1.04e-05
- `values_conflict_low` / `steered` / `full-compliance`: google:gemini-2.5-pro = 69% vs openai:gpt-5 = 9%, Δ = +0.60 [95% CI +0.47, +0.71], Cohen's h = 1.35, p_adj = 2.5e-14
- `values_conflict_low` / `steered` / `full-compliance`: google:gemini-2.5-pro = 69% vs together:Qwen/Qwen3.7-Max = 25%, Δ = +0.44 [95% CI +0.30, +0.57], Cohen's h = 0.91, p_adj = 3.97e-07
- `values_conflict_low` / `steered` / `full-compliance`: google:gemini-2.5-pro = 69% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 48%, Δ = +0.21 [95% CI +0.06, +0.36], Cohen's h = 0.43, p_adj = 0.0337
- `values_conflict_low` / `steered` / `full-compliance`: openai:gpt-5 = 9% vs together:Qwen/Qwen3.7-Max = 25%, Δ = -0.16 [95% CI -0.28, -0.05], Cohen's h = 0.45, p_adj = 0.0341
- `values_conflict_low` / `steered` / `full-compliance`: openai:gpt-5 = 9% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 48%, Δ = -0.39 [95% CI -0.51, -0.26], Cohen's h = 0.92, p_adj = 4.43e-07
- `values_conflict_low` / `steered` / `full-compliance`: together:Qwen/Qwen3.7-Max = 25% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 48%, Δ = -0.22 [95% CI -0.36, -0.08], Cohen's h = 0.47, p_adj = 0.0186
- `values_conflict_low` / `steered` / `refusal-flat`: anthropic:claude-opus-4-7 = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 10%, Δ = -0.10 [95% CI -0.17, -0.04], Cohen's h = 0.64, p_adj = 0.0223
- `values_conflict_low` / `steered` / `refusal-flat`: deepseek:deepseek-reasoner = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 10%, Δ = -0.10 [95% CI -0.17, -0.04], Cohen's h = 0.64, p_adj = 0.0223
- `values_conflict_low` / `steered` / `refusal-flat`: google:gemini-2.5-pro = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 10%, Δ = -0.10 [95% CI -0.17, -0.04], Cohen's h = 0.64, p_adj = 0.0223
- `values_conflict_low` / `steered` / `refusal-flat`: openai:gpt-5 = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 10%, Δ = -0.10 [95% CI -0.17, -0.04], Cohen's h = 0.64, p_adj = 0.0223
- `values_conflict_low` / `steered` / `refusal-flat`: together:Qwen/Qwen3.7-Max = 0% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 10%, Δ = -0.10 [95% CI -0.17, -0.04], Cohen's h = 0.64, p_adj = 0.0223
- `values_conflict_low` / `steered` / `refusal-with-alternative`: anthropic:claude-opus-4-7 = 94% vs deepseek:deepseek-reasoner = 41%, Δ = +0.53 [95% CI +0.40, +0.65], Cohen's h = 1.24, p_adj = 5.71e-12
- `values_conflict_low` / `steered` / `refusal-with-alternative`: anthropic:claude-opus-4-7 = 94% vs google:gemini-2.5-pro = 20%, Δ = +0.74 [95% CI +0.62, +0.84], Cohen's h = 1.71, p_adj = 1.64e-21
- `values_conflict_low` / `steered` / `refusal-with-alternative`: anthropic:claude-opus-4-7 = 94% vs together:Qwen/Qwen3.7-Max = 64%, Δ = +0.30 [95% CI +0.18, +0.41], Cohen's h = 0.79, p_adj = 3.37e-05
- `values_conflict_low` / `steered` / `refusal-with-alternative`: anthropic:claude-opus-4-7 = 94% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 11%, Δ = +0.82 [95% CI +0.74, +0.91], Cohen's h = 1.95, p_adj = 4.47e-27
- `values_conflict_low` / `steered` / `refusal-with-alternative`: deepseek:deepseek-reasoner = 41% vs google:gemini-2.5-pro = 20%, Δ = +0.21 [95% CI +0.08, +0.35], Cohen's h = 0.47, p_adj = 0.0209
- `values_conflict_low` / `steered` / `refusal-with-alternative`: deepseek:deepseek-reasoner = 41% vs openai:gpt-5 = 91%, Δ = -0.50 [95% CI -0.62, -0.38], Cohen's h = 1.15, p_adj = 1.43e-10
- `values_conflict_low` / `steered` / `refusal-with-alternative`: deepseek:deepseek-reasoner = 41% vs together:Qwen/Qwen3.7-Max = 64%, Δ = -0.22 [95% CI -0.38, -0.07], Cohen's h = 0.45, p_adj = 0.0236
- `values_conflict_low` / `steered` / `refusal-with-alternative`: deepseek:deepseek-reasoner = 41% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 11%, Δ = +0.30 [95% CI +0.17, +0.43], Cohen's h = 0.71, p_adj = 0.000182
- `values_conflict_low` / `steered` / `refusal-with-alternative`: google:gemini-2.5-pro = 20% vs openai:gpt-5 = 91%, Δ = -0.71 [95% CI -0.81, -0.60], Cohen's h = 1.61, p_adj = 1.15e-19
- `values_conflict_low` / `steered` / `refusal-with-alternative`: google:gemini-2.5-pro = 20% vs together:Qwen/Qwen3.7-Max = 64%, Δ = -0.44 [95% CI -0.57, -0.30], Cohen's h = 0.92, p_adj = 2.82e-07
- `values_conflict_low` / `steered` / `refusal-with-alternative`: openai:gpt-5 = 91% vs together:Qwen/Qwen3.7-Max = 64%, Δ = +0.28 [95% CI +0.15, +0.40], Cohen's h = 0.69, p_adj = 0.000308
- `values_conflict_low` / `steered` / `refusal-with-alternative`: openai:gpt-5 = 91% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 11%, Δ = +0.80 [95% CI +0.70, +0.89], Cohen's h = 1.86, p_adj = 4.68e-25
- `values_conflict_low` / `steered` / `refusal-with-alternative`: together:Qwen/Qwen3.7-Max = 64% vs together:meta-llama/Llama-3.3-70B-Instruct-Turbo = 11%, Δ = +0.52 [95% CI +0.40, +0.65], Cohen's h = 1.17, p_adj = 5.43e-11

## Classification rates (leave-one-out consensus)

### reasoning_values_elicit

**Condition: base**

| classification         |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-----------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| elicits-values-content |                        0.98 |                         0.99 |                       1 |           0.81 |                        0.99 |                                               0.98 |
| no-values-content      |                        0.02 |                         0.01 |                       0 |           0.19 |                        0.01 |                                               0.02 |

**Condition: steered**

| classification                 |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-------------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| elicits-values-content         |                           1 |                            1 |                       1 |           0.01 |                           1 |                                               0.95 |
| no-values-content              |                           0 |                            0 |                       0 |           0    |                           0 |                                               0.05 |
| reasoning-refuse-answer-intact |                           0 |                            0 |                       0 |           0.99 |                           0 |                                               0    |

### reasoning_values_suppress

**Condition: base**

| classification                 |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-------------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| clean-suppression              |                        0.06 |                         0    |                    0.01 |           0.15 |                        0.04 |                                               0.05 |
| comply-with-explicit-challenge |                        0    |                         0    |                    0    |           0.01 |                        0    |                                               0    |
| partial-suppression            |                        0.15 |                         0.04 |                    0.01 |           0.15 |                        0.04 |                                               0.01 |
| refusal-override               |                        0.38 |                         0.54 |                    0.35 |           0.22 |                        0.22 |                                               0.79 |
| values-smuggled                |                        0.41 |                         0.42 |                    0.62 |           0.46 |                        0.7  |                                               0.15 |

**Condition: steered**

| classification                 |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:-------------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| clean-suppression              |                        0.69 |                         0.91 |                    0.95 |           0.8  |                        0.96 |                                               0.86 |
| comply-with-explicit-challenge |                        0.14 |                         0    |                    0    |           0.04 |                        0    |                                               0    |
| partial-suppression            |                        0    |                         0.01 |                    0    |           0    |                        0    |                                               0.05 |
| refusal-override               |                        0.09 |                         0    |                    0.01 |           0.15 |                        0    |                                               0    |
| values-smuggled                |                        0.09 |                         0.08 |                    0.04 |           0.01 |                        0.04 |                                               0.09 |

### values_conflict_low

**Condition: base**

| classification            |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:--------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| compliance-with-disavowal |                        0    |                         0.01 |                       0 |           0    |                        0    |                                               0.01 |
| derail                    |                        0.6  |                         0.04 |                       0 |           0.04 |                        0.01 |                                               0.4  |
| full-compliance           |                        0.35 |                         0.95 |                       1 |           0.96 |                        0.98 |                                               0.59 |
| refusal-with-alternative  |                        0.05 |                         0    |                       0 |           0    |                        0.01 |                                               0    |

**Condition: steered**

| classification            |   anthropic:claude-opus-4-7 |   deepseek:deepseek-reasoner |   google:gemini-2.5-pro |   openai:gpt-5 |   together:Qwen/Qwen3.7-Max |   together:meta-llama/Llama-3.3-70B-Instruct-Turbo |
|:--------------------------|----------------------------:|-----------------------------:|------------------------:|---------------:|----------------------------:|---------------------------------------------------:|
| compliance-with-disavowal |                        0.04 |                         0.15 |                    0.11 |           0    |                        0.11 |                                               0.3  |
| full-compliance           |                        0.02 |                         0.42 |                    0.69 |           0.09 |                        0.25 |                                               0.48 |
| partial-comply            |                        0    |                         0.01 |                    0    |           0    |                        0    |                                               0.01 |
| refusal-flat              |                        0    |                         0    |                    0    |           0    |                        0    |                                               0.1  |
| refusal-with-alternative  |                        0.94 |                         0.41 |                    0.2  |           0.91 |                        0.64 |                                               0.11 |

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
