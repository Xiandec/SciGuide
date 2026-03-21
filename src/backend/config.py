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
    db_password: str = Field(
        default="postgres",
        validation_alias="DB_PASSWORD",
    )
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

    # Workspace lifecycle integrations
    workspace_lifecycle_mode: str = Field(
        default="noop",
        validation_alias="WORKSPACE_LIFECYCLE_MODE",
    )
    workspace_lifecycle_timeout_seconds: float = Field(
        default=10.0,
        validation_alias="WORKSPACE_LIFECYCLE_TIMEOUT_SECONDS",
    )
    qdrant_url: str = Field(
        default="http://qdrant:6333",
        validation_alias="QDRANT_URL",
    )
    qdrant_collection_prefix: str = Field(
        default="workspace_",
        validation_alias="QDRANT_COLLECTION_PREFIX",
    )
    qdrant_vector_size: int = Field(
        default=1536,
        validation_alias="QDRANT_VECTOR_SIZE",
    )
    qdrant_distance: str = Field(
        default="Cosine",
        validation_alias="QDRANT_DISTANCE",
    )
    neo4j_url: str = Field(
        default="http://neo4j:7474",
        validation_alias="NEO4J_URL",
    )
    neo4j_username: str = Field(
        default="neo4j",
        validation_alias="NEO4J_USERNAME",
    )
    neo4j_password: str = Field(
        default="neo4j",
        validation_alias="NEO4J_PASSWORD",
    )
    neo4j_database: str = Field(
        default="neo4j",
        validation_alias="NEO4J_DATABASE",
    )
    neo4j_workspace_root_label: str = Field(
        default="WorkspaceGraphRoot",
        validation_alias="NEO4J_WORKSPACE_ROOT_LABEL",
    )


settings = Settings()
