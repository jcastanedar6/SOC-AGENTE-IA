from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Agente SOC"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = "sqlite:///./agente_soc.db"

    opencode_api_url: str = "http://localhost:11434"
    opencode_model: str = "opencode"
    opencode_timeout: int = 120

    telegram_bot_token: str = ""
    telegram_chat_ids: str = ""

    @property
    def telegram_chat_id_list(self) -> list[str]:
        return [cid.strip() for cid in self.telegram_chat_ids.split(",") if cid.strip()]

    chroma_persist_dir: str = "./chroma_db"
    embedder_model: str = "all-MiniLM-L6-v2"
    rag_top_k: int = 5

    correlation_window_seconds: int = 60
    anomaly_threshold: float = 0.7
    brute_force_threshold: int = 5
    agent_cycle_interval_seconds: int = 60

    auth_secret_key: str = "soc-agent-secret-cambiame-en-produccion"
    auth_jwt_expire_minutes: int = 480
    auth_username: str = "socIA"
    auth_secret_question: str = "¿Qué rolén?"
    auth_secret_answer: str = "las chelas"
    auth_allowed_phones: str = ""

    @property
    def auth_allowed_phone_list(self) -> list[str]:
        return [p.strip() for p in self.auth_allowed_phones.split(",") if p.strip()]


settings = Settings()
