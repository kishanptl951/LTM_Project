import json
import logging
import os
import re
from typing import Any, Callable

import requests

from src.config import settings

logger = logging.getLogger(__name__)

DEFAULT_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "policy_number": {
            "type": "string",
            "description": "Insurance policy number/code, e.g. POL-12345, Policy #, or Policy ID",
        },
        "incident_date": {
            "type": "string",
            "description": "Date accident/incident occurred, in YYYY-MM-DD or standard date format",
        },
        "vehicle_registration": {
            "type": "string",
            "description": "Vehicle registration / license plate number, e.g. TS09AB1234 or Reg No.",
        },
        "claim_id": {
            "type": "string",
            "description": "Claim reference or claim identification number",
        },
        "claimant_name": {
            "type": "string",
            "description": "Full name of the claimant or insured individual",
        },
        "policy_holder": {
            "type": "string",
            "description": "Name of the policy holder if distinct from claimant",
        },
        "claim_type": {
            "type": "string",
            "description": "Nature or category of claim (e.g. Motor, Collision, Comprehensive)",
        },
        "reported_date": {
            "type": "string",
            "description": "Date when the claim was filed or reported to insurer",
        },
        "policy_start_date": {
            "type": "string",
            "description": "Policy effective or commencement date",
        },
        "policy_end_date": {
            "type": "string",
            "description": "Policy expiration or end date",
        },
        "coverage_type": {
            "type": "string",
            "description": "Type of coverage, e.g. Comprehensive, Third Party",
        },
        "coverage_limit": {
            "type": "number",
            "description": "Policy coverage limit, IDV, or sum insured amount as number",
        },
        "deductible": {
            "type": "number",
            "description": "Policy compulsory deductible or excess amount as number",
        },
        "estimated_repair_cost": {
            "type": "number",
            "description": "Total estimated repair cost as number",
        },
        "parts_cost": {
            "type": "number",
            "description": "Parts cost component as number",
        },
        "labor_cost": {
            "type": "number",
            "description": "Labor charges component as number",
        },
        "police_report_number": {
            "type": "string",
            "description": "FIR number or police station report number",
        },
        "police_station": {
            "type": "string",
            "description": "Name or location of police station where report was lodged",
        },
        "incident_location": {
            "type": "string",
            "description": "Location or place where accident/incident occurred",
        },
        "incident_description": {
            "type": "string",
            "description": "Description of how the accident or incident occurred",
        },
        "workshop_name": {
            "type": "string",
            "description": "Name of the automobile repair workshop or garage",
        },
    },
}


