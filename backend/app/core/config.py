from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_prefix="FRYING_PAN_")

    app_name: str = "Frying-PAN API"
    storage_root: str = "../storage"
    database_url: str = "postgresql+psycopg://frying_pan:frying_pan@postgres:5432/frying_pan"
    cors_origins: str = "http://localhost:3000"
    session_cookie_name: str = "frying_pan_session"
    session_ttl_hours: int = 24 * 7

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
