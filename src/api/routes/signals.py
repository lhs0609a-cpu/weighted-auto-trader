"""
신호 API 라우트
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...config.constants import TradingStyle
from ...core.broker import IBrokerClient, create_broker_from_settings
from ...services import AnalysisService, ScreeningService

router = APIRouter(prefix="/signals", tags=["신호"])

_broker: Optional[IBrokerClient] = None


def get_broker() -> IBrokerClient:
    """설정 기반 브로커 클라이언트 생성"""
    global _broker
    if _broker is None:
        _broker = create_broker_from_settings()
    return _broker


class AnalyzeRequest(BaseModel):
    """분석 요청 스키마"""
    stock_code: str
    trading_style: str = "DAYTRADING"


class ScreeningRequest(BaseModel):
    """스크리닝 요청 스키마"""
    trading_style: str = "DAYTRADING"
    filters: Optional[dict] = None
    sort_by: str = "total_score"
    sort_order: str = "desc"
    limit: int = 20


@router.post("/analyze")
async def analyze_stock(
    request: AnalyzeRequest,
    broker: IBrokerClient = Depends(get_broker)
):
    """종목 분석 요청"""
    await broker.connect()

    try:
        trading_style = TradingStyle(request.trading_style)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 매매 스타일: {request.trading_style}"
        )

    try:
        analysis_service = AnalysisService(broker)
        result = await analysis_service.analyze_stock(
            request.stock_code,
            trading_style
        )

        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screening")
async def screen_stocks(
    request: ScreeningRequest,
    broker: IBrokerClient = Depends(get_broker)
):
    """종목 스크리닝"""
    await broker.connect()

    try:
        trading_style = TradingStyle(request.trading_style)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 매매 스타일: {request.trading_style}"
        )

    try:
        screening_service = ScreeningService(broker)
        result = await screening_service.screen_stocks(
            trading_style=trading_style,
            filters=request.filters,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            limit=request.limit
        )

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top/{trading_style}")
async def get_top_signals(
    trading_style: str,
    limit: int = 10,
    broker: IBrokerClient = Depends(get_broker)
):
    """상위 신호 종목 조회"""
    await broker.connect()

    try:
        style = TradingStyle(trading_style)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 매매 스타일: {trading_style}"
        )

    try:
        screening_service = ScreeningService(broker)
        result = await screening_service.get_top_signals(
            trading_style=style,
            limit=limit
        )

        return {
            "success": True,
            "data": {
                "trading_style": trading_style,
                "count": len(result),
                "items": result
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
