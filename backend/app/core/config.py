from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://lexrag:lexrag@localhost:5433/lexrag"
    upload_dir: str = "../data/uploads"
    ocr_tmp_dir: str = "../data/ocr_tmp"
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    secret_key: str = "dev-only-insecure-secret-change-me"
    token_ttl_seconds: int = 60 * 60 * 24 * 7
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    # "local" loads the model in-process via sentence-transformers (needs
    # torch, ~1GB+ RAM once both embedding+reranker models are loaded --
    # fine for local dev, too much for a 512MB free host). "huggingface_api"
    # calls HF's hosted inference API instead, so no local ML dependency is
    # needed at all. See app/retrieval/embedding.py.
    embedding_provider: str = "local"
    hf_api_token: str = ""
    # Cross-encoder reranking has no remote-API fallback here (see
    # app/retrieval/search.py) -- disabling it in production avoids loading
    # a second local model, trading some retrieval precision for fitting in
    # a RAM-constrained host. hybrid_search() falls back to the RRF fused
    # score for both ranking and the confidence gate when this is off.
    enable_reranker: bool = True
    # Comma-separated list of allowed CORS origins, e.g.
    # "https://app.example.com,https://www.example.com". Defaults to the
    # local dev client portal only.
    cors_allowed_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def ocr_tmp_path(self) -> Path:
        p = Path(self.ocr_tmp_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
