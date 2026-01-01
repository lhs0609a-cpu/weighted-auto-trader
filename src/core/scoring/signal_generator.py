"""
신호 생성기
- 점수 기반 매매 신호 생성
- 필수 조건 체크
- 매매 파라미터 생성
"""
from typing import Dict, List
from dataclasses import dataclass

from ...config.constants import (
    TradingStyle, SignalType, SIGNAL_THRESHOLDS,
    MANDATORY_CONDITIONS, TRADE_PARAMS
)
from .calculator import ScoreCalculator


@dataclass
class SignalResult:
    """신호 결과"""
    signal: SignalType
    total_score: float
    scores_breakdown: Dict[str, float]
    details: Dict[str, str]
    mandatory_check: Dict[str, bool]
    trade_params: Dict
    confidence: float
    reasons: List[str]


class SignalGenerator:
    """신호 생성기 구현"""

    def __init__(self, style: TradingStyle):
        self.style = style
        self.calculator = ScoreCalculator(style)
        self.thresholds = SIGNAL_THRESHOLDS[style]
        self.mandatory_config = MANDATORY_CONDITIONS[style]
        self.trade_config = TRADE_PARAMS[style]

    def check_mandatory(self, indicators: Dict) -> Dict[str, bool]:
        """필수 조건 체크"""
        checks = {}

        volume_data = indicators.get('volume', {})
        order_book_data = indicators.get('order_book', {})
        vwap_data = indicators.get('vwap', {})
        rsi_data = indicators.get('rsi', {})
        ma_data = indicators.get('ma', {})

        if self.style == TradingStyle.SCALPING:
            checks['체결강도≥120%'] = order_book_data.get('strength', 0) >= 120
            checks['거래량≥200%'] = volume_data.get('volume_ratio', 0) >= 200

        elif self.style == TradingStyle.DAYTRADING:
            checks['체결강도≥110%'] = order_book_data.get('strength', 0) >= 110
            checks['거래량≥200%'] = volume_data.get('volume_ratio', 0) >= 200
            checks['VWAP상단'] = vwap_data.get('vwap_position', '') in ['above', 'at']

        else:  # SWING
            checks['RSI<70'] = rsi_data.get('rsi', 100) < 70
            checks['20일선위'] = ma_data.get('above_ma20', False)
            checks['거래량증가'] = volume_data.get('volume_ratio', 0) >= 100

        checks['all_passed'] = all(v for k, v in checks.items() if k != 'all_passed')
        return checks

    def generate(self, indicators: Dict, current_price: float = 0) -> SignalResult:
        """매매 신호 생성"""
        # 점수 계산
        score_result = self.calculator.calculate_total(indicators)
        total_score = score_result['total_score']

        # 필수 조건 체크
        mandatory = self.check_mandatory(indicators)

        # 신호 결정
        signal = self._determine_signal(total_score, mandatory)

        # 매매 파라미터 생성
        if current_price == 0:
            current_price = indicators.get('vwap', {}).get('current_price', 0)
        trade_params = self._generate_trade_params(current_price, signal)

        # 신뢰도 계산
        confidence = min(total_score / 100, 1.0)
        if not mandatory['all_passed']:
            confidence *= 0.7

        # 판단 근거 생성
        reasons = self._generate_reasons(score_result, mandatory, signal)

        return SignalResult(
            signal=signal,
            total_score=total_score,
            scores_breakdown=score_result['scores_breakdown'],
            details=score_result['details'],
            mandatory_check=mandatory,
            trade_params=trade_params,
            confidence=round(confidence, 2),
            reasons=reasons
        )

    def _determine_signal(self, score: float, mandatory: Dict) -> SignalType:
        """신호 결정"""
        if not mandatory['all_passed']:
            if score >= self.thresholds.watch:
                return SignalType.WATCH
            else:
                return SignalType.HOLD

        if score >= self.thresholds.strong_buy:
            return SignalType.STRONG_BUY
        elif score >= self.thresholds.buy:
            return SignalType.BUY
        elif score >= self.thresholds.watch:
            return SignalType.WATCH
        else:
            return SignalType.HOLD

    def _generate_trade_params(self, price: float, signal: SignalType) -> Dict:
        """매매 파라미터 생성"""
        if signal in [SignalType.HOLD, SignalType.WATCH]:
            return {'action': 'NONE'}

        if price <= 0:
            return {'action': 'NONE', 'error': 'Invalid price'}

        params = self.trade_config

        stop_loss = price * (1 + params.stop_loss_pct / 100)
        take_profit_1 = price * (1 + params.take_profit_1_pct / 100)
        take_profit_2 = price * (1 + params.take_profit_2_pct / 100)

        return {
            'action': 'BUY',
            'entry_price': price,
            'stop_loss': round(stop_loss, 0),
            'stop_loss_pct': params.stop_loss_pct,
            'take_profit_1': round(take_profit_1, 0),
            'take_profit_1_pct': params.take_profit_1_pct,
            'take_profit_2': round(take_profit_2, 0),
            'take_profit_2_pct': params.take_profit_2_pct,
            'trailing_stop_pct': params.trailing_stop_pct,
            'position_size_pct': params.position_size_pct
        }

    def _generate_reasons(
        self,
        score_result: Dict,
        mandatory: Dict,
        signal: SignalType
    ) -> List[str]:
        """판단 근거 생성"""
        reasons = []

        # 점수 기반 근거 (상위 3개 지표)
        scores = score_result['scores_breakdown']
        details = score_result['details']
        top_indicators = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]

        for ind, score in top_indicators:
            if score > 0:
                reasons.append(f"[{ind}] {details.get(ind, '')}")

        # 필수 조건 미충족 시
        if not mandatory['all_passed']:
            failed = [k for k, v in mandatory.items() if k != 'all_passed' and not v]
            if failed:
                reasons.append(f"필수조건 미충족: {', '.join(failed)}")

        # 신호별 추가 설명
        if signal == SignalType.STRONG_BUY:
            reasons.insert(0, f"총점 {score_result['total_score']:.1f}점 - 강력 매수 신호")
        elif signal == SignalType.BUY:
            reasons.insert(0, f"총점 {score_result['total_score']:.1f}점 - 매수 신호")
        elif signal == SignalType.WATCH:
            reasons.insert(0, f"총점 {score_result['total_score']:.1f}점 - 관심 종목")
        else:
            reasons.insert(0, f"총점 {score_result['total_score']:.1f}점 - 대기")

        return reasons


def signal_to_dict(signal_result: SignalResult) -> Dict:
    """SignalResult를 dict로 변환"""
    return {
        'signal': signal_result.signal.value,
        'total_score': signal_result.total_score,
        'scores_breakdown': signal_result.scores_breakdown,
        'details': signal_result.details,
        'mandatory_check': signal_result.mandatory_check,
        'trade_params': signal_result.trade_params,
        'confidence': signal_result.confidence,
        'reasons': signal_result.reasons
    }
