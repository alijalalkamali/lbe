"""Tests for eval item schemas and JSONL I/O."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from lbe.io.dataset import (
    ConsistencyItem,
    FaithfulnessItem,
    SteerabilityItem,
)
from lbe.io.jsonl import read_jsonl, write_jsonl


def test_steerability_item_construction():
    """Build a SteerabilityItem directly and verify fields."""
    item = SteerabilityItem(
        id="test_001",
        category="length_control",
        base_prompt="Describe X.",
        steering_instruction="Describe X in two sentences.",
        expected_behavior_change="Two-sentence response.",
    )
    assert item.id == "test_001"
    assert item.item_type == "steerability"
    assert item.metadata == {}


def test_steerability_item_rejects_bad_type():
    """Pydantic should reject the wrong item_type literal."""
    with pytest.raises(ValidationError):  # ValidationError, but Pydantic's exact class
        SteerabilityItem(
            id="test_002",
            category="format",
            item_type="not_a_real_type",  # invalid literal
            base_prompt="X",
            steering_instruction="Y",
            expected_behavior_change="Z",
        )


def test_consistency_item_optional_correct_answer():
    """Consistency items can omit correct_answer for non-factual questions."""
    item = ConsistencyItem(
        id="test_003",
        category="factual",
        base_prompt="What is 2 + 2?",
        paraphrases=["What does 2 plus 2 equal?", "Calculate 2 + 2."],
    )
    assert item.correct_answer is None


def test_faithfulness_item_construction():
    """Build a FaithfulnessItem and verify its fields."""
    item = FaithfulnessItem(
        id="test_004",
        category="arithmetic",
        question="If X = 5 and Y = 3, what is X * Y?",
        correct_answer="15",
        intervention_target="multiplication step",
    )
    assert item.item_type == "faithfulness"


def test_jsonl_roundtrip(tmp_path: Path):
    """Items written to JSONL should read back identically."""
    items = [
        SteerabilityItem(
            id=f"rt_{i:03d}",
            category="test",
            base_prompt=f"Prompt {i}",
            steering_instruction=f"Steered prompt {i}",
            expected_behavior_change=f"Change {i}",
        )
        for i in range(3)
    ]
    path = tmp_path / "roundtrip.jsonl"
    write_jsonl(path, items)

    loaded = list(read_jsonl(path, SteerabilityItem))
    assert len(loaded) == 3
    assert loaded[0].id == "rt_000"
    assert loaded[2].base_prompt == "Prompt 2"


def test_jsonl_reads_real_steerability_file():
    """Verify the hand-crafted eval items file loads cleanly."""
    items = list(read_jsonl("data/steerability_items.jsonl", SteerabilityItem))
    assert len(items) == 10
    assert all(item.item_type == "steerability" for item in items)
    # Spot-check: categories should include at least 3 distinct values
    categories = {item.category for item in items}
    assert len(categories) >= 3
