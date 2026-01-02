"""
설정 API 라우터
"""
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ...auth.dependencies import get_current_active_user
from ...auth.models import User
from ...config.constants import TradingStyle, DEFAULT_INDICATOR_WEIGHTS

router = APIRouter(prefix="/settings", tags=["Settings"])


class IndicatorWeights(BaseModel):
    """지표 가중치"""
    volume: float = Field(default=25, ge=0, le=50)
    order_book: float = Field(default=20, ge=0, le=50)
    vwap: float = Field(default=18, ge=0, le=50)
    rsi: float = Field(default=12, ge=0, le=50)
    macd: float = Field(default=10, ge=0, le=50)
    ma: float = Field(default=8, ge=0, le=50)
    bollinger: float = Field(default=5, ge=0, le=50)
    obv: float = Field(default=2, ge=0, le=50)


class TradingSettings(BaseModel):
    """매매 설정"""
    trading_style: str = Field(default="DAYTRADING")
    auto_trade_enabled: bool = Field(default=False)
    max_positions: int = Field(default=5, ge=1, le=20)
    max_position_size_pct: float = Field(default=20, ge=5, le=50)
    stop_loss_pct: float = Field(default=1.5, ge=0.5, le=10)
    take_profit1_pct: float = Field(default=2.0, ge=1, le=20)
    take_profit2_pct: float = Field(default=3.0, ge=2, le=30)
    trailing_stop_pct: float = Field(default=1.0, ge=0.5, le=5)


class NotificationSettings(BaseModel):
    """알림 설정"""
    telegram_enabled: bool = Field(default=False)
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None


class AllSettings(BaseModel):
    """전체 설정"""
    trading: TradingSettings = Field(default_factory=TradingSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    indicator_weights: IndicatorWeights = Field(default_factory=IndicatorWeights)


# 사용자별 설정 저장소 (실제 환경에서는 DB 사용)
_user_settings: Dict[int, AllSettings] = {}


def get_user_settings(user_id: int) -> AllSettings:
    """사용자 설정 조회"""
    if user_id not in _user_settings:
        _user_settings[user_id] = AllSettings()
    return _user_settings[user_id]


def save_user_settings(user_id: int, settings: AllSettings) -> AllSettings:
    """사용자 설정 저장"""
    _user_settings[user_id] = settings
    return settings


@router.get("/", response_model=AllSettings)
async def get_settings(current_user: User = Depends(get_current_active_user)):
    """
    전체 설정 조회
    """
    return get_user_settings(current_user.id)


@router.put("/", response_model=AllSettings)
async def update_all_settings(
    settings: AllSettings,
    current_user: User = Depends(get_current_active_user)
):
    """
    전체 설정 업데이트
    """
    # 지표 가중치 합계 검증
    weights = settings.indicator_weights
    total_weight = (
        weights.volume + weights.order_book + weights.vwap +
        weights.rsi + weights.macd + weights.ma +
        weights.bollinger + weights.obv
    )
    if abs(total_weight - 100) > 0.1:
        raise HTTPException(
            status_code=400,
            detail=f"지표 가중치 합계가 100이어야 합니다 (현재: {total_weight})"
        )

    return save_user_settings(current_user.id, settings)


@router.get("/trading", response_model=TradingSettings)
async def get_trading_settings(current_user: User = Depends(get_current_active_user)):
    """
    매매 설정 조회
    """
    settings = get_user_settings(current_user.id)
    return settings.trading


@router.put("/trading", response_model=TradingSettings)
async def update_trading_settings(
    trading: TradingSettings,
    current_user: User = Depends(get_current_active_user)
):
    """
    매매 설정 업데이트
    """
    settings = get_user_settings(current_user.id)
    settings.trading = trading
    save_user_settings(current_user.id, settings)
    return trading


@router.get("/notifications", response_model=NotificationSettings)
async def get_notification_settings(
    current_user: User = Depends(get_current_active_user)
):
    """
    알림 설정 조회
    """
    settings = get_user_settings(current_user.id)
    return settings.notifications


@router.put("/notifications", response_model=NotificationSettings)
async def update_notification_settings(
    notifications: NotificationSettings,
    current_user: User = Depends(get_current_active_user)
):
    """
    알림 설정 업데이트
    """
    settings = get_user_settings(current_user.id)
    settings.notifications = notifications
    save_user_settings(current_user.id, settings)
    return notifications


@router.post("/notifications/test")
async def test_telegram_notification(
    current_user: User = Depends(get_current_active_user)
):
    """
    텔레그램 알림 테스트
    """
    settings = get_user_settings(current_user.id)
    notifications = settings.notifications

    if not notifications.telegram_enabled:
        raise HTTPException(status_code=400, detail="텔레그램 알림이 비활성화되어 있습니다")

    if not notifications.telegram_bot_token or not notifications.telegram_chat_id:
        raise HTTPException(status_code=400, detail="텔레그램 설정이 완료되지 않았습니다")

    # 테스트 메시지 전송
    from ...services.notification_service import TelegramNotificationService

    telegram = TelegramNotificationService(
        bot_token=notifications.telegram_bot_token,
        chat_id=notifications.telegram_chat_id
    )

    try:
        await telegram.start()
        telegram.queue_message(
            "<b>테스트 알림</b>\n\n"
            "WeightedAutoTrader에서 보내는 테스트 메시지입니다.\n"
            "알림이 정상적으로 설정되었습니다!"
        )
        await telegram.stop()
        return {"success": True, "message": "테스트 메시지가 전송되었습니다"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전송 실패: {str(e)}")


@router.get("/weights", response_model=IndicatorWeights)
async def get_indicator_weights(current_user: User = Depends(get_current_active_user)):
    """
    지표 가중치 조회
    """
    settings = get_user_settings(current_user.id)
    return settings.indicator_weights


@router.put("/weights", response_model=IndicatorWeights)
async def update_indicator_weights(
    weights: IndicatorWeights,
    current_user: User = Depends(get_current_active_user)
):
    """
    지표 가중치 업데이트
    """
    # 합계 검증
    total_weight = (
        weights.volume + weights.order_book + weights.vwap +
        weights.rsi + weights.macd + weights.ma +
        weights.bollinger + weights.obv
    )
    if abs(total_weight - 100) > 0.1:
        raise HTTPException(
            status_code=400,
            detail=f"지표 가중치 합계가 100이어야 합니다 (현재: {total_weight})"
        )

    settings = get_user_settings(current_user.id)
    settings.indicator_weights = weights
    save_user_settings(current_user.id, settings)
    return weights


@router.get("/defaults")
async def get_default_settings():
    """
    기본 설정값 조회 (인증 불필요)
    """
    return {
        "trading": {
            "trading_style": "DAYTRADING",
            "auto_trade_enabled": False,
            "max_positions": 5,
            "max_position_size_pct": 20,
            "stop_loss_pct": 1.5,
            "take_profit1_pct": 2.0,
            "take_profit2_pct": 3.0,
            "trailing_stop_pct": 1.0
        },
        "indicator_weights": {
            "volume": 25,
            "order_book": 20,
            "vwap": 18,
            "rsi": 12,
            "macd": 10,
            "ma": 8,
            "bollinger": 5,
            "obv": 2
        }
    }
