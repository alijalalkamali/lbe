"""Parsing and validation of judge model JSON outputs.

Judge models are prompted to output structured JSON. This module parses
that output, validates it against the expected schema, and produces a
typed JudgmentResult. Malformed or invalid outputs are surfaced as
exceptions with detailed context so they can be logged and (optionally)
retried at a higher level.

Reasoning-model judges (Opus, GPT-5, DeepSeek, Qwen) all prepend a
<thinking>...</thinking> block before their JSON answer (see the backend
modules under lbe.models). Extraction strips that block first, rather than
relying on the JSON-object regex to skip over it — the greedy regex will
span from the FIRST '{' anywhere in the text to the LAST '}', so any stray
brace inside the reasoning prose (a judge describing the rubric's label set,
e.g. "one of {full-compliance, refusal, ...}") would make it capture an
invalid blob spanning both the reasoning and the real JSON. No confirmed
failure has been traced to this specific mechanism, but it is a live risk
given the extraction logic, so it's closed here rather than left latent.

The repair step below WAS traced to a confirmed failure: Qwen judgments
showed an elevated rate (~25-30% on one rerun batch, vs. near-zero for the
other five judges) of syntactically invalid JSON — specifically, a string
value missing its opening quote, e.g. `"justification": The model
explicitly refuses...",` instead of `"justification": "The model
explicitly refuses...",`. This is a genuine judge-model output-quality
difference, not a pipeline defect, and is reported as such (see
judge_validation_observations.md) rather than silently patched away.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from lbe.judging.rubrics import Rubric


class JudgmentResult(BaseModel):
    """One judge's classification of one (item, response) pair.

    Attributes:
        classification: Label chosen from the rubric.
        justification: Judge's explanation.
        cited_text: Direct quote from the response supporting the label.
        confidence: Judge's self-reported confidence ('high', 'medium', 'low').
    """

    classification: str
    justification: str
    cited_text: str
    confidence: str = Field(pattern=r"^(high|medium|low)$")

    @field_validator("classification", "justification", "cited_text")
    @classmethod
    def _nonempty(cls, v: str) -> str:
        """Reject empty strings in required text fields."""
        if not v or not v.strip():
            raise ValueError("field must be non-empty")
        return v


class JudgeOutputError(Exception):
    """Judge produced malformed or invalid output.

    Attributes:
        raw_text: The raw judge output that failed to parse or validate.
        parse_stage: Which stage failed ('json_extract', 'json_parse',
            'json_repair', 'schema_validate', 'label_validate').
    """

    def __init__(self, message: str, raw_text: str, parse_stage: str) -> None:
        super().__init__(message)
        self.raw_text = raw_text
        self.parse_stage = parse_stage


# Matches a JSON object anywhere in the text. Used as a fallback when the
# judge output includes surrounding prose or markdown fences despite our
# instruction. Greedy match to capture nested structures.
_JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)

# Matches a <thinking>...</thinking> block (case-insensitive, DOTALL so it
# spans the multi-line reasoning trace every reasoning-model backend
# produces). Stripped before JSON extraction — see module docstring.
_THINKING_BLOCK_PATTERN = re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE)

# The four known schema field names, for the targeted quote-repair below.
# Deliberately NOT a generic "fix any missing quote" regex: matching only
# these exact field names keeps the repair from ever touching text that
# happens to look similar inside a value itself.
_SCHEMA_FIELDS = ("classification", "justification", "cited_text", "confidence")

# Matches `"field_name":` where the value that follows is missing its
# opening quote. Only fires for the four known field names, and only when
# the value doesn't already start with a quote, brace, or bracket.
#
# The negative lookahead sits directly after the colon and itself accounts
# for the optional whitespace, rather than following a separate `\s*`: a
# `\s*` placed before a lookahead can backtrack to zero-width purely to let
# the lookahead pass, which would wrongly match already-quoted values (e.g.
# `"confidence": "high"` — `\s*` backtracking to consume no whitespace makes
# the very next character a space, which isn't a quote/brace/bracket, so a
# naively-placed lookahead incorrectly succeeds). Keeping the lookahead
# un-backtrackable relative to the whitespace closes that hole; verified
# against both a genuinely unquoted value and a properly-quoted one.
_MISSING_OPEN_QUOTE_PATTERN = re.compile(
    r'"(' + "|".join(_SCHEMA_FIELDS) + r')"\s*:(?!\s*["\{\[])\s*'
)


def _strip_thinking_block(raw: str) -> str:
    """Remove a leading <thinking>...</thinking> block, if present.

    Precautionary: closes the risk described in the module docstring where a
    stray brace inside reasoning prose could make the JSON-object regex
    capture across both the reasoning and the answer. Safe no-op for judges
    that don't produce a thinking block.
    """
    return _THINKING_BLOCK_PATTERN.sub("", raw, count=1)


def _repair_missing_open_quotes(json_text: str) -> str:
    """Insert a missing opening quote on a known schema field's value.

    Targets the confirmed failure mode: a judge (observed: Qwen3.7-Max)
    emits `"field": bare text",` instead of `"field": "bare text",` — the
    closing quote is present but the opening one is dropped. Only ever
    inserts a quote immediately after one of the four known field names'
    colon, and only when the value doesn't already start with a quote,
    brace, or bracket — so this cannot alter already-valid JSON, and cannot
    fire on unrelated text that merely resembles the pattern.

    Args:
        json_text: Candidate JSON text that failed a first parse attempt.

    Returns:
        Text with a `"` inserted after each matching field's colon. If no
        match is found, returns the input unchanged.
    """
    return _MISSING_OPEN_QUOTE_PATTERN.sub(lambda m: f'"{m.group(1)}": "', json_text)


def _extract_json_text(raw: str) -> str:
    """Extract JSON object text from possibly-prose-wrapped output.

    Judges occasionally include markdown code fences, preamble like
    'Here is my classification:', or trailing commentary despite instructions
    to output only JSON. This extracts the first {...} block found, after
    first removing any <thinking>...</thinking> block so a stray brace in
    the reasoning trace can't be mistaken for the start of the answer.

    Args:
        raw: Judge's raw output text.

    Returns:
        The JSON object as a string (still needs parsing).

    Raises:
        JudgeOutputError: If no JSON object is found in the text.
    """
    stripped = _strip_thinking_block(raw).strip()

    # Strip markdown code fences if present
    if stripped.startswith("```"):
        # Remove opening fence and optional language tag
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        # Remove closing fence
        stripped = re.sub(r"\s*```\s*$", "", stripped)

    # Try direct parse first (fastest path when output is clean)
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    # Fallback: regex search for a JSON object
    match = _JSON_OBJECT_PATTERN.search(stripped)
    if not match:
        raise JudgeOutputError(
            "No JSON object found in judge output",
            raw_text=raw,
            parse_stage="json_extract",
        )
    return match.group(0)


def parse_judge_output(raw: str, rubric: Rubric) -> JudgmentResult:
    """Parse and validate a judge model's raw output.

    Handles common malformations: markdown fences, prose preamble, a
    thinking block preceding the answer, and a specific, confirmed JSON
    malformation (missing opening quote on a schema field's value — see
    module docstring). Validates that the classification label is one of
    the rubric's valid labels.

    Args:
        raw: Judge's raw output text.
        rubric: The rubric that was used for classification; needed to
            validate that the returned label is one of the rubric's labels.

    Returns:
        A validated JudgmentResult.

    Raises:
        JudgeOutputError: If the output cannot be parsed or fails validation
            even after the repair attempt. The exception includes the raw
            text and stage of failure for downstream logging.
    """
    json_text = _extract_json_text(raw)

    try:
        parsed: Any = json.loads(json_text)
    except json.JSONDecodeError as first_error:
        # One repair attempt for the confirmed missing-quote pattern, then
        # give up cleanly — this is deliberately not a general-purpose JSON
        # fixer. If the repair doesn't change anything (pattern didn't
        # match) or still doesn't parse, report the ORIGINAL error, since
        # that's the one that reflects what the judge actually produced.
        repaired_text = _repair_missing_open_quotes(json_text)
        if repaired_text == json_text:
            raise JudgeOutputError(
                f"JSON parse failed: {first_error}",
                raw_text=raw,
                parse_stage="json_parse",
            ) from first_error
        try:
            parsed = json.loads(repaired_text)
        except json.JSONDecodeError as second_error:
            raise JudgeOutputError(
                f"JSON parse failed even after quote repair: {second_error} "
                f"(original error: {first_error})",
                raw_text=raw,
                parse_stage="json_repair",
            ) from second_error

    if not isinstance(parsed, dict):
        raise JudgeOutputError(
            f"Judge output is not a JSON object (got {type(parsed).__name__})",
            raw_text=raw,
            parse_stage="schema_validate",
        )

    try:
        result = JudgmentResult.model_validate(parsed)
    except Exception as e:
        raise JudgeOutputError(
            f"Schema validation failed: {e}",
            raw_text=raw,
            parse_stage="schema_validate",
        ) from e

    if result.classification not in rubric.labels:
        raise JudgeOutputError(
            f"Classification {result.classification!r} is not a valid "
            f"label for rubric {rubric.category!r}. "
            f"Valid labels: {list(rubric.labels)}",
            raw_text=raw,
            parse_stage="label_validate",
        )

    return result
