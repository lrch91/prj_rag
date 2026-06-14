"""应用配置，从 .env 和环境变量读取"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore")

    # 应用
    app_name: str = "EnterpriseRAG"
    debug: bool = True
    secret_key: str = "change-me"

    # 日志
    log_dir: str = "./data/logs"
    log_level: str = "INFO"
    log_retention: str = "7 days"
    log_rotation: str = "10 MB"

    # SQLite
    database_url: str = "sqlite+aiosqlite:///./data/rag.db"

    # Milvus
    milvus_mode: str = "cloud"  # "local" 或 "cloud"
    milvus_db_path: str = "./data/milvus_lite.db"  # 本地模式
    zilliz_uri: str = ""  # 云端模式：Zilliz Cloud 端点
    zilliz_token: str = ""  # 云端模式：Zilliz Cloud API Token

    # 文件存储
    upload_dir: str = "./data/files"

    # 智谱
    zhipuai_api_key: str = ""

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = ""

    # DeepSeek（OpenAI 兼容）
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    # Anthropic
    anthropic_api_key: str = ""

    # Qwen
    qwen_api_key: str = ""

    # JWT
    jwt_secret_key: str = "jwt-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Embedding
    embedding_model: str = "zhipu-embedding-3"
    embedding_dimensions: int = 1024

    # Reranker
    reranker_model: str = "zhipu-bge-reranker-large"
    reranker_enabled: bool = True

    # LLM
    default_llm_model: str = "deepseek-v4-pro"
    available_models: str = "deepseek-v4-pro"  # 逗号分隔的模型 ID 列表

    # 查询改写
    query_rewrite_enabled: bool = True
    query_rewrite_model: str = "deepseek-v4-pro"

    def get_available_models(self) -> list[dict]:
        models = []
        for name in self.available_models.split(","):
            name = name.strip()
            if name:
                label = {"deepseek-v4-pro": "DeepSeek V4-Pro", "claude-sonnet-4-20250514": "Claude Sonnet 4",
                         "qwen-max": "Qwen Max", "moonshot-v1-8k": "Kimi", "gpt-4o": "GPT-4o"}.get(name, name)
                models.append({"id": name, "name": label})
        return models


settings = Settings()

# 确保数据目录存在
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
