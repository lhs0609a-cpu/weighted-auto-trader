"""
브로커 클라이언트 패키지
"""
from .interfaces import (
    IBrokerClient,
    Quote,
    OHLCV,
    OrderBook,
    OrderResult,
    Balance,
    HoldingStock,
    OrderType,
    OrderSide
)
from .mock_client import MockBrokerClient
from .kis_client import KISClient


def create_broker_client(
    broker_type: str = "mock",
    app_key: str = "",
    app_secret: str = "",
    account_no: str = "",
    is_paper: bool = True,
    **kwargs
) -> IBrokerClient:
    """
    브로커 클라이언트 팩토리 함수

    Args:
        broker_type: 브로커 타입 ("mock", "kis")
        app_key: API 앱 키 (KIS용)
        app_secret: API 앱 시크릿 (KIS용)
        account_no: 계좌번호 (KIS용)
        is_paper: 모의투자 여부 (KIS용)
        **kwargs: 추가 파라미터

    Returns:
        IBrokerClient 구현체
    """
    if broker_type.lower() == "kis":
        if not all([app_key, app_secret, account_no]):
            raise ValueError("KIS 클라이언트는 app_key, app_secret, account_no가 필요합니다")
        return KISClient(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            is_paper=is_paper
        )
    else:
        # 기본: Mock 클라이언트
        initial_balance = kwargs.get("initial_balance", 50_000_000)
        return MockBrokerClient(initial_balance=initial_balance)


def create_broker_from_settings() -> IBrokerClient:
    """
    설정 파일에서 브로커 클라이언트 생성

    Returns:
        IBrokerClient 구현체
    """
    from src.config.settings import get_settings

    settings = get_settings()

    # KIS API 키가 설정되어 있으면 KIS 클라이언트 사용
    if settings.kis_app_key and settings.kis_app_secret and settings.kis_account_no:
        return KISClient(
            app_key=settings.kis_app_key,
            app_secret=settings.kis_app_secret,
            account_no=settings.kis_account_no,
            is_paper=settings.kis_is_paper
        )
    else:
        # API 키 없으면 Mock 클라이언트
        return MockBrokerClient()


__all__ = [
    # Interfaces & Types
    "IBrokerClient",
    "Quote",
    "OHLCV",
    "OrderBook",
    "OrderResult",
    "Balance",
    "HoldingStock",
    "OrderType",
    "OrderSide",
    # Clients
    "MockBrokerClient",
    "KISClient",
    # Factory
    "create_broker_client",
    "create_broker_from_settings",
]
