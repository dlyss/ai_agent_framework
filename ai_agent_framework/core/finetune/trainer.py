"""Fine-tuning trainer for full and LoRA training."""

import os
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
from dataclasses import dataclass, field
from pydantic import BaseModel
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from datasets import Dataset

from app.config import get_settings


class TrainingConfig(BaseModel):
    """Training configuration."""
    # Model
    model_name_or_path: str
    output_dir: Optional[str] = None
    
    # Training parameters
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    max_grad_norm: float = 1.0
    
    # Sequence length
    max_seq_length: int = 2048
    
    # Optimization
    optim: str = "adamw_torch"
    lr_scheduler_type: str = "cosine"
    
    # Logging
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    save_total_limit: int = 3
    
    # Mixed precision
    fp16: bool = False
    bf16: bool = False
    
    # Device
    device_map: str = "auto"
    
    # LoRA specific (if using LoRA)
    use_lora: bool = False
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    lora_target_modules: List[str] = ["q_proj", "v_proj"]


class FineTuneTrainer:
    """Fine-tuning trainer supporting full and LoRA training."""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        settings = get_settings()
        
        self.output_dir = config.output_dir or settings.finetune_output_dir
        self.logging_dir = settings.finetune_logging_dir
        
        self.model = None
        self.tokenizer = None
        self.trainer = None
        
        # Create directories
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.logging_dir).mkdir(parents=True, exist_ok=True)
    
    def load_model(self):
        """Load model and tokenizer."""
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name_or_path,
            trust_remote_code=True,
            padding_side="right"
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Determine torch dtype
        torch_dtype = torch.float32
        if self.config.bf16:
            torch_dtype = torch.bfloat16
        elif self.config.fp16:
            torch_dtype = torch.float16
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name_or_path,
            torch_dtype=torch_dtype,
            device_map=self.config.device_map,
            trust_remote_code=True,
        )
        
        # Apply LoRA if configured
        if self.config.use_lora:
            self._apply_lora()
        
        # Enable gradient checkpointing
        if hasattr(self.model, "gradient_checkpointing_enable"):
            self.model.gradient_checkpointing_enable()
    
    def _apply_lora(self):
        """Apply LoRA adapters to the model."""
        from peft import LoraConfig, get_peft_model, TaskType
        
        lora_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.lora_target_modules,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
    
    def prepare_dataset(
        self,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None
    ) -> tuple:
        """Prepare datasets for training.
        
        Args:
            train_dataset: Training dataset
            eval_dataset: Optional evaluation dataset
            
        Returns:
            Tuple of (processed_train, processed_eval)
        """
        def tokenize_function(examples):
            # Handle different formats
            if "text" in examples:
                texts = examples["text"]
            elif "instruction" in examples:
                texts = []
                for i in range(len(examples["instruction"])):
                    text = f"### Instruction:\n{examples['instruction'][i]}\n\n"
                    if examples.get("input") and examples["input"][i]:
                        text += f"### Input:\n{examples['input'][i]}\n\n"
                    text += f"### Response:\n{examples['output'][i]}"
                    texts.append(text)
            else:
                raise ValueError("Dataset must have 'text' or 'instruction' field")
            
            tokenized = self.tokenizer(
                texts,
                truncation=True,
                max_length=self.config.max_seq_length,
                padding="max_length",
            )
            tokenized["labels"] = tokenized["input_ids"].copy()
            return tokenized
        
        train_processed = train_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=train_dataset.column_names
        )
        
        eval_processed = None
        if eval_dataset:
            eval_processed = eval_dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=eval_dataset.column_names
            )
        
        return train_processed, eval_processed
    
    def train(
        self,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        callbacks: Optional[List] = None
    ) -> Dict[str, Any]:
        """Run training.
        
        Args:
            train_dataset: Training dataset
            eval_dataset: Optional evaluation dataset
            callbacks: Optional training callbacks
            
        Returns:
            Training metrics
        """
        if self.model is None:
            self.load_model()
        
        # Prepare datasets
        train_data, eval_data = self.prepare_dataset(train_dataset, eval_dataset)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            warmup_ratio=self.config.warmup_ratio,
            max_grad_norm=self.config.max_grad_norm,
            optim=self.config.optim,
            lr_scheduler_type=self.config.lr_scheduler_type,
            logging_dir=self.logging_dir,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps if eval_data else None,
            evaluation_strategy="steps" if eval_data else "no",
            save_total_limit=self.config.save_total_limit,
            fp16=self.config.fp16,
            bf16=self.config.bf16,
            report_to=["tensorboard"],
            load_best_model_at_end=True if eval_data else False,
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Initialize trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_data,
            eval_dataset=eval_data,
            data_collator=data_collator,
            callbacks=callbacks,
        )
        
        # Train
        train_result = self.trainer.train()
        
        # Save model
        self.save_model()
        
        return {
            "train_loss": train_result.training_loss,
            "train_steps": train_result.global_step,
            "metrics": train_result.metrics
        }
    
    def save_model(self, path: Optional[str] = None):
        """Save the trained model.
        
        Args:
            path: Optional custom save path
        """
        save_path = path or self.output_dir
        
        if self.config.use_lora:
            # Save LoRA adapters
            self.model.save_pretrained(save_path)
        else:
            # Save full model
            self.trainer.save_model(save_path)
        
        self.tokenizer.save_pretrained(save_path)
    
    def load_trained_model(self, path: Optional[str] = None):
        """Load a trained model.
        
        Args:
            path: Model path (default: output_dir)
        """
        load_path = path or self.output_dir
        
        self.tokenizer = AutoTokenizer.from_pretrained(load_path)
        
        if self.config.use_lora:
            from peft import PeftModel
            
            base_model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name_or_path,
                device_map=self.config.device_map,
                trust_remote_code=True,
            )
            self.model = PeftModel.from_pretrained(base_model, load_path)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                load_path,
                device_map=self.config.device_map,
                trust_remote_code=True,
            )
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> str:
        """Generate text with the trained model.
        
        Args:
            prompt: Input prompt
            max_new_tokens: Max tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                **kwargs
            )
        
        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        )
        return response
