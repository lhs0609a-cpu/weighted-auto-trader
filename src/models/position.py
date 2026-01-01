"""
포지션 모델
"""
import uuid
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class Position(Base):
    """포지션 테이블"""
    __tablename__ = "positions"

    position_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="포지션 ID")
    stock_code = Column(String(10), ForeignKey("stocks.code"), nullable=False, comment="종목코드")
    trading_style = Column(String(20), nullable=False, comment="매매 스타일")

    # 포지션 정보
    entry_order_id = Column(String(50), ForeignKey("orders.order_id"), comment="진입 주문번호")
    entry_price = Column(Numeric(15, 2), nullable=False, comment="평균 매수가")
    quantity = Column(Integer, nullable=False, comment="보유 수량")

    # 손익 관리
    stop_loss_price = Column(Numeric(15, 2), comment="손절가")
    take_profit_1 = Column(Numeric(15, 2), comment="1차 익절가")
    take_profit_2 = Column(Numeric(15, 2), comment="2차 익절가")
    trailing_stop_pct = Column(Numeric(5, 2), comment="트레일링 비율")
    highest_price = Column(Numeric(15, 2), comment="최고가 (트레일링용)")

    # 현재 상태
    current_price = Column(Numeric(15, 2), comment="현재가")
    unrealized_pnl = Column(Numeric(15, 2), comment="미실현 손익")
    unrealized_pnl_pct = Column(Numeric(10, 2), comment="미실현 손익률")

    # 상태
    status = Column(String(20), nullable=False, comment="포지션 상태")

    # 시간
    entry_time = Column(DateTime, default=func.now(), comment="진입시간")
    exit_time = Column(DateTime, comment="청산시간")

    def __repr__(self):
        return f"<Position(stock_code={self.stock_code}, qty={self.quantity}, status={self.status})>"
