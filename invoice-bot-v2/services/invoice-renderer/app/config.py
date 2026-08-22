from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    invoice_output_dir: Path = Path("/data/invoices")
    assets_dir: Path = Path(__file__).resolve().parent.parent / "assets"

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")


settings = Settings()

