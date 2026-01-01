"""
거래내역 리포지토리
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ...models.trade_history import TradeHistory


class TradeHistoryRepository(BaseRepository[TradeHistory]):
    """거래내역 리포지토리"""

    def __init__(self, session: AsyncSession):
        super().__init__(TradeHistory, session)

    async def get_by_stock(self, stock_code: str, limit: int = 100) -> List[TradeHistory]:
        """종목별 거래내역 조회"""
        query = (
            select(TradeHistory)
            .where(TradeHistory.stock_code == stock_code)
            .order_by(desc(TradeHistory.exit_time))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_style(self, trading_style: str, limit: int = 100) -> List[TradeHistory]:
        """매매 스타일별 거래내역 조회"""
        query = (
            select(TradeHistory)
            .where(TradeHistory.trading_style == trading_style)
            .order_by(desc(TradeHistory.exit_time))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_in_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[TradeHistory]:
        """기간별 거래내역 조회"""
        query = (
            select(TradeHistory)
            .where(
                and_(
                    TradeHistory.exit_time >= start_date,
                    TradeHistory.exit_time <= end_date
                )
            )
            .order_by(desc(TradeHistory.exit_time))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_today_trades(self) -> List[TradeHistory]:
        """오늘 거래내역 조회"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.get_in_range(today, datetime.now())

    async def get_winning_trades(self, limit: int = 100) -> List[TradeHistory]:
        """수익 거래 조회"""
        query = (
            select(TradeHistory)
            .where(TradeHistory.realized_pnl > 0)
            .order_by(desc(TradeHistory.realized_pnl))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_losing_trades(self, limit: int = 100) -> List[TradeHistory]:
        """손실 거래 조회"""
        query = (
            select(TradeHistory)
            .where(TradeHistory.realized_pnl < 0)
            .order_by(TradeHistory.realized_pnl)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_pnl(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """총 손익 조회"""
        query = select(func.sum(TradeHistory.realized_pnl))

        if start_date and end_date:
            query = query.where(
                and_(
                    TradeHistory.exit_time >= start_date,
                    TradeHistory.exit_time <= end_date
                )
            )

        result = await self.session.execute(query)
        return float(result.scalar() or 0)

    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """거래 통계 조회"""
        if start_date and end_date:
            trades = await self.get_in_range(start_date, end_date)
        else:
            trades = await self.get_all(limit=10000)

        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
                "max_profit": 0,
                "max_loss": 0,
                "avg_holding_time": 0
            }

        pnl_list = [float(t.realized_pnl or 0) for t in trades]
        winning = [p for p in pnl_list if p > 0]
        losing = [p for p in pnl_list if p < 0]

        # 평균 보유 시간 계산
        holding_times = []
        for t in trades:
            if t.entry_time and t.exit_time:
                delta = t.exit_time - t.entry_time
                holding_times.append(delta.total_seconds() / 60)  # 분 단위

        return {
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": round(len(winning) / len(trades) * 100, 2) if trades else 0,
            "total_pnl": sum(pnl_list),
            "avg_pnl": sum(pnl_list) / len(trades) if trades else 0,
            "max_profit": max(pnl_list) if pnl_list else 0,
            "max_loss": min(pnl_list) if pnl_list else 0,
            "avg_holding_time": sum(holding_times) / len(holding_times) if holding_times else 0,
            "profit_factor": abs(sum(winning) / sum(losing)) if losing and sum(losing) != 0 else 0
        }

    async def get_monthly_summary(self, year: int, month: int) -> Dict:
        """월간 요약"""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        return await self.get_statistics(start, end)
