"""
MACD (Moving Average Convergence Divergence) 지표 계산기
"""
from typing import Dict, List
from .base import IIndicator, OHLCV


class MACDIndicator(IIndicator):
    """MACD 지표"""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal_period = signal

    @property
    def name(self) -> str:
        return "macd"

    def calculate(self, data: List[OHLCV]) -> Dict:
        """
        MACD 계산

        Returns:
            {
                'macd': float,         # MACD 값
                'signal': float,       # Signal 선
                'histogram': float,    # 히스토그램
                'prev_histogram': float,
                'cross_signal': str    # 'golden_cross', 'dead_cross', 'none'
            }
        """
        if len(data) < self.slow + self.signal_period:
            return {
                'macd': 0,
                'signal': 0,
                'histogram': 0,
                'prev_histogram': 0,
                'cross_signal': 'none'
            }

        closes = [d.close for d in data]

        # EMA 계산
        ema_fast = self._ema(closes, self.fast)
        ema_slow = self._ema(closes, self.slow)

        # MACD 라인
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]

        # Signal 라인
        signal_line = self._ema(macd_line, self.signal_period)

        # 히스토그램
        histogram = [m - s for m, s in zip(macd_line, signal_line)]

        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        current_histogram = histogram[-1]
        prev_histogram = histogram[-2] if len(histogram) > 1 else 0

        # 크로스 신호
        if prev_histogram < 0 and current_histogram > 0:
            cross_signal = 'golden_cross'
        elif prev_histogram > 0 and current_histogram < 0:
            cross_signal = 'dead_cross'
        else:
            cross_signal = 'none'

        return {
            'macd': round(current_macd, 2),
            'signal': round(current_signal, 2),
            'histogram': round(current_histogram, 2),
            'prev_histogram': round(prev_histogram, 2),
            'cross_signal': cross_signal
        }

    def _ema(self, data: List[float], period: int) -> List[float]:
        """지수이동평균 계산"""
        if len(data) < period:
            return [0] * len(data)

        ema = [sum(data[:period]) / period]
        multiplier = 2 / (period + 1)

        for price in data[period:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])

        # 앞부분 패딩
        return [0] * (period - 1) + ema
