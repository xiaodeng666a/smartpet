import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import dotenv
from langchain_openai import ChatOpenAI

from src.middlware.retry_middleware import ModelRetryMiddleware


dotenv.load_dotenv(Path(__file__).resolve().parents[1] / ".env")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelConfig:
    id: str
    name: str
    provider: str
    api_key_env: str
    base_url: str
    description: Optional[str] = None


MODELS: dict[str, ModelConfig] = {
    "qwen-flash-character": ModelConfig(
        id="qwen-flash-character",
        name="Qwen Flash Character",
        provider="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="Fast role-style model for the desktop pet assistant",
    ),
    "qwen-plus-character": ModelConfig(
        id="qwen-plus-character",
        name="Qwen Plus Character",
        provider="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="Stronger role-style model for the desktop pet assistant",
    ),
}


DEFAULT_MODEL_KEY = os.getenv("DEFAULT_MODEL", "qwen-flash-character")
DEFAULT_MODEL = MODELS.get(DEFAULT_MODEL_KEY, MODELS["qwen-flash-character"])
GUARDRAILS_MODEL = DEFAULT_MODEL


def _normalize_api_keys() -> None:
    for key in ["DASHSCOPE_API_KEY", "OPENAI_API_KEY"]:
        value = os.getenv(key)
        if value:
            os.environ[key] = value.strip()
            logger.info("%s configured", key)


_normalize_api_keys()


def get_api_key(env_name: str | None = None) -> str | None:
    if env_name:
        value = os.getenv(env_name)
        return value.strip() if value else None

    return os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")


def is_key_loaded() -> bool:
    return bool(get_api_key())


def build_chat_model(
    model_config: ModelConfig | None = None,
    *,
    temperature: float = 0.7,
) -> ChatOpenAI:
    config = model_config or DEFAULT_MODEL
    return ChatOpenAI(
        model=config.id,
        base_url=config.base_url,
        api_key=get_api_key(config.api_key_env),
        temperature=temperature,
    )


MAX_RETRIES = int(os.getenv("MODEL_MAX_RETRIES", "2"))

configurable_model = build_chat_model(DEFAULT_MODEL)
logger.info("Default model: %s (%s)", DEFAULT_MODEL.name, DEFAULT_MODEL.id)

model_retry_middleware = ModelRetryMiddleware(max_retries=MAX_RETRIES)


__all__ = [
    "MODELS",
    "DEFAULT_MODEL",
    "GUARDRAILS_MODEL",
    "ModelConfig",
    "configurable_model",
    "model_retry_middleware",
    "build_chat_model",
    "get_api_key",
    "is_key_loaded",
    "MAX_RETRIES",
    "logger",
]
