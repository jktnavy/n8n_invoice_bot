import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from .providers import ProviderConfig

ROOT_DIR = Path(__file__).resolve().parents[3]


class OpenAIProvider:
    def __init__(
        self,
        config: ProviderConfig,
        transport: Callable[[dict, str], dict] | None = None,
        base_url: str = "https://api.openai.com/v1/responses",
    ):
        self.config = config
        self.base_url = config.base_url or base_url
        self.transport = transport or self._default_transport

    def classify_intent(self, message: str) -> dict:
        return self._structured_request(
            schema_path=ROOT_DIR / "llm" / "schemas" / "intent.schema.json",
            schema_name="intent_classification",
            system_prompt_path=ROOT_DIR / "llm" / "system-prompts" / "intent-classifier.md",
            user_payload={"message": message},
        )

    def extract_invoice(self, message: str, context: dict | None = None) -> dict:
        return self._structured_request(
            schema_path=ROOT_DIR / "llm" / "schemas" / "invoice-draft.schema.json",
            schema_name="invoice_draft_extraction",
            system_prompt_path=ROOT_DIR / "llm" / "system-prompts" / "invoice-parser.md",
            user_payload={"message": message, "context": context or {}},
        )

    def extract_patch(self, message: str, active_draft: dict) -> dict:
        return self._structured_request(
            schema_path=ROOT_DIR / "llm" / "schemas" / "invoice-patch.schema.json",
            schema_name="invoice_patch_extraction",
            system_prompt_path=ROOT_DIR / "llm" / "system-prompts" / "invoice-patch-parser.md",
            user_payload={"message": message, "active_draft": active_draft},
        )

    def _structured_request(
        self,
        schema_path: Path,
        schema_name: str,
        system_prompt_path: Path,
        user_payload: dict,
    ) -> dict:
        if not self.config.api_key:
            raise ValueError("LLM_API_KEY is required for OpenAI provider")
        if not self.config.model:
            raise ValueError("LLM_MODEL is required for OpenAI provider")

        schema = json.loads(schema_path.read_text())
        system_prompt = system_prompt_path.read_text()
        request_payload = {
            "model": self.config.model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        response = self.transport(request_payload, self.config.api_key)
        parsed = _parse_structured_response(response)
        _validate_structured_payload(parsed, schema)
        return parsed

    def _default_transport(self, payload: dict, api_key: str) -> dict:
        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API request failed with HTTP {exc.code}: {_redact(body)}") from exc


def _parse_structured_response(response: dict) -> dict:
    if "output_text" in response and response["output_text"]:
        return json.loads(response["output_text"])

    for output in response.get("output", []):
        for content in output.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return json.loads(content["text"])

    raise ValueError("OpenAI response did not contain structured output text")


def _validate_structured_payload(value: object, schema: dict, path: str = "$") -> None:
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path}: expected constant {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: unexpected value {value!r}")

    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(value, expected_type):
        raise ValueError(f"{path}: expected type {expected_type!r}")

    if isinstance(value, (int, float)) and "minimum" in schema and value < schema["minimum"]:
        raise ValueError(f"{path}: value below minimum {schema['minimum']!r}")

    if isinstance(value, (int, float)) and "maximum" in schema and value > schema["maximum"]:
        raise ValueError(f"{path}: value above maximum {schema['maximum']!r}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ValueError(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra_keys = sorted(set(value) - set(properties))
            if extra_keys:
                raise ValueError(f"{path}: unexpected properties {extra_keys!r}")

        for key, child_schema in properties.items():
            if key in value:
                _validate_structured_payload(value[key], child_schema, f"{path}.{key}")

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            _validate_structured_payload(item, schema["items"], f"{path}[{index}]")


def _matches_type(value: object, expected_type: str | list[str]) -> bool:
    expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
    for item in expected_types:
        if item == "null" and value is None:
            return True
        if item == "object" and isinstance(value, dict):
            return True
        if item == "array" and isinstance(value, list):
            return True
        if item == "string" and isinstance(value, str):
            return True
        if item == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if item == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if item == "boolean" and isinstance(value, bool):
            return True
    return False


def _redact(value: str) -> str:
    return value.replace("Bearer ", "Bearer [redacted] ")
