"""Configuration settings for the application."""

from pydantic import Field, field_validator
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
    qdrant_api_key: str | None = Field(
        default=None,
        validation_alias="QDRANT_API_KEY",
    )
    qdrant_prefer_grpc: bool = Field(
        default=False,
        validation_alias="QDRANT_PREFER_GRPC",
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
    minio_endpoint: str = Field(
        default="minio:9000",
        validation_alias="MINIO_ENDPOINT",
    )
    minio_access_key: str = Field(
        default="minioadmin",
        validation_alias="MINIO_ACCESS_KEY",
    )
    minio_secret_key: str = Field(
        default="minioadmin",
        validation_alias="MINIO_SECRET_KEY",
    )
    minio_secure: bool = Field(
        default=False,
        validation_alias="MINIO_SECURE",
    )
    minio_bucket_name: str = Field(
        default="workspace-documents",
        validation_alias="MINIO_BUCKET_NAME",
    )
    minio_region: str | None = Field(
        default=None,
        validation_alias="MINIO_REGION",
    )
    pipeline_neo4j_uri: str = Field(
        default="bolt://neo4j:7687",
        validation_alias="PIPELINE_NEO4J_URI",
    )
    openrouter_api_key: str = Field(
        default="",
        validation_alias="OPENROUTER_API_KEY",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias="OPENROUTER_BASE_URL",
    )
    openrouter_model_name: str = Field(
        default="nvidia/nemotron-3-super-120b-a12b:free",
        validation_alias="OPENROUTER_MODEL_NAME",
    )
    pipeline_embedding_model_name: str = Field(
        default="BAAI/bge-m3",
        validation_alias="PIPELINE_EMBEDDING_MODEL_NAME",
    )
    pipeline_reranker_model_name: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        validation_alias="PIPELINE_RERANKER_MODEL_NAME",
    )
    pipeline_model_cache_dir: str = Field(
        default="/app/data/hf_cache",
        validation_alias="PIPELINE_MODEL_CACHE_DIR",
    )
    huggingface_token: str | None = Field(
        default=None,
        validation_alias="HUGGINGFACE_TOKEN",
    )
    pipeline_chunk_size: int = Field(
        default=900,
        validation_alias="PIPELINE_CHUNK_SIZE",
    )
    pipeline_chunk_overlap: int = Field(
        default=120,
        validation_alias="PIPELINE_CHUNK_OVERLAP",
    )
    pipeline_request_timeout_seconds: float = Field(
        default=60.0,
        validation_alias="PIPELINE_REQUEST_TIMEOUT_SECONDS",
    )

    @field_validator("openrouter_api_key", mode="before")
    @classmethod
    def normalize_openrouter_api_key(
        cls,
        value: str | None,
    ) -> str:
        """Strip the OpenRouter API key before it reaches consumers."""
        if value is None:
            return ""
        return value.strip()


settings = Settings()
