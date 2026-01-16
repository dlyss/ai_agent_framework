"""Fine-tuning routes."""

import os
import uuid
from typing import Optional, Dict
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.api.auth import get_current_user
from app.config import get_settings
from core.finetune.data_processor import DataProcessor, TrainingExample
from core.finetune.trainer import FineTuneTrainer, TrainingConfig
from schemas.auth import UserResponse
from schemas.finetune import (
    TrainingExampleInput,
    DatasetUploadRequest,
    DatasetUploadResponse,
    TrainingConfigInput,
    TrainingStartRequest,
    TrainingStartResponse,
    TrainingStatusResponse,
    TrainedModelInfo,
    TrainedModelsResponse,
)


router = APIRouter(prefix="/finetune", tags=["Fine-tuning"])

# Store training jobs status
training_jobs: Dict[str, Dict] = {}
datasets_store: Dict[str, list] = {}


@router.post("/datasets", response_model=DatasetUploadResponse)
async def upload_dataset(
    request: DatasetUploadRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload training dataset."""
    try:
        processor = DataProcessor(format=request.format)
        
        # Convert to TrainingExample
        examples = [
            TrainingExample(
                instruction=ex.instruction,
                input=ex.input,
                output=ex.output
            )
            for ex in request.examples
        ]
        
        # Validate
        validation = processor.validate_examples(examples)
        
        if validation["invalid"] > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Invalid examples found",
                    "validation": validation
                }
            )
        
        # Store dataset
        datasets_store[request.name] = examples
        
        # Save to file
        settings = get_settings()
        dataset_dir = Path(settings.finetune_output_dir) / "datasets"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        converted = processor.convert(examples)
        processor.save_jsonl(converted, str(dataset_dir / f"{request.name}.jsonl"))
        
        return DatasetUploadResponse(
            name=request.name,
            count=len(examples),
            format=request.format,
            validation=validation
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets")
async def list_datasets(
    current_user: UserResponse = Depends(get_current_user)
):
    """List available datasets."""
    return {
        "datasets": [
            {
                "name": name,
                "count": len(examples)
            }
            for name, examples in datasets_store.items()
        ]
    }


@router.delete("/datasets/{name}")
async def delete_dataset(
    name: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a dataset."""
    if name not in datasets_store:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    del datasets_store[name]
    
    # Delete file
    settings = get_settings()
    dataset_file = Path(settings.finetune_output_dir) / "datasets" / f"{name}.jsonl"
    if dataset_file.exists():
        dataset_file.unlink()
    
    return {"success": True, "message": f"Dataset {name} deleted"}


def run_training(job_id: str, dataset_name: str, config: TrainingConfigInput, eval_split: float):
    """Background training task."""
    try:
        training_jobs[job_id]["status"] = "running"
        
        # Get dataset
        examples = datasets_store.get(dataset_name)
        if not examples:
            training_jobs[job_id]["status"] = "failed"
            training_jobs[job_id]["error"] = "Dataset not found"
            return
        
        # Split dataset
        processor = DataProcessor()
        train_examples, eval_examples = processor.split_dataset(
            examples, 
            train_ratio=1 - eval_split
        )
        
        # Create HF datasets
        train_dataset = processor.to_hf_dataset(train_examples)
        eval_dataset = processor.to_hf_dataset(eval_examples) if eval_examples else None
        
        # Create trainer config
        settings = get_settings()
        trainer_config = TrainingConfig(
            model_name_or_path=config.model_name_or_path,
            output_dir=str(Path(settings.finetune_output_dir) / "models" / config.output_name),
            num_train_epochs=config.num_train_epochs,
            learning_rate=config.learning_rate,
            per_device_train_batch_size=config.per_device_train_batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            max_seq_length=config.max_seq_length,
            use_lora=config.use_lora,
            lora_r=config.lora_r,
            lora_alpha=config.lora_alpha,
        )
        
        # Initialize trainer
        trainer = FineTuneTrainer(trainer_config)
        
        # Train
        result = trainer.train(train_dataset, eval_dataset)
        
        training_jobs[job_id]["status"] = "completed"
        training_jobs[job_id]["progress"] = 100
        training_jobs[job_id]["metrics"] = result
        
    except Exception as e:
        training_jobs[job_id]["status"] = "failed"
        training_jobs[job_id]["error"] = str(e)


@router.post("/train", response_model=TrainingStartResponse)
async def start_training(
    request: TrainingStartRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """Start a training job."""
    # Check dataset exists
    if request.dataset_name not in datasets_store:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Create job
    job_id = str(uuid.uuid4())
    training_jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "current_step": 0,
        "total_steps": 0,
        "loss": None,
        "metrics": {},
        "error": None,
        "config": request.config.model_dump()
    }
    
    # Start background training
    background_tasks.add_task(
        run_training,
        job_id,
        request.dataset_name,
        request.config,
        request.eval_split
    )
    
    return TrainingStartResponse(
        job_id=job_id,
        status="pending",
        message="Training job started"
    )


@router.get("/train/{job_id}", response_model=TrainingStatusResponse)
async def get_training_status(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get training job status."""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = training_jobs[job_id]
    
    return TrainingStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        current_step=job["current_step"],
        total_steps=job["total_steps"],
        loss=job["loss"],
        metrics=job["metrics"],
        error=job["error"]
    )


@router.delete("/train/{job_id}")
async def cancel_training(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Cancel a training job."""
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Note: Actual cancellation would require more complex handling
    training_jobs[job_id]["status"] = "cancelled"
    
    return {"success": True, "message": "Training job cancelled"}


@router.get("/models", response_model=TrainedModelsResponse)
async def list_trained_models(
    current_user: UserResponse = Depends(get_current_user)
):
    """List trained models."""
    settings = get_settings()
    models_dir = Path(settings.finetune_output_dir) / "models"
    
    models = []
    if models_dir.exists():
        for model_path in models_dir.iterdir():
            if model_path.is_dir():
                # Check for adapter config (LoRA) or full model
                is_lora = (model_path / "adapter_config.json").exists()
                config_file = model_path / "config.json"
                
                config = {}
                if config_file.exists():
                    import json
                    with open(config_file) as f:
                        config = json.load(f)
                
                models.append(TrainedModelInfo(
                    name=model_path.name,
                    path=str(model_path),
                    base_model=config.get("_name_or_path", "unknown"),
                    created_at=str(model_path.stat().st_mtime),
                    is_lora=is_lora,
                    config=config
                ))
    
    return TrainedModelsResponse(models=models)


@router.delete("/models/{model_name}")
async def delete_trained_model(
    model_name: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a trained model."""
    settings = get_settings()
    model_path = Path(settings.finetune_output_dir) / "models" / model_name
    
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model not found")
    
    import shutil
    shutil.rmtree(model_path)
    
    return {"success": True, "message": f"Model {model_name} deleted"}
