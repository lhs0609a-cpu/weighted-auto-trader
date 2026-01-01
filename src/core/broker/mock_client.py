"""
Mock 브로커 클라이언트
- API 키 없이 테스트용 가상 데이터 생성
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np

from .interfaces import (
    IBrokerClient, Quote, OHLCV, OrderBook, OrderResult,
    Balance, HoldingStock, OrderType, OrderSide
)


# 샘플 종목 데이터
MOCK_STOCKS = {
    "005930": {"name": "삼성전자", "market": "KOSPI", "base_price": 75000, "market_cap": 450_000_000_000_000},
    "000660": {"name": "SK하이닉스", "market": "KOSPI", "base_price": 175000, "market_cap": 120_000_000_000_000},
    "035420": {"name": "NAVER", "market": "KOSPI", "base_price": 210000, "market_cap": 35_000_000_000_000},
    "035720": {"name": "카카오", "market": "KOSPI", "base_price": 52000, "market_cap": 23_000_000_000_000},
    "005380": {"name": "현대차", "market": "KOSPI", "base_price": 210000, "market_cap": 45_000_000_000_000},
    "051910": {"name": "LG화학", "market": "KOSPI", "base_price": 450000, "market_cap": 32_000_000_000_000},
    "006400": {"name": "삼성SDI", "market": "KOSPI", "base_price": 480000, "market_cap": 33_000_000_000_000},
    "068270": {"name": "셀트리온", "market": "KOSPI", "base_price": 175000, "market_cap": 22_000_000_000_000},
    "028260": {"name": "삼성물산", "market": "KOSPI", "base_price": 120000, "market_cap": 22_000_000_000_000},
    "012330": {"name": "현대모비스", "market": "KOSPI", "base_price": 240000, "market_cap": 22_000_000_000_000},
    "373220": {"name": "LG에너지솔루션", "market": "KOSPI", "base_price": 420000, "market_cap": 98_000_000_000_000},
    "207940": {"name": "삼성바이오로직스", "market": "KOSPI", "base_price": 800000, "market_cap": 56_000_000_000_000},
    "086790": {"name": "하나금융지주", "market": "KOSPI", "base_price": 52000, "market_cap": 15_000_000_000_000},
    "105560": {"name": "KB금융", "market": "KOSPI", "base_price": 72000, "market_cap": 28_000_000_000_000},
    "055550": {"name": "신한지주", "market": "KOSPI", "base_price": 45000, "market_cap": 23_000_000_000_000},
    # KOSDAQ 종목
    "247540": {"name": "에코프로비엠", "market": "KOSDAQ", "base_price": 280000, "market_cap": 20_000_000_000_000},
    "091990": {"name": "셀트리온헬스케어", "market": "KOSDAQ", "base_price": 75000, "market_cap": 10_000_000_000_000},
    "293490": {"name": "카카오게임즈", "market": "KOSDAQ", "base_price": 22000, "market_cap": 2_000_000_000_000},
    "263750": {"name": "펄어비스", "market": "KOSDAQ", "base_price": 48000, "market_cap": 2_500_000_000_000},
    "041510": {"name": "에스엠", "market": "KOSDAQ", "base_price": 120000, "market_cap": 3_000_000_000_000},
}


class MockBrokerClient(IBrokerClient):
    """Mock 브로커 클라이언트 구현"""

    def __init__(self, initial_balance: float = 50_000_000):
        self.initial_balance = initial_balance
        self.available_cash = initial_balance
        self.holdings: Dict[str, HoldingStock] = {}
        self.orders: Dict[str, OrderResult] = {}
        self._price_cache: Dict[str, float] = {}
        self._connected = False

    async def connect(self) -> bool:
        """연결 (Mock에서는 항상 성공)"""
        self._connected = True
        # 초기 가격 캐시 설정
        for code, info in MOCK_STOCKS.items():
            self._price_cache[code] = info["base_price"]
        return True

    async def disconnect(self) -> None:
        """연결 해제"""
        self._connected = False

    def _simulate_price_movement(self, stock_code: str) -> float:
        """가격 변동 시뮬레이션"""
        if stock_code not in self._price_cache:
            base = MOCK_STOCKS.get(stock_code, {}).get("base_price", 50000)
            self._price_cache[stock_code] = base

        current = self._price_cache[stock_code]
        # -0.5% ~ +0.5% 랜덤 변동
        change_pct = random.uniform(-0.005, 0.005)
        new_price = current * (1 + change_pct)
        # 호가 단위 맞춤
        new_price = self._round_to_tick(new_price)
        self._price_cache[stock_code] = new_price
        return new_price

    def _round_to_tick(self, price: float) -> float:
        """호가 단위로 반올림"""
        if price < 2000:
            return round(price)
        elif price < 5000:
            return round(price / 5) * 5
        elif price < 20000:
            return round(price / 10) * 10
        elif price < 50000:
            return round(price / 50) * 50
        elif price < 200000:
            return round(price / 100) * 100
        elif price < 500000:
            return round(price / 500) * 500
        else:
            return round(price / 1000) * 1000

    async def get_quote(self, stock_code: str) -> Quote:
        """현재가 조회"""
        if stock_code not in MOCK_STOCKS:
            raise ValueError(f"존재하지 않는 종목코드: {stock_code}")

        info = MOCK_STOCKS[stock_code]
        price = self._simulate_price_movement(stock_code)
        base_price = info["base_price"]
        prev_close = base_price * random.uniform(0.97, 1.03)
        prev_close = self._round_to_tick(prev_close)

        change = price - prev_close
        change_rate = (change / prev_close) * 100

        # 거래량 시뮬레이션 (시가총액에 따라 조정)
        avg_volume = int(info["market_cap"] / price / 100)
        volume = int(avg_volume * random.uniform(0.5, 3.0))

        # 당일 시가/고가/저가 시뮬레이션
        open_price = prev_close * random.uniform(0.99, 1.01)
        high = max(price, open_price) * random.uniform(1.0, 1.02)
        low = min(price, open_price) * random.uniform(0.98, 1.0)

        return Quote(
            stock_code=stock_code,
            name=info["name"],
            price=price,
            change=change,
            change_rate=round(change_rate, 2),
            volume=volume,
            trade_amount=int(volume * price),
            open=self._round_to_tick(open_price),
            high=self._round_to_tick(high),
            low=self._round_to_tick(low),
            prev_close=prev_close,
            timestamp=datetime.now()
        )

    async def get_quotes(self, stock_codes: List[str]) -> List[Quote]:
        """복수 종목 현재가 조회"""
        return [await self.get_quote(code) for code in stock_codes if code in MOCK_STOCKS]

    async def get_ohlcv(
        self,
        stock_code: str,
        period: str,
        count: int = 100
    ) -> List[OHLCV]:
        """OHLCV 데이터 조회"""
        if stock_code not in MOCK_STOCKS:
            raise ValueError(f"존재하지 않는 종목코드: {stock_code}")

        info = MOCK_STOCKS[stock_code]
        base_price = info["base_price"]

        # 기간에 따른 시간 간격 설정
        if period == "D":
            interval = timedelta(days=1)
        elif period == "W":
            interval = timedelta(weeks=1)
        elif period == "1":
            interval = timedelta(minutes=1)
        elif period == "5":
            interval = timedelta(minutes=5)
        elif period == "15":
            interval = timedelta(minutes=15)
        elif period == "30":
            interval = timedelta(minutes=30)
        elif period == "60":
            interval = timedelta(hours=1)
        else:
            interval = timedelta(days=1)

        # OHLCV 데이터 생성
        ohlcv_list = []
        current_time = datetime.now()
        current_price = base_price

        # 트렌드 시뮬레이션 (상승/하락/횡보)
        trend = random.choice([-1, 0, 1])
        trend_strength = random.uniform(0.0005, 0.002)

        for i in range(count):
            timestamp = current_time - (interval * (count - i - 1))

            # 가격 변동 시뮬레이션
            daily_change = random.uniform(-0.03, 0.03) + (trend * trend_strength)
            open_price = current_price
            close_price = open_price * (1 + daily_change)

            high = max(open_price, close_price) * random.uniform(1.0, 1.02)
            low = min(open_price, close_price) * random.uniform(0.98, 1.0)

            # 거래량 시뮬레이션
            avg_volume = int(info["market_cap"] / base_price / 100)
            volume = int(avg_volume * random.uniform(0.3, 2.5))

            ohlcv_list.append(OHLCV(
                timestamp=timestamp,
                open=self._round_to_tick(open_price),
                high=self._round_to_tick(high),
                low=self._round_to_tick(low),
                close=self._round_to_tick(close_price),
                volume=volume
            ))

            current_price = close_price

        return ohlcv_list

    async def get_orderbook(self, stock_code: str) -> OrderBook:
        """호가 조회"""
        if stock_code not in MOCK_STOCKS:
            raise ValueError(f"존재하지 않는 종목코드: {stock_code}")

        quote = await self.get_quote(stock_code)
        current_price = quote.price
        tick = self._get_tick_size(current_price)

        # 10단계 호가 생성
        ask_prices = []
        bid_prices = []
        ask_volumes = []
        bid_volumes = []

        base_volume = int(quote.volume / 100)

        for i in range(10):
            ask_prices.append(current_price + tick * (i + 1))
            bid_prices.append(current_price - tick * (i + 1))
            # 1호가에 가까울수록 잔량이 많음
            ask_volumes.append(int(base_volume * random.uniform(0.5, 2.0) * (10 - i) / 10))
            bid_volumes.append(int(base_volume * random.uniform(0.5, 2.0) * (10 - i) / 10))

        return OrderBook(
            stock_code=stock_code,
            ask_prices=ask_prices,
            ask_volumes=ask_volumes,
            bid_prices=bid_prices,
            bid_volumes=bid_volumes,
            total_ask_volume=sum(ask_volumes),
            total_bid_volume=sum(bid_volumes),
            timestamp=datetime.now()
        )

    def _get_tick_size(self, price: float) -> float:
        """호가 단위 반환"""
        if price < 2000:
            return 1
        elif price < 5000:
            return 5
        elif price < 20000:
            return 10
        elif price < 50000:
            return 50
        elif price < 200000:
            return 100
        elif price < 500000:
            return 500
        else:
            return 1000

    async def get_execution_data(self, stock_code: str) -> Dict:
        """체결 데이터 조회 (체결강도 계산용)"""
        if stock_code not in MOCK_STOCKS:
            raise ValueError(f"존재하지 않는 종목코드: {stock_code}")

        quote = await self.get_quote(stock_code)
        total_volume = quote.volume

        # 매수/매도 체결량 시뮬레이션
        # 상승세면 매수 비중 높음, 하락세면 매도 비중 높음
        if quote.change_rate > 1:
            buy_ratio = random.uniform(0.55, 0.70)
        elif quote.change_rate < -1:
            buy_ratio = random.uniform(0.30, 0.45)
        else:
            buy_ratio = random.uniform(0.45, 0.55)

        buy_volume = int(total_volume * buy_ratio)
        sell_volume = total_volume - buy_volume

        return {
            "stock_code": stock_code,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "total_volume": total_volume,
            "strength": round((buy_volume / sell_volume * 100) if sell_volume > 0 else 999.99, 2),
            "timestamp": datetime.now()
        }

    async def get_balance(self) -> Balance:
        """잔고 조회"""
        total_purchase = 0
        total_evaluation = 0

        for holding in self.holdings.values():
            total_purchase += holding.avg_price * holding.quantity
            current_price = self._price_cache.get(holding.stock_code, holding.avg_price)
            holding.current_price = current_price
            holding.evaluation = current_price * holding.quantity
            holding.pnl = holding.evaluation - (holding.avg_price * holding.quantity)
            holding.pnl_rate = (holding.pnl / (holding.avg_price * holding.quantity)) * 100 if holding.avg_price > 0 else 0
            total_evaluation += holding.evaluation

        total_pnl = total_evaluation - total_purchase
        total_asset = self.available_cash + total_evaluation

        return Balance(
            total_asset=total_asset,
            available_cash=self.available_cash,
            total_purchase=total_purchase,
            total_evaluation=total_evaluation,
            total_pnl=total_pnl,
            total_pnl_rate=(total_pnl / total_purchase * 100) if total_purchase > 0 else 0
        )

    async def get_positions(self) -> List[HoldingStock]:
        """보유 종목 조회"""
        # 현재가 업데이트
        for holding in self.holdings.values():
            current_price = self._price_cache.get(holding.stock_code, holding.avg_price)
            holding.current_price = current_price
            holding.evaluation = current_price * holding.quantity
            holding.pnl = holding.evaluation - (holding.avg_price * holding.quantity)
            holding.pnl_rate = (holding.pnl / (holding.avg_price * holding.quantity)) * 100

        return list(self.holdings.values())

    async def place_order(
        self,
        stock_code: str,
        order_side: OrderSide,
        order_type: OrderType,
        quantity: int,
        price: Optional[float] = None
    ) -> OrderResult:
        """주문 실행"""
        if stock_code not in MOCK_STOCKS:
            raise ValueError(f"존재하지 않는 종목코드: {stock_code}")

        quote = await self.get_quote(stock_code)
        executed_price = price if order_type == OrderType.LIMIT else quote.price

        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"

        if order_side == OrderSide.BUY:
            required_amount = executed_price * quantity
            if required_amount > self.available_cash:
                return OrderResult(
                    order_id=order_id,
                    stock_code=stock_code,
                    order_side=order_side,
                    order_type=order_type,
                    order_price=executed_price,
                    order_qty=quantity,
                    executed_price=None,
                    executed_qty=0,
                    status="REJECTED",
                    message="잔고 부족"
                )

            # 매수 체결
            self.available_cash -= required_amount

            if stock_code in self.holdings:
                # 기존 보유 종목 추가 매수
                holding = self.holdings[stock_code]
                total_qty = holding.quantity + quantity
                total_cost = (holding.avg_price * holding.quantity) + (executed_price * quantity)
                holding.avg_price = total_cost / total_qty
                holding.quantity = total_qty
            else:
                # 신규 매수
                self.holdings[stock_code] = HoldingStock(
                    stock_code=stock_code,
                    stock_name=MOCK_STOCKS[stock_code]["name"],
                    quantity=quantity,
                    avg_price=executed_price,
                    current_price=executed_price,
                    evaluation=executed_price * quantity,
                    pnl=0,
                    pnl_rate=0
                )

            status = "FILLED"
            message = "체결 완료"

        else:  # SELL
            if stock_code not in self.holdings:
                return OrderResult(
                    order_id=order_id,
                    stock_code=stock_code,
                    order_side=order_side,
                    order_type=order_type,
                    order_price=executed_price,
                    order_qty=quantity,
                    executed_price=None,
                    executed_qty=0,
                    status="REJECTED",
                    message="보유 종목 없음"
                )

            holding = self.holdings[stock_code]
            if holding.quantity < quantity:
                return OrderResult(
                    order_id=order_id,
                    stock_code=stock_code,
                    order_side=order_side,
                    order_type=order_type,
                    order_price=executed_price,
                    order_qty=quantity,
                    executed_price=None,
                    executed_qty=0,
                    status="REJECTED",
                    message="보유 수량 부족"
                )

            # 매도 체결
            self.available_cash += executed_price * quantity
            holding.quantity -= quantity

            if holding.quantity == 0:
                del self.holdings[stock_code]

            status = "FILLED"
            message = "체결 완료"

        result = OrderResult(
            order_id=order_id,
            stock_code=stock_code,
            order_side=order_side,
            order_type=order_type,
            order_price=executed_price,
            order_qty=quantity,
            executed_price=executed_price,
            executed_qty=quantity,
            status=status,
            message=message
        )

        self.orders[order_id] = result
        return result

    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소 (Mock에서는 항상 실패 - 이미 체결됨)"""
        return False

    async def get_stock_list(self, market: str = None) -> List[Dict]:
        """종목 리스트 조회"""
        stocks = []
        for code, info in MOCK_STOCKS.items():
            if market is None or info["market"] == market:
                stocks.append({
                    "code": code,
                    "name": info["name"],
                    "market": info["market"],
                    "market_cap": info["market_cap"]
                })
        return stocks
