"""
자동매매 API 라우트
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...services import get_auto_trader, AutoTraderStatus
from ...config.constants import TradingStyle


router = APIRouter(prefix="/auto-trader", tags=["Auto Trader"])


# === Request/Response Models ===

class AutoTraderConfigUpdate(BaseModel):
    """자동매매 설정 업데이트"""
    enabled: Optional[bool] = None
    trading_style: Optional[str] = None
    auto_buy_enabled: Optional[bool] = None
    auto_sell_enabled: Optional[bool] = None
    max_positions: Optional[int] = None
    max_daily_trades: Optional[int] = None
    max_position_pct: Optional[float] = None
    daily_loss_limit_pct: Optional[float] = None
    daily_profit_target_pct: Optional[float] = None
    min_score: Optional[float] = None
    signal_types: Optional[List[str]] = None
    screening_interval: Optional[int] = None
    position_check_interval: Optional[int] = None


class WatchStockRequest(BaseModel):
    """관심종목 요청"""
    stock_code: str


class AutoTraderStatusResponse(BaseModel):
    """자동매매 상태 응답"""
    success: bool
    data: dict


# === Routes ===

@router.get("/status")
async def get_auto_trader_status():
    """자동매매 상태 조회"""
    trader = get_auto_trader()
    return {
        "success": True,
        "data": trader.get_status_info()
    }


@router.post("/start")
async def start_auto_trading():
    """자동매매 시작"""
    trader = get_auto_trader()

    if trader.is_running:
        return {
            "success": False,
            "message": "자동매매가 이미 실행 중입니다"
        }

    try:
        await trader.start()
        return {
            "success": True,
            "message": "자동매매가 시작되었습니다",
            "data": trader.get_status_info()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자동매매 시작 실패: {str(e)}")


@router.post("/stop")
async def stop_auto_trading():
    """자동매매 중지"""
    trader = get_auto_trader()

    if not trader._running:
        return {
            "success": False,
            "message": "자동매매가 실행 중이 아닙니다"
        }

    try:
        await trader.stop()
        return {
            "success": True,
            "message": "자동매매가 중지되었습니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자동매매 중지 실패: {str(e)}")


@router.post("/pause")
async def pause_auto_trading():
    """자동매매 일시 정지"""
    trader = get_auto_trader()

    if not trader._running:
        return {
            "success": False,
            "message": "자동매매가 실행 중이 아닙니다"
        }

    trader.pause()
    return {
        "success": True,
        "message": "자동매매가 일시 정지되었습니다"
    }


@router.post("/resume")
async def resume_auto_trading():
    """자동매매 재개"""
    trader = get_auto_trader()

    if not trader._running:
        return {
            "success": False,
            "message": "자동매매가 실행 중이 아닙니다"
        }

    trader.resume()
    return {
        "success": True,
        "message": "자동매매가 재개되었습니다"
    }


@router.put("/config")
async def update_auto_trader_config(config: AutoTraderConfigUpdate):
    """자동매매 설정 업데이트"""
    trader = get_auto_trader()

    updates = {}
    if config.enabled is not None:
        updates['enabled'] = config.enabled
    if config.trading_style is not None:
        updates['trading_style'] = TradingStyle(config.trading_style)
    if config.auto_buy_enabled is not None:
        updates['auto_buy_enabled'] = config.auto_buy_enabled
    if config.auto_sell_enabled is not None:
        updates['auto_sell_enabled'] = config.auto_sell_enabled
    if config.max_positions is not None:
        updates['max_positions'] = config.max_positions
    if config.max_daily_trades is not None:
        updates['max_daily_trades'] = config.max_daily_trades
    if config.max_position_pct is not None:
        updates['max_position_pct'] = config.max_position_pct
    if config.daily_loss_limit_pct is not None:
        updates['daily_loss_limit_pct'] = config.daily_loss_limit_pct
    if config.daily_profit_target_pct is not None:
        updates['daily_profit_target_pct'] = config.daily_profit_target_pct
    if config.min_score is not None:
        updates['min_score'] = config.min_score
    if config.signal_types is not None:
        updates['signal_types'] = config.signal_types
    if config.screening_interval is not None:
        updates['screening_interval'] = config.screening_interval
    if config.position_check_interval is not None:
        updates['position_check_interval'] = config.position_check_interval

    if updates:
        trader.update_config(**updates)

    return {
        "success": True,
        "message": "설정이 업데이트되었습니다",
        "data": trader.get_status_info()
    }


@router.get("/config")
async def get_auto_trader_config():
    """자동매매 설정 조회"""
    trader = get_auto_trader()
    config = trader.config

    return {
        "success": True,
        "data": {
            "enabled": config.enabled,
            "trading_style": config.trading_style.value,
            "auto_buy_enabled": config.auto_buy_enabled,
            "auto_sell_enabled": config.auto_sell_enabled,
            "max_positions": config.max_positions,
            "max_daily_trades": config.max_daily_trades,
            "max_position_pct": config.max_position_pct,
            "daily_loss_limit_pct": config.daily_loss_limit_pct,
            "daily_profit_target_pct": config.daily_profit_target_pct,
            "min_score": config.min_score,
            "signal_types": config.signal_types,
            "screening_interval": config.screening_interval,
            "position_check_interval": config.position_check_interval,
            "market_open": str(config.market_open),
            "market_close": str(config.market_close),
        }
    }


@router.get("/watchlist")
async def get_watchlist():
    """관심종목 목록 조회"""
    trader = get_auto_trader()
    return {
        "success": True,
        "data": {
            "stocks": trader.get_watched_stocks(),
            "count": len(trader.get_watched_stocks())
        }
    }


@router.post("/watchlist")
async def add_to_watchlist(request: WatchStockRequest):
    """관심종목 추가"""
    trader = get_auto_trader()
    trader.add_watch_stock(request.stock_code)

    return {
        "success": True,
        "message": f"{request.stock_code} 종목이 추가되었습니다",
        "data": {
            "stocks": trader.get_watched_stocks(),
            "count": len(trader.get_watched_stocks())
        }
    }


@router.delete("/watchlist/{stock_code}")
async def remove_from_watchlist(stock_code: str):
    """관심종목 제거"""
    trader = get_auto_trader()
    trader.remove_watch_stock(stock_code)

    return {
        "success": True,
        "message": f"{stock_code} 종목이 제거되었습니다",
        "data": {
            "stocks": trader.get_watched_stocks(),
            "count": len(trader.get_watched_stocks())
        }
    }


@router.get("/positions")
async def get_positions():
    """현재 포지션 조회"""
    trader = get_auto_trader()
    position_summary = trader.trading_engine.position_manager.get_position_summary()

    return {
        "success": True,
        "data": position_summary
    }


@router.get("/statistics")
async def get_trading_statistics():
    """거래 통계 조회"""
    trader = get_auto_trader()

    return {
        "success": True,
        "data": {
            "today_trades": trader._today_trades,
            "today_pnl": trader._today_pnl,
            "start_balance": trader._start_balance,
            "positions": trader.trading_engine.position_manager.get_position_summary(),
            "screening_stats": trader.screening_service.get_screening_stats()
        }
    }
