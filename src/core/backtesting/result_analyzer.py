"""
백테스트 결과 분석기
- 성과 분석
- 리스크 지표
- 보고서 생성
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import math


@dataclass
class BacktestResult:
    """백테스트 결과"""
    # 기본 정보
    start_date: datetime
    end_date: datetime
    trading_days: int
    initial_capital: float
    final_equity: float

    # 수익률
    total_return: float  # %
    annualized_return: float  # %
    monthly_return: float  # %

    # 거래 통계
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float  # %
    avg_win: float
    avg_loss: float
    profit_factor: float
    avg_holding_period: float  # days

    # 리스크 지표
    max_drawdown: float  # %
    max_drawdown_duration: int  # days
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # 기타
    equity_curve: List[Dict] = field(default_factory=list)
    monthly_returns: Dict[str, float] = field(default_factory=dict)
    trade_distribution: Dict[str, int] = field(default_factory=dict)


class ResultAnalyzer:
    """결과 분석기"""

    def __init__(self, risk_free_rate: float = 0.035):
        """
        Args:
            risk_free_rate: 무위험 수익률 (연 3.5%)
        """
        self.risk_free_rate = risk_free_rate

    def analyze(self, backtest_result: Dict) -> BacktestResult:
        """백테스트 결과 분석"""
        equity_curve = backtest_result.get('equity_curve', [])
        trade_history = backtest_result.get('trade_history', [])
        config = backtest_result.get('config', {})
        performance = backtest_result.get('performance', {})
        trades_stats = backtest_result.get('trades', {})

        if not equity_curve:
            raise ValueError("자산 곡선 데이터가 없습니다")

        # 기간 정보
        start_date = datetime.fromisoformat(equity_curve[0]['timestamp'])
        end_date = datetime.fromisoformat(equity_curve[-1]['timestamp'])
        trading_days = len(equity_curve)

        # 수익률 계산
        initial_capital = config.get('initial_capital', 10_000_000)
        final_equity = performance.get('final_equity', initial_capital)
        total_return = performance.get('total_return', 0)

        years = max((end_date - start_date).days / 365, 0.01)
        annualized_return = ((final_equity / initial_capital) ** (1 / years) - 1) * 100
        monthly_return = ((final_equity / initial_capital) ** (1 / (years * 12)) - 1) * 100

        # 거래 통계
        total_trades = trades_stats.get('total_trades', 0)
        winning_trades = trades_stats.get('winning_trades', 0)
        losing_trades = trades_stats.get('losing_trades', 0)
        win_rate = trades_stats.get('win_rate', 0)
        avg_win = trades_stats.get('avg_win', 0)
        avg_loss = trades_stats.get('avg_loss', 0)
        profit_factor = trades_stats.get('profit_factor', 0)

        # 평균 보유 기간
        avg_holding_period = self._calculate_avg_holding_period(trade_history)

        # 리스크 지표
        daily_returns = self._calculate_daily_returns(equity_curve)
        max_drawdown = performance.get('max_drawdown', 0)
        max_dd_duration = self._calculate_max_dd_duration(equity_curve)
        sharpe = self._calculate_sharpe_ratio(daily_returns)
        sortino = self._calculate_sortino_ratio(daily_returns)
        calmar = self._calculate_calmar_ratio(annualized_return, max_drawdown)

        # 월별 수익률
        monthly_returns = self._calculate_monthly_returns(equity_curve)

        # 거래 분포
        trade_distribution = self._analyze_trade_distribution(trade_history)

        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            trading_days=trading_days,
            initial_capital=initial_capital,
            final_equity=final_equity,
            total_return=total_return,
            annualized_return=round(annualized_return, 2),
            monthly_return=round(monthly_return, 2),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor if isinstance(profit_factor, (int, float)) else 0,
            avg_holding_period=round(avg_holding_period, 1),
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            sharpe_ratio=round(sharpe, 2),
            sortino_ratio=round(sortino, 2),
            calmar_ratio=round(calmar, 2),
            equity_curve=equity_curve,
            monthly_returns=monthly_returns,
            trade_distribution=trade_distribution
        )

    def _calculate_daily_returns(self, equity_curve: List[Dict]) -> List[float]:
        """일일 수익률 계산"""
        returns = []
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i - 1]['equity']
            curr_equity = equity_curve[i]['equity']
            daily_return = (curr_equity / prev_equity - 1) * 100
            returns.append(daily_return)
        return returns

    def _calculate_avg_holding_period(self, trade_history: List[Dict]) -> float:
        """평균 보유 기간 계산"""
        if not trade_history:
            return 0

        total_days = 0
        for trade in trade_history:
            entry = datetime.fromisoformat(trade['entry_time'])
            exit_time = datetime.fromisoformat(trade['exit_time'])
            days = (exit_time - entry).total_seconds() / 86400
            total_days += days

        return total_days / len(trade_history)

    def _calculate_max_dd_duration(self, equity_curve: List[Dict]) -> int:
        """최대 낙폭 지속 기간 계산"""
        if not equity_curve:
            return 0

        peak = equity_curve[0]['equity']
        peak_idx = 0
        max_duration = 0
        current_duration = 0

        for i, point in enumerate(equity_curve):
            equity = point['equity']
            if equity >= peak:
                peak = equity
                peak_idx = i
                if current_duration > max_duration:
                    max_duration = current_duration
                current_duration = 0
            else:
                current_duration = i - peak_idx

        return max(max_duration, current_duration)

    def _calculate_sharpe_ratio(self, daily_returns: List[float]) -> float:
        """샤프 비율 계산"""
        if not daily_returns:
            return 0

        avg_return = sum(daily_returns) / len(daily_returns)
        std_dev = self._calculate_std(daily_returns)

        if std_dev == 0:
            return 0

        # 연율화
        daily_rf = self.risk_free_rate / 252
        excess_return = avg_return - daily_rf
        annualized_sharpe = (excess_return / std_dev) * math.sqrt(252)

        return annualized_sharpe

    def _calculate_sortino_ratio(self, daily_returns: List[float]) -> float:
        """소르티노 비율 계산 (하방 리스크만 고려)"""
        if not daily_returns:
            return 0

        avg_return = sum(daily_returns) / len(daily_returns)
        negative_returns = [r for r in daily_returns if r < 0]

        if not negative_returns:
            return float('inf') if avg_return > 0 else 0

        downside_std = self._calculate_std(negative_returns)
        if downside_std == 0:
            return 0

        daily_rf = self.risk_free_rate / 252
        excess_return = avg_return - daily_rf
        annualized_sortino = (excess_return / downside_std) * math.sqrt(252)

        return annualized_sortino

    def _calculate_calmar_ratio(self, annualized_return: float, max_drawdown: float) -> float:
        """칼마 비율 계산"""
        if max_drawdown == 0:
            return 0
        return annualized_return / max_drawdown

    def _calculate_std(self, values: List[float]) -> float:
        """표준편차 계산"""
        if len(values) < 2:
            return 0
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    def _calculate_monthly_returns(self, equity_curve: List[Dict]) -> Dict[str, float]:
        """월별 수익률 계산"""
        if not equity_curve:
            return {}

        monthly_returns = {}
        month_start_equity = equity_curve[0]['equity']
        current_month = datetime.fromisoformat(equity_curve[0]['timestamp']).strftime('%Y-%m')

        for point in equity_curve:
            timestamp = datetime.fromisoformat(point['timestamp'])
            month_key = timestamp.strftime('%Y-%m')

            if month_key != current_month:
                # 이전 달 수익률 저장
                monthly_return = (point['equity'] / month_start_equity - 1) * 100
                monthly_returns[current_month] = round(monthly_return, 2)

                # 새 달 시작
                month_start_equity = point['equity']
                current_month = month_key

        # 마지막 달
        if equity_curve:
            final_return = (equity_curve[-1]['equity'] / month_start_equity - 1) * 100
            monthly_returns[current_month] = round(final_return, 2)

        return monthly_returns

    def _analyze_trade_distribution(self, trade_history: List[Dict]) -> Dict[str, int]:
        """거래 분포 분석"""
        distribution = {
            'by_exit_reason': {},
            'by_pnl_range': {
                'big_loss': 0,      # -5% 이하
                'small_loss': 0,    # -5% ~ 0%
                'small_profit': 0,  # 0% ~ 5%
                'big_profit': 0     # 5% 이상
            },
            'by_weekday': {str(i): 0 for i in range(7)}
        }

        for trade in trade_history:
            # 청산 사유별
            reason = trade.get('exit_reason', 'UNKNOWN')
            distribution['by_exit_reason'][reason] = distribution['by_exit_reason'].get(reason, 0) + 1

            # 손익 범위별
            pnl_rate = trade.get('pnl_rate', 0)
            if pnl_rate <= -5:
                distribution['by_pnl_range']['big_loss'] += 1
            elif pnl_rate < 0:
                distribution['by_pnl_range']['small_loss'] += 1
            elif pnl_rate < 5:
                distribution['by_pnl_range']['small_profit'] += 1
            else:
                distribution['by_pnl_range']['big_profit'] += 1

            # 요일별
            exit_time = datetime.fromisoformat(trade['exit_time'])
            weekday = str(exit_time.weekday())
            distribution['by_weekday'][weekday] += 1

        return distribution

    def generate_report(self, result: BacktestResult) -> str:
        """리포트 생성"""
        report = f"""
