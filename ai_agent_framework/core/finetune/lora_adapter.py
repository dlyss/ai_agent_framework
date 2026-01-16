"""LoRA Adapter management."""

from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import (
    LoraConfig,
    get_peft_model,
    PeftModel,
    TaskType,
)


class LoRAConfig(BaseModel):
    """LoRA configuration."""
    r: int = 8                              # Rank
    lora_alpha: int = 16                    # Alpha scaling
    lora_dropout: float = 0.1               # Dropout
    target_modules: List[str] = ["q_proj", "v_proj", "k_proj", "o_proj"]
    bias: str = "none"                      # none, all, lora_only
    task_type: str = "CAUSAL_LM"
    
    # Quantization
    use_4bit: bool = False
    use_8bit: bool = False
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    

class LoRAAdapter:
    """LoRA adapter for efficient fine-tuning."""
    
    def __init__(
        self,
        base_model_path: str,
        config: Optional[LoRAConfig] = None,
        device_map: str = "auto"
    ):
        self.base_model_path = base_model_path
        self.config = config or LoRAConfig()
        self.device_map = device_map
        
        self.model = None
        self.tokenizer = None
        self.peft_model = None
    
    def _get_quantization_config(self):
        """Get BitsAndBytes quantization config."""
        if not (self.config.use_4bit or self.config.use_8bit):
            return None
        
        from transformers import BitsAndBytesConfig
        
        if self.config.use_4bit:
            compute_dtype = getattr(torch, self.config.bnb_4bit_compute_dtype)
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
                bnb_4bit_use_double_quant=True,
            )
        else:
            return BitsAndBytesConfig(load_in_8bit=True)
    
    def load_base_model(self):
        """Load the base model with optional quantization."""
        quant_config = self._get_quantization_config()
        
        load_kwargs = {
            "pretrained_model_name_or_path": self.base_model_path,
            "device_map": self.device_map,
            "trust_remote_code": True,
        }
        
        if quant_config:
            load_kwargs["quantization_config"] = quant_config
        else:
            load_kwargs["torch_dtype"] = torch.float16
        
        self.model = AutoModelForCausalLM.from_pretrained(**load_kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_path,
            trust_remote_code=True
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def apply_lora(self) -> None:
        """Apply LoRA adapters to the model."""
        if self.model is None:
            self.load_base_model()
        
        # Prepare model for k-bit training if quantized
        if self.config.use_4bit or self.config.use_8bit:
            from peft import prepare_model_for_kbit_training
            self.model = prepare_model_for_kbit_training(self.model)
        
        # Create LoRA config
        task_type = getattr(TaskType, self.config.task_type)
        lora_config = LoraConfig(
            r=self.config.r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.target_modules,
            bias=self.config.bias,
            task_type=task_type,
        )
        
        # Apply LoRA
        self.peft_model = get_peft_model(self.model, lora_config)
        self.peft_model.print_trainable_parameters()
    
    def save_adapter(self, path: str):
        """Save LoRA adapter weights.
        
        Args:
            path: Save path
        """
        if self.peft_model is None:
            raise ValueError("No LoRA model to save. Call apply_lora() first.")
        
        Path(path).mkdir(parents=True, exist_ok=True)
        self.peft_model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
    
    def load_adapter(self, adapter_path: str):
        """Load a saved LoRA adapter.
        
        Args:
            adapter_path: Path to saved adapter
        """
        if self.model is None:
            self.load_base_model()
        
        self.peft_model = PeftModel.from_pretrained(
            self.model,
            adapter_path,
            device_map=self.device_map
        )
        
        # Load tokenizer if available
        tokenizer_path = Path(adapter_path)
        if (tokenizer_path / "tokenizer_config.json").exists():
            self.tokenizer = AutoTokenizer.from_pretrained(adapter_path)
    
    def merge_and_save(self, output_path: str):
        """Merge LoRA weights with base model and save.
        
        Args:
            output_path: Output path for merged model
        """
        if self.peft_model is None:
            raise ValueError("No LoRA model to merge. Load adapter first.")
        
        # Merge weights
        merged_model = self.peft_model.merge_and_unload()
        
        # Save
        Path(output_path).mkdir(parents=True, exist_ok=True)
        merged_model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
    
    def list_adapters(self, adapters_dir: str) -> List[Dict[str, Any]]:
        """List available adapters in directory.
        
        Args:
            adapters_dir: Directory containing adapters
            
        Returns:
            List of adapter info dicts
        """
        adapters = []
        adapters_path = Path(adapters_dir)
        
        if not adapters_path.exists():
            return adapters
        
        for path in adapters_path.iterdir():
            if path.is_dir():
                config_file = path / "adapter_config.json"
                if config_file.exists():
                    import json
                    with open(config_file) as f:
                        config = json.load(f)
                    adapters.append({
                        "name": path.name,
                        "path": str(path),
                        "config": config
                    })
        
        return adapters
    
    def switch_adapter(self, adapter_name: str, adapters_dir: str):
        """Switch to a different adapter.
        
        Args:
            adapter_name: Name of adapter to switch to
            adapters_dir: Directory containing adapters
        """
        adapter_path = Path(adapters_dir) / adapter_name
        if not adapter_path.exists():
            raise ValueError(f"Adapter not found: {adapter_name}")
        
        self.load_adapter(str(adapter_path))
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text using the LoRA model.
        
        Args:
            prompt: Input prompt
            max_new_tokens: Max tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        model = self.peft_model or self.model
        if model is None:
            raise ValueError("No model loaded.")
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                **kwargs
            )
        
        return self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        )
