"""
OBV (On-Balance Volume) 지표 계산기
"""
from typing import Dict, List
from .base import IIndicator, OHLCV


class OBVIndicator(IIndicator):
    """OBV 지표"""

    @property
    def name(self) -> str:
        return "obv"

    def calculate(self, data: List[OHLCV]) -> Dict:
        """
        OBV 계산

        Returns:
            {
                'obv': float,          # OBV 값
                'obv_trend': str,      # 'up', 'down', 'flat'
                'obv_new_high': bool,  # 신고가 여부
                'obv_divergence': str  # 'bullish', 'bearish', 'none'
            }
        """
        if len(data) < 2:
            return {
                'obv': 0,
                'obv_trend': 'flat',
                'obv_new_high': False,
                'obv_divergence': 'none'
            }

        # OBV 계산
        obv = [0]
        for i in range(1, len(data)):
            if data[i].close > data[i-1].close:
                obv.append(obv[-1] + data[i].volume)
            elif data[i].close < data[i-1].close:
                obv.append(obv[-1] - data[i].volume)
            else:
                obv.append(obv[-1])

        current_obv = obv[-1]

        # 추세 판단 (최근 5일)
        if len(obv) >= 5:
            recent_obv = obv[-5:]
            if all(recent_obv[i] < recent_obv[i+1] for i in range(len(recent_obv)-1)):
                obv_trend = 'up'
            elif all(recent_obv[i] > recent_obv[i+1] for i in range(len(recent_obv)-1)):
                obv_trend = 'down'
            else:
                obv_trend = 'flat'
        else:
            obv_trend = 'flat'

        # 신고가 여부 (최근 20일 기준)
        lookback = min(20, len(obv))
        max_obv = max(obv[-lookback:])
        obv_new_high = current_obv >= max_obv

        # 다이버전스 판단
        obv_divergence = self._check_divergence(data, obv)

        return {
            'obv': current_obv,
            'obv_trend': obv_trend,
            'obv_new_high': obv_new_high,
            'obv_divergence': obv_divergence
        }

    def _check_divergence(self, data: List[OHLCV], obv: List[float]) -> str:
        """다이버전스 확인"""
        if len(data) < 10:
            return 'none'

        # 최근 10일 데이터로 간단한 다이버전스 판단
        recent_prices = [d.close for d in data[-10:]]
        recent_obv = obv[-10:]

        price_change = recent_prices[-1] - recent_prices[0]
        obv_change = recent_obv[-1] - recent_obv[0]

        # 상승 다이버전스: 가격 하락, OBV 상승
        if price_change < 0 and obv_change > 0:
            return 'bullish'
        # 하락 다이버전스: 가격 상승, OBV 하락
        elif price_change > 0 and obv_change < 0:
            return 'bearish'
        else:
            return 'none'
