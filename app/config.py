"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class ModelProvider(BaseModel):
    """Configuration for a single LLM provider."""

    name: str
    api_key: str
    base_url: str
    model: str


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    app_name: str = "AI Capability Service"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # DeepSeek
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # Qwen (Alibaba DashScope)
    qwen_api_key: str | None = None
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    # OpenAI (optional fallback)
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # Default provider: deepseek | qwen | openai
    default_provider: str = "deepseek"

    # HTTP timeout for LLM API calls (seconds)
    llm_timeout: int = 60
    llm_max_retries: int = 2

    # Capability defaults
    default_summary_max_length: int = 120

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @property
    def use_real_model(self) -> bool:
        """Whether at least one model API key is configured."""
        return any([
            self.deepseek_api_key,
            self.qwen_api_key,
            self.openai_api_key,
        ])

    def get_provider(self, name: str | None = None) -> ModelProvider | None:
        """Return the provider config by name, falling back to the default."""
        target = name or self.default_provider
        providers: dict[str, tuple[str | None, str, str]] = {
            "deepseek": (self.deepseek_api_key, self.deepseek_base_url, self.deepseek_model),
            "qwen": (self.qwen_api_key, self.qwen_base_url, self.qwen_model),
            "openai": (self.openai_api_key, self.openai_base_url, self.openai_model),
        }

        if target in providers:
            api_key, base_url, model = providers[target]
            if api_key:
                return ModelProvider(name=target, api_key=api_key, base_url=base_url, model=model)

        # Fallback: pick the first configured provider
        for pname, (api_key, base_url, model) in providers.items():
            if api_key:
                return ModelProvider(name=pname, api_key=api_key, base_url=base_url, model=model)

        return None

    def list_providers(self) -> list[str]:
        """Return names of all configured providers."""
        result = []
        if self.deepseek_api_key:
            result.append("deepseek")
        if self.qwen_api_key:
            result.append("qwen")
        if self.openai_api_key:
            result.append("openai")
        return result


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()

