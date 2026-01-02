"""
환경 설정 모듈
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # App Settings
    app_name: str = "WeightedAutoTrader"
    app_env: str = "development"
    debug: bool = True

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/wat_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Korea Investment Securities API
    kis_app_key: str = ""
    kis_app_secret: str = ""
    kis_account_no: str = ""  # 계좌번호 (XXXXXXXX-XX 형식)
    kis_is_paper: bool = True  # True: 모의투자, False: 실전투자

    # Broker Settings
    broker_type: str = "mock"  # "mock" or "kis"

    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Trading Settings
    default_trading_style: str = "DAYTRADING"
    auto_trade_enabled: bool = False
    max_positions: int = 5
    daily_loss_limit_pct: float = -2.0
    position_size_pct: float = 20.0
    total_capital: float = 10_000_000

    # Auto Trading Settings
    auto_buy_enabled: bool = True
    auto_sell_enabled: bool = True
    max_daily_trades: int = 20
    daily_profit_target_pct: float = 5.0
    min_signal_score: float = 70.0
    screening_interval: int = 60  # 스크리닝 간격 (초)
    position_check_interval: int = 10  # 포지션 체크 간격 (초)

    # Telegram Notifications
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐시됨)"""
    return Settings()
