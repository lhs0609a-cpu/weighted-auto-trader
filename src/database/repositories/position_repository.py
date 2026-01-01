"""
포지션 리포지토리
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ...models.position import Position


class PositionRepository(BaseRepository[Position]):
    """포지션 리포지토리"""

    def __init__(self, session: AsyncSession):
        super().__init__(Position, session)

    async def get_by_stock(self, stock_code: str) -> List[Position]:
        """종목별 포지션 조회"""
        query = select(Position).where(Position.stock_code == stock_code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_open_positions(self) -> List[Position]:
        """열린 포지션 조회"""
        query = select(Position).where(Position.status == "OPEN")
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_style(self, trading_style: str) -> List[Position]:
        """매매 스타일별 포지션 조회"""
        query = select(Position).where(Position.trading_style == trading_style)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_open_by_stock(self, stock_code: str) -> Optional[Position]:
        """종목의 열린 포지션 조회"""
        query = select(Position).where(
            and_(
                Position.stock_code == stock_code,
                Position.status == "OPEN"
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def close_position(
        self,
        position_id: str,
        exit_time: datetime,
        exit_price: float,
        realized_pnl: float
    ) -> Optional[Position]:
        """포지션 청산"""
        position = await self.get(position_id)
        if position:
            position.status = "CLOSED"
            position.exit_time = exit_time
            position.current_price = exit_price
            position.unrealized_pnl = 0
            await self.session.flush()
            await self.session.refresh(position)
        return position

    async def update_price(
        self,
        position_id: str,
        current_price: float,
        highest_price: float
    ) -> Optional[Position]:
        """가격 업데이트"""
        position = await self.get(position_id)
        if position:
            position.current_price = current_price
            if highest_price > (position.highest_price or 0):
                position.highest_price = highest_price

            # 손익 계산
            entry_price = float(position.entry_price)
            quantity = position.quantity
            position.unrealized_pnl = (current_price - entry_price) * quantity
            position.unrealized_pnl_pct = ((current_price / entry_price) - 1) * 100

            await self.session.flush()
            await self.session.refresh(position)
        return position

    async def get_total_unrealized_pnl(self) -> float:
        """총 미실현 손익"""
        positions = await self.get_open_positions()
        return sum(float(p.unrealized_pnl or 0) for p in positions)

    async def count_open_positions(self) -> int:
        """열린 포지션 수"""
        from sqlalchemy import func
        query = select(func.count()).select_from(Position).where(Position.status == "OPEN")
        result = await self.session.execute(query)
        return result.scalar() or 0
