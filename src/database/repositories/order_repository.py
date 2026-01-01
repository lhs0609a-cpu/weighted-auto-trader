"""
주문 리포지토리
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ...models.order import Order


class OrderRepository(BaseRepository[Order]):
    """주문 리포지토리"""

    def __init__(self, session: AsyncSession):
        super().__init__(Order, session)

    async def get_by_stock(self, stock_code: str) -> List[Order]:
        """종목별 주문 조회"""
        query = (
            select(Order)
            .where(Order.stock_code == stock_code)
            .order_by(desc(Order.created_at))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_orders(self) -> List[Order]:
        """대기 주문 조회"""
        query = select(Order).where(Order.status == "PENDING")
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_filled_orders(self, limit: int = 100) -> List[Order]:
        """체결 완료 주문 조회"""
        query = (
            select(Order)
            .where(Order.status == "FILLED")
            .order_by(desc(Order.created_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_today_orders(self) -> List[Order]:
        """오늘 주문 조회"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query = (
            select(Order)
            .where(Order.created_at >= today)
            .order_by(desc(Order.created_at))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_orders_in_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Order]:
        """기간별 주문 조회"""
        query = (
            select(Order)
            .where(
                and_(
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
            .order_by(desc(Order.created_at))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_order_status(
        self,
        order_id: str,
        status: str,
        executed_price: Optional[float] = None,
        executed_qty: Optional[int] = None,
        message: Optional[str] = None
    ) -> Optional[Order]:
        """주문 상태 업데이트"""
        order = await self.get(order_id)
        if order:
            order.status = status
            if executed_price is not None:
                order.executed_price = executed_price
            if executed_qty is not None:
                order.executed_qty = executed_qty
            if message is not None:
                order.message = message
            await self.session.flush()
            await self.session.refresh(order)
        return order

    async def cancel_order(self, order_id: str) -> Optional[Order]:
        """주문 취소"""
        return await self.update_order_status(order_id, "CANCELED")

    async def get_daily_summary(self) -> dict:
        """일일 주문 요약"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        orders = await self.get_orders_in_range(today, datetime.now())

        filled_orders = [o for o in orders if o.status == "FILLED"]
        buy_orders = [o for o in filled_orders if o.order_side == "BUY"]
        sell_orders = [o for o in filled_orders if o.order_side == "SELL"]

        return {
            "total_orders": len(orders),
            "filled_orders": len(filled_orders),
            "pending_orders": len([o for o in orders if o.status == "PENDING"]),
            "canceled_orders": len([o for o in orders if o.status == "CANCELED"]),
            "buy_count": len(buy_orders),
            "sell_count": len(sell_orders),
            "total_buy_amount": sum(
                float(o.executed_price or 0) * (o.executed_qty or 0)
                for o in buy_orders
            ),
            "total_sell_amount": sum(
                float(o.executed_price or 0) * (o.executed_qty or 0)
                for o in sell_orders
            )
        }
