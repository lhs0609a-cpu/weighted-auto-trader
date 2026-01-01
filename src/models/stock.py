"""
종목 마스터 모델
"""
from sqlalchemy import Column, String, BigInteger, Numeric, Boolean, DateTime, func
from .base import Base, TimestampMixin


class Stock(Base, TimestampMixin):
    """종목 마스터 테이블"""
    __tablename__ = "stocks"

    code = Column(String(10), primary_key=True, comment="종목코드")
    name = Column(String(100), nullable=False, comment="종목명")
    market = Column(String(10), nullable=False, comment="시장구분 (KOSPI/KOSDAQ)")
    sector = Column(String(50), comment="업종")
    market_cap = Column(BigInteger, comment="시가총액")
    per = Column(Numeric(10, 2), comment="PER")
    pbr = Column(Numeric(10, 2), comment="PBR")
    debt_ratio = Column(Numeric(10, 2), comment="부채비율")
    is_active = Column(Boolean, default=True, comment="활성 여부")

    def __repr__(self):
        return f"<Stock(code={self.code}, name={self.name})>"
