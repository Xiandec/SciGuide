"""Configuration settings for the application."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings configuration class for application environment variables.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    host: str = Field(default="0.0.0.0", validation_alias="APP_HOST")
    port: int = Field(default=8000, validation_alias="APP_PORT")
    access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        validation_alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )
    algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    secret_key: str = Field(
        default="your-super-secret-key",
        validation_alias="JWT_SECRET_KEY",
    )

    # Database
    db_name: str = Field(default="sciguide", validation_alias="DB_NAME")
    db_user: str = Field(default="postgres", validation_alias="DB_USER")
    db_password: str = Field(default="postgres", validation_alias="DB_PASSWORD")
    db_host: str = Field(default="db", validation_alias="DB_HOST")
    db_port: int = Field(default=5432, validation_alias="DB_PORT")

    # Redis
    redis_host: str = Field(default="redis", validation_alias="REDIS_HOST")
    redis_port: int = Field(default=6379, validation_alias="REDIS_PORT")
    redis_db: int = Field(default=0, validation_alias="REDIS_DB")
    redis_password: str | None = Field(
        default=None,
        validation_alias="REDIS_PASSWORD",
    )


settings = Settings()
