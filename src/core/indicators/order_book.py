"""
호가/체결강도 지표 계산기
"""
from typing import Dict
from .base import IIndicator


class OrderBookIndicator(IIndicator):
    """호가/체결강도 지표"""

    @property
    def name(self) -> str:
        return "order_book"

    def calculate(self, data: Dict) -> Dict:
        """
        체결강도 계산

        Input:
            {
                'buy_volume': int,     # 매수 체결량
                'sell_volume': int     # 매도 체결량
            }

        Returns:
            {
                'strength': float,     # 체결강도 (%)
                'pressure': str,       # 'buy', 'sell', 'neutral'
                'buy_volume': int,
                'sell_volume': int
            }
        """
        buy_vol = data.get('buy_volume', 0)
        sell_vol = data.get('sell_volume', 0)

        # 체결강도 계산
        if sell_vol == 0:
            strength = 999.99 if buy_vol > 0 else 100.0
        else:
            strength = (buy_vol / sell_vol) * 100

        # 매수/매도 압력 판단
        if strength >= 120:
            pressure = 'buy'
        elif strength <= 80:
            pressure = 'sell'
        else:
            pressure = 'neutral'

        return {
            'strength': round(strength, 2),
            'pressure': pressure,
            'buy_volume': buy_vol,
            'sell_volume': sell_vol
        }


class OrderBookDepthIndicator:
    """호가창 분석 지표"""

    def calculate(self, orderbook: Dict) -> Dict:
        """
        호가창 분석

        Input:
            {
                'ask_volumes': List[int],   # 매도 잔량 (10단계)
                'bid_volumes': List[int],   # 매수 잔량 (10단계)
                'total_ask_volume': int,
                'total_bid_volume': int
            }

        Returns:
            {
                'bid_ask_ratio': float,     # 매수/매도 잔량 비율
                'imbalance': str,           # 'buy_heavy', 'sell_heavy', 'balanced'
                'wall_detected': bool,      # 매물벽 감지
                'wall_side': str            # 'ask', 'bid', 'none'
            }
        """
        total_ask = orderbook.get('total_ask_volume', 0)
        total_bid = orderbook.get('total_bid_volume', 0)
        ask_volumes = orderbook.get('ask_volumes', [])
        bid_volumes = orderbook.get('bid_volumes', [])

        # 매수/매도 잔량 비율
        if total_ask == 0:
            bid_ask_ratio = 999.99 if total_bid > 0 else 1.0
        else:
            bid_ask_ratio = total_bid / total_ask

        # 불균형 판단
        if bid_ask_ratio >= 1.3:
            imbalance = 'buy_heavy'
        elif bid_ask_ratio <= 0.7:
            imbalance = 'sell_heavy'
        else:
            imbalance = 'balanced'

        # 매물벽 감지 (특정 호가에 평균의 3배 이상 잔량)
        wall_detected = False
        wall_side = 'none'

        if ask_volumes:
            avg_ask = sum(ask_volumes) / len(ask_volumes)
            if any(v > avg_ask * 3 for v in ask_volumes):
                wall_detected = True
                wall_side = 'ask'

        if bid_volumes and not wall_detected:
            avg_bid = sum(bid_volumes) / len(bid_volumes)
            if any(v > avg_bid * 3 for v in bid_volumes):
                wall_detected = True
                wall_side = 'bid'

        return {
            'bid_ask_ratio': round(bid_ask_ratio, 2),
            'imbalance': imbalance,
            'wall_detected': wall_detected,
            'wall_side': wall_side
        }
