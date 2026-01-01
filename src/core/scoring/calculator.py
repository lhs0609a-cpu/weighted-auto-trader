"""
점수 계산기
- 각 지표별 점수 계산
- 스타일별 가중치 적용
"""
from typing import Dict, Tuple
from ...config.constants import (
    TradingStyle, WEIGHT_CONFIGS, WeightConfig,
    VOLUME_SCORE_THRESHOLDS, STRENGTH_SCORE_THRESHOLDS
)


class ScoreCalculator:
    """점수 계산기 구현"""

    def __init__(self, style: TradingStyle):
        self.style = style
        self.weights = WEIGHT_CONFIGS[style]

    def calc_volume_score(self, data: Dict) -> Tuple[float, str]:
        """거래량 점수"""
        ratio = data.get('volume_ratio', 0)
        max_score = self.weights.volume

        for threshold, multiplier in VOLUME_SCORE_THRESHOLDS:
            if ratio >= threshold:
                score = max_score * multiplier
                return score, f"거래량 {ratio:.0f}%"

        return 0, f"거래량 부족 {ratio:.0f}%"

    def calc_order_book_score(self, data: Dict) -> Tuple[float, str]:
        """체결강도 점수"""
        strength = data.get('strength', 0)
        max_score = self.weights.order_book
        thresholds = STRENGTH_SCORE_THRESHOLDS[self.style]

        for threshold, multiplier in thresholds:
            if strength >= threshold:
                score = max_score * multiplier
                return score, f"체결강도 {strength:.1f}%"

        return 0, f"체결강도 약함 {strength:.1f}%"

    def calc_vwap_score(self, data: Dict) -> Tuple[float, str]:
        """VWAP 점수"""
        max_score = self.weights.vwap
        position = data.get('vwap_position', 'at')
        price_vs_vwap = data.get('price_vs_vwap', 0)

        if self.style == TradingStyle.SCALPING:
            # 스캘핑: VWAP 근처에서 거래 선호
            if position == 'at':
                return max_score * 1.0, f"VWAP 중립 ({price_vs_vwap:+.1f}%)"
            elif position == 'above' and price_vs_vwap <= 2:
                return max_score * 0.8, f"VWAP 상단 ({price_vs_vwap:+.1f}%)"
            elif position == 'below' and price_vs_vwap >= -2:
                return max_score * 0.6, f"VWAP 하단 ({price_vs_vwap:+.1f}%)"
            else:
                return max_score * 0.3, f"VWAP 이탈 ({price_vs_vwap:+.1f}%)"

        elif self.style == TradingStyle.DAYTRADING:
            # 단타: VWAP 상단 돌파 선호
            if position == 'above':
                if price_vs_vwap >= 1:
                    return max_score * 1.0, f"VWAP 상단 돌파 ({price_vs_vwap:+.1f}%)"
                else:
                    return max_score * 0.8, f"VWAP 상단 ({price_vs_vwap:+.1f}%)"
            elif position == 'at':
                return max_score * 0.5, f"VWAP 중립 ({price_vs_vwap:+.1f}%)"
            else:
                return 0, f"VWAP 하단 ({price_vs_vwap:+.1f}%)"

        else:  # SWING
            # 스윙: VWAP 위치 참고
            if position == 'above':
                return max_score * 0.8, f"VWAP 상단 ({price_vs_vwap:+.1f}%)"
            elif position == 'at':
                return max_score * 1.0, f"VWAP 지지 ({price_vs_vwap:+.1f}%)"
            else:
                return max_score * 0.5, f"VWAP 하단 ({price_vs_vwap:+.1f}%)"

    def calc_ma_score(self, data: Dict) -> Tuple[float, str]:
        """이동평균선 점수"""
        max_score = self.weights.ma
        arrangement = data.get('arrangement')
        cross_signal = data.get('cross_signal')
        above_ma5 = data.get('above_ma5', False)
        above_ma20 = data.get('above_ma20', False)
        above_ma60 = data.get('above_ma60', False)

        score = 0
        details = []

        # 배열 점수
        if arrangement == 'golden':
            score += max_score * 0.5
            details.append("정배열")
        elif arrangement == 'partial':
            score += max_score * 0.25
            details.append("혼조")
        elif arrangement == 'dead':
            details.append("역배열")

        # 크로스 신호
        if cross_signal == 'golden_cross':
            score += max_score * 0.3
            details.append("골든크로스")
        elif cross_signal == 'dead_cross':
            details.append("데드크로스")

        # 이평선 위치
        if above_ma5:
            score += max_score * 0.1
        if above_ma20:
            score += max_score * 0.1

        return min(score, max_score), ", ".join(details) if details else "이평선 분석"

    def calc_rsi_score(self, data: Dict) -> Tuple[float, str]:
        """RSI 점수"""
        max_score = self.weights.rsi
        rsi = data.get('rsi', 50)
        status = data.get('rsi_status', 'neutral')
        trend = data.get('rsi_trend', 'stable')

        if self.style in [TradingStyle.SCALPING, TradingStyle.DAYTRADING]:
            # 단기 매매: 중립~과열 구간 선호 (모멘텀)
            if 50 <= rsi < 70:
                score = max_score * 1.0
                detail = f"RSI {rsi:.0f} 상승세"
            elif 40 <= rsi < 50:
                score = max_score * 0.7
                detail = f"RSI {rsi:.0f} 중립"
            elif rsi >= 70:
                score = max_score * 0.3
                detail = f"RSI {rsi:.0f} 과열"
            elif 30 <= rsi < 40:
                score = max_score * 0.5
                detail = f"RSI {rsi:.0f} 하락세"
            else:
                score = max_score * 0.2
                detail = f"RSI {rsi:.0f} 과매도"
        else:  # SWING
            # 스윙: 과매도 구간 반등 선호
            if rsi <= 30:
                score = max_score * 1.0
                detail = f"RSI {rsi:.0f} 과매도 (반등 기대)"
            elif 30 < rsi <= 40:
                score = max_score * 0.8
                detail = f"RSI {rsi:.0f} 저점 접근"
            elif 40 < rsi < 60:
                score = max_score * 0.6
                detail = f"RSI {rsi:.0f} 중립"
            elif 60 <= rsi < 70:
                score = max_score * 0.4
                detail = f"RSI {rsi:.0f} 상승 추세"
            else:
                score = max_score * 0.2
                detail = f"RSI {rsi:.0f} 과열"

        return score, detail

    def calc_macd_score(self, data: Dict) -> Tuple[float, str]:
        """MACD 점수"""
        max_score = self.weights.macd
        if max_score == 0:
            return 0, "MACD 미적용"

        histogram = data.get('histogram', 0)
        prev_histogram = data.get('prev_histogram', 0)
        cross_signal = data.get('cross_signal', 'none')

        score = 0
        details = []

        # 크로스 신호
        if cross_signal == 'golden_cross':
            score += max_score * 0.6
            details.append("MACD 골든크로스")
        elif cross_signal == 'dead_cross':
            details.append("MACD 데드크로스")
        else:
            # 히스토그램 방향
            if histogram > 0:
                if histogram > prev_histogram:
                    score += max_score * 0.8
                    details.append("MACD 상승 확대")
                else:
                    score += max_score * 0.5
                    details.append("MACD 양수")
            else:
                if histogram > prev_histogram:
                    score += max_score * 0.3
                    details.append("MACD 하락 축소")
                else:
                    details.append("MACD 음수")

        return score, details[0] if details else "MACD 분석"

    def calc_bollinger_score(self, data: Dict) -> Tuple[float, str]:
        """볼린저밴드 점수"""
        max_score = self.weights.bollinger
        if max_score == 0:
            return 0, "볼린저 미적용"

        position = data.get('position', 'middle')
        squeeze = data.get('squeeze', False)

        if self.style in [TradingStyle.SCALPING, TradingStyle.DAYTRADING]:
            # 단기: 중심선 접근 시 반등 선호
            if position == 'lower':
                score = max_score * 1.0
                detail = "볼린저 하단 반등 기대"
            elif position == 'middle':
                score = max_score * 0.6
                detail = "볼린저 중심"
            else:
                score = max_score * 0.3
                detail = "볼린저 상단 주의"
        else:  # SWING
            if position == 'lower':
                score = max_score * 1.0
                detail = "볼린저 하단 반등"
            elif position == 'middle':
                score = max_score * 0.7
                detail = "볼린저 중심"
            else:
                score = max_score * 0.4
                detail = "볼린저 상단"

        if squeeze:
            detail += " (스퀴즈)"

        return score, detail

    def calc_obv_score(self, data: Dict) -> Tuple[float, str]:
        """OBV 점수"""
        max_score = self.weights.obv
        if max_score == 0:
            return 0, "OBV 미적용"

        trend = data.get('obv_trend', 'flat')
        new_high = data.get('obv_new_high', False)
        divergence = data.get('obv_divergence', 'none')

        score = 0
        details = []

        if trend == 'up':
            score += max_score * 0.5
            details.append("OBV 상승")
        elif trend == 'down':
            details.append("OBV 하락")

        if new_high:
            score += max_score * 0.3
            details.append("OBV 신고가")

        if divergence == 'bullish':
            score += max_score * 0.2
            details.append("상승 다이버전스")
        elif divergence == 'bearish':
            details.append("하락 다이버전스")

        return min(score, max_score), ", ".join(details) if details else "OBV 분석"

    def calculate_total(self, indicators: Dict) -> Dict:
        """전체 점수 계산"""
        scores = {}
        details = {}

        calc_methods = {
            'volume': (self.calc_volume_score, indicators.get('volume', {})),
            'order_book': (self.calc_order_book_score, indicators.get('order_book', {})),
            'vwap': (self.calc_vwap_score, indicators.get('vwap', {})),
            'ma': (self.calc_ma_score, indicators.get('ma', {})),
            'rsi': (self.calc_rsi_score, indicators.get('rsi', {})),
            'macd': (self.calc_macd_score, indicators.get('macd', {})),
            'bollinger': (self.calc_bollinger_score, indicators.get('bollinger', {})),
            'obv': (self.calc_obv_score, indicators.get('obv', {}))
        }

        for name, (method, data) in calc_methods.items():
            score, detail = method(data)
            scores[name] = round(score, 2)
            details[name] = detail

        total_score = sum(scores.values())

        return {
            'total_score': round(total_score, 2),
            'scores_breakdown': scores,
            'details': details
        }
