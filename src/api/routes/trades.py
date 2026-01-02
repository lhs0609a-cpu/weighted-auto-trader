"""
거래 API 라우터
- 주문 실행 (매수/매도)
- 주문 취소
- 거래 내역 조회
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ...core.broker import IBrokerClient, OrderType, OrderSide, create_broker_from_settings
from ...auth.dependencies import get_current_active_user
from ...auth.models import User

router = APIRouter(prefix="/trades", tags=["Trades"])

# 브로커 인스턴스
_broker: Optional[IBrokerClient] = None


def get_broker() -> IBrokerClient:
    """설정 기반 브로커 클라이언트 생성"""
    global _broker
    if _broker is None:
        _broker = create_broker_from_settings()
    return _broker


# ==================== 주문 관련 스키마 ====================

class OrderRequest(BaseModel):
    """주문 요청"""
    stock_code: str = Field(..., description="종목코드")
    quantity: int = Field(..., ge=1, description="주문 수량")
    price: Optional[float] = Field(None, description="주문 가격 (지정가 주문시)")
    order_type: str = Field("MARKET", description="주문 유형 (MARKET/LIMIT)")


class OrderResponse(BaseModel):
    """주문 응답"""
    order_id: str
    stock_code: str
    order_side: str
    order_type: str
    order_price: float
    order_qty: int
    executed_price: Optional[float]
    executed_qty: int
    status: str
    message: str


class CancelOrderRequest(BaseModel):
    """주문 취소 요청"""
    order_id: str = Field(..., description="주문번호")
    stock_code: Optional[str] = Field(None, description="종목코드 (KIS용)")


# ==================== 주문 실행 API ====================

@router.post("/order/buy", response_model=OrderResponse)
async def place_buy_order(
    request: OrderRequest,
    current_user: User = Depends(get_current_active_user),
    broker: IBrokerClient = Depends(get_broker)
):
    """
    매수 주문 실행

    - order_type: MARKET (시장가), LIMIT (지정가)
    - 지정가 주문시 price 필수
    """
    await broker.connect()

    # 주문 유형 파싱
    try:
        order_type = OrderType[request.order_type.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 주문 유형: {request.order_type}"
        )

    # 지정가 주문시 가격 확인
    if order_type == OrderType.LIMIT and not request.price:
        raise HTTPException(
            status_code=400,
            detail="지정가 주문에는 가격이 필요합니다"
        )

    try:
        result = await broker.place_order(
            stock_code=request.stock_code,
            order_side=OrderSide.BUY,
            order_type=order_type,
            quantity=request.quantity,
            price=request.price
        )

        return OrderResponse(
            order_id=result.order_id,
            stock_code=result.stock_code,
            order_side=result.order_side.value,
            order_type=result.order_type.value,
            order_price=result.order_price,
            order_qty=result.order_qty,
            executed_price=result.executed_price,
            executed_qty=result.executed_qty,
            status=result.status,
            message=result.message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order/sell", response_model=OrderResponse)
async def place_sell_order(
    request: OrderRequest,
    current_user: User = Depends(get_current_active_user),
    broker: IBrokerClient = Depends(get_broker)
):
    """
    매도 주문 실행

    - order_type: MARKET (시장가), LIMIT (지정가)
    - 지정가 주문시 price 필수
    """
    await broker.connect()

    # 주문 유형 파싱
    try:
        order_type = OrderType[request.order_type.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 주문 유형: {request.order_type}"
        )

    # 지정가 주문시 가격 확인
    if order_type == OrderType.LIMIT and not request.price:
        raise HTTPException(
            status_code=400,
            detail="지정가 주문에는 가격이 필요합니다"
        )

    try:
        result = await broker.place_order(
            stock_code=request.stock_code,
            order_side=OrderSide.SELL,
            order_type=order_type,
            quantity=request.quantity,
            price=request.price
        )

        return OrderResponse(
            order_id=result.order_id,
            stock_code=result.stock_code,
            order_side=result.order_side.value,
            order_type=result.order_type.value,
            order_price=result.order_price,
            order_qty=result.order_qty,
            executed_price=result.executed_price,
            executed_qty=result.executed_qty,
            status=result.status,
            message=result.message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order/cancel")
async def cancel_order(
    request: CancelOrderRequest,
    current_user: User = Depends(get_current_active_user),
    broker: IBrokerClient = Depends(get_broker)
):
    """
    주문 취소

    - KIS의 경우 stock_code:order_id 형식으로 전달 필요
    """
    await broker.connect()

    try:
        # KIS는 종목코드:주문번호 형식
        order_id = request.order_id
        if request.stock_code:
            order_id = f"{request.stock_code}:{request.order_id}"

        success = await broker.cancel_order(order_id)

        if success:
            return {
                "success": True,
                "message": "주문이 취소되었습니다",
                "order_id": request.order_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="주문 취소에 실패했습니다 (이미 체결되었거나 존재하지 않는 주문)"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/order/history")
async def get_order_history(
    current_user: User = Depends(get_current_active_user),
    broker: IBrokerClient = Depends(get_broker),
    date: Optional[str] = Query(None, description="조회 일자 (YYYYMMDD)")
):
    """
    주문 체결 내역 조회 (당일)

    - KIS API를 통해 실제 체결 내역 조회
    """
    await broker.connect()

    try:
        # KIS 클라이언트인 경우 주문 내역 조회
        if hasattr(broker, 'get_order_history'):
            history = await broker.get_order_history(date)
            return {
                "success": True,
                "data": {
                    "date": date or datetime.now().strftime("%Y%m%d"),
                    "count": len(history),
                    "items": history
                }
            }
        else:
            # Mock 브로커는 주문 내역 없음
            return {
                "success": True,
                "data": {
                    "date": date or datetime.now().strftime("%Y%m%d"),
                    "count": 0,
                    "items": []
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 거래 내역 스키마 ====================

class Trade(BaseModel):
    """거래 내역"""
    trade_id: str
    stock_code: str
    stock_name: str
    side: str  # BUY, SELL
    quantity: int
    entry_price: float
    exit_price: float
    pnl: float
    pnl_rate: float
    commission: float
    exit_reason: str
    entry_time: str
    exit_time: str


class TradeStatistics(BaseModel):
    """거래 통계"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl: float
    max_profit: float
    max_loss: float
    avg_holding_time: str


