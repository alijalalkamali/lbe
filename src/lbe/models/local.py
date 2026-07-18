"""Local HuggingFace model backend.

Loads any HuggingFace causal language model (Llama, Qwen, Gemma, etc.) and
runs inference locally on the GPU. Wraps the messy details of tokenization,
device placement, and generation behind the Model interface.

Not used for the behavioral study (all six study models are API-served).
This backend is the entry point for the mechanistic-interpretability phase,
where open-weight models are run locally to access hidden states.

Sampling controls:
    Unlike the API backends, this one CAN honor temperature/seed per call,
    so it accepts them as optional keyword arguments beyond the declared
    Model.generate() interface. Callers using only the declared signature
    get greedy, deterministic decoding — see the temperature default below.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from lbe.models.base import GenerationOutput, Model


class LocalHFModel(Model):
    """A locally-loaded HuggingFace causal LM running on GPU.

    Loads weights once at construction. All subsequent generate() calls reuse
    the loaded model. Designed for evaluation, not training — runs in
    inference mode with no_grad to save memory and compute.
    """

    def __init__(
        self,
        model_name: str,
        device: str = "cuda:0",
        dtype: torch.dtype = torch.float16,
    ):
        super().__init__(model_name)
        self.device = device
        self.dtype = dtype

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map=device,
        )
        self.model.eval()  # disable dropout, batch-norm running stats, etc.

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 500,
        temperature: float = 0.0,
        seed: int | None = None,
    ) -> GenerationOutput:
        """Generate a completion locally.

        Args:
            prompt: The input text.
            max_new_tokens: Maximum new tokens to generate.
            temperature: Sampling temperature. Defaults to 0.0 (greedy,
                deterministic) rather than 1.0, because every use of this
                backend in this project is an evaluation or interpretability
                run where reproducibility is required. A caller who wants
                sampling must ask for it explicitly.
            seed: Torch seed, applied only when temperature > 0 makes
                generation stochastic. Ignored under greedy decoding, where
                it has no effect anyway.

        Returns:
            GenerationOutput with finish_reason set to "length" if the
            generation ran to the token ceiling without emitting EOS, or
            "stop" if it terminated naturally — matching the vocabulary the
            API backends report, so truncation checks are uniform across
            backends.
        """
        if seed is not None and temperature > 0.0:
            torch.manual_seed(seed)

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        prompt_length = inputs.input_ids.shape[1]

        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=temperature > 0.0,
                temperature=temperature if temperature > 0.0 else 1.0,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Strip the prompt tokens; we only want the new generation
        new_token_ids = output_ids[0, prompt_length:]
        text = self.tokenizer.decode(new_token_ids, skip_special_tokens=True)

        # HF doesn't report a finish_reason, so derive one that matches the
        # API backends' vocabulary: generation is truncated iff it produced
        # the full token allowance without ever emitting EOS.
        emitted_eos = bool((new_token_ids == self.tokenizer.eos_token_id).any())
        hit_ceiling = new_token_ids.shape[0] >= max_new_tokens
        finish_reason = "length" if (hit_ceiling and not emitted_eos) else "stop"

        return GenerationOutput(
            text=text,
            prompt=prompt,
            model_name=self.model_name,
            finish_reason=finish_reason,
        )
