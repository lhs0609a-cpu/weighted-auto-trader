"""
VWAP (거래량 가중평균가격) 지표 계산기
"""
from typing import Dict, List
from .base import IIndicator, OHLCV


class VWAPIndicator(IIndicator):
    """VWAP 지표"""

    @property
    def name(self) -> str:
        return "vwap"

    def calculate(self, data: List[OHLCV]) -> Dict:
        """
        VWAP 계산

        Returns:
            {
                'vwap': float,             # VWAP 값
                'price_vs_vwap': float,    # 현재가 대비 VWAP (%)
                'vwap_position': str       # 'above', 'at', 'below'
            }
        """
        if not data:
            return {
                'vwap': 0,
                'price_vs_vwap': 0,
                'vwap_position': 'at'
            }

        # Typical Price * Volume의 누적합
        cumulative_tp_vol = 0
        cumulative_vol = 0

        for d in data:
            typical_price = (d.high + d.low + d.close) / 3
            cumulative_tp_vol += typical_price * d.volume
            cumulative_vol += d.volume

        # VWAP 계산
        vwap = cumulative_tp_vol / cumulative_vol if cumulative_vol > 0 else 0

        # 현재가
        current_price = data[-1].close

        # 현재가 대비 VWAP 비율
        price_vs_vwap = ((current_price - vwap) / vwap * 100) if vwap > 0 else 0

        # 위치 판단
        if price_vs_vwap > 1:
            vwap_position = 'above'
        elif price_vs_vwap < -1:
            vwap_position = 'below'
        else:
            vwap_position = 'at'

        return {
            'vwap': round(vwap, 2),
            'current_price': current_price,
            'price_vs_vwap': round(price_vs_vwap, 2),
            'vwap_position': vwap_position
        }
