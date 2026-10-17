from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    falkordb_host: str = "localhost"
    falkordb_port: int = 6379
    falkordb_graph: str = "threatweaver"
    otx_api_key: str | None = None
    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-flash"
    otx_base_url: str = "https://otx.alienvault.com"
    otx_timeout_seconds: float = 12.0
    cors_origins: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
