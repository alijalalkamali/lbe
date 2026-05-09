"""Tests for the local HuggingFace Model backend.

Uses Qwen 2.5 0.5B as the test model
 - small enough to load fast, real
 enough to verify the full pipeline
 (tokenize, forward pass, generate,
 decode).
"""

import pytest

from lbe.models import GenerationOutput, LocalHFModel, load_model

# Small model, fast load. First test run downloads weights; subsequent runs are cashed.
TEST_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"


@pytest.fixture(scope="module")
def model():
    """Load the model once per test module."""
    return LocalHFModel(TEST_MODEL)


def test_model_generates_text(model):
    """Basic smoke test: model produces non-empty output for a real prompt."""
    output = model.generate("The capital of France is", max_new_tokens=10, seed=42)

    assert isinstance(output, GenerationOutput)
    assert isinstance(output.text, str)
    assert len(output.text) > 0
    assert output.model_name == TEST_MODEL


def test_local_model_seed_is_reproducible(model):
    """Same seed should produce identical output."""
    out1 = model.generate("Once upon a time", max_new_tokens=20, seed=42, temperature=1.0)
    out2 = model.generate("Once upon a time", max_new_tokens=20, seed=42, temperature=1.0)
    assert out1.text == out2.text


def test_local_model_greedy_is_deterministic(model):
    """Greedy decoding (temperature=0) should always produce the same output."""
    out1 = model.generate("The sky is", max_new_tokens=10, temperature=0.0)
    out2 = model.generate("The sky is", max_new_tokens=10, temperature=0.0)
    assert out1.text == out2.text


def test_load_model_factory_returns_local_for_hf_id():
    """Factory should pick LocalHFModel for names containing '/'."""
    model = load_model(TEST_MODEL)
    assert isinstance(model, LocalHFModel)


def test_load_model_factory_rejects_unknown_names():
    """Factroy should raise on names it can't classify."""
    with pytest.raises(ValueError, match="Cannot determine backend"):
        load_model("not-a-real-model-name")