# 거래 내역 저장소 (실제 환경에서는 DB 사용)
_user_trades: dict = {}


def get_mock_trades() -> List[Trade]:
    """모의 거래 데이터 생성"""
    return [
        Trade(
            trade_id="T001",
            stock_code="005930",
            stock_name="삼성전자",
            side="SELL",
            quantity=50,
            entry_price=71000,
            exit_price=72500,
            pnl=75000,
            pnl_rate=2.11,
            commission=108,
            exit_reason="TAKE_PROFIT_1",
            entry_time="2024-01-15T09:30:00",
            exit_time="2024-01-15T14:25:00"
        ),
        Trade(
            trade_id="T002",
            stock_code="000660",
            stock_name="SK하이닉스",
            side="SELL",
            quantity=20,
            entry_price=180000,
            exit_price=176000,
            pnl=-80000,
            pnl_rate=-2.22,
            commission=534,
            exit_reason="STOP_LOSS",
            entry_time="2024-01-15T10:15:00",
            exit_time="2024-01-15T11:30:00"
        ),
        Trade(
            trade_id="T003",
            stock_code="035420",
            stock_name="NAVER",
            side="SELL",
            quantity=30,
            entry_price=210000,
            exit_price=218000,
            pnl=240000,
            pnl_rate=3.81,
            commission=642,
            exit_reason="TAKE_PROFIT_2",
            entry_time="2024-01-14T09:45:00",
            exit_time="2024-01-15T10:00:00"
        ),
        Trade(
            trade_id="T004",
            stock_code="035720",
            stock_name="카카오",
            side="SELL",
            quantity=100,
            entry_price=52000,
            exit_price=51500,
            pnl=-50000,
            pnl_rate=-0.96,
            commission=78,
            exit_reason="TRAILING_STOP",
            entry_time="2024-01-14T13:00:00",
            exit_time="2024-01-14T15:15:00"
        ),
        Trade(
            trade_id="T005",
            stock_code="051910",
            stock_name="LG화학",
            side="SELL",
            quantity=10,
            entry_price=385000,
            exit_price=395000,
            pnl=100000,
            pnl_rate=2.60,
            commission=585,
            exit_reason="TAKE_PROFIT_1",
            entry_time="2024-01-13T10:30:00",
            exit_time="2024-01-14T11:00:00"
        ),
        Trade(
            trade_id="T006",
            stock_code="006400",
            stock_name="삼성SDI",
            side="SELL",
            quantity=15,
            entry_price=420000,
            exit_price=435000,
            pnl=225000,
            pnl_rate=3.57,
            commission=963,
            exit_reason="TAKE_PROFIT_2",
            entry_time="2024-01-12T10:00:00",
            exit_time="2024-01-13T14:30:00"
        ),
        Trade(
            trade_id="T007",
            stock_code="003670",
            stock_name="포스코퓨처엠",
            side="SELL",
            quantity=25,
            entry_price=310000,
            exit_price=302000,
            pnl=-200000,
            pnl_rate=-2.58,
            commission=765,
            exit_reason="STOP_LOSS",
            entry_time="2024-01-11T11:00:00",
            exit_time="2024-01-11T15:00:00"
        ),
    ]


def calculate_statistics(trades: List[Trade]) -> TradeStatistics:
    """거래 통계 계산"""
    if not trades:
        return TradeStatistics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0,
            total_pnl=0,
            avg_pnl=0,
            max_profit=0,
            max_loss=0,
            avg_holding_time="0h"
        )

    winning = [t for t in trades if t.pnl > 0]
    losing = [t for t in trades if t.pnl <= 0]
    total_pnl = sum(t.pnl for t in trades)

    # 평균 보유 시간 계산
    total_minutes = 0
    for t in trades:
        entry = datetime.fromisoformat(t.entry_time)
        exit_time = datetime.fromisoformat(t.exit_time)
        total_minutes += (exit_time - entry).total_seconds() / 60

    avg_minutes = total_minutes / len(trades) if trades else 0
    if avg_minutes >= 60:
        avg_holding = f"{int(avg_minutes // 60)}h {int(avg_minutes % 60)}m"
    else:
        avg_holding = f"{int(avg_minutes)}m"

    return TradeStatistics(
        total_trades=len(trades),
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate=round(len(winning) / len(trades) * 100, 1) if trades else 0,
        total_pnl=total_pnl,
        avg_pnl=round(total_pnl / len(trades), 0) if trades else 0,
        max_profit=max((t.pnl for t in winning), default=0),
        max_loss=min((t.pnl for t in losing), default=0),
        avg_holding_time=avg_holding
    )


# ==================== 거래 내역 조회 API ====================

@router.get("/", response_model=List[Trade])
async def get_trades(
    current_user: User = Depends(get_current_active_user),
    start_date: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
    stock_code: Optional[str] = Query(None, description="종목 코드"),
    side: Optional[str] = Query(None, description="매매 유형 (BUY/SELL)"),
    result: Optional[str] = Query(None, description="결과 (win/loss)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    거래 내역 조회

    - 필터링: 날짜, 종목, 매매유형, 결과
    - 페이징: limit, offset
    """
    # Mock 데이터 사용 (실제로는 DB에서 조회)
    trades = get_mock_trades()

    # 필터링
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        trades = [t for t in trades if datetime.fromisoformat(t.exit_time) >= start_dt]

    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        trades = [t for t in trades if datetime.fromisoformat(t.exit_time) < end_dt]

    if stock_code:
        trades = [t for t in trades if t.stock_code == stock_code]

    if side:
        trades = [t for t in trades if t.side.upper() == side.upper()]

    if result:
        if result.lower() == "win":
            trades = [t for t in trades if t.pnl > 0]
        elif result.lower() == "loss":
            trades = [t for t in trades if t.pnl <= 0]

    # 날짜 내림차순 정렬
    trades.sort(key=lambda t: t.exit_time, reverse=True)

    # 페이징
    return trades[offset:offset + limit]


@router.get("/statistics", response_model=TradeStatistics)
async def get_trade_statistics(
    current_user: User = Depends(get_current_active_user),
    period: Optional[str] = Query("all", description="기간 (today/week/month/all)")
):
    """
    거래 통계 조회

    - period: today (오늘), week (최근 7일), month (최근 30일), all (전체)
    """
    trades = get_mock_trades()

    # 기간 필터링
    now = datetime.now()
    if period == "today":
        start_dt = now.replace(hour=0, minute=0, second=0)
        trades = [t for t in trades if datetime.fromisoformat(t.exit_time) >= start_dt]
    elif period == "week":
        start_dt = now - timedelta(days=7)
        trades = [t for t in trades if datetime.fromisoformat(t.exit_time) >= start_dt]
    elif period == "month":
        start_dt = now - timedelta(days=30)
        trades = [t for t in trades if datetime.fromisoformat(t.exit_time) >= start_dt]

    return calculate_statistics(trades)


@router.get("/daily-summary")
async def get_daily_summary(
    current_user: User = Depends(get_current_active_user),
    days: int = Query(7, ge=1, le=30, description="조회 일수")
):
    """
    일별 거래 요약 조회
    """
    trades = get_mock_trades()

    # 날짜별 그룹화
    daily_data = {}
    for trade in trades:
        date = datetime.fromisoformat(trade.exit_time).strftime("%Y-%m-%d")
        if date not in daily_data:
            daily_data[date] = {"trades": 0, "wins": 0, "pnl": 0}
        daily_data[date]["trades"] += 1
        if trade.pnl > 0:
            daily_data[date]["wins"] += 1
        daily_data[date]["pnl"] += trade.pnl

    # 결과 포맷팅
    result = []
    for date, data in sorted(daily_data.items(), reverse=True)[:days]:
        result.append({
            "date": date,
            "total_trades": data["trades"],
            "winning_trades": data["wins"],
            "win_rate": round(data["wins"] / data["trades"] * 100, 1) if data["trades"] > 0 else 0,
            "total_pnl": data["pnl"]
        })

    return {
        "success": True,
        "data": result
    }


@router.get("/detail/{trade_id}", response_model=Trade)
async def get_trade_detail(
    trade_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    개별 거래 상세 조회
    """
    trades = get_mock_trades()
    trade = next((t for t in trades if t.trade_id == trade_id), None)

    if not trade:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")

    return trade


@router.get("/stock/{stock_code}")
async def get_trades_by_stock(
    stock_code: str,
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(20, ge=1, le=100)
):
    """
    종목별 거래 내역 조회
    """
    trades = get_mock_trades()
    stock_trades = [t for t in trades if t.stock_code == stock_code]

    if not stock_trades:
        return {
            "success": True,
            "data": {
                "stock_code": stock_code,
                "trades": [],
                "statistics": None
            }
        }

    stats = calculate_statistics(stock_trades)

    return {
        "success": True,
        "data": {
            "stock_code": stock_code,
            "trades": stock_trades[:limit],
            "statistics": stats
        }
    }


@router.get("/analysis/exit-reasons")
async def analyze_exit_reasons(
    current_user: User = Depends(get_current_active_user)
):
    """
    청산 사유별 분석
    """
    trades = get_mock_trades()

    # 청산 사유별 집계
    reasons = {}
    for trade in trades:
        reason = trade.exit_reason
        if reason not in reasons:
            reasons[reason] = {"count": 0, "total_pnl": 0, "wins": 0}
        reasons[reason]["count"] += 1
        reasons[reason]["total_pnl"] += trade.pnl
        if trade.pnl > 0:
            reasons[reason]["wins"] += 1

    # 결과 포맷팅
    result = []
    for reason, data in reasons.items():
        result.append({
            "exit_reason": reason,
            "count": data["count"],
            "win_rate": round(data["wins"] / data["count"] * 100, 1),
            "total_pnl": data["total_pnl"],
            "avg_pnl": round(data["total_pnl"] / data["count"], 0)
        })

    return {
        "success": True,
        "data": sorted(result, key=lambda x: x["count"], reverse=True)
    }
