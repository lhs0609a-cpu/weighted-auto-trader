"""
볼린저밴드 지표 계산기
"""
from typing import Dict, List
import numpy as np
from .base import IIndicator, OHLCV


class BollingerBandIndicator(IIndicator):
    """볼린저밴드 지표"""

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev

    @property
    def name(self) -> str:
        return "bollinger"

    def calculate(self, data: List[OHLCV]) -> Dict:
        """
        볼린저밴드 계산

        Returns:
            {
                'upper': float,        # 상단 밴드
                'middle': float,       # 중심선 (20MA)
                'lower': float,        # 하단 밴드
                'bandwidth': float,    # 밴드폭
                'prev_bandwidth': float,
                'position': str,       # 'upper', 'middle', 'lower'
                'squeeze': bool        # 스퀴즈 여부
            }
        """
        if len(data) < self.period:
            return {
                'upper': 0,
                'middle': 0,
                'lower': 0,
                'bandwidth': 0,
                'prev_bandwidth': 0,
                'position': 'middle',
                'squeeze': False
            }

        closes = [d.close for d in data]

        # 중심선 (SMA)
        middle = np.mean(closes[-self.period:])

        # 표준편차
        std = np.std(closes[-self.period:])

        # 상단/하단 밴드
        upper = middle + (self.std_dev * std)
        lower = middle - (self.std_dev * std)

        # 밴드폭
        bandwidth = upper - lower

        # 이전 밴드폭 계산
        if len(closes) > self.period:
            prev_closes = closes[-self.period-1:-1]
            prev_middle = np.mean(prev_closes)
            prev_std = np.std(prev_closes)
            prev_upper = prev_middle + (self.std_dev * prev_std)
            prev_lower = prev_middle - (self.std_dev * prev_std)
            prev_bandwidth = prev_upper - prev_lower
        else:
            prev_bandwidth = bandwidth

        # 현재가 위치 판단
        current_price = closes[-1]
        band_range = upper - lower

        if band_range > 0:
            position_ratio = (current_price - lower) / band_range
            if position_ratio >= 0.8:
                position = 'upper'
            elif position_ratio <= 0.2:
                position = 'lower'
            else:
                position = 'middle'
        else:
            position = 'middle'

        # 스퀴즈 여부 (밴드폭 축소)
        squeeze = bandwidth < prev_bandwidth * 0.8 if prev_bandwidth > 0 else False

        return {
            'upper': round(upper, 2),
            'middle': round(middle, 2),
            'lower': round(lower, 2),
            'bandwidth': round(bandwidth, 2),
            'prev_bandwidth': round(prev_bandwidth, 2),
            'position': position,
            'squeeze': squeeze
        }
