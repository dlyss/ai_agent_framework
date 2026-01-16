"""模型配置管理API"""
import os
import yaml
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/models", tags=["models"])

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../config/models.yml")


class ModelConfig(BaseModel):
    id: str
    name: str
    provider: str
    api_key: str = ""
    base_url: str = ""
    enabled: bool = True


class ModelConfigResponse(BaseModel):
    id: str
    name: str
    provider: str
    api_key_masked: str
    base_url: str
    enabled: bool


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    enabled: Optional[bool] = None


def mask_api_key(api_key: str) -> str:
    """掩码API Key，只显示前4位和后4位"""
    if not api_key or len(api_key) < 12:
        return "****" if api_key else ""
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


def load_models() -> List[dict]:
    """从YML文件加载模型配置"""
    if not os.path.exists(CONFIG_PATH):
        return []
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("models", [])


def save_models(models: List[dict]):
    """保存模型配置到YML文件"""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    data = {"models": models}
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


@router.get("", response_model=List[ModelConfigResponse])
async def get_models():
    """获取所有模型配置（敏感信息掩码）"""
    models = load_models()
    return [
        ModelConfigResponse(
            id=m.get("id", ""),
            name=m.get("name", ""),
            provider=m.get("provider", ""),
            api_key_masked=mask_api_key(m.get("api_key", "")),
            base_url=m.get("base_url", ""),
            enabled=m.get("enabled", True),
        )
        for m in models
    ]


@router.get("/{model_id}", response_model=ModelConfigResponse)
async def get_model(model_id: str):
    """获取单个模型配置"""
    models = load_models()
    for m in models:
        if m.get("id") == model_id:
            return ModelConfigResponse(
                id=m.get("id", ""),
                name=m.get("name", ""),
                provider=m.get("provider", ""),
                api_key_masked=mask_api_key(m.get("api_key", "")),
                base_url=m.get("base_url", ""),
                enabled=m.get("enabled", True),
            )
    raise HTTPException(status_code=404, detail="Model not found")


@router.post("", response_model=ModelConfigResponse)
async def create_model(config: ModelConfig):
    """创建新模型配置"""
    models = load_models()
    for m in models:
        if m.get("id") == config.id:
            raise HTTPException(status_code=400, detail="Model ID already exists")
    
    new_model = {
        "id": config.id,
        "name": config.name,
        "provider": config.provider,
        "api_key": config.api_key,
        "base_url": config.base_url,
        "enabled": config.enabled,
    }
    models.append(new_model)
    save_models(models)
    
    return ModelConfigResponse(
        id=new_model["id"],
        name=new_model["name"],
        provider=new_model["provider"],
        api_key_masked=mask_api_key(new_model["api_key"]),
        base_url=new_model["base_url"],
        enabled=new_model["enabled"],
    )


@router.put("/{model_id}", response_model=ModelConfigResponse)
async def update_model(model_id: str, config: ModelConfigUpdate):
    """更新模型配置"""
    models = load_models()
    for i, m in enumerate(models):
        if m.get("id") == model_id:
            if config.name is not None:
                models[i]["name"] = config.name
            if config.provider is not None:
                models[i]["provider"] = config.provider
            if config.api_key is not None:
                models[i]["api_key"] = config.api_key
            if config.base_url is not None:
                models[i]["base_url"] = config.base_url
            if config.enabled is not None:
                models[i]["enabled"] = config.enabled
            
            save_models(models)
            
            return ModelConfigResponse(
                id=models[i]["id"],
                name=models[i]["name"],
                provider=models[i]["provider"],
                api_key_masked=mask_api_key(models[i].get("api_key", "")),
                base_url=models[i]["base_url"],
                enabled=models[i]["enabled"],
            )
    
    raise HTTPException(status_code=404, detail="Model not found")


@router.delete("/{model_id}")
async def delete_model(model_id: str):
    """删除模型配置"""
    models = load_models()
    for i, m in enumerate(models):
        if m.get("id") == model_id:
            models.pop(i)
            save_models(models)
            return {"message": "Model deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Model not found")
