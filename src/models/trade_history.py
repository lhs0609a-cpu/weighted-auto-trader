"""
매매 이력 모델
"""
import uuid
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Interval, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class TradeHistory(Base):
    """매매 이력 테이블"""
    __tablename__ = "trade_history"

    trade_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="매매 ID")
    position_id = Column(UUID(as_uuid=True), ForeignKey("positions.position_id"), comment="포지션 ID")
    stock_code = Column(String(10), nullable=False, comment="종목코드")
    trading_style = Column(String(20), nullable=False, comment="매매 스타일")

    # 매매 정보
    entry_price = Column(Numeric(15, 2), nullable=False, comment="진입가격")
    exit_price = Column(Numeric(15, 2), nullable=False, comment="청산가격")
    quantity = Column(Integer, nullable=False, comment="수량")

    # 손익
    realized_pnl = Column(Numeric(15, 2), nullable=False, comment="실현 손익")
    realized_pnl_pct = Column(Numeric(10, 2), nullable=False, comment="수익률")

    # 매매 근거
    entry_signal_id = Column(UUID(as_uuid=True), comment="진입 신호 ID")
    exit_reason = Column(String(50), comment="청산 사유")
    entry_score = Column(Numeric(5, 2), comment="진입 점수")
    exit_score = Column(Numeric(5, 2), comment="청산 점수")

    # 시간
    entry_time = Column(DateTime, nullable=False, comment="진입시간")
    exit_time = Column(DateTime, nullable=False, comment="청산시간")
    hold_duration = Column(Interval, comment="보유 기간")

    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<TradeHistory(stock_code={self.stock_code}, pnl={self.realized_pnl_pct}%)>"


class DailyPerformance(Base):
    """일별 성과 테이블"""
    __tablename__ = "daily_performance"

    date = Column(DateTime, primary_key=True, comment="날짜")
    trading_style = Column(String(20), primary_key=True, comment="매매 스타일")

    # 거래 통계
    total_trades = Column(Integer, default=0, comment="총 거래 수")
    winning_trades = Column(Integer, default=0, comment="수익 거래 수")
    losing_trades = Column(Integer, default=0, comment="손실 거래 수")

    # 손익
    total_pnl = Column(Numeric(20, 2), default=0, comment="총 손익")
    total_pnl_pct = Column(Numeric(10, 2), default=0, comment="총 손익률")

    # 지표
    win_rate = Column(Numeric(5, 2), comment="승률")
    avg_win = Column(Numeric(15, 2), comment="평균 수익")
    avg_loss = Column(Numeric(15, 2), comment="평균 손실")
    profit_factor = Column(Numeric(10, 2), comment="손익비")
    max_drawdown = Column(Numeric(10, 2), comment="최대 낙폭")

    def __repr__(self):
        return f"<DailyPerformance(date={self.date}, style={self.trading_style}, win_rate={self.win_rate}%)>"
