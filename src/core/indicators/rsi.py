"""
RSI (Relative Strength Index) 지표 계산기
"""
from typing import Dict, List
import numpy as np
from .base import IIndicator, OHLCV


class RSIIndicator(IIndicator):
    """RSI 지표"""

    def __init__(self, period: int = 14):
        self.period = period

    @property
    def name(self) -> str:
        return "rsi"

    def calculate(self, data: List[OHLCV]) -> Dict:
        """
        RSI 계산

        Returns:
            {
                'rsi': float,          # RSI 값 (0-100)
                'rsi_status': str,     # 'overbought', 'oversold', 'neutral'
                'rsi_trend': str       # 'rising', 'falling', 'stable'
            }
        """
        if len(data) < self.period + 1:
            return {
                'rsi': 50,
                'rsi_status': 'neutral',
                'rsi_trend': 'stable'
            }

        closes = [d.close for d in data]

        # 가격 변화 계산
        changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]

        gains = [c if c > 0 else 0 for c in changes]
        losses = [-c if c < 0 else 0 for c in changes]

        # Wilder's smoothing을 사용한 평균 계산
        avg_gain = self._wilder_smooth(gains[-self.period:])
        avg_loss = self._wilder_smooth(losses[-self.period:])

        # RSI 계산
        if avg_loss == 0:
            rsi = 100
        elif avg_gain == 0:
            rsi = 0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # 상태 판단
        if rsi >= 70:
            rsi_status = 'overbought'
        elif rsi <= 30:
            rsi_status = 'oversold'
        else:
            rsi_status = 'neutral'

        # RSI 추세 판단 (최근 5개 RSI 비교)
        if len(changes) >= self.period + 5:
            recent_rsis = []
            for i in range(5):
                idx = -(5 - i)
                g = gains[idx - self.period:idx] if idx != 0 else gains[-self.period:]
                l = losses[idx - self.period:idx] if idx != 0 else losses[-self.period:]
                ag = self._wilder_smooth(g)
                al = self._wilder_smooth(l)
                if al == 0:
                    recent_rsis.append(100)
                elif ag == 0:
                    recent_rsis.append(0)
                else:
                    recent_rsis.append(100 - (100 / (1 + ag / al)))

            if len(recent_rsis) >= 3:
                if recent_rsis[-1] > recent_rsis[-3]:
                    rsi_trend = 'rising'
                elif recent_rsis[-1] < recent_rsis[-3]:
                    rsi_trend = 'falling'
                else:
                    rsi_trend = 'stable'
            else:
                rsi_trend = 'stable'
        else:
            rsi_trend = 'stable'

        return {
            'rsi': round(rsi, 2),
            'rsi_status': rsi_status,
            'rsi_trend': rsi_trend
        }

    def _wilder_smooth(self, values: List[float]) -> float:
        """Wilder's smoothing 방식 평균 계산"""
        if not values:
            return 0
        return np.mean(values)
