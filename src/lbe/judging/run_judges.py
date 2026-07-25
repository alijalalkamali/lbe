"""Judge runner: iterates (item, response, condition, judge) tuples and
collects classifications.

Design goals:
    - Resumable: skips (item, condition, judge) combinations already judged
      in the output file. If the run crashes or is killed, restart picks up
      where it left off. Only SUCCESSFUL judgments count as "already judged"
      — rows left behind by a failed call (empty classification) are treated
      as not-yet-judged so a re-run naturally re-attempts them.
    - Per-judge output files: each judge's classifications go in their own
      JSONL file, keyed by responder model + condition + item id. This
      isolates per-judge failures and lets you rerun a single judge without
      touching others.
    - Failure recording: judge output errors are recorded to a separate
      errors file with the raw text preserved for post-hoc analysis.
    - Fail-fast on fatal conditions: quota exhaustion, billing failure, or an
      inaccessible model fails every remaining call in a section identically.
      Rather than grind through hundreds of guaranteed failures, the section
      aborts immediately (progress saved) and the caller moves on to the next
      judge×responder combination.
    - Cost tracking: logs approximate token usage per judgment (from the
      judge model's response metadata where available).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from lbe.io.dataset import EvalResult, SteerabilityItem
from lbe.io.jsonl import read_jsonl, write_jsonl
from lbe.judging.judge_output import JudgeOutputError, parse_judge_output
from lbe.judging.judge_prompt import build_judge_prompt
from lbe.judging.rubrics import Rubric, get_rubric
from lbe.models.loader import load_model


class FatalJudgeError(Exception):
    """A judge-level error that makes continuing this judge×responder section
    pointless — quota exhaustion, billing failure, invalid/expired key, or a
    model that's inaccessible to this project. Unlike a per-item parse or
    transient API error (which we record and move past), these fail every
    remaining call identically, so we abort the whole section immediately and
    let the caller move on to the next judge×responder combination rather than
    grinding through hundreds of guaranteed failures.
    """


# Substrings that identify a fatal, section-wide condition. Matched against
# the string form of the raised exception. Deliberately conservative: only
# quota/billing/auth/access conditions, not transient timeouts or rate spikes
# that a later item might survive.
_FATAL_ERROR_MARKERS = (
    "insufficient_quota",
    "exceeded your current quota",
    "resource_exhausted",
    "no longer available to new users",
    "invalid_api_key",
    "invalid x-api-key",
    "authentication",
    "permission_denied",
    "billing",
)


def _is_fatal_error(exc: Exception) -> bool:
    """True if this exception indicates a section-wide fatal condition
    (quota/billing/auth/access) rather than a per-item transient failure."""
    text = repr(exc).lower()
    return any(marker in text for marker in _FATAL_ERROR_MARKERS)


class JudgmentRecord(BaseModel):
    """One row of judgment data — the output written to per-judge JSONL files.

    Attributes:
        item_id: Item ID (e.g., 'vcl_001').
        category: Item category (e.g., 'values_conflict_low').
        responder_model: The model whose response was judged (e.g.,
            'anthropic:claude-opus-4-7').
        condition: 'base' or 'steered'.
        judge_model: The model that produced this classification.
        classification: Rubric label chosen.
        justification: Judge's explanation.
        cited_text: Direct quote supporting the label.
        confidence: 'high', 'medium', or 'low'.
        error: If the judge output failed to parse, error message here;
            classification and other fields will be empty.
        raw_output: Judge's raw text output (kept for auditing).
    """

    item_id: str
    category: str
    responder_model: str
    condition: str
    judge_model: str
    classification: str = ""
    justification: str = ""
    cited_text: str = ""
    confidence: str = ""
    error: str = ""
    raw_output: str = ""


def _make_key(item_id: str, condition: str) -> str:
    """Key used to deduplicate already-judged combinations within a file."""
    return f"{item_id}::{condition}"


def _load_already_judged(judge_output_path: Path) -> set[str]:
    """Read an existing judge output file and return the set of keys
    SUCCESSFULLY judged. Used for resumability.

    Only records with a non-empty classification and no error count as
    "already judged". Rows left behind by a failed call (empty classification,
    or a populated `error`) are deliberately NOT counted, so a re-run
    re-attempts exactly those items rather than treating a prior failure as
    done. This is what makes a plain pipeline re-run fill real gaps without a
    separate purge step.

    Args:
        judge_output_path: Path to the judge's JSONL file.

    Returns:
        Set of keys (formatted "<item_id>::<condition>") successfully judged.
        Empty set if the file doesn't exist.
    """
    if not judge_output_path.exists():
        return set()

    already: set[str] = set()
    for record in read_jsonl(judge_output_path, JudgmentRecord):
        if record.classification.strip() and not record.error:
            already.add(_make_key(record.item_id, record.condition))
    return already


def _load_responder_results(
    results_path: Path,
) -> list[EvalResult]:
    """Load a responder model's result file. Small wrapper around read_jsonl."""
    return list(read_jsonl(results_path, EvalResult))


