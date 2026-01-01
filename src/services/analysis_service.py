"""
분석 서비스
- 종목 분석
- 지표 계산
- 신호 생성
"""
from typing import Dict, List, Optional
from datetime import datetime

from ..config.constants import TradingStyle
from ..core.broker import IBrokerClient, OHLCV as BrokerOHLCV
from ..core.indicators import (
    OHLCV, VolumeIndicator, VWAPIndicator, MovingAverageIndicator,
    RSIIndicator, MACDIndicator, BollingerBandIndicator,
    OBVIndicator, OrderBookIndicator
)
from ..core.scoring import SignalGenerator, signal_to_dict


class AnalysisService:
    """분석 서비스"""

    def __init__(self, broker: IBrokerClient):
        self.broker = broker

        # 지표 계산기 초기화
        self.volume_indicator = VolumeIndicator(period=20)
        self.vwap_indicator = VWAPIndicator()
        self.ma_indicator = MovingAverageIndicator([5, 20, 60, 120])
        self.rsi_indicator = RSIIndicator(period=14)
        self.macd_indicator = MACDIndicator(fast=12, slow=26, signal=9)
        self.bollinger_indicator = BollingerBandIndicator(period=20, std_dev=2.0)
        self.obv_indicator = OBVIndicator()
        self.order_book_indicator = OrderBookIndicator()

    def _convert_ohlcv(self, broker_data: List[BrokerOHLCV]) -> List[OHLCV]:
        """브로커 OHLCV를 지표 OHLCV로 변환"""
        return [
            OHLCV(
                timestamp=str(d.timestamp),
                open=d.open,
                high=d.high,
                low=d.low,
                close=d.close,
                volume=d.volume
            )
            for d in broker_data
        ]

    async def analyze_stock(
        self,
        stock_code: str,
        trading_style: TradingStyle,
        period: str = "D"
    ) -> Dict:
        """
        종목 분석 수행

        Args:
            stock_code: 종목코드
            trading_style: 매매 스타일
            period: 봉 기간 (D, 1, 5, 15, 30, 60)

        Returns:
            분석 결과 딕셔너리
        """
        # 1. OHLCV 데이터 조회
        ohlcv_data = await self.broker.get_ohlcv(stock_code, period, count=150)
        ohlcv_list = self._convert_ohlcv(ohlcv_data)

        # 2. 현재가 조회
        quote = await self.broker.get_quote(stock_code)

        # 3. 체결 데이터 조회
        execution_data = await self.broker.get_execution_data(stock_code)

        # 4. 모든 지표 계산
        indicators = await self._calculate_all_indicators(ohlcv_list, execution_data)

        # 5. 신호 생성
        signal_generator = SignalGenerator(trading_style)
        signal_result = signal_generator.generate(indicators, quote.price)

        # 6. 결과 조합
        return {
            'stock_code': stock_code,
            'stock_name': quote.name,
            'current_price': quote.price,
            'change': quote.change,
            'change_rate': quote.change_rate,
            'volume': quote.volume,
            'trading_style': trading_style.value,
            'indicators': indicators,
            **signal_to_dict(signal_result),
            'timestamp': datetime.now().isoformat()
        }

    async def _calculate_all_indicators(
        self,
        ohlcv_list: List[OHLCV],
        execution_data: Dict
    ) -> Dict:
        """모든 지표 계산"""
        indicators = {}

        # 거래량
        indicators['volume'] = self.volume_indicator.calculate(ohlcv_list)

        # VWAP
        indicators['vwap'] = self.vwap_indicator.calculate(ohlcv_list)

        # 이동평균선
        indicators['ma'] = self.ma_indicator.calculate(ohlcv_list)

        # RSI
        indicators['rsi'] = self.rsi_indicator.calculate(ohlcv_list)

        # MACD
        indicators['macd'] = self.macd_indicator.calculate(ohlcv_list)

        # 볼린저밴드
        indicators['bollinger'] = self.bollinger_indicator.calculate(ohlcv_list)

        # OBV
        indicators['obv'] = self.obv_indicator.calculate(ohlcv_list)

        # 체결강도
        indicators['order_book'] = self.order_book_indicator.calculate(execution_data)

        return indicators

    async def get_stock_indicators(
        self,
        stock_code: str,
        period: str = "D"
    ) -> Dict:
        """종목 지표만 조회"""
        ohlcv_data = await self.broker.get_ohlcv(stock_code, period, count=150)
        ohlcv_list = self._convert_ohlcv(ohlcv_data)
        execution_data = await self.broker.get_execution_data(stock_code)

        return await self._calculate_all_indicators(ohlcv_list, execution_data)
