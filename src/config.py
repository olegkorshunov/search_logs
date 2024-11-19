from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str = Field(..., env="DB_HOST")
    db_port: str = Field(..., env="DB_PORT")
    db_user: str = Field(..., env="DB_USER")
    db_pass: str = Field(..., env="DB_PASS")
    db_name: str = Field(..., env="DB_NAME")

    maillog_path: str = Field(..., env="MAILLOG_PATH")

    @property
    def postgres_dsn_async(self) -> PostgresDsn:
        return f"postgresql+asyncpg://{self.db_name}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def postgres_dsn_sync(self) -> PostgresDsn:
        return f"postgresql://{self.db_name}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}?async_fallback=True"

    model_config = SettingsConfigDict(env_file=".env.example-app", env_file_encoding="utf-8")


settings = Settings()