def _get_response_for_condition(result: EvalResult, condition: str) -> str:
    """Extract the base or steered response from an EvalResult.

    Args:
        result: Loaded EvalResult with raw_completions=[base, steered].
        condition: 'base' or 'steered'.

    Returns:
        The response text for the requested condition.

    Raises:
        ValueError: If condition is not 'base'/'steered' or raw_completions
            doesn't have enough entries.
    """
    if condition == "base":
        idx = 0
    elif condition == "steered":
        idx = 1
    else:
        raise ValueError(f"condition must be 'base' or 'steered', got {condition!r}")

    if len(result.raw_completions) <= idx:
        raise ValueError(
            f"EvalResult for {result.item_id} has only "
            f"{len(result.raw_completions)} completions; cannot get index {idx}"
        )
    return result.raw_completions[idx]


def _call_judge_with_retry(
    judge: Any,
    prompt: str,
    rubric: Rubric,
    max_reparse_retries: int = 1,
) -> tuple[str, dict | None]:
    """Call the judge model and return (raw_output, parsed_dict_or_None).

    If the judge output fails to parse, retries up to max_reparse_retries
    times with a stronger instruction. If all attempts fail, returns the
    last raw output with parsed=None.

    A fatal condition (quota/billing/auth/access) is NOT retried — it is
    raised as FatalJudgeError so the caller can abort the whole section.

    Args:
        judge: Judge model backend (has .generate method).
        prompt: The judge prompt.
        rubric: Rubric for validation.
        max_reparse_retries: Number of re-attempts on parse failure.

    Returns:
        Tuple of (raw_output_text, parsed_result_dict or None).

    Raises:
        FatalJudgeError: If the generation call fails with a section-wide
            fatal condition.
    """
    reparse_prompt_suffix = (
        "\n\nIMPORTANT: Your previous response was not valid JSON. "
        "Output ONLY a JSON object with keys: classification, justification, "
        "cited_text, confidence. No prose, no code fences, no other text."
    )

    current_prompt = prompt
    last_raw: str = ""

    for attempt in range(max_reparse_retries + 1):
        try:
            raw = judge.generate(current_prompt, max_new_tokens=800).text
        except Exception as e:
            if _is_fatal_error(e):
                # Don't waste the reparse retry on a quota/auth failure —
                # it will fail identically. Propagate to abort the section.
                raise FatalJudgeError(repr(e)) from e
            raise  # transient/other error: let caller's handling deal with it
        last_raw = raw

        try:
            result = parse_judge_output(raw, rubric)
            return raw, result.model_dump()
        except JudgeOutputError:
            if attempt < max_reparse_retries:
                # Retry with stronger format instruction
                current_prompt = prompt + reparse_prompt_suffix
            # else: fall through and return with parsed=None

    return last_raw, None


