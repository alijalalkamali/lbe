"""Local HuggingFace model backend.

Loads any HuggingFace causal language model (Llama, Qwen, Mistral, etc.) and
runs inference locally on the GPU. Wraps the messy details of tokenization,
device placement, and generation behind the Model interface.
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
        max_new_tokens: int = 256,
        temperature: float = 1.0,
        seed: int | None = None,
    ) -> GenerationOutput:
        if seed is not None:
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

        return GenerationOutput(
            text=text,
            prompt=prompt,
            model_name=self.model_name,
        )
