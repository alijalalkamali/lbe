#!/usr/bin/env bash
# verify_before_commit.sh
#
# Checks that every fix discussed this session is actually present in the
# local repo, not just executed once from a temp copy. Run from the repo
# root. Prints PASS/FAIL per check and a final summary; exits 1 if anything
# failed, so it's usable as a pre-commit gate.

set -uo pipefail

FAIL=0
check() {
    local desc="$1"
    local result="$2"
    if [ "$result" -eq 0 ]; then
        echo "PASS  $desc"
    else
        echo "FAIL  $desc"
        FAIL=1
    fi
}

echo "=== Interface / GenerationOutput refactor ==="

grep -q "class GenerationOutput" src/lbe/models/base.py 2>/dev/null
check "base.py defines GenerationOutput" $?

grep -q "TRUNCATION_FINISH_REASONS" src/lbe/models/base.py 2>/dev/null
check "base.py defines TRUNCATION_FINISH_REASONS" $?

for f in anthropic_backend openai_backend deepseek_backend google_backend together_backend local; do
    path="src/lbe/models/${f}.py"
    # Check for actual construction of GenerationOutput, not the return-type
    # annotation string -- the annotation's exact formatting (line wrapping,
    # spacing) can be changed by an auto-formatter without changing behavior,
    # but constructing the object is what actually matters.
    grep -q "GenerationOutput(" "$path" 2>/dev/null
    check "${f}.py constructs/returns a GenerationOutput" $?
    grep -q "finish_reason=" "$path" 2>/dev/null
    check "${f}.py captures finish_reason" $?
done

echo ""
echo "=== Schema / eval pipeline ==="

grep -q "finish_reasons:" src/lbe/io/dataset.py 2>/dev/null
check "dataset.py: EvalResult has finish_reasons field" $?

grep -q "finish_reasons=\[base.finish_reason" src/lbe/evals/steerability_v2.py 2>/dev/null
check "steerability_v2.py: run_v2_item records finish_reasons" $?

echo ""
echo "=== Judge prompt / leakage toggle ==="

grep -q "include_expected_behavior_change" src/lbe/judging/judge_prompt.py 2>/dev/null
check "judge_prompt.py: has include_expected_behavior_change param" $?

echo ""
echo "=== Judge output parsing fixes ==="

grep -q "_strip_thinking_block" src/lbe/judging/judge_output.py 2>/dev/null
check "judge_output.py: strips <thinking> block before extraction" $?

grep -q "_repair_missing_open_quotes" src/lbe/judging/judge_output.py 2>/dev/null
check "judge_output.py: has missing-quote repair" $?

echo ""
echo "=== Aggregation / analysis pipeline ==="

grep -q "def compute_judge_divergence" src/lbe/judging/aggregate.py 2>/dev/null
check "aggregate.py: has compute_judge_divergence (not compute_self_preference_bias)" $?

# Finding the OLD function is the failure case here, so this is inverted
# relative to the check() helper's normal "grep found it = PASS" logic --
# handled directly rather than forcing it through check().
if grep -q "def compute_self_preference_bias" src/lbe/judging/aggregate.py 2>/dev/null; then
    echo "FAIL  aggregate.py: OLD compute_self_preference_bias should be removed"
    FAIL=1
else
    echo "PASS  aggregate.py: OLD compute_self_preference_bias is GONE"
fi

grep -q "compute_judge_divergence" scripts/run_judge_pipeline.py 2>/dev/null
check "run_judge_pipeline.py: calls compute_judge_divergence (not old function)" $?

grep -q "judge_divergence_summary.csv" scripts/run_judge_pipeline.py 2>/dev/null
check "run_judge_pipeline.py: writes judge_divergence_summary.csv" $?

grep -q "comply-with-explicit-challenge" scripts/analyze_judgments.py 2>/dev/null
check "analyze_judgments.py: focus_classifications includes v2 labels" $?

echo ""
echo "=== Manual one-line edits ==="

grep -q "judge.generate(current_prompt, max_new_tokens=800).text" src/lbe/judging/run_judges.py 2>/dev/null
check "run_judges.py:~160 has .text appended to generate() call" $?

# -q on the first grep would suppress all output, leaving nothing for the
# second grep to see -- must omit -q there so the -A2 context lines are
# actually piped through.
grep -A2 "analyst.generate(" scripts/open_coding_pass.py 2>/dev/null | grep -q "\.text"
check "open_coding_pass.py:~490 has .text appended to generate() call" $?

echo ""
echo "=== New tooling scripts present ==="

for f in find_truncated.py invalidate_judgments.py run_leakage_test.py; do
    [ -f "scripts/$f" ]
    check "scripts/$f exists" $?
done

[ -f "src/lbe/judging/leakage.py" ]
check "src/lbe/judging/leakage.py exists" $?

echo ""
echo "=== Repo hygiene ==="

if [ -f .gitignore ]; then
    grep -q "\.env" .gitignore 2>/dev/null && grep -q "__pycache__" .gitignore 2>/dev/null
    check ".gitignore covers .env and __pycache__" $?
    grep -q "\.bak" .gitignore 2>/dev/null
    check ".gitignore covers .bak backup files" $?
else
    echo "FAIL  .gitignore does not exist"
    FAIL=1
fi

# Crude secret scan: look for suspicious hardcoded key patterns in tracked
# Python files. Not a substitute for a real secret scanner, but catches the
# obvious "pasted a key while iterating" case.
echo ""
echo "=== Quick secret scan (hardcoded API keys) ==="
PY_FILES="$(git ls-files '*.py' 2>/dev/null)"
if [ -z "$PY_FILES" ]; then
    echo "PASS  no tracked .py files yet (nothing to scan)"
else
    MATCHES="$(printf '%s\n' "$PY_FILES" | while IFS= read -r f; do
        grep -lE "(sk-ant-|sk-proj-|sk-[a-zA-Z0-9]{20,})" "$f" 2>/dev/null
    done)"
    if [ -n "$MATCHES" ]; then
        echo "FAIL  possible hardcoded API key found in tracked .py files:"
        echo "$MATCHES"
        FAIL=1
    else
        echo "PASS  no obvious hardcoded API keys in tracked .py files"
    fi
fi

echo ""
echo "=== Bytecode / backup files not staged ==="
if git status --porcelain 2>/dev/null | grep -qE "\.(pyc|bak)$|__pycache__"; then
    echo "FAIL  .pyc/.bak/__pycache__ files are staged — check .gitignore"
    git status --porcelain | grep -E "\.(pyc|bak)$|__pycache__"
    FAIL=1
else
    echo "PASS  no .pyc/.bak/__pycache__ files staged"
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "ALL CHECKS PASSED — safe to commit."
else
    echo "SOME CHECKS FAILED — fix the FAIL lines above before committing."
fi
exit $FAIL
