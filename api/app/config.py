"""Settings are read from environment variables (see .env.example)."""
import os


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


class Settings:
    # Any OpenAI-compatible API works: OpenAI, Groq, OpenRouter, Ollama, LM Studio...
    @property
    def llm_api_key(self) -> str:
        return _get("LLM_API_KEY")

    @property
    def llm_base_url(self) -> str:
        return _get("LLM_BASE_URL", "https://api.openai.com/v1")

    @property
    def llm_model(self) -> str:
        return _get("LLM_MODEL", "gpt-4o-mini")

    @property
    def db_path(self) -> str:
        return _get("DB_PATH", "data/inboxpilot.db")

    @property
    def kb_dir(self) -> str:
        return _get("KB_DIR", "knowledge_base")


settings = Settings()