def run_judge_on_responder(
    judge_model_name: str,
    responder_model_name: str,
    items_path: Path,
    responder_results_path: Path,
    output_path: Path,
    conditions: tuple[str, ...] = ("base", "steered"),
    error_log_path: Path | None = None,
) -> None:
    """Run one judge model across all (item, condition) pairs for one
    responder model, writing classifications to output_path.

    Resumable: if output_path already contains SUCCESSFUL judgments for some
    (item_id, condition) keys, those are skipped and only missing or
    previously-failed combinations are judged.

    Args:
        judge_model_name: Model identifier for the judge (loader.py format,
            e.g., 'anthropic:claude-sonnet-4-6').
        responder_model_name: Identifier of the model whose responses are
            being judged (recorded in each JudgmentRecord).
        items_path: Path to items JSONL (e.g., data/steerability_items_v2.jsonl).
        responder_results_path: Path to the responder's results JSONL
            (e.g., results/steerability_v2_anthropic_claude-opus-4-7.jsonl).
        output_path: Path where this judge's classifications will be
            appended.
        conditions: Which conditions to judge; default ('base', 'steered').
        error_log_path: Optional path to log parse errors with raw output.

    Raises:
        FatalJudgeError: If a section-wide fatal condition (quota/billing/
            auth/access) is hit. Progress judged before the abort is saved
            first. Callers that run many sections should catch this and
            continue to the next combination.
    """
    print(f"Judge: {judge_model_name}")
    print(f"Responder: {responder_model_name}")
    print(f"Output: {output_path}")

    # Load items indexed by id for O(1) lookup
    items = {i.id: i for i in read_jsonl(items_path, SteerabilityItem)}
    responder_results = _load_responder_results(responder_results_path)

    # Determine which combinations still need judging. Only successful
    # judgments count as done, so previously-failed rows are re-attempted.
    already_judged = _load_already_judged(output_path)
    total_planned = len(responder_results) * len(conditions)
    to_judge = [
        (r, cond)
        for r in responder_results
        for cond in conditions
        if _make_key(r.item_id, cond) not in already_judged
    ]

    if not to_judge:
        print(f"All {total_planned} combinations already judged. Nothing to do.")
        return

    print(
        f"To judge: {len(to_judge)} / {total_planned} "
        f"({len(already_judged)} already done, resuming)"
    )

    judge = load_model(judge_model_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing records first so we can rewrite the file atomically.
    # Keep only SUCCESSFUL prior records — drop any empty/errored rows so a
    # resumed run doesn't re-accumulate the failed rows it's re-attempting.
    existing_records = [
        r
        for r in (read_jsonl(output_path, JudgmentRecord) if output_path.exists() else [])
        if r.classification.strip() and not r.error
    ]
    new_records: list[JudgmentRecord] = []

    def _persist() -> None:
        """Write successful existing + all new records, and (if configured)
        the errors file. Called on progress checkpoints and on abort."""
        write_jsonl(output_path, existing_records + new_records)
        if error_log_path is not None:
            errors = [r for r in new_records if r.error]
            if errors:
                error_log_path.parent.mkdir(parents=True, exist_ok=True)
                write_jsonl(error_log_path, errors)

    start_time = time.time()
    for idx, (result, condition) in enumerate(to_judge, 1):
        item = items.get(result.item_id)
        if item is None:
            print(f"  Skipping {result.item_id}: not found in items file")
            continue

        rubric = get_rubric(item.category)
        response_text = _get_response_for_condition(result, condition)

        prompt = build_judge_prompt(
            rubric=rubric,
            item_base_prompt=item.base_prompt,
            item_steering_instruction=item.steering_instruction,
            response_to_judge=response_text,
            condition=condition,
            expected_behavior_change=item.expected_behavior_change,
        )

        record = JudgmentRecord(
            item_id=item.id,
            category=item.category,
            responder_model=responder_model_name,
            condition=condition,
            judge_model=judge_model_name,
        )

        try:
            raw, parsed = _call_judge_with_retry(judge, prompt, rubric)
            record.raw_output = raw
            if parsed is not None:
                record.classification = parsed["classification"]
                record.justification = parsed["justification"]
                record.cited_text = parsed["cited_text"]
                record.confidence = parsed["confidence"]
            else:
                record.error = "parse_failed_after_retries"
        except FatalJudgeError as e:
            # Section-wide fatal condition (quota/billing/auth/access).
            # Persist everything judged so far this run, then abort the
            # section so the caller moves on to the next combination.
            print(
                f"\n  FATAL for judge={judge_model_name} "
                f"responder={responder_model_name}: {e}\n"
                f"  Skipping the rest of this combination. "
                f"{len(new_records)} judged this run before abort; progress saved."
            )
            _persist()
            raise
        except Exception as e:
            # Non-parse errors (transient API failures, timeouts): record and
            # continue to the next item.
            record.error = f"call_failed: {e!r}"

        new_records.append(record)

        # Progress + intermediate save every 20 judgments
        if idx % 20 == 0 or idx == len(to_judge):
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (len(to_judge) - idx) / rate if rate > 0 else float("inf")
            print(
                f"  [{idx}/{len(to_judge)}] "
                f"elapsed={elapsed:.0f}s rate={rate:.2f}/s eta={eta:.0f}s"
            )
            _persist()

    # Final write (in case last progress-save didn't fire on exact boundary)
    _persist()

    if error_log_path is not None:
        errors = [r for r in new_records if r.error]
        if errors:
            print(f"Wrote {len(errors)} error records to {error_log_path.name}")

    num_success = sum(1 for r in new_records if not r.error)
    print(
        f"Done. Wrote {len(new_records)} new judgments "
        f"({num_success} successful, {len(new_records) - num_success} errors)."
    )
