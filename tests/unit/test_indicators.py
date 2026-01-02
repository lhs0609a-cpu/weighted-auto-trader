"""
지표 모듈 단위 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.core.indicators import (
    VolumeIndicator,
    VWAPIndicator,
    RSIIndicator,
    MACDIndicator,
    MovingAverageIndicator,
    BollingerBandsIndicator,
    OBVIndicator,
    OrderBookIndicator
)


class TestVolumeIndicator:
    """거래량 지표 테스트"""

    def setup_method(self):
        self.indicator = VolumeIndicator()

    @pytest.mark.asyncio
    async def test_volume_ratio_calculation(self):
        """거래량 비율 계산 테스트"""
        market_data = {
            'volume': 1000000,
            'avg_volume_5d': 500000,
            'avg_volume_20d': 400000
        }

        result = await self.indicator.calculate(market_data)

        assert 'volume_ratio' in result
        assert result['volume_ratio'] == 200  # 1000000 / 500000 * 100
        assert 'signal' in result

    @pytest.mark.asyncio
    async def test_high_volume_bullish_signal(self):
        """높은 거래량 강세 신호 테스트"""
        market_data = {
            'volume': 1500000,
            'avg_volume_5d': 500000,
            'avg_volume_20d': 400000
        }

        result = await self.indicator.calculate(market_data)

        assert result['signal'] == 'bullish'
        assert result['score'] >= 70

    @pytest.mark.asyncio
    async def test_low_volume_neutral_signal(self):
        """낮은 거래량 중립 신호 테스트"""
        market_data = {
            'volume': 400000,
            'avg_volume_5d': 500000,
            'avg_volume_20d': 400000
        }

        result = await self.indicator.calculate(market_data)

        assert result['signal'] in ['neutral', 'bearish']
        assert result['score'] <= 60


class TestRSIIndicator:
    """RSI 지표 테스트"""

    def setup_method(self):
        self.indicator = RSIIndicator()

    @pytest.mark.asyncio
    async def test_rsi_oversold(self):
        """과매도 구간 테스트"""
        market_data = {
            'prices': [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86]
        }

        result = await self.indicator.calculate(market_data)

        assert 'rsi' in result
        # 지속 하락이면 RSI가 낮아야 함
        assert result['rsi'] < 40

    @pytest.mark.asyncio
    async def test_rsi_overbought(self):
        """과매수 구간 테스트"""
        market_data = {
            'prices': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
        }

        result = await self.indicator.calculate(market_data)

        assert 'rsi' in result
        # 지속 상승이면 RSI가 높아야 함
        assert result['rsi'] > 60

    @pytest.mark.asyncio
    async def test_rsi_neutral(self):
        """중립 구간 테스트"""
        market_data = {
            'prices': [100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100]
        }

        result = await self.indicator.calculate(market_data)

        assert 'rsi' in result
        assert 40 <= result['rsi'] <= 60


class TestMACDIndicator:
    """MACD 지표 테스트"""

    def setup_method(self):
        self.indicator = MACDIndicator()

    @pytest.mark.asyncio
    async def test_macd_bullish_crossover(self):
        """MACD 골든크로스 테스트"""
        # 상승 추세 가격 데이터
        prices = [100 + i * 0.5 for i in range(30)]
        market_data = {'prices': prices}

        result = await self.indicator.calculate(market_data)

        assert 'macd' in result
        assert 'signal_line' in result
        assert 'histogram' in result

    @pytest.mark.asyncio
    async def test_macd_bearish_crossover(self):
        """MACD 데드크로스 테스트"""
        # 하락 추세 가격 데이터
        prices = [100 - i * 0.5 for i in range(30)]
        market_data = {'prices': prices}

        result = await self.indicator.calculate(market_data)

        assert 'macd' in result
        assert 'signal_line' in result


class TestVWAPIndicator:
    """VWAP 지표 테스트"""

    def setup_method(self):
        self.indicator = VWAPIndicator()

    @pytest.mark.asyncio
    async def test_price_above_vwap(self):
        """가격이 VWAP 위에 있을 때 테스트"""
        market_data = {
            'current_price': 110,
            'vwap': 100,
            'typical_prices': [100, 101, 102, 103, 105],
            'volumes': [1000, 1100, 1200, 1300, 1500]
        }

        result = await self.indicator.calculate(market_data)

        assert result['signal'] == 'bullish'
        assert result['position'] == 'above'

    @pytest.mark.asyncio
    async def test_price_below_vwap(self):
        """가격이 VWAP 아래에 있을 때 테스트"""
        market_data = {
            'current_price': 90,
            'vwap': 100,
            'typical_prices': [100, 99, 98, 97, 95],
            'volumes': [1000, 1100, 1200, 1300, 1500]
        }

        result = await self.indicator.calculate(market_data)

        assert result['signal'] == 'bearish'
        assert result['position'] == 'below'


class TestBollingerBandsIndicator:
    """볼린저 밴드 지표 테스트"""

    def setup_method(self):
        self.indicator = BollingerBandsIndicator()

    @pytest.mark.asyncio
    async def test_price_near_upper_band(self):
        """가격이 상단밴드 근처일 때 테스트"""
        market_data = {
            'current_price': 115,
            'prices': [100] * 20,  # 평균 100
            'upper_band': 120,
            'middle_band': 100,
            'lower_band': 80
        }

        result = await self.indicator.calculate(market_data)

        assert 'band_position' in result
        assert result['band_position'] > 0.7

    @pytest.mark.asyncio
    async def test_price_near_lower_band(self):
        """가격이 하단밴드 근처일 때 테스트"""
        market_data = {
            'current_price': 85,
            'prices': [100] * 20,
            'upper_band': 120,
            'middle_band': 100,
            'lower_band': 80
        }

        result = await self.indicator.calculate(market_data)

        assert 'band_position' in result
        assert result['band_position'] < 0.3


class TestOrderBookIndicator:
    """호가창 지표 테스트"""

    def setup_method(self):
        self.indicator = OrderBookIndicator()

    @pytest.mark.asyncio
    async def test_strong_bid_pressure(self):
        """강한 매수 압력 테스트"""
        market_data = {
            'bid_volume': 150000,
            'ask_volume': 100000,
            'total_bid_orders': 500,
            'total_ask_orders': 300
        }

        result = await self.indicator.calculate(market_data)

        assert result['signal'] == 'bullish'
        assert result['strength'] > 100

    @pytest.mark.asyncio
    async def test_strong_ask_pressure(self):
        """강한 매도 압력 테스트"""
        market_data = {
            'bid_volume': 100000,
            'ask_volume': 150000,
            'total_bid_orders': 300,
            'total_ask_orders': 500
        }

        result = await self.indicator.calculate(market_data)

        assert result['signal'] == 'bearish'
        assert result['strength'] < 100


class TestOBVIndicator:
    """OBV 지표 테스트"""

    def setup_method(self):
        self.indicator = OBVIndicator()

    @pytest.mark.asyncio
    async def test_obv_increasing(self):
        """OBV 상승 테스트"""
        market_data = {
            'prices': [100, 101, 102, 103, 104],
            'volumes': [1000, 1100, 1200, 1300, 1400]
        }

        result = await self.indicator.calculate(market_data)

        assert 'obv' in result
        assert 'trend' in result
        # 가격 상승 + 거래량 증가 = OBV 상승
        assert result['trend'] == 'increasing'

    @pytest.mark.asyncio
    async def test_obv_decreasing(self):
        """OBV 하락 테스트"""
        market_data = {
            'prices': [104, 103, 102, 101, 100],
            'volumes': [1000, 1100, 1200, 1300, 1400]
        }

        result = await self.indicator.calculate(market_data)

        assert 'obv' in result
        # 가격 하락 + 거래량 증가 = OBV 하락
        assert result['trend'] == 'decreasing'


class TestMovingAverageIndicator:
    """이동평균 지표 테스트"""

    def setup_method(self):
        self.indicator = MovingAverageIndicator()

    @pytest.mark.asyncio
    async def test_golden_cross(self):
        """골든크로스 테스트"""
        market_data = {
            'current_price': 110,
            'ma_5': 108,
            'ma_20': 100,
            'ma_60': 95
        }

        result = await self.indicator.calculate(market_data)

        assert result['signal'] == 'bullish'
        assert 'golden_cross' in result

    @pytest.mark.asyncio
    async def test_death_cross(self):
        """데드크로스 테스트"""
        market_data = {
            'current_price': 90,
            'ma_5': 92,
            'ma_20': 100,
            'ma_60': 105
        }

        result = await self.indicator.calculate(market_data)

        assert result['signal'] == 'bearish'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
