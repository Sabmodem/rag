import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    # Qdrant Config
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    collection_name: str = os.getenv("COLLECTION_NAME", "construction_rules")

    # MinIO / S3 Config
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadminpassword")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "rag-images")
    minio_public_url: str = os.getenv("MINIO_PUBLIC_URL", "http://phoenix.lan/images")

    # ML Models Config
    embed_model_name: str = os.getenv("EMBED_MODEL_NAME", "intfloat/multilingual-e5-small")
    reranker_model_name: str = os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-v2-m3")
    
    # Path & File Config
    docs_dir: Path = Path(os.getenv("DOCS_DIR", "./docs"))
    lua_filter_path: Path = Path(os.getenv("LUA_FILTER_PATH", "clean.lua"))


settings = Settings()