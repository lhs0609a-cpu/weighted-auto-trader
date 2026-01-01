"""
포지션 관리자
- 포지션 생성/조회/수정
- 손익 계산
- 트레일링 스탑 관리
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from ...config.constants import (
    TradingStyle, PositionStatus, ExitReason, TradeParams, TRADE_PARAMS
)


@dataclass
class PositionInfo:
    """포지션 정보"""
    position_id: str
    stock_code: str
    stock_name: str
    trading_style: TradingStyle

    # 진입 정보
    entry_price: float
    quantity: int
    entry_time: datetime

    # 손익 관리 설정
    stop_loss_price: float
    take_profit_1: float
    take_profit_2: float
    trailing_stop_pct: float

    # 현재 상태
    current_price: float = 0
    highest_price: float = 0
    unrealized_pnl: float = 0
    unrealized_pnl_pct: float = 0

    # 부분 청산 정보
    sold_quantity: int = 0
    remaining_quantity: int = 0
    realized_pnl: float = 0

    status: PositionStatus = PositionStatus.OPEN
    exit_time: Optional[datetime] = None
    exit_reason: Optional[ExitReason] = None


class PositionManager:
    """포지션 관리자"""

    def __init__(self):
        self._positions: Dict[str, PositionInfo] = {}
        self._positions_by_stock: Dict[str, List[str]] = {}

    def create_position(
        self,
        stock_code: str,
        stock_name: str,
        entry_price: float,
        quantity: int,
        style: TradingStyle,
        trade_params: Optional[Dict] = None
    ) -> PositionInfo:
        """새 포지션 생성"""
        position_id = str(uuid.uuid4())

        # 매매 파라미터 설정
        if trade_params:
            stop_loss = trade_params.get('stop_loss', entry_price * 0.98)
            take_profit_1 = trade_params.get('take_profit_1', entry_price * 1.02)
            take_profit_2 = trade_params.get('take_profit_2', entry_price * 1.05)
            trailing_pct = trade_params.get('trailing_stop_pct', 0.5)
        else:
            params = TRADE_PARAMS[style]
            stop_loss = entry_price * (1 + params.stop_loss_pct / 100)
            take_profit_1 = entry_price * (1 + params.take_profit_1_pct / 100)
            take_profit_2 = entry_price * (1 + params.take_profit_2_pct / 100)
            trailing_pct = params.trailing_stop_pct

        position = PositionInfo(
            position_id=position_id,
            stock_code=stock_code,
            stock_name=stock_name,
            trading_style=style,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now(),
            stop_loss_price=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            trailing_stop_pct=trailing_pct,
            current_price=entry_price,
            highest_price=entry_price,
            remaining_quantity=quantity
        )

        self._positions[position_id] = position

        if stock_code not in self._positions_by_stock:
            self._positions_by_stock[stock_code] = []
        self._positions_by_stock[stock_code].append(position_id)

        return position

    def update_price(self, position_id: str, current_price: float) -> Optional[ExitReason]:
        """가격 업데이트 및 청산 조건 체크"""
        position = self._positions.get(position_id)
        if not position or position.status == PositionStatus.CLOSED:
            return None

        position.current_price = current_price

        # 최고가 갱신
        if current_price > position.highest_price:
            position.highest_price = current_price

        # 손익 계산
        position.unrealized_pnl = (current_price - position.entry_price) * position.remaining_quantity
        position.unrealized_pnl_pct = ((current_price / position.entry_price) - 1) * 100

        # 청산 조건 체크
        exit_reason = self._check_exit_conditions(position)

        return exit_reason

    def _check_exit_conditions(self, position: PositionInfo) -> Optional[ExitReason]:
        """청산 조건 체크"""
        price = position.current_price

        # 손절 체크
        if price <= position.stop_loss_price:
            return ExitReason.STOP_LOSS

        # 트레일링 스탑 체크 (최고가 대비)
        if position.highest_price > position.entry_price:
            trailing_stop_price = position.highest_price * (1 - position.trailing_stop_pct / 100)
            if price <= trailing_stop_price and price > position.entry_price:
                return ExitReason.TRAILING_STOP

        # 1차 익절 체크 (아직 1차 익절 안했으면)
        if position.sold_quantity == 0 and price >= position.take_profit_1:
            return ExitReason.TAKE_PROFIT_1

        # 2차 익절 체크
        if price >= position.take_profit_2:
            return ExitReason.TAKE_PROFIT_2

        return None

    def partial_close(
        self,
        position_id: str,
        quantity: int,
        price: float,
        reason: ExitReason
    ) -> bool:
        """부분 청산"""
        position = self._positions.get(position_id)
        if not position:
            return False

        if quantity > position.remaining_quantity:
            quantity = position.remaining_quantity

        # 손익 계산
        pnl = (price - position.entry_price) * quantity
        position.realized_pnl += pnl
        position.sold_quantity += quantity
        position.remaining_quantity -= quantity

        if position.remaining_quantity <= 0:
            position.status = PositionStatus.CLOSED
            position.exit_time = datetime.now()
            position.exit_reason = reason
        else:
            position.status = PositionStatus.PARTIAL_CLOSED

        return True

    def close_position(
        self,
        position_id: str,
        price: float,
        reason: ExitReason
    ) -> bool:
        """포지션 전량 청산"""
        position = self._positions.get(position_id)
        if not position:
            return False

        return self.partial_close(position_id, position.remaining_quantity, price, reason)

    def get_position(self, position_id: str) -> Optional[PositionInfo]:
        """포지션 조회"""
        return self._positions.get(position_id)

    def get_positions_by_stock(self, stock_code: str) -> List[PositionInfo]:
        """종목별 포지션 조회"""
        position_ids = self._positions_by_stock.get(stock_code, [])
        return [self._positions[pid] for pid in position_ids if pid in self._positions]

    def get_open_positions(self) -> List[PositionInfo]:
        """열린 포지션 목록"""
        return [p for p in self._positions.values() if p.status != PositionStatus.CLOSED]

    def get_all_positions(self) -> List[PositionInfo]:
        """전체 포지션 목록"""
        return list(self._positions.values())

    def get_total_unrealized_pnl(self) -> float:
        """총 미실현 손익"""
        return sum(p.unrealized_pnl for p in self.get_open_positions())

    def get_total_realized_pnl(self) -> float:
        """총 실현 손익"""
        return sum(p.realized_pnl for p in self._positions.values())

    def get_position_summary(self) -> Dict:
        """포지션 요약"""
        open_positions = self.get_open_positions()

        return {
            "total_positions": len(self._positions),
            "open_positions": len(open_positions),
            "total_unrealized_pnl": self.get_total_unrealized_pnl(),
            "total_realized_pnl": self.get_total_realized_pnl(),
            "positions": [
                {
                    "position_id": p.position_id,
                    "stock_code": p.stock_code,
                    "stock_name": p.stock_name,
                    "quantity": p.remaining_quantity,
                    "entry_price": p.entry_price,
                    "current_price": p.current_price,
                    "unrealized_pnl": p.unrealized_pnl,
                    "unrealized_pnl_pct": round(p.unrealized_pnl_pct, 2),
                    "status": p.status.value
                }
                for p in open_positions
            ]
        }
