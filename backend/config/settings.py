"""Application settings — все настройки в .env"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # App
    app_name: str = "SCADA.AI v3"
    app_version: str = "3.3.2.2"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Database
    db_host: str = "172.27.10.216"
    db_port: int = 5432
    db_name: str = "scada_ai"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_connect_timeout: int = 30
    db_command_timeout: int = 120
    
    # YandexGPT
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_gpt_model: str = "yandexgpt-lite"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1500
    llm_timeout: int = 60
    
    # SCADA REST API
    scada_base_url: str = "http://localhost:8080"
    scada_timeout: int = 30
    
    # Location
    city: str = "Нижний Тагил"
    timezone: str = "Asia/Yekaterinburg"
    latitude: float = 57.9167
    longitude: float = 59.9417
    
    # Security
    jwt_secret: str = "scada-ai-super-secret-jwt-key-32-bytes-min!"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    
    # Modules
    enabled_modules: str = "hello,health,logs"
    
    # Logs
    log_poll_interval_ms: int = 2000
    log_poll_max_entries: int = 500

    # License
    license_file: str = str(PROJECT_ROOT / "license.lic")
    license_public_key: str = str(PROJECT_ROOT / "backend" / "core" / "license" / "keys" / "public_key.pem")
    license_grace_period_days: int = 3

    @property
    def enabled_modules_list(self) -> list[str]:
        """Возвращает список активных модулей (парсит CSV)"""
        if not self.enabled_modules:
            return []
        return [m.strip() for m in self.enabled_modules.split(",") if m.strip()]

    @property
    def database_url(self) -> str:
        """Полный URL для подключения к PostgreSQL"""
        password = quote_plus(self.db_password)
        return f"postgresql://{self.db_user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()
