"""
NeuroFence - Member 3: Activation Tracker
=========================================

What this file does
-------------------
1. Loads a local Hugging Face model + tokenizer (offline capable).
2. Finds the transformer blocks of the model automatically
   (we do NOT hardcode layer names - different models use different names).
3. Registers PyTorch *forward hooks* on a few selected blocks.
4. Runs a prompt through the model; the hooks "listen" and copy the
   activation tensor that each block produces.
5. Converts the tensor into small JSON-friendly data + basic statistics.

Concept: what is a forward hook?
--------------------------------
A forward hook is a small function that PyTorch calls automatically every
time a layer finishes its forward pass. It receives the layer's output, so
we can look at (and save) the internal activations without changing the model.

Concept: what do we store?
--------------------------
A block output has shape [batch, tokens, hidden_size] (e.g. [1, 12, 768]).
To keep the JSON small we average over the tokens, so every layer becomes
ONE vector of `hidden_size` numbers. Position i of that vector = "neuron i"
(activation position). The detector later compares position by position.
"""

import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from torch import nn


# ---------------------------------------------------------------------------
# 1. Model loading
# ---------------------------------------------------------------------------
def load_model(model_name_or_path: str, local_only: bool = False,
               dtype: Optional[str] = None, device_map: Optional[str] = None):
    """Load tokenizer + causal LM.

    model_name_or_path : Hugging Face name (e.g. "distilgpt2") or a local folder.
    local_only         : True => never touch the internet (offline / sandbox mode).
    dtype              : None (float32), "float16" or "bfloat16" - use float16 for big models (Mistral-7B).
    device_map         : None (CPU) or "auto" (needs `pip install accelerate`; spreads big models over GPU/CPU).
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if local_only:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

    kwargs = {"local_files_only": local_only}
    if dtype:
        kwargs["torch_dtype"] = getattr(torch, dtype)
    if device_map:
        kwargs["device_map"] = device_map
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, local_files_only=local_only)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name_or_path, **kwargs)
    model.eval()  # inference mode (no dropout)
    return model, tokenizer


# ---------------------------------------------------------------------------
# 2. Architecture inspection
# ---------------------------------------------------------------------------
_BLOCK_LIST_NAMES = ("h", "layers", "layer", "blocks", "block")


def find_transformer_blocks(model: nn.Module) -> Tuple[str, List[Tuple[str, nn.Module]]]:
    """Find the ModuleList that holds the transformer blocks.

    Uses model.named_modules() and picks the longest ModuleList whose name
    looks like a block list (GPT-2: 'transformer.h', LLaMA: 'model.layers',
    GPT-NeoX: 'gpt_neox.layers', OPT: 'model.decoder.layers', ...).
    Returns (list_name, [(full_module_name, module), ...]).
    """
    best_name, best_list = None, None
    for name, module in model.named_modules():
        if isinstance(module, nn.ModuleList) and len(module) >= 2:
            if name.split(".")[-1].lower() in _BLOCK_LIST_NAMES:
                if best_list is None or len(module) > len(best_list):
                    best_name, best_list = name, module

    if best_list is None:  # fallback: any longest ModuleList
        for name, module in model.named_modules():
            if isinstance(module, nn.ModuleList) and len(module) >= 2:
                if best_list is None or len(module) > len(best_list):
                    best_name, best_list = name, module

    if best_list is None:
        raise RuntimeError(
            "Could not find transformer blocks automatically. "
            "Run: python activation/inspect_model.py --model <name> and check the layer names."
        )
    blocks = [(f"{best_name}.{i}", child) for i, child in enumerate(best_list)]
    return best_name, blocks


def choose_layer_indices(total_blocks: int, num_layers: Optional[int]) -> List[int]:
    """Pick evenly spaced block indices (always includes first and last)."""
    if num_layers is None or num_layers >= total_blocks:
        return list(range(total_blocks))
    if num_layers <= 1:
        return [total_blocks - 1]
    idx = np.linspace(0, total_blocks - 1, num_layers).round().astype(int)
    return sorted(set(int(i) for i in idx))


# ---------------------------------------------------------------------------
# 3. The tracker
# ---------------------------------------------------------------------------
class ActivationTracker:
    """Registers forward hooks on selected blocks and captures activations."""

    def __init__(
        self,
        model: nn.Module,
        num_layers: Optional[int] = 4,
        layer_indices: Optional[List[int]] = None,
        max_values: int = 768,
    ):
        self.model = model
        self.max_values = max_values
        self.list_name, self.blocks = find_transformer_blocks(model)
        self.layer_indices = layer_indices or choose_layer_indices(len(self.blocks), num_layers)

        # key ("layer_8") -> full module path ("transformer.h.8")
        self.layer_map: Dict[str, str] = {}
        self._captured: Dict[str, torch.Tensor] = {}
        self._handles = []
        self._register_hooks()

    # -- hooks -------------------------------------------------------------
    def _make_hook(self, key: str):
        def hook(module, inputs, output):
            out = output
            if isinstance(out, (tuple, list)):      # many blocks return (hidden, ...)
                out = out[0]
            if not isinstance(out, torch.Tensor):   # e.g. ModelOutput objects
                out = getattr(out, "last_hidden_state", None)
            if out is None:
                return
            # detach from graph -> CPU -> float32
            self._captured[key] = out.detach().float().cpu()
        return hook

    def _register_hooks(self):
        for i in self.layer_indices:
            path, module = self.blocks[i]
            key = f"layer_{i}"
            self.layer_map[key] = path
            self._handles.append(module.register_forward_hook(self._make_hook(key)))

    def remove_hooks(self):
        for h in self._handles:
            h.remove()
        self._handles = []

    # -- running a prompt ---------------------------------------------------
    def _pool(self, tensor: torch.Tensor) -> np.ndarray:
        """[1, tokens, hidden] -> [hidden] by averaging over tokens."""
        if tensor.dim() == 3:
            vec = tensor[0].mean(dim=0)
        elif tensor.dim() == 2:
            vec = tensor.mean(dim=0)
        else:
            vec = tensor.flatten()
        return vec.numpy()

    def run_prompt(self, tokenizer, prompt: str, max_length: int = 128) -> dict:
        """Run ONE prompt and return {"activations": ..., "statistics": ..., "num_tokens": n}."""
        self._captured.clear()
        text = prompt if prompt and prompt.strip() else " "
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        with torch.no_grad():
            self.model(**inputs)

        activations, statistics = {}, {}
        for key, tensor in self._captured.items():
            full = tensor.numpy()
            pooled = self._pool(tensor)
            activations[key] = [round(float(v), 5) for v in pooled[: self.max_values]]
            statistics[key] = {
                "mean": round(float(full.mean()), 6),
                "std": round(float(full.std()), 6),
                "min": round(float(full.min()), 6),
                "max": round(float(full.max()), 6),
            }
        return {
            "activations": activations,
            "statistics": statistics,
            "num_tokens": int(inputs["input_ids"].shape[1]),
        }
