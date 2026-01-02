"""
스코어링 모듈 단위 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.core.scoring import ScoreCalculator, SignalGenerator
from src.config.constants import TradingStyle, SignalType


class TestScoreCalculator:
    """점수 계산기 테스트"""

    def setup_method(self):
        self.calculator = ScoreCalculator()

    def test_weighted_score_calculation(self):
        """가중 점수 계산 테스트"""
        indicator_scores = {
            'volume': {'score': 80, 'weight': 25},
            'order_book': {'score': 70, 'weight': 20},
            'vwap': {'score': 75, 'weight': 18},
            'rsi': {'score': 60, 'weight': 12},
            'macd': {'score': 65, 'weight': 10},
            'ma': {'score': 70, 'weight': 8},
            'bollinger': {'score': 55, 'weight': 5},
            'obv': {'score': 72, 'weight': 2}
        }

        total_score = self.calculator.calculate_weighted_score(
            indicator_scores,
            TradingStyle.DAYTRADING
        )

        assert 0 <= total_score <= 100
        # 대략적인 예상 점수 범위 확인
        assert 65 <= total_score <= 80

    def test_high_score_calculation(self):
        """높은 점수 계산 테스트"""
        indicator_scores = {
            'volume': {'score': 95, 'weight': 25},
            'order_book': {'score': 90, 'weight': 20},
            'vwap': {'score': 88, 'weight': 18},
            'rsi': {'score': 85, 'weight': 12},
            'macd': {'score': 90, 'weight': 10},
            'ma': {'score': 85, 'weight': 8},
            'bollinger': {'score': 80, 'weight': 5},
            'obv': {'score': 88, 'weight': 2}
        }

        total_score = self.calculator.calculate_weighted_score(
            indicator_scores,
            TradingStyle.DAYTRADING
        )

        assert total_score >= 85

    def test_low_score_calculation(self):
        """낮은 점수 계산 테스트"""
        indicator_scores = {
            'volume': {'score': 30, 'weight': 25},
            'order_book': {'score': 35, 'weight': 20},
            'vwap': {'score': 40, 'weight': 18},
            'rsi': {'score': 25, 'weight': 12},
            'macd': {'score': 30, 'weight': 10},
            'ma': {'score': 35, 'weight': 8},
            'bollinger': {'score': 45, 'weight': 5},
            'obv': {'score': 30, 'weight': 2}
        }

        total_score = self.calculator.calculate_weighted_score(
            indicator_scores,
            TradingStyle.DAYTRADING
        )

        assert total_score <= 40

    def test_style_specific_weights(self):
        """매매 스타일별 가중치 적용 테스트"""
        indicator_scores = {
            'volume': {'score': 90},
            'order_book': {'score': 50},
            'vwap': {'score': 50},
            'rsi': {'score': 50},
            'macd': {'score': 50},
            'ma': {'score': 50},
            'bollinger': {'score': 50},
            'obv': {'score': 50}
        }

        # SCALPING은 volume, order_book 가중치가 높음
        scalping_score = self.calculator.calculate_weighted_score(
            indicator_scores,
            TradingStyle.SCALPING
        )

        # SWING은 ma, rsi 가중치가 높음
        swing_score = self.calculator.calculate_weighted_score(
            indicator_scores,
            TradingStyle.SWING
        )

        # Volume이 높으면 SCALPING 점수가 더 높아야 함
        assert scalping_score > swing_score


class TestSignalGenerator:
    """신호 생성기 테스트"""

    def setup_method(self):
        self.generator = SignalGenerator()

    def test_strong_buy_signal(self):
        """강력 매수 신호 테스트"""
        analysis_result = {
            'total_score': 85,
            'mandatory_check': {'all_passed': True},
            'confidence': 0.9
        }

        signal = self.generator.generate_signal(
            analysis_result,
            TradingStyle.DAYTRADING
        )

        assert signal == SignalType.STRONG_BUY

    def test_buy_signal(self):
        """매수 신호 테스트"""
        analysis_result = {
            'total_score': 72,
            'mandatory_check': {'all_passed': True},
            'confidence': 0.75
        }

        signal = self.generator.generate_signal(
            analysis_result,
            TradingStyle.DAYTRADING
        )

        assert signal == SignalType.BUY

    def test_watch_signal(self):
        """관심 신호 테스트"""
        analysis_result = {
            'total_score': 62,
            'mandatory_check': {'all_passed': True},
            'confidence': 0.6
        }

        signal = self.generator.generate_signal(
            analysis_result,
            TradingStyle.DAYTRADING
        )

        assert signal == SignalType.WATCH

    def test_hold_signal(self):
        """대기 신호 테스트"""
        analysis_result = {
            'total_score': 50,
            'mandatory_check': {'all_passed': True},
            'confidence': 0.5
        }

        signal = self.generator.generate_signal(
            analysis_result,
            TradingStyle.DAYTRADING
        )

        assert signal == SignalType.HOLD

    def test_sell_signal(self):
        """매도 신호 테스트"""
        analysis_result = {
            'total_score': 30,
            'mandatory_check': {'all_passed': True},
            'confidence': 0.4
        }

        signal = self.generator.generate_signal(
            analysis_result,
            TradingStyle.DAYTRADING
        )

        assert signal == SignalType.SELL

    def test_mandatory_check_failure(self):
        """필수 조건 실패시 테스트"""
        analysis_result = {
            'total_score': 85,
            'mandatory_check': {'all_passed': False},
            'confidence': 0.9
        }

        signal = self.generator.generate_signal(
            analysis_result,
            TradingStyle.DAYTRADING
        )

        # 필수 조건 미충족시 신호 하향
        assert signal != SignalType.STRONG_BUY

    def test_swing_style_thresholds(self):
        """스윙 스타일 임계값 테스트"""
        # SWING 스타일은 임계값이 다름
        analysis_result = {
            'total_score': 78,
            'mandatory_check': {'all_passed': True},
            'confidence': 0.8
        }

        signal = self.generator.generate_signal(
            analysis_result,
            TradingStyle.SWING
        )

        # SWING은 임계값이 더 낮으므로 STRONG_BUY 가능
        assert signal in [SignalType.STRONG_BUY, SignalType.BUY]


class TestSignalReasons:
    """신호 사유 생성 테스트"""

    def setup_method(self):
        self.generator = SignalGenerator()

    def test_generate_reasons_bullish(self):
        """강세 사유 생성 테스트"""
        indicator_results = {
            'volume': {'score': 85, 'signal': 'bullish', 'volume_ratio': 250},
            'order_book': {'score': 80, 'signal': 'bullish', 'strength': 130},
            'vwap': {'score': 75, 'signal': 'bullish'},
            'rsi': {'score': 60, 'signal': 'neutral', 'rsi': 55},
        }

        reasons = self.generator.generate_reasons(indicator_results, 80)

        assert len(reasons) > 0
        assert any('volume' in r.lower() or '거래량' in r for r in reasons)

    def test_generate_reasons_bearish(self):
        """약세 사유 생성 테스트"""
        indicator_results = {
            'volume': {'score': 30, 'signal': 'bearish', 'volume_ratio': 50},
            'order_book': {'score': 35, 'signal': 'bearish', 'strength': 70},
            'vwap': {'score': 40, 'signal': 'bearish'},
            'rsi': {'score': 25, 'signal': 'bearish', 'rsi': 25},
        }

        reasons = self.generator.generate_reasons(indicator_results, 35)

        assert len(reasons) > 0


class TestConfidenceCalculation:
    """신뢰도 계산 테스트"""

    def setup_method(self):
        self.calculator = ScoreCalculator()

    def test_high_confidence(self):
        """높은 신뢰도 테스트"""
        indicator_results = {
            'volume': {'score': 85, 'signal': 'bullish'},
            'order_book': {'score': 80, 'signal': 'bullish'},
            'vwap': {'score': 82, 'signal': 'bullish'},
            'rsi': {'score': 78, 'signal': 'bullish'},
            'macd': {'score': 80, 'signal': 'bullish'},
        }

        confidence = self.calculator.calculate_confidence(indicator_results)

        assert confidence >= 0.8

    def test_low_confidence_mixed_signals(self):
        """혼합 신호시 낮은 신뢰도 테스트"""
        indicator_results = {
            'volume': {'score': 85, 'signal': 'bullish'},
            'order_book': {'score': 30, 'signal': 'bearish'},
            'vwap': {'score': 50, 'signal': 'neutral'},
            'rsi': {'score': 75, 'signal': 'bullish'},
            'macd': {'score': 40, 'signal': 'bearish'},
        }

        confidence = self.calculator.calculate_confidence(indicator_results)

        assert confidence < 0.7

    def test_medium_confidence(self):
        """중간 신뢰도 테스트"""
        indicator_results = {
            'volume': {'score': 70, 'signal': 'bullish'},
            'order_book': {'score': 65, 'signal': 'bullish'},
            'vwap': {'score': 55, 'signal': 'neutral'},
            'rsi': {'score': 60, 'signal': 'neutral'},
            'macd': {'score': 62, 'signal': 'bullish'},
        }

        confidence = self.calculator.calculate_confidence(indicator_results)

        assert 0.5 <= confidence <= 0.8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
