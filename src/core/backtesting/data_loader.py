"""
백테스팅 데이터 로더
- OHLCV 데이터 로드
- 데이터 전처리
- 캐싱
"""
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import os


@dataclass
class OHLCVData:
    """OHLCV 데이터"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    value: int = 0  # 거래대금
    change: float = 0  # 전일대비
    change_rate: float = 0  # 등락률


@dataclass
class TickData:
    """틱 데이터 (분봉/초봉)"""
    timestamp: datetime
    price: float
    volume: int
    bid_price: float = 0
    ask_price: float = 0
    bid_volume: int = 0
    ask_volume: int = 0


@dataclass
class StockData:
    """종목 데이터"""
    stock_code: str
    stock_name: str
    ohlcv: List[OHLCVData] = field(default_factory=list)
    ticks: List[TickData] = field(default_factory=list)


class BacktestDataLoader:
    """백테스트 데이터 로더"""

    def __init__(self, data_dir: str = "./data/backtest"):
        self.data_dir = data_dir
        self._cache: Dict[str, StockData] = {}
        os.makedirs(data_dir, exist_ok=True)

    def load_ohlcv(
        self,
        stock_code: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"  # 1m, 5m, 15m, 30m, 1h, 1d
    ) -> List[OHLCVData]:
        """OHLCV 데이터 로드"""
        cache_key = f"{stock_code}_{timeframe}"

        # 캐시 확인
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return self._filter_by_date(cached.ohlcv, start_date, end_date)

        # 파일에서 로드
        file_path = os.path.join(
            self.data_dir,
            f"{stock_code}_{timeframe}.json"
        )

        if os.path.exists(file_path):
            data = self._load_from_file(file_path)
            self._cache[cache_key] = StockData(
                stock_code=stock_code,
                stock_name="",
                ohlcv=data
            )
            return self._filter_by_date(data, start_date, end_date)

        # 데이터 없으면 빈 리스트
        return []

    def _load_from_file(self, file_path: str) -> List[OHLCVData]:
        """파일에서 데이터 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            ohlcv_list = []
            for item in raw_data:
                ohlcv = OHLCVData(
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    open=float(item['open']),
                    high=float(item['high']),
                    low=float(item['low']),
                    close=float(item['close']),
                    volume=int(item['volume']),
                    value=int(item.get('value', 0)),
                    change=float(item.get('change', 0)),
                    change_rate=float(item.get('change_rate', 0))
                )
                ohlcv_list.append(ohlcv)

            return ohlcv_list
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            return []

    def save_ohlcv(
        self,
        stock_code: str,
        data: List[OHLCVData],
        timeframe: str = "1d"
    ):
        """OHLCV 데이터 저장"""
        file_path = os.path.join(
            self.data_dir,
            f"{stock_code}_{timeframe}.json"
        )

        raw_data = []
        for ohlcv in data:
            raw_data.append({
                'timestamp': ohlcv.timestamp.isoformat(),
                'open': ohlcv.open,
                'high': ohlcv.high,
                'low': ohlcv.low,
                'close': ohlcv.close,
                'volume': ohlcv.volume,
                'value': ohlcv.value,
                'change': ohlcv.change,
                'change_rate': ohlcv.change_rate
            })

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)

        # 캐시 업데이트
        cache_key = f"{stock_code}_{timeframe}"
        self._cache[cache_key] = StockData(
            stock_code=stock_code,
            stock_name="",
            ohlcv=data
        )

    def _filter_by_date(
        self,
        data: List[OHLCVData],
        start_date: datetime,
        end_date: datetime
    ) -> List[OHLCVData]:
        """날짜 범위로 필터링"""
        return [
            d for d in data
            if start_date <= d.timestamp <= end_date
        ]

    def generate_mock_data(
        self,
        stock_code: str,
        stock_name: str,
        start_date: datetime,
        end_date: datetime,
        initial_price: float = 50000,
        volatility: float = 0.02,
        trend: float = 0.0001
    ) -> List[OHLCVData]:
        """모의 데이터 생성 (테스트용)"""
        import random

        data = []
        current_price = initial_price
        current_date = start_date

        while current_date <= end_date:
            # 주말 제외
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            # 랜덤 변동
            daily_return = random.gauss(trend, volatility)
            open_price = current_price
            close_price = current_price * (1 + daily_return)

            # 고가/저가
            high_price = max(open_price, close_price) * (1 + random.uniform(0, volatility))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, volatility))

            # 거래량
            base_volume = random.randint(100000, 1000000)
            volume = int(base_volume * (1 + abs(daily_return) * 10))

            change = close_price - open_price
            change_rate = (close_price / open_price - 1) * 100

            ohlcv = OHLCVData(
                timestamp=current_date,
                open=round(open_price),
                high=round(high_price),
                low=round(low_price),
                close=round(close_price),
                volume=volume,
                value=int(volume * close_price),
                change=round(change),
                change_rate=round(change_rate, 2)
            )
            data.append(ohlcv)

            current_price = close_price
            current_date += timedelta(days=1)

        return data

    def generate_intraday_mock_data(
        self,
        stock_code: str,
        date: datetime,
        initial_price: float = 50000,
        volatility: float = 0.005
    ) -> List[TickData]:
        """장중 모의 데이터 생성 (1분봉)"""
        import random

        data = []
        current_price = initial_price
        current_time = date.replace(hour=9, minute=0, second=0)
        end_time = date.replace(hour=15, minute=30, second=0)

        while current_time <= end_time:
            # 1분마다 데이터 생성
            price_change = random.gauss(0, volatility)
            current_price = current_price * (1 + price_change)

            volume = random.randint(100, 10000)
            spread = current_price * 0.001

            tick = TickData(
                timestamp=current_time,
                price=round(current_price),
                volume=volume,
                bid_price=round(current_price - spread / 2),
                ask_price=round(current_price + spread / 2),
                bid_volume=random.randint(1000, 50000),
                ask_volume=random.randint(1000, 50000)
            )
            data.append(tick)

            current_time += timedelta(minutes=1)

        return data

    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()

    def get_available_stocks(self) -> List[str]:
        """저장된 종목 목록 조회"""
        stocks = set()
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json'):
                stock_code = filename.split('_')[0]
                stocks.add(stock_code)
        return list(stocks)

    def get_date_range(self, stock_code: str, timeframe: str = "1d") -> Optional[tuple]:
        """데이터 날짜 범위 조회"""
        data = self.load_ohlcv(
            stock_code,
            datetime(1900, 1, 1),
            datetime(2100, 1, 1),
            timeframe
        )
        if not data:
            return None

        return (data[0].timestamp, data[-1].timestamp)
