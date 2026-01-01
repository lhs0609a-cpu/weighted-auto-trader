"""
거래량 지표 계산기
"""
from typing import Dict, List
import numpy as np
from .base import IIndicator, OHLCV


class VolumeIndicator(IIndicator):
    """거래량 지표"""

    def __init__(self, period: int = 20):
        self.period = period

    @property
    def name(self) -> str:
        return "volume"

    def calculate(self, data: List[OHLCV]) -> Dict:
        """
        거래량 관련 지표 계산

        Returns:
            {
                'current_volume': int,     # 현재 거래량
                'avg_volume': float,       # 평균 거래량
                'volume_ratio': float,     # 거래량 비율 (%)
                'is_volume_surge': bool,   # 거래량 급증 여부 (200% 이상)
                'volume_trend': str        # 'increasing', 'decreasing', 'stable'
            }
        """
        if len(data) < self.period:
            return {
                'current_volume': data[-1].volume if data else 0,
                'avg_volume': 0,
                'volume_ratio': 0,
                'is_volume_surge': False,
                'volume_trend': 'stable'
            }

        volumes = [d.volume for d in data]
        current_volume = volumes[-1]

        # 평균 거래량 (이전 period 기간)
        avg_volume = np.mean(volumes[-self.period-1:-1])

        # 거래량 비율
        volume_ratio = (current_volume / avg_volume * 100) if avg_volume > 0 else 0

        # 급등 여부
        is_volume_surge = volume_ratio >= 200

        # 추세 판단 (최근 5개)
        recent = volumes[-5:]
        if len(recent) >= 5:
            if all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
                volume_trend = 'increasing'
            elif all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
                volume_trend = 'decreasing'
            else:
                volume_trend = 'stable'
        else:
            volume_trend = 'stable'

        return {
            'current_volume': current_volume,
            'avg_volume': round(avg_volume, 0),
            'volume_ratio': round(volume_ratio, 2),
            'is_volume_surge': is_volume_surge,
            'volume_trend': volume_trend
        }
