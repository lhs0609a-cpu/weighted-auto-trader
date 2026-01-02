"""
포트폴리오 API 라우트
"""
from typing import Optional
from fastapi import APIRouter, Depends

from ...core.broker import IBrokerClient, create_broker_from_settings

router = APIRouter(prefix="/portfolio", tags=["포트폴리오"])

_broker: Optional[IBrokerClient] = None


def get_broker() -> IBrokerClient:
    """설정 기반 브로커 클라이언트 생성"""
    global _broker
    if _broker is None:
        _broker = create_broker_from_settings()
    return _broker


@router.get("/summary")
async def get_portfolio_summary(
    broker: IBrokerClient = Depends(get_broker)
):
    """포트폴리오 요약"""
    await broker.connect()
    balance = await broker.get_balance()
    positions = await broker.get_positions()

    return {
        "success": True,
        "data": {
            "balance": {
                "total_asset": balance.total_asset,
                "available_cash": balance.available_cash,
                "total_purchase": balance.total_purchase,
                "total_evaluation": balance.total_evaluation,
                "total_pnl": balance.total_pnl,
                "total_pnl_rate": round(balance.total_pnl_rate, 2)
            },
            "positions": [
                {
                    "stock_code": p.stock_code,
                    "stock_name": p.stock_name,
                    "quantity": p.quantity,
                    "avg_price": p.avg_price,
                    "current_price": p.current_price,
                    "evaluation": p.evaluation,
                    "pnl": p.pnl,
                    "pnl_rate": round(p.pnl_rate, 2)
                }
                for p in positions
            ],
            "position_count": len(positions)
        }
    }


@router.get("/positions")
async def get_positions(
    broker: IBrokerClient = Depends(get_broker)
):
    """보유 종목 조회"""
    await broker.connect()
    positions = await broker.get_positions()

    return {
        "success": True,
        "data": {
            "count": len(positions),
            "items": [
                {
                    "stock_code": p.stock_code,
                    "stock_name": p.stock_name,
                    "quantity": p.quantity,
                    "avg_price": p.avg_price,
                    "current_price": p.current_price,
                    "evaluation": p.evaluation,
                    "pnl": p.pnl,
                    "pnl_rate": round(p.pnl_rate, 2)
                }
                for p in positions
            ]
        }
    }


@router.get("/balance")
async def get_balance(
    broker: IBrokerClient = Depends(get_broker)
):
    """잔고 조회"""
    await broker.connect()
    balance = await broker.get_balance()

    return {
        "success": True,
        "data": {
            "total_asset": balance.total_asset,
            "available_cash": balance.available_cash,
            "total_purchase": balance.total_purchase,
            "total_evaluation": balance.total_evaluation,
            "total_pnl": balance.total_pnl,
            "total_pnl_rate": round(balance.total_pnl_rate, 2)
        }
    }
