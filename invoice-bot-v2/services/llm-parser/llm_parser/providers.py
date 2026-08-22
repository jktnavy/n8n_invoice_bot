import os
from dataclasses import dataclass
from typing import Protocol


class LLMProvider(Protocol):
    def classify_intent(self, message: str) -> dict:
        ...

    def extract_invoice(self, message: str, context: dict | None = None) -> dict:
        ...

    def extract_patch(self, message: str, active_draft: dict) -> dict:
        ...


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    model: str
    api_key: str


def provider_from_env() -> LLMProvider:
    config = ProviderConfig(
        provider=os.environ.get("LLM_PROVIDER", "openai").strip().lower(),
        model=os.environ.get("LLM_MODEL", "").strip(),
        api_key=os.environ.get("LLM_API_KEY", "").strip(),
    )
    if config.provider == "mock":
        from .mock_provider import MockProvider

        return MockProvider()
    if config.provider == "openai":
        return OpenAIProvider(config)
    if config.provider in {"deepseek", "gemini", "openrouter"}:
        return NotImplementedProvider(config)
    raise ValueError(f"Unsupported LLM_PROVIDER: {config.provider}")


class OpenAIProvider:
    def __init__(self, config: ProviderConfig):
        self.config = config

    def classify_intent(self, message: str) -> dict:
        raise NotImplementedError("OpenAI Responses API wiring belongs in n8n or a later parser service phase")

    def extract_invoice(self, message: str, context: dict | None = None) -> dict:
        raise NotImplementedError("OpenAI Responses API wiring belongs in n8n or a later parser service phase")

    def extract_patch(self, message: str, active_draft: dict) -> dict:
        raise NotImplementedError("OpenAI Responses API wiring belongs in n8n or a later parser service phase")


class NotImplementedProvider:
    def __init__(self, config: ProviderConfig):
        self.config = config

    def classify_intent(self, message: str) -> dict:
        raise NotImplementedError(f"{self.config.provider} provider is reserved behind the same interface")

    def extract_invoice(self, message: str, context: dict | None = None) -> dict:
        raise NotImplementedError(f"{self.config.provider} provider is reserved behind the same interface")

    def extract_patch(self, message: str, active_draft: dict) -> dict:
        raise NotImplementedError(f"{self.config.provider} provider is reserved behind the same interface")