================================================================================
                          백테스트 결과 보고서
================================================================================

[기간 정보]
- 시작일: {result.start_date.strftime('%Y-%m-%d')}
- 종료일: {result.end_date.strftime('%Y-%m-%d')}
- 거래일수: {result.trading_days}일

[수익률]
- 초기 자본: {result.initial_capital:,.0f}원
- 최종 자산: {result.final_equity:,.0f}원
- 총 수익률: {result.total_return:+.2f}%
- 연환산 수익률: {result.annualized_return:+.2f}%
- 월 평균 수익률: {result.monthly_return:+.2f}%

[거래 통계]
- 총 거래 횟수: {result.total_trades}회
- 승리: {result.winning_trades}회 / 패배: {result.losing_trades}회
- 승률: {result.win_rate:.1f}%
- 평균 수익: {result.avg_win:,.0f}원
- 평균 손실: {result.avg_loss:,.0f}원
- Profit Factor: {result.profit_factor:.2f}
- 평균 보유 기간: {result.avg_holding_period:.1f}일

[리스크 지표]
- 최대 낙폭 (MDD): {result.max_drawdown:.2f}%
- MDD 지속 기간: {result.max_drawdown_duration}일
- 샤프 비율: {result.sharpe_ratio:.2f}
- 소르티노 비율: {result.sortino_ratio:.2f}
- 칼마 비율: {result.calmar_ratio:.2f}

