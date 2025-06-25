import os
from typing import Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    """Configuration for LLM orchestrator."""
    
    # Azure AI settings
    azure_ai_key: str = Field(..., alias="AZURE_AI_KEY")
    azure_ai_endpoint: str = Field("https://ai-bryanjavierjaramilloc0912ai799661901077.services.ai.azure.com/models", alias="AZURE_AI_ENDPOINT")
    azure_ai_model: str = Field("DeepSeek-R1", alias="AZURE_AI_MODEL")
    
    # Redis settings
    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_db: int = Field(0, alias="REDIS_DB")
    
    # Agent settings
    max_iterations: int = Field(10, alias="AGENT_MAX_ITERATIONS")
    memory_window_size: int = Field(10, alias="AGENT_MEMORY_WINDOW")
    enable_reflection: bool = Field(True, alias="AGENT_ENABLE_REFLECTION")
    
    # Performance settings
    cache_ttl_hours: int = Field(24, alias="CACHE_TTL_HOURS")
    max_retries: int = Field(3, alias="MAX_RETRIES")
    timeout_seconds: int = Field(30, alias="TIMEOUT_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global config instance
config = LLMConfig() 