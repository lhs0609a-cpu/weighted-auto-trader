"""
주문 관리자
- 주문 생성/취소
- 주문 상태 관리
- 체결 처리
"""
from typing import Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid
import asyncio

from ...config.constants import OrderType, OrderSide, OrderStatus
from ...core.broker.interfaces import IBrokerClient, OrderResult


@dataclass
class OrderInfo:
    """주문 정보"""
    order_id: str
    stock_code: str
    stock_name: str
    order_side: OrderSide
    order_type: OrderType
    order_price: float
    order_quantity: int
    executed_price: float = 0
    executed_quantity: int = 0
    status: OrderStatus = OrderStatus.PENDING
    message: str = ""
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class OrderManager:
    """주문 관리자"""

    def __init__(self, broker: IBrokerClient):
        self.broker = broker
        self._orders: Dict[str, OrderInfo] = {}
        self._pending_orders: List[str] = []
        self._order_callbacks: List[Callable[[OrderInfo], Awaitable[None]]] = []

    def register_callback(self, callback: Callable[[OrderInfo], Awaitable[None]]):
        """주문 체결 콜백 등록"""
        self._order_callbacks.append(callback)

    async def _notify_callbacks(self, order: OrderInfo):
        """콜백 호출"""
        for callback in self._order_callbacks:
            try:
                await callback(order)
            except Exception as e:
                print(f"Order callback error: {e}")

    async def place_order(
        self,
        stock_code: str,
        stock_name: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        price: Optional[float] = None
    ) -> OrderInfo:
        """주문 실행"""
        order_id = str(uuid.uuid4())

        order = OrderInfo(
            order_id=order_id,
            stock_code=stock_code,
            stock_name=stock_name,
            order_side=side,
            order_type=order_type,
            order_price=price or 0,
            order_quantity=quantity
        )

        self._orders[order_id] = order
        self._pending_orders.append(order_id)

        try:
            # 브로커 주문 실행
            from ...core.broker.interfaces import OrderSide as BrokerOrderSide
            from ...core.broker.interfaces import OrderType as BrokerOrderType

            broker_side = BrokerOrderSide.BUY if side == OrderSide.BUY else BrokerOrderSide.SELL
            broker_type = BrokerOrderType.MARKET if order_type == OrderType.MARKET else BrokerOrderType.LIMIT

            result: OrderResult = await self.broker.place_order(
                stock_code=stock_code,
                order_side=broker_side,
                order_type=broker_type,
                quantity=quantity,
                price=price
            )

            # 결과 반영
            order.executed_price = result.executed_price or 0
            order.executed_quantity = result.executed_qty
            order.message = result.message

            if result.executed_qty >= quantity:
                order.status = OrderStatus.FILLED
            elif result.executed_qty > 0:
                order.status = OrderStatus.PARTIAL
            else:
                order.status = OrderStatus.PENDING

            order.updated_at = datetime.now()

            if order.status in [OrderStatus.FILLED, OrderStatus.PARTIAL]:
                await self._notify_callbacks(order)

        except Exception as e:
            order.status = OrderStatus.CANCELED
            order.message = str(e)
            order.updated_at = datetime.now()

        finally:
            if order_id in self._pending_orders:
                self._pending_orders.remove(order_id)

        return order

    async def place_market_buy(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int
    ) -> OrderInfo:
        """시장가 매수"""
        return await self.place_order(
            stock_code=stock_code,
            stock_name=stock_name,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=quantity
        )

    async def place_market_sell(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int
    ) -> OrderInfo:
        """시장가 매도"""
        return await self.place_order(
            stock_code=stock_code,
            stock_name=stock_name,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=quantity
        )

    async def place_limit_buy(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        price: float
    ) -> OrderInfo:
        """지정가 매수"""
        return await self.place_order(
            stock_code=stock_code,
            stock_name=stock_name,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price
        )

    async def place_limit_sell(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        price: float
    ) -> OrderInfo:
        """지정가 매도"""
        return await self.place_order(
            stock_code=stock_code,
            stock_name=stock_name,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price
        )

    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        order = self._orders.get(order_id)
        if not order:
            return False

        if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIAL]:
            return False

        try:
            result = await self.broker.cancel_order(order_id)
            if result:
                order.status = OrderStatus.CANCELED
                order.updated_at = datetime.now()
                if order_id in self._pending_orders:
                    self._pending_orders.remove(order_id)
            return result
        except Exception as e:
            order.message = f"Cancel failed: {e}"
            return False

    def get_order(self, order_id: str) -> Optional[OrderInfo]:
        """주문 조회"""
        return self._orders.get(order_id)

    def get_pending_orders(self) -> List[OrderInfo]:
        """대기 주문 목록"""
        return [self._orders[oid] for oid in self._pending_orders if oid in self._orders]

    def get_orders_by_stock(self, stock_code: str) -> List[OrderInfo]:
        """종목별 주문 목록"""
        return [o for o in self._orders.values() if o.stock_code == stock_code]

    def get_filled_orders(self) -> List[OrderInfo]:
        """체결 완료 주문 목록"""
        return [o for o in self._orders.values() if o.status == OrderStatus.FILLED]

    def get_order_history(self, limit: int = 100) -> List[OrderInfo]:
        """주문 내역 조회"""
        orders = sorted(
            self._orders.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        return orders[:limit]

    def get_order_summary(self) -> Dict:
        """주문 요약"""
        orders = list(self._orders.values())
        filled = [o for o in orders if o.status == OrderStatus.FILLED]
        pending = [o for o in orders if o.status == OrderStatus.PENDING]

        buy_orders = [o for o in filled if o.order_side == OrderSide.BUY]
        sell_orders = [o for o in filled if o.order_side == OrderSide.SELL]

        return {
            "total_orders": len(orders),
            "filled_orders": len(filled),
            "pending_orders": len(pending),
            "buy_orders": len(buy_orders),
            "sell_orders": len(sell_orders),
            "total_buy_amount": sum(o.executed_price * o.executed_quantity for o in buy_orders),
            "total_sell_amount": sum(o.executed_price * o.executed_quantity for o in sell_orders)
        }
