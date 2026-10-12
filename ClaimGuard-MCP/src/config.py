from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "ClaimGuard-MCP"
    environment: str = "development"
    debug: bool = True

    database_path: str = str(PROJECT_ROOT / "data" / "claimguard.duckdb")

    input_dir: str = str(PROJECT_ROOT / "data" / "input")
    policies_dir: str = str(PROJECT_ROOT / "data" / "policies")
    sample_claims_dir: str = str(PROJECT_ROOT / "data" / "sample_claims")
    reports_dir: str = str(PROJECT_ROOT / "reports")

    model_name: str = "Qwen/Qwen2-VL-7B-Instruct"
    vision_api_url: str = ""

    # Multi-Language OCR Support (e.g. "hin+eng+tam+tel")
    ocr_languages: str = "hin+eng+tam+tel"

    # LLM-Powered Field Extraction Fallback (Tier 2)
    llm_provider: str = "openai"  # "openai" or "gemini"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    llm_fallback_enabled: bool = True
    llm_timeout_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()