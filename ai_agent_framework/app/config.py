"""Application configuration management."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "AI Agent Framework"
    app_env: str = "development"
    debug: bool = True
    
    # MySQL Database
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "ai_agent"
    
    @property
    def database_url(self) -> str:
        """Get async MySQL connection URL."""
        return f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    @property
    def sync_database_url(self) -> str:
        """Get sync MySQL connection URL."""
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    # JWT
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_api_base: str = "https://api.openai.com/v1"
    
    # Qwen (DashScope)
    dashscope_api_key: Optional[str] = None
    
    # LLaMA
    llama_model_path: Optional[str] = None
    llama_api_base: str = "http://localhost:8080"
    
    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_user: str = ""
    milvus_password: str = ""
    milvus_db_name: str = "ai_agent"
    
    # Embedding
    embedding_model: str = "BAAI/bge-base-zh-v1.5"
    embedding_device: str = "cpu"
    
    # Default LLM
    default_llm_provider: str = "openai"
    default_model_name: str = "gpt-3.5-turbo"
    default_temperature: float = 0.7
    default_max_tokens: int = 2048
    
    # Memory
    short_term_memory_size: int = 10
    long_term_memory_collection: str = "long_term_memory"
    
    # Fine-tuning
    finetune_output_dir: str = "./finetune_output"
    finetune_logging_dir: str = "./finetune_logs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
