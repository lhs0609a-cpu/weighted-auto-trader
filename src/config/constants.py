"""
상수 정의 모듈
- 가중치 설정
- 임계값
- 매매 파라미터
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict


class TradingStyle(str, Enum):
    """매매 스타일"""
    SCALPING = "SCALPING"
    DAYTRADING = "DAYTRADING"
    SWING = "SWING"


class SignalType(str, Enum):
    """매매 신호 종류"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    WATCH = "WATCH"
    HOLD = "HOLD"
    SELL = "SELL"


class OrderType(str, Enum):
    """주문 유형"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderSide(str, Enum):
    """주문 방향"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """주문 상태"""
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELED = "CANCELED"


class PositionStatus(str, Enum):
    """포지션 상태"""
    OPEN = "OPEN"
    PARTIAL_CLOSED = "PARTIAL_CLOSED"
    CLOSED = "CLOSED"


class ExitReason(str, Enum):
    """청산 사유"""
    TAKE_PROFIT_1 = "TAKE_PROFIT_1"
    TAKE_PROFIT_2 = "TAKE_PROFIT_2"
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    MANUAL = "MANUAL"
    SIGNAL = "SIGNAL"


@dataclass
class WeightConfig:
    """가중치 설정"""
    volume: int
    order_book: int
    vwap: int
    ma: int
    rsi: int
    macd: int
    bollinger: int
    obv: int

    def to_dict(self) -> Dict[str, int]:
        return {
            "volume": self.volume,
            "order_book": self.order_book,
            "vwap": self.vwap,
            "ma": self.ma,
            "rsi": self.rsi,
            "macd": self.macd,
            "bollinger": self.bollinger,
            "obv": self.obv
        }


# 스타일별 가중치 설정
WEIGHT_CONFIGS: Dict[TradingStyle, WeightConfig] = {
    TradingStyle.SCALPING: WeightConfig(
        volume=25, order_book=30, vwap=20, ma=10,
        rsi=5, macd=3, bollinger=5, obv=2
    ),
    TradingStyle.DAYTRADING: WeightConfig(
        volume=30, order_book=15, vwap=25, ma=15,
        rsi=8, macd=5, bollinger=2, obv=0
    ),
    TradingStyle.SWING: WeightConfig(
        volume=20, order_book=5, vwap=10, ma=20,
        rsi=18, macd=15, bollinger=7, obv=5
    )
}


@dataclass
class TradeParams:
    """매매 파라미터"""
    stop_loss_pct: float      # 손절 비율 (%)
    take_profit_1_pct: float  # 1차 익절 비율 (%)
    take_profit_2_pct: float  # 2차 익절 비율 (%)
    trailing_stop_pct: float  # 트레일링 스탑 비율 (%)
    position_size_pct: float  # 포지션 비중 (%)


# 스타일별 매매 파라미터
TRADE_PARAMS: Dict[TradingStyle, TradeParams] = {
    TradingStyle.SCALPING: TradeParams(
        stop_loss_pct=-0.5,
        take_profit_1_pct=0.5,
        take_profit_2_pct=1.0,
        trailing_stop_pct=0.2,
        position_size_pct=30
    ),
    TradingStyle.DAYTRADING: TradeParams(
        stop_loss_pct=-1.5,
        take_profit_1_pct=2.0,
        take_profit_2_pct=3.0,
        trailing_stop_pct=0.5,
        position_size_pct=20
    ),
    TradingStyle.SWING: TradeParams(
        stop_loss_pct=-5.0,
        take_profit_1_pct=7.0,
        take_profit_2_pct=15.0,
        trailing_stop_pct=2.0,
        position_size_pct=15
    )
}


@dataclass
class SignalThreshold:
    """신호 판정 임계값"""
    strong_buy: float
    buy: float
    watch: float


# 스타일별 신호 임계값
SIGNAL_THRESHOLDS: Dict[TradingStyle, SignalThreshold] = {
    TradingStyle.SCALPING: SignalThreshold(
        strong_buy=85, buy=75, watch=60
    ),
    TradingStyle.DAYTRADING: SignalThreshold(
        strong_buy=80, buy=70, watch=55
    ),
    TradingStyle.SWING: SignalThreshold(
        strong_buy=75, buy=65, watch=50
    )
}


# 필수 조건 체크 기준
MANDATORY_CONDITIONS: Dict[TradingStyle, Dict[str, float]] = {
    TradingStyle.SCALPING: {
        "strength_min": 120,      # 체결강도 최소값
        "volume_ratio_min": 200   # 거래량 비율 최소값
    },
    TradingStyle.DAYTRADING: {
        "strength_min": 110,
        "volume_ratio_min": 200,
        "vwap_above": True        # VWAP 상단
    },
    TradingStyle.SWING: {
        "rsi_max": 70,            # RSI 최대값
        "above_ma20": True,       # 20일선 위
        "volume_ratio_min": 100   # 거래량 증가
    }
}


# 거래량 점수 매핑 (거래량 비율 -> 점수 배율)
VOLUME_SCORE_THRESHOLDS = [
    (500, 1.0),
    (300, 0.8),
    (200, 0.6),
    (150, 0.4),
    (100, 0.2)
]


# 체결강도 점수 매핑
STRENGTH_SCORE_THRESHOLDS: Dict[TradingStyle, list] = {
    TradingStyle.SCALPING: [
        (150, 1.0), (130, 0.83), (120, 0.67), (110, 0.5), (100, 0.33)
    ],
    TradingStyle.DAYTRADING: [
        (140, 1.0), (120, 0.8), (110, 0.6), (100, 0.4)
    ],
    TradingStyle.SWING: [
        (115, 1.0), (105, 0.6)
    ]
}


# 시장 구분
class Market(str, Enum):
    """시장 구분"""
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"


# 기본 스크리닝 필터
DEFAULT_SCREENING_FILTERS = {
    "market_cap_min": 100_000_000_000,   # 시가총액 최소 1000억
    "market_cap_max": 50_000_000_000_000, # 시가총액 최대 50조
    "volume_ratio_min": 100,              # 거래량 비율 최소 100%
    "price_min": 1000,                    # 주가 최소 1000원
    "price_max": 1_000_000,               # 주가 최대 100만원
}


# 이동평균선 기간
MA_PERIODS = [5, 20, 60, 120]

# RSI 기간
RSI_PERIOD = 14

# MACD 설정
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# 볼린저밴드 설정
BOLLINGER_PERIOD = 20
BOLLINGER_STD_DEV = 2.0

# 거래량 평균 계산 기간
VOLUME_PERIOD = 20

# 기본 지표 가중치
DEFAULT_INDICATOR_WEIGHTS = {
    "volume": 25,
    "order_book": 20,
    "vwap": 18,
    "rsi": 12,
    "macd": 10,
    "ma": 8,
    "bollinger": 5,
    "obv": 2
}
