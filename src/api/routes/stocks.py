"""
종목 API 라우트
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from ...core.broker import MockBrokerClient
from ...services import AnalysisService

router = APIRouter(prefix="/stocks", tags=["종목"])

# 의존성 주입을 위한 브로커 인스턴스
_broker = None


def get_broker():
    global _broker
    if _broker is None:
        _broker = MockBrokerClient()
    return _broker


@router.get("")
async def get_stocks(
    market: Optional[str] = None,
    broker: MockBrokerClient = Depends(get_broker)
):
    """종목 목록 조회"""
    await broker.connect()
    stocks = await broker.get_stock_list(market)
    return {
        "success": True,
        "data": {
            "total_count": len(stocks),
            "items": stocks
        }
    }


@router.get("/{stock_code}")
async def get_stock_detail(
    stock_code: str,
    broker: MockBrokerClient = Depends(get_broker)
):
    """종목 상세 조회"""
    await broker.connect()
    try:
        quote = await broker.get_quote(stock_code)
        return {
            "success": True,
            "data": {
                "stock_code": quote.stock_code,
                "name": quote.name,
                "price": quote.price,
                "change": quote.change,
                "change_rate": quote.change_rate,
                "volume": quote.volume,
                "trade_amount": quote.trade_amount,
                "open": quote.open,
                "high": quote.high,
                "low": quote.low,
                "prev_close": quote.prev_close,
                "timestamp": quote.timestamp.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{stock_code}/indicators")
async def get_stock_indicators(
    stock_code: str,
    period: str = "D",
    broker: MockBrokerClient = Depends(get_broker)
):
    """종목 지표 조회"""
    await broker.connect()
    try:
        analysis_service = AnalysisService(broker)
        indicators = await analysis_service.get_stock_indicators(stock_code, period)
        quote = await broker.get_quote(stock_code)

        return {
            "success": True,
            "data": {
                "stock_code": stock_code,
                "stock_name": quote.name,
                "current_price": quote.price,
                "indicators": indicators
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{stock_code}/ohlcv")
async def get_stock_ohlcv(
    stock_code: str,
    period: str = "D",
    count: int = 100,
    broker: MockBrokerClient = Depends(get_broker)
):
    """종목 OHLCV 조회"""
    await broker.connect()
    try:
        ohlcv_data = await broker.get_ohlcv(stock_code, period, count)
        return {
            "success": True,
            "data": {
                "stock_code": stock_code,
                "period": period,
                "count": len(ohlcv_data),
                "ohlcv": [
                    {
                        "timestamp": d.timestamp.isoformat(),
                        "open": d.open,
                        "high": d.high,
                        "low": d.low,
                        "close": d.close,
                        "volume": d.volume
                    }
                    for d in ohlcv_data
                ]
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
