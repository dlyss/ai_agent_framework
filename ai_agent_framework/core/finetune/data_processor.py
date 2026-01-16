"""Data processor for fine-tuning datasets."""

import json
from typing import List, Optional, Dict, Any, Iterator
from pathlib import Path
from pydantic import BaseModel
from datasets import Dataset


class TrainingExample(BaseModel):
    """Training example model."""
    instruction: str
    input: str = ""
    output: str
    metadata: Dict[str, Any] = {}


class DataProcessor:
    """Process and prepare data for fine-tuning."""
    
    FORMATS = ["alpaca", "sharegpt", "openai", "qa"]
    
    def __init__(
        self,
        format: str = "alpaca",
        max_length: int = 2048,
        truncate: bool = True
    ):
        if format not in self.FORMATS:
            raise ValueError(f"Unsupported format: {format}. Use: {self.FORMATS}")
        
        self.format = format
        self.max_length = max_length
        self.truncate = truncate
    
    def load_jsonl(self, filepath: str) -> List[Dict]:
        """Load data from JSONL file."""
        data = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    
    def load_json(self, filepath: str) -> List[Dict]:
        """Load data from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return [data]
    
    def save_jsonl(self, data: List[Dict], filepath: str):
        """Save data to JSONL file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    def convert_to_alpaca(self, examples: List[TrainingExample]) -> List[Dict]:
        """Convert to Alpaca format.
        
        Format: {"instruction": ..., "input": ..., "output": ...}
        """
        return [
            {
                "instruction": ex.instruction,
                "input": ex.input,
                "output": ex.output
            }
            for ex in examples
        ]
    
    def convert_to_sharegpt(self, examples: List[TrainingExample]) -> List[Dict]:
        """Convert to ShareGPT format.
        
        Format: {"conversations": [{"from": "human", "value": ...}, {"from": "gpt", "value": ...}]}
        """
        results = []
        for ex in examples:
            user_content = ex.instruction
            if ex.input:
                user_content += f"\n\n{ex.input}"
            
            results.append({
                "conversations": [
                    {"from": "human", "value": user_content},
                    {"from": "gpt", "value": ex.output}
                ]
            })
        return results
    
    def convert_to_openai(self, examples: List[TrainingExample]) -> List[Dict]:
        """Convert to OpenAI fine-tuning format.
        
        Format: {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
        """
        results = []
        for ex in examples:
            user_content = ex.instruction
            if ex.input:
                user_content += f"\n\n{ex.input}"
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": ex.output}
            ]
            results.append({"messages": messages})
        return results
    
    def convert_to_qa(self, examples: List[TrainingExample]) -> List[Dict]:
        """Convert to simple Q&A format.
        
        Format: {"question": ..., "answer": ...}
        """
        results = []
        for ex in examples:
            question = ex.instruction
            if ex.input:
                question += f"\n{ex.input}"
            results.append({
                "question": question,
                "answer": ex.output
            })
        return results
    
    def convert(
        self,
        examples: List[TrainingExample],
        target_format: Optional[str] = None
    ) -> List[Dict]:
        """Convert examples to target format.
        
        Args:
            examples: List of TrainingExample
            target_format: Target format (default: self.format)
            
        Returns:
            Converted data list
        """
        fmt = target_format or self.format
        
        converters = {
            "alpaca": self.convert_to_alpaca,
            "sharegpt": self.convert_to_sharegpt,
            "openai": self.convert_to_openai,
            "qa": self.convert_to_qa,
        }
        
        return converters[fmt](examples)
    
    def parse_alpaca(self, data: List[Dict]) -> List[TrainingExample]:
        """Parse Alpaca format data."""
        return [
            TrainingExample(
                instruction=item.get("instruction", ""),
                input=item.get("input", ""),
                output=item.get("output", "")
            )
            for item in data
        ]
    
    def parse_sharegpt(self, data: List[Dict]) -> List[TrainingExample]:
        """Parse ShareGPT format data."""
        examples = []
        for item in data:
            conversations = item.get("conversations", [])
            if len(conversations) >= 2:
                human_msg = next(
                    (c["value"] for c in conversations if c["from"] == "human"),
                    ""
                )
                gpt_msg = next(
                    (c["value"] for c in conversations if c["from"] == "gpt"),
                    ""
                )
                examples.append(TrainingExample(
                    instruction=human_msg,
                    output=gpt_msg
                ))
        return examples
    
    def to_hf_dataset(
        self,
        examples: List[TrainingExample],
        tokenizer=None
    ) -> Dataset:
        """Convert to HuggingFace Dataset.
        
        Args:
            examples: List of TrainingExample
            tokenizer: Optional tokenizer for preprocessing
            
        Returns:
            HuggingFace Dataset
        """
        data = self.convert(examples)
        dataset = Dataset.from_list(data)
        
        if tokenizer and self.format == "alpaca":
            def format_prompt(example):
                prompt = f"### Instruction:\n{example['instruction']}\n\n"
                if example.get('input'):
                    prompt += f"### Input:\n{example['input']}\n\n"
                prompt += f"### Response:\n{example['output']}"
                return {"text": prompt}
            
            dataset = dataset.map(format_prompt)
        
        return dataset
    
    def split_dataset(
        self,
        examples: List[TrainingExample],
        train_ratio: float = 0.9,
        seed: int = 42
    ) -> tuple:
        """Split dataset into train and validation.
        
        Args:
            examples: List of examples
            train_ratio: Ratio for training set
            seed: Random seed
            
        Returns:
            Tuple of (train_examples, val_examples)
        """
        import random
        random.seed(seed)
        
        shuffled = examples.copy()
        random.shuffle(shuffled)
        
        split_idx = int(len(shuffled) * train_ratio)
        return shuffled[:split_idx], shuffled[split_idx:]
    
    def validate_examples(
        self,
        examples: List[TrainingExample]
    ) -> Dict[str, Any]:
        """Validate training examples.
        
        Args:
            examples: List of examples to validate
            
        Returns:
            Validation report
        """
        report = {
            "total": len(examples),
            "valid": 0,
            "invalid": 0,
            "errors": [],
            "stats": {
                "avg_instruction_length": 0,
                "avg_output_length": 0,
                "max_instruction_length": 0,
                "max_output_length": 0,
            }
        }
        
        instruction_lengths = []
        output_lengths = []
        
        for i, ex in enumerate(examples):
            if not ex.instruction.strip():
                report["errors"].append(f"Example {i}: Empty instruction")
                report["invalid"] += 1
                continue
            if not ex.output.strip():
                report["errors"].append(f"Example {i}: Empty output")
                report["invalid"] += 1
                continue
            
            report["valid"] += 1
            instruction_lengths.append(len(ex.instruction))
            output_lengths.append(len(ex.output))
        
        if instruction_lengths:
            report["stats"]["avg_instruction_length"] = sum(instruction_lengths) / len(instruction_lengths)
            report["stats"]["max_instruction_length"] = max(instruction_lengths)
        if output_lengths:
            report["stats"]["avg_output_length"] = sum(output_lengths) / len(output_lengths)
            report["stats"]["max_output_length"] = max(output_lengths)
        
        return report
