"""
트레이딩 엔진
- 매매 신호 기반 자동 매매
- 포지션/주문 통합 관리
- 리스크 관리
"""
from typing import Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime
import asyncio

from ...config.constants import (
    TradingStyle, SignalType, OrderSide, OrderType,
    ExitReason, PositionStatus, TRADE_PARAMS
)
from ...core.broker.interfaces import IBrokerClient
from ...core.scoring.signal_generator import SignalGenerator, SignalResult
from .position_manager import PositionManager, PositionInfo
from .order_manager import OrderManager, OrderInfo


@dataclass
class TradingConfig:
    """트레이딩 설정"""
    style: TradingStyle
    max_positions: int = 5
    max_position_pct: float = 20.0
    total_capital: float = 10_000_000
    enable_auto_trade: bool = False
    enable_partial_close: bool = True
    partial_close_ratio: float = 0.5


@dataclass
class TradeDecision:
    """매매 판단 결과"""
    stock_code: str
    stock_name: str
    action: str  # BUY, SELL, HOLD
    signal: SignalResult
    quantity: int = 0
    price: float = 0
    reason: str = ""


class TradingEngine:
    """트레이딩 엔진"""

    def __init__(
        self,
        broker: IBrokerClient,
        config: TradingConfig
    ):
        self.broker = broker
        self.config = config
        self.signal_generator = SignalGenerator(config.style)
        self.position_manager = PositionManager()
        self.order_manager = OrderManager(broker)

        self._running = False
        self._trade_callbacks: List[Callable[[TradeDecision], Awaitable[None]]] = []

        # 주문 체결 콜백 등록
        self.order_manager.register_callback(self._on_order_filled)

    def register_trade_callback(self, callback: Callable[[TradeDecision], Awaitable[None]]):
        """매매 콜백 등록"""
        self._trade_callbacks.append(callback)

    async def _notify_trade(self, decision: TradeDecision):
        """매매 콜백 호출"""
        for callback in self._trade_callbacks:
            try:
                await callback(decision)
            except Exception as e:
                print(f"Trade callback error: {e}")

    async def _on_order_filled(self, order: OrderInfo):
        """주문 체결 처리"""
        if order.order_side == OrderSide.BUY:
            # 포지션 생성
            trade_params = TRADE_PARAMS[self.config.style]
            self.position_manager.create_position(
                stock_code=order.stock_code,
                stock_name=order.stock_name,
                entry_price=order.executed_price,
                quantity=order.executed_quantity,
                style=self.config.style
            )

    async def analyze_stock(
        self,
        stock_code: str,
        indicators: Dict,
        current_price: float
    ) -> TradeDecision:
        """종목 분석 및 매매 판단"""
        # 현재가 조회
        if current_price == 0:
            quote = await self.broker.get_quote(stock_code)
            current_price = quote.price
            stock_name = quote.name
        else:
            stock_name = indicators.get('stock_name', stock_code)

        # 신호 생성
        signal = self.signal_generator.generate(indicators, current_price)

        # 기존 포지션 확인
        existing_positions = self.position_manager.get_positions_by_stock(stock_code)
        open_positions = [p for p in existing_positions if p.status != PositionStatus.CLOSED]

        # 매매 판단
        action = "HOLD"
        quantity = 0
        reason = ""

        if signal.signal in [SignalType.STRONG_BUY, SignalType.BUY]:
            if len(open_positions) == 0:
                # 신규 매수
                if self._can_open_position():
                    action = "BUY"
                    quantity = self._calculate_position_size(current_price)
                    reason = signal.reasons[0] if signal.reasons else "매수 신호"
                else:
                    reason = "최대 포지션 수 초과"
            else:
                reason = "이미 보유 중"

        elif signal.signal == SignalType.SELL:
            if len(open_positions) > 0:
                action = "SELL"
                quantity = sum(p.remaining_quantity for p in open_positions)
                reason = "매도 신호"

        decision = TradeDecision(
            stock_code=stock_code,
            stock_name=stock_name,
            action=action,
            signal=signal,
            quantity=quantity,
            price=current_price,
            reason=reason
        )

        return decision

    async def execute_decision(self, decision: TradeDecision) -> Optional[OrderInfo]:
        """매매 판단 실행"""
        if not self.config.enable_auto_trade:
            return None

        if decision.action == "HOLD":
            return None

        if decision.action == "BUY" and decision.quantity > 0:
            order = await self.order_manager.place_market_buy(
                stock_code=decision.stock_code,
                stock_name=decision.stock_name,
                quantity=decision.quantity
            )
            await self._notify_trade(decision)
            return order

        elif decision.action == "SELL" and decision.quantity > 0:
            order = await self.order_manager.place_market_sell(
                stock_code=decision.stock_code,
                stock_name=decision.stock_name,
                quantity=decision.quantity
            )

            # 포지션 청산 처리
            positions = self.position_manager.get_positions_by_stock(decision.stock_code)
            for pos in positions:
                if pos.status != PositionStatus.CLOSED:
                    self.position_manager.close_position(
                        pos.position_id,
                        decision.price,
                        ExitReason.SIGNAL
                    )

            await self._notify_trade(decision)
            return order

        return None

    async def update_positions(self, prices: Dict[str, float]):
        """포지션 가격 업데이트 및 청산 체크"""
        for position in self.position_manager.get_open_positions():
            stock_code = position.stock_code
            if stock_code not in prices:
                continue

            current_price = prices[stock_code]
            exit_reason = self.position_manager.update_price(
                position.position_id,
                current_price
            )

            if exit_reason:
                await self._handle_exit(position, current_price, exit_reason)

    async def _handle_exit(
        self,
        position: PositionInfo,
        price: float,
        reason: ExitReason
    ):
        """청산 처리"""
        if not self.config.enable_auto_trade:
            return

        if reason == ExitReason.TAKE_PROFIT_1 and self.config.enable_partial_close:
            # 1차 익절: 부분 청산
            sell_qty = int(position.remaining_quantity * self.config.partial_close_ratio)
            if sell_qty > 0:
                await self.order_manager.place_market_sell(
                    stock_code=position.stock_code,
                    stock_name=position.stock_name,
                    quantity=sell_qty
                )
                self.position_manager.partial_close(
                    position.position_id,
                    sell_qty,
                    price,
                    reason
                )
        else:
            # 전량 청산
            await self.order_manager.place_market_sell(
                stock_code=position.stock_code,
                stock_name=position.stock_name,
                quantity=position.remaining_quantity
            )
            self.position_manager.close_position(
                position.position_id,
                price,
                reason
            )

    def _can_open_position(self) -> bool:
        """신규 포지션 가능 여부"""
        open_count = len(self.position_manager.get_open_positions())
        return open_count < self.config.max_positions

    def _calculate_position_size(self, price: float) -> int:
        """포지션 크기 계산"""
        if price <= 0:
            return 0

        params = TRADE_PARAMS[self.config.style]
        position_amount = self.config.total_capital * (params.position_size_pct / 100)
        quantity = int(position_amount / price)

        return max(1, quantity)

    def get_status(self) -> Dict:
        """엔진 상태 조회"""
        return {
            "running": self._running,
            "style": self.config.style.value,
            "auto_trade_enabled": self.config.enable_auto_trade,
            "positions": self.position_manager.get_position_summary(),
            "orders": self.order_manager.get_order_summary()
        }

    async def start(self):
        """엔진 시작"""
        self._running = True
        await self.broker.connect()

    async def stop(self):
        """엔진 중지"""
        self._running = False
        await self.broker.disconnect()

    def set_auto_trade(self, enabled: bool):
        """자동매매 설정"""
        self.config.enable_auto_trade = enabled

    def update_config(self, **kwargs):
        """설정 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