class LLMExtractionService:
    """
    Tier-2 LLM-powered extraction service for insurance claim documents.
    Used as a fallback when critical fields (e.g. policy_number, incident_date,
    vehicle_registration) cannot be resolved via deterministic regex patterns.

    Supports both OpenAI (/chat/completions with json_object) and Google Gemini
    (/models/{model}:generateContent with application/json).
    """

    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
        client: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self.client = client
        self.timeout = timeout or settings.llm_timeout_seconds

        # Resolve provider
        prov = provider or settings.llm_provider or "openai"
        self.provider = prov.lower().strip()

        # Resolve API keys and model defaults
        if self.provider == "gemini":
            self.api_key = (
                api_key
                or settings.gemini_api_key
                or os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
                or ""
            )
            self.model = model or settings.gemini_model or "gemini-1.5-flash"
            self.base_url = base_url or "https://generativelanguage.googleapis.com/v1beta"
        else:
            self.provider = "openai"
            self.api_key = (
                api_key
                or settings.openai_api_key
                or os.getenv("OPENAI_API_KEY")
                or ""
            )
            self.model = model or settings.openai_model or "gpt-4o-mini"
            self.base_url = (
                base_url
                or settings.openai_base_url
                or "https://api.openai.com/v1"
            ).rstrip("/")

        # Auto-detect Gemini if provider was default openai but only Gemini key is present
        if not self.api_key and not self.client and provider is None:
            gem_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or settings.gemini_api_key
            if gem_key:
                self.provider = "gemini"
                self.api_key = gem_key
                self.model = settings.gemini_model or "gemini-1.5-flash"
                self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def is_available(self) -> bool:
        """Check if LLM extraction is configured and available for execution."""
        if not settings.llm_fallback_enabled:
            return False
        if self.client is not None:
            return True
        return bool(self.api_key and self.api_key.strip())

    def extract_fields(
        self,
        text: str,
        missing_fields: list[str] | None = None,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Extract missing structured fields from document text using the configured LLM.

        Args:
            text: Raw extracted text from document.
            missing_fields: Optional list of specific field names to focus extraction on.
            schema: Optional custom JSON schema; defaults to DEFAULT_EXTRACTION_SCHEMA.

        Returns:
            Dict mapping field names to extracted non-empty values.
        """
        if not text or not text.strip():
            return {}

        target_schema = self._build_target_schema(missing_fields, schema)

        # 1. Use injected mock client if provided (for testing / custom pipelines)
        if self.client is not None:
            try:
                res = self.client(text, target_schema)
                return self._clean_extracted_data(res, target_schema)
            except Exception as exc:
                logger.warning("Custom LLM client extraction failed: %s", exc)
                return {}

        if not self.is_available():
            logger.debug(
                "LLM extraction skipped: no API key configured for provider '%s'.",
                self.provider,
            )
            return {}

        # 2. Invoke appropriate provider
        try:
            if self.provider == "gemini":
                return self._call_gemini(text, target_schema)
            return self._call_openai(text, target_schema)
        except Exception as exc:
            logger.warning(
                "Tier-2 LLM extraction via %s (%s) failed: %s",
                self.provider,
                self.model,
                exc,
            )
            return {}

    def _build_target_schema(
        self,
        missing_fields: list[str] | None,
        schema: dict[str, Any] | None,
    ) -> dict[str, Any]:
        base_schema = schema or DEFAULT_EXTRACTION_SCHEMA
        if not missing_fields:
            return base_schema

        all_props = base_schema.get("properties", {})
        filtered_props = {
            f: all_props[f]
            for f in missing_fields
            if f in all_props
        }
        # If any requested field isn't in default schema, still include it generically
        for f in missing_fields:
            if f not in filtered_props:
                filtered_props[f] = {
                    "type": "string",
                    "description": f"Extracted value for {f.replace('_', ' ')}",
                }

        return {
            "type": "object",
            "properties": filtered_props,
        }

    def _call_openai(self, text: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Call OpenAI chat completion endpoint with JSON schema mode."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        system_prompt = (
            "You are an expert insurance document extraction system. "
            "Analyze the given document text and extract the requested fields into strict JSON format. "
            "Only extract values explicitly stated or clearly identified in the text. "
            "If a field cannot be determined, set its value to null. "
            "Do not hallucinate or guess values."
        )

        user_prompt = (
            f"Extract the requested fields from this insurance document text:\n\n"
            f"```text\n{text}\n```\n\n"
            f"Target JSON Schema:\n{json.dumps(schema, indent=2)}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        logger.info(
            "Calling OpenAI (%s) for Tier-2 field extraction...", self.model
        )
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            logger.warning(
                "OpenAI API responded with status %d: %s",
                response.status_code,
                response.text[:300],
            )
            return {}

        resp_data = response.json()
        content = resp_data["choices"][0]["message"]["content"]
        return self._parse_json_payload(content, schema)

    def _call_gemini(self, text: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Call Google Gemini generateContent endpoint with JSON output mode."""
        url = (
            f"{self.base_url}/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        prompt = (
            "You are an expert insurance document extraction system.\n"
            "Analyze the given insurance document text and extract the requested fields.\n"
            "Output strict JSON conforming to the requested schema.\n"
            "If a field is not found in the text, use null.\n"
            "Do not invent or hallucinate data.\n\n"
            f"Target Schema:\n{json.dumps(schema, indent=2)}\n\n"
            f"Document Text:\n{text}"
        )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0,
            },
        }

        logger.info(
            "Calling Google Gemini (%s) for Tier-2 field extraction...", self.model
        )
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            logger.warning(
                "Gemini API responded with status %d: %s",
                response.status_code,
                response.text[:300],
            )
            return {}

        resp_data = response.json()
        candidates = resp_data.get("candidates", [])
        if not candidates:
            return {}

        content = candidates[0]["content"]["parts"][0]["text"]
        return self._parse_json_payload(content, schema)

    def _parse_json_payload(
        self,
        raw_text: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Strip markdown fences and parse the JSON string into cleaned data."""
        if not raw_text:
            return {}

        cleaned = raw_text.strip()
        # Remove markdown ```json ... ``` code fence if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return self._clean_extracted_data(parsed, schema)
            return {}
        except Exception as exc:
            logger.warning("Failed to parse LLM JSON output (%s): %s", cleaned[:150], exc)
            return {}

    def _clean_extracted_data(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Filter out None, empty, or placeholder strings from the extracted dict."""
        results: dict[str, Any] = {}
        allowed_props = schema.get("properties", {})

        for key, val in data.items():
            if key not in allowed_props and key not in DEFAULT_EXTRACTION_SCHEMA.get("properties", {}):
                continue
            if val is None:
                continue
            val_str = str(val).strip()
            if not val_str or val_str.lower() in {"null", "none", "n/a", "not mentioned", "unknown"}:
                continue
            results[key] = val

        return results
