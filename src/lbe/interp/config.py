"""
Configuration for activation harvesting.

Two hardware profiles are supported explicitly, because dtype and attention
implementation are hardware-determined, not free choices:

  - "local_dev"  : Pascal-generation GPU (e.g. GTX 1080 Ti). No bf16 support,
                   no FlashAttention kernel support. Use fp16 + eager attention.
  - "rental_gpu" : Ampere-or-newer (e.g. H100). Use bf16 + flash_attention_2.

Using the wrong profile on the wrong hardware will raise at model-load time
rather than silently degrading precision or speed.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import torch

HardwareProfile = Literal["local_dev", "rental_gpu"]

_PROFILE_SETTINGS: dict[HardwareProfile, dict] = {
    "local_dev": {
        "torch_dtype": torch.float16,
        "attn_implementation": "eager",
    },
    "rental_gpu": {
        "torch_dtype": torch.bfloat16,
        "attn_implementation": "flash_attention_2",
    },
}


@dataclass
class HarvestConfig:
    # --- model ---
    model_name: str
    hardware_profile: HardwareProfile
    device_map: str = "auto"

    # --- what to harvest ---
    layer_stride: int = 4  # sample every Nth decoder layer
    layer_indices: list[int] | None = None  # explicit override; if set, layer_stride is ignored

    # --- data selection ---
    category: str = "values_conflict_low"
    condition: str = "base"
    responder_model: str = "together:meta-llama/Llama-3.3-70B-Instruct-Turbo"

    # --- output ---
    output_dir: Path = Path("results/interp/activations")

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        if self.hardware_profile not in _PROFILE_SETTINGS:
            raise ValueError(
                f"Unknown hardware_profile {self.hardware_profile!r}; "
                f"expected one of {list(_PROFILE_SETTINGS)}"
            )

    @property
    def torch_dtype(self) -> torch.dtype:
        return _PROFILE_SETTINGS[self.hardware_profile]["torch_dtype"]

    @property
    def attn_implementation(self) -> str:
        return _PROFILE_SETTINGS[self.hardware_profile]["attn_implementation"]

    def resolve_layer_indices(self, n_layers: int) -> list[int]:
        """Every-Nth-layer sample, or an explicit override if provided."""
        if self.layer_indices is not None:
            bad = [i for i in self.layer_indices if not (0 <= i < n_layers)]
            if bad:
                raise ValueError(f"layer_indices out of range for {n_layers}-layer model: {bad}")
            return sorted(self.layer_indices)
        return list(range(0, n_layers, self.layer_stride))
