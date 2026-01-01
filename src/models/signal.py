"""
매매 신호 모델
"""
import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class Signal(Base):
    """매매 신호 테이블"""
    __tablename__ = "signals"

    signal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="신호 ID")
    stock_code = Column(String(10), ForeignKey("stocks.code"), nullable=False, comment="종목코드")
    trading_style = Column(String(20), nullable=False, comment="매매 스타일")
    signal_type = Column(String(20), nullable=False, comment="신호 종류")
    total_score = Column(Numeric(5, 2), nullable=False, comment="총점")

    # 지표별 점수
    volume_score = Column(Numeric(5, 2), comment="거래량 점수")
    order_book_score = Column(Numeric(5, 2), comment="호가/체결강도 점수")
    vwap_score = Column(Numeric(5, 2), comment="VWAP 점수")
    ma_score = Column(Numeric(5, 2), comment="이동평균선 점수")
    rsi_score = Column(Numeric(5, 2), comment="RSI 점수")
    macd_score = Column(Numeric(5, 2), comment="MACD 점수")
    bollinger_score = Column(Numeric(5, 2), comment="볼린저밴드 점수")
    obv_score = Column(Numeric(5, 2), comment="OBV 점수")

    # 지표 원본 값
    current_price = Column(Numeric(15, 2), comment="현재가")
    vwap = Column(Numeric(15, 2), comment="VWAP")
    volume_ratio = Column(Numeric(10, 2), comment="거래량 비율")
    strength = Column(Numeric(10, 2), comment="체결강도")
    rsi = Column(Numeric(5, 2), comment="RSI")

    # 메타정보
    mandatory_passed = Column(Boolean, comment="필수조건 충족 여부")
    details = Column(JSON, comment="상세 정보")
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Signal(stock_code={self.stock_code}, signal_type={self.signal_type}, score={self.total_score})>"
