"""
브로커 클라이언트 인터페이스
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Quote:
    """시세 데이터"""
    stock_code: str
    name: str
    price: float
    change: float
    change_rate: float
    volume: int
    trade_amount: int
    open: float
    high: float
    low: float
    prev_close: float
    timestamp: datetime
    extra: Dict[str, Any] = field(default_factory=dict)  # 추가 정보 (PER, PBR 등)


@dataclass
class OHLCV:
    """OHLCV 데이터"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class OrderBook:
    """호가 데이터"""
    stock_code: str
    ask_prices: List[float]      # 매도 호가 (10단계)
    ask_volumes: List[int]       # 매도 잔량
    bid_prices: List[float]      # 매수 호가
    bid_volumes: List[int]       # 매수 잔량
    total_ask_volume: int        # 총 매도 잔량
    total_bid_volume: int        # 총 매수 잔량
    timestamp: datetime
    extra: Dict[str, Any] = field(default_factory=dict)  # 추가 정보 (예상체결가 등)


@dataclass
class OrderResult:
    """주문 결과"""
    order_id: str
    stock_code: str
    order_side: OrderSide
    order_type: OrderType
    order_price: float
    order_qty: int
    executed_price: Optional[float]
    executed_qty: int
    status: str
    message: str


@dataclass
class Balance:
    """잔고 정보"""
    total_asset: float
    available_cash: float
    total_purchase: float
    total_evaluation: float
    total_pnl: float
    total_pnl_rate: float


@dataclass
class HoldingStock:
    """보유 종목"""
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: float
    current_price: float
    evaluation: float
    pnl: float
    pnl_rate: float


class IBrokerClient(ABC):
    """브로커 클라이언트 인터페이스"""

    @abstractmethod
    async def connect(self) -> bool:
        """API 연결"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """연결 해제"""
        pass

    @abstractmethod
    async def get_quote(self, stock_code: str) -> Quote:
        """현재가 조회"""
        pass

    @abstractmethod
    async def get_quotes(self, stock_codes: List[str]) -> List[Quote]:
        """복수 종목 현재가 조회"""
        pass

    @abstractmethod
    async def get_ohlcv(
        self,
        stock_code: str,
        period: str,
        count: int = 100
    ) -> List[OHLCV]:
        """OHLCV 데이터 조회"""
        pass

    @abstractmethod
    async def get_orderbook(self, stock_code: str) -> OrderBook:
        """호가 조회"""
        pass

    @abstractmethod
    async def get_execution_data(self, stock_code: str) -> Dict:
        """체결 데이터 조회 (체결강도 계산용)"""
        pass

    @abstractmethod
    async def get_balance(self) -> Balance:
        """잔고 조회"""
        pass

    @abstractmethod
    async def get_positions(self) -> List[HoldingStock]:
        """보유 종목 조회"""
        pass

    @abstractmethod
    async def place_order(
        self,
        stock_code: str,
        order_side: OrderSide,
        order_type: OrderType,
        quantity: int,
        price: Optional[float] = None
    ) -> OrderResult:
        """주문 실행"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        pass

    @abstractmethod
    async def get_stock_list(self, market: str = None) -> List[Dict]:
        """종목 리스트 조회"""
        pass
