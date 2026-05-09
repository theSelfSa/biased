from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "biased-api"
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql://postgres:postgres@localhost:5433/biased"
    demo_workspace_slug: str = "swasthya-care-pharmacy"
    demo_workspace_name: str = "Swasthya Care Pharmacy"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
