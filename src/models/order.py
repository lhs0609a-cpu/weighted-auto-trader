"""
주문 모델
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class Order(Base):
    """주문 테이블"""
    __tablename__ = "orders"

    order_id = Column(String(50), primary_key=True, comment="주문번호")
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.signal_id"), comment="신호 ID")
    stock_code = Column(String(10), ForeignKey("stocks.code"), nullable=False, comment="종목코드")
    trading_style = Column(String(20), nullable=False, comment="매매 스타일")

    # 주문 정보
    order_type = Column(String(10), nullable=False, comment="주문 방향 (BUY/SELL)")
    order_method = Column(String(10), nullable=False, comment="주문 유형 (MARKET/LIMIT)")
    order_price = Column(Numeric(15, 2), comment="주문가격")
    order_qty = Column(Integer, nullable=False, comment="주문수량")

    # 체결 정보
    executed_price = Column(Numeric(15, 2), comment="체결가격")
    executed_qty = Column(Integer, default=0, comment="체결수량")
    executed_amount = Column(Numeric(20, 2), comment="체결금액")

    # 상태
    status = Column(String(20), nullable=False, comment="주문 상태")

    # 시간
    order_time = Column(DateTime, default=func.now(), comment="주문시간")
    executed_time = Column(DateTime, comment="체결시간")

    def __repr__(self):
        return f"<Order(order_id={self.order_id}, stock_code={self.stock_code}, type={self.order_type})>"
