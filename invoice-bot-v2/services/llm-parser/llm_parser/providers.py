import os
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse


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
    base_url: str = ""


def provider_from_env() -> LLMProvider:
    config = ProviderConfig(
        provider=os.environ.get("LLM_PROVIDER", "openai").strip().lower(),
        model=os.environ.get("LLM_MODEL", "").strip(),
        api_key=os.environ.get("LLM_API_KEY", "").strip(),
        base_url=os.environ.get("LLM_BASE_URL", "").strip(),
    )
    if config.provider == "mock":
        from .mock_provider import MockProvider

        return MockProvider()
    if config.provider == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(config)
    if config.provider in {"deepseek", "openrouter"}:
        if not config.base_url:
            raise ValueError(f"LLM_BASE_URL is required for {config.provider} provider")
        validate_responses_base_url(config.base_url, config.provider)
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(config)
    if config.provider == "gemini":
        return NotImplementedProvider(config)
    raise ValueError(f"Unsupported LLM_PROVIDER: {config.provider}")


def validate_responses_base_url(base_url: str, provider: str) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"LLM_BASE_URL for {provider} must be an HTTPS URL")
    if parsed.username or parsed.password:
        raise ValueError(f"LLM_BASE_URL for {provider} must not include credentials")
    if parsed.query or parsed.fragment:
        raise ValueError(f"LLM_BASE_URL for {provider} must not include query or fragment")
    if not parsed.path.rstrip("/").endswith("/responses"):
        raise ValueError(f"LLM_BASE_URL for {provider} must point to a /responses endpoint")


class NotImplementedProvider:
    def __init__(self, config: ProviderConfig):
        self.config = config

    def classify_intent(self, message: str) -> dict:
        raise NotImplementedError(f"{self.config.provider} provider is reserved behind the same interface")

    def extract_invoice(self, message: str, context: dict | None = None) -> dict:
        raise NotImplementedError(f"{self.config.provider} provider is reserved behind the same interface")

    def extract_patch(self, message: str, active_draft: dict) -> dict:
        raise NotImplementedError(f"{self.config.provider} provider is reserved behind the same interface")