[월별 수익률]
"""
        for month, ret in result.monthly_returns.items():
            bar = "+" * int(abs(ret)) if ret >= 0 else "-" * int(abs(ret))
            report += f"  {month}: {ret:+.2f}% {bar[:20]}\n"

        report += """
[청산 사유 분포]
"""
        if result.trade_distribution:
            for reason, count in result.trade_distribution.get('by_exit_reason', {}).items():
                pct = count / result.total_trades * 100 if result.total_trades > 0 else 0
                report += f"  - {reason}: {count}회 ({pct:.1f}%)\n"

        report += """
================================================================================
"""
        return report

    def compare_results(self, results: List[BacktestResult]) -> Dict:
        """여러 결과 비교"""
        if not results:
            return {}

        comparison = {
            'summary': [],
            'best_return': None,
            'best_sharpe': None,
            'lowest_mdd': None
        }

        best_return = -float('inf')
        best_sharpe = -float('inf')
        lowest_mdd = float('inf')

        for i, result in enumerate(results):
            summary = {
                'index': i,
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades
            }
            comparison['summary'].append(summary)

            if result.total_return > best_return:
                best_return = result.total_return
                comparison['best_return'] = i

            if result.sharpe_ratio > best_sharpe:
                best_sharpe = result.sharpe_ratio
                comparison['best_sharpe'] = i

            if result.max_drawdown < lowest_mdd:
                lowest_mdd = result.max_drawdown
                comparison['lowest_mdd'] = i

        return comparison
