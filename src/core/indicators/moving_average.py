"""
이동평균선 지표 계산기
"""
from typing import Dict, List
import numpy as np
from .base import IIndicator, OHLCV


class MovingAverageIndicator(IIndicator):
    """이동평균선 지표"""

    def __init__(self, periods: List[int] = None):
        self.periods = periods or [5, 20, 60, 120]

    @property
    def name(self) -> str:
        return "ma"

    def calculate(self, data: List[OHLCV]) -> Dict:
        """
        이동평균선 계산

        Returns:
            {
                'ma5': float,
                'ma20': float,
                'ma60': float,
                'ma120': float,
                'current_price': float,
                'arrangement': str,    # 'golden', 'partial', 'dead'
                'cross_signal': str,   # 'golden_cross', 'dead_cross', 'none'
                'above_ma5': bool,
                'above_ma20': bool,
                'above_ma60': bool,
                'above_ma120': bool
            }
        """
        if not data:
            return self._empty_result()

        closes = [d.close for d in data]
        current_price = closes[-1]
        result = {'current_price': current_price}

        # 각 기간별 이동평균 계산
        for period in self.periods:
            if len(closes) >= period:
                ma = np.mean(closes[-period:])
                result[f'ma{period}'] = round(ma, 2)
                result[f'above_ma{period}'] = current_price >= ma
            else:
                result[f'ma{period}'] = None
                result[f'above_ma{period}'] = None

        # 배열 판단 (정배열/역배열/혼조)
        ma5 = result.get('ma5')
        ma20 = result.get('ma20')
        ma60 = result.get('ma60')

        if ma5 and ma20 and ma60:
            if ma5 > ma20 > ma60:
                result['arrangement'] = 'golden'
            elif ma5 < ma20 < ma60:
                result['arrangement'] = 'dead'
            else:
                result['arrangement'] = 'partial'
        else:
            result['arrangement'] = None

        # 크로스 신호 (5MA, 20MA 기준)
        if len(closes) >= 21:
            prev_ma5 = np.mean(closes[-6:-1])
            prev_ma20 = np.mean(closes[-21:-1])

            if ma5 and ma20:
                if prev_ma5 <= prev_ma20 and ma5 > ma20:
                    result['cross_signal'] = 'golden_cross'
                elif prev_ma5 >= prev_ma20 and ma5 < ma20:
                    result['cross_signal'] = 'dead_cross'
                else:
                    result['cross_signal'] = 'none'
            else:
                result['cross_signal'] = None
        else:
            result['cross_signal'] = None

        return result

    def _empty_result(self) -> Dict:
        result = {'current_price': 0, 'arrangement': None, 'cross_signal': None}
        for period in self.periods:
            result[f'ma{period}'] = None
            result[f'above_ma{period}'] = None
        return result
