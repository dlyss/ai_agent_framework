"""Fine-tuning schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TrainingExampleInput(BaseModel):
    """Training example input."""
    instruction: str = Field(..., description="Instruction/question")
    input: str = Field("", description="Optional additional input")
    output: str = Field(..., description="Expected output/answer")


class DatasetUploadRequest(BaseModel):
    """Dataset upload request."""
    examples: List[TrainingExampleInput]
    format: str = Field("alpaca", description="Format: alpaca, sharegpt, openai, qa")
    name: str = Field(..., description="Dataset name")


class DatasetUploadResponse(BaseModel):
    """Dataset upload response."""
    name: str
    count: int
    format: str
    validation: Dict[str, Any]


class TrainingConfigInput(BaseModel):
    """Training configuration input."""
    model_name_or_path: str = Field(..., description="Base model path")
    output_name: str = Field(..., description="Output model name")
    
    # Training parameters
    num_train_epochs: int = Field(3, ge=1, le=100)
    learning_rate: float = Field(2e-5, gt=0)
    per_device_train_batch_size: int = Field(4, ge=1)
    gradient_accumulation_steps: int = Field(4, ge=1)
    max_seq_length: int = Field(2048, ge=128)
    
    # LoRA settings
    use_lora: bool = Field(True, description="Use LoRA for efficient training")
    lora_r: int = Field(8, ge=1)
    lora_alpha: int = Field(16, ge=1)
    
    # Quantization
    use_4bit: bool = False
    use_8bit: bool = False


class TrainingStartRequest(BaseModel):
    """Training start request."""
    dataset_name: str
    config: TrainingConfigInput
    eval_split: float = Field(0.1, ge=0, le=0.5)


class TrainingStartResponse(BaseModel):
    """Training start response."""
    job_id: str
    status: str
    message: str


class TrainingStatusResponse(BaseModel):
    """Training status response."""
    job_id: str
    status: str  # pending, running, completed, failed
    progress: float  # 0-100
    current_step: int
    total_steps: int
    loss: Optional[float] = None
    metrics: Dict[str, Any] = {}
    error: Optional[str] = None


class TrainedModelInfo(BaseModel):
    """Trained model information."""
    name: str
    path: str
    base_model: str
    created_at: str
    is_lora: bool
    config: Dict[str, Any] = {}


class TrainedModelsResponse(BaseModel):
    """Trained models list response."""
    models: List[TrainedModelInfo]
