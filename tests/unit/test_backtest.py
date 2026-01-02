"""
백테스팅 모듈 단위 테스트
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.core.backtesting import (
    BacktestEngine,
    BacktestConfig,
    BacktestDataLoader,
    OHLCVData,
    ResultAnalyzer
)
from src.config.constants import TradingStyle


class TestBacktestDataLoader:
    """데이터 로더 테스트"""

    def setup_method(self):
        self.loader = BacktestDataLoader(data_dir="./test_data")

    def test_generate_mock_data(self):
        """모의 데이터 생성 테스트"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        data = self.loader.generate_mock_data(
            stock_code="005930",
            stock_name="삼성전자",
            start_date=start_date,
            end_date=end_date,
            initial_price=70000,
            volatility=0.02
        )

        assert len(data) > 0
        # 주말 제외하면 대략 22일
        assert len(data) <= 25

        for ohlcv in data:
            assert ohlcv.high >= ohlcv.low
            assert ohlcv.high >= ohlcv.open
            assert ohlcv.high >= ohlcv.close
            assert ohlcv.low <= ohlcv.open
            assert ohlcv.low <= ohlcv.close
            assert ohlcv.volume > 0

    def test_generate_intraday_data(self):
        """장중 모의 데이터 생성 테스트"""
        date = datetime(2024, 1, 15)

        data = self.loader.generate_intraday_mock_data(
            stock_code="005930",
            date=date,
            initial_price=70000
        )

        assert len(data) > 0
        # 09:00 ~ 15:30 = 390분
        assert len(data) == 391

        for tick in data:
            assert tick.price > 0
            assert tick.volume >= 0


class TestBacktestConfig:
    """백테스트 설정 테스트"""

    def test_default_config(self):
        """기본 설정 테스트"""
        config = BacktestConfig()

        assert config.initial_capital == 10_000_000
        assert config.trading_style == TradingStyle.DAYTRADING
        assert config.commission_rate == 0.00015
        assert config.slippage_rate == 0.001
        assert config.max_positions == 5

    def test_custom_config(self):
        """커스텀 설정 테스트"""
        config = BacktestConfig(
            initial_capital=50_000_000,
            trading_style=TradingStyle.SWING,
            max_positions=10,
            use_trailing_stop=False
        )

        assert config.initial_capital == 50_000_000
        assert config.trading_style == TradingStyle.SWING
        assert config.max_positions == 10
        assert config.use_trailing_stop == False


class TestBacktestEngine:
    """백테스트 엔진 테스트"""

    def setup_method(self):
        self.config = BacktestConfig(
            initial_capital=10_000_000,
            trading_style=TradingStyle.DAYTRADING,
            max_positions=3
        )
        self.loader = BacktestDataLoader()
        self.engine = BacktestEngine(self.config, self.loader)

    def test_engine_initialization(self):
        """엔진 초기화 테스트"""
        assert self.engine.capital == 10_000_000
        assert self.engine.available_cash == 10_000_000
        assert len(self.engine.positions) == 0
        assert len(self.engine.trades) == 0

    def test_engine_reset(self):
        """엔진 리셋 테스트"""
        self.engine.available_cash = 5_000_000
        self.engine.positions['005930'] = MagicMock()

        self.engine.reset()

        assert self.engine.capital == 10_000_000
        assert self.engine.available_cash == 10_000_000
        assert len(self.engine.positions) == 0

    @pytest.mark.asyncio
    async def test_run_backtest_no_data(self):
        """데이터 없을 때 백테스트 테스트"""
        result = await self.engine.run(
            stock_codes=['INVALID'],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )

        assert 'error' in result

    def test_calculate_total_equity(self):
        """총 자산 계산 테스트"""
        self.engine.available_cash = 5_000_000

        # Mock position
        mock_position = MagicMock()
        mock_position.current_price = 100000
        mock_position.quantity = 50
        self.engine.positions['005930'] = mock_position

        equity = self.engine._calculate_total_equity()

        assert equity == 5_000_000 + (100000 * 50)

    def test_max_drawdown_calculation(self):
        """최대 낙폭 계산 테스트"""
        self.engine.equity_curve = [
            {'equity': 10_000_000},
            {'equity': 10_500_000},
            {'equity': 10_200_000},
            {'equity': 9_800_000},
            {'equity': 10_300_000},
        ]

        mdd = self.engine._calculate_max_drawdown()

        # Peak: 10.5M, Trough: 9.8M
        # MDD = (10.5 - 9.8) / 10.5 * 100 = 6.67%
        assert 6 < mdd < 7


class TestResultAnalyzer:
    """결과 분석기 테스트"""

    def setup_method(self):
        self.analyzer = ResultAnalyzer()

    def test_analyze_result(self):
        """결과 분석 테스트"""
        backtest_result = {
            'config': {
                'initial_capital': 10_000_000,
                'trading_style': 'DAYTRADING'
            },
            'performance': {
                'final_equity': 12_000_000,
                'total_return': 20,
                'max_drawdown': 5
            },
            'trades': {
                'total_trades': 100,
                'winning_trades': 60,
                'losing_trades': 40,
                'win_rate': 60,
                'avg_win': 50000,
                'avg_loss': -30000,
                'profit_factor': 2.5
            },
            'equity_curve': [
                {'timestamp': '2024-01-01T09:00:00', 'equity': 10_000_000},
                {'timestamp': '2024-01-02T09:00:00', 'equity': 10_200_000},
                {'timestamp': '2024-01-03T09:00:00', 'equity': 10_400_000},
                {'timestamp': '2024-01-04T09:00:00', 'equity': 10_100_000},
                {'timestamp': '2024-01-05T09:00:00', 'equity': 10_600_000},
            ],
            'trade_history': [
                {
                    'entry_time': '2024-01-01T10:00:00',
                    'exit_time': '2024-01-01T14:00:00',
                    'pnl': 50000,
                    'pnl_rate': 2.5,
                    'exit_reason': 'TAKE_PROFIT_1'
                }
            ]
        }

        result = self.analyzer.analyze(backtest_result)

        assert result.total_return == 20
        assert result.total_trades == 100
        assert result.win_rate == 60
        assert result.max_drawdown == 5

    def test_sharpe_ratio_calculation(self):
        """샤프 비율 계산 테스트"""
        daily_returns = [0.5, 0.3, -0.2, 0.4, 0.1, -0.1, 0.3, 0.2, -0.3, 0.4]

        sharpe = self.analyzer._calculate_sharpe_ratio(daily_returns)

        # 양수 수익률이면 양수 샤프
        assert sharpe > 0

    def test_sortino_ratio_calculation(self):
        """소르티노 비율 계산 테스트"""
        daily_returns = [0.5, 0.3, -0.2, 0.4, 0.1, -0.1, 0.3, 0.2, -0.3, 0.4]

        sortino = self.analyzer._calculate_sortino_ratio(daily_returns)

        # 소르티노는 하방 리스크만 고려하므로 샤프보다 클 수 있음
        assert sortino != 0

    def test_monthly_returns_calculation(self):
        """월별 수익률 계산 테스트"""
        equity_curve = [
            {'timestamp': '2024-01-01T09:00:00', 'equity': 10_000_000},
            {'timestamp': '2024-01-15T09:00:00', 'equity': 10_500_000},
            {'timestamp': '2024-01-31T09:00:00', 'equity': 11_000_000},
            {'timestamp': '2024-02-15T09:00:00', 'equity': 10_800_000},
            {'timestamp': '2024-02-28T09:00:00', 'equity': 11_200_000},
        ]

        monthly_returns = self.analyzer._calculate_monthly_returns(equity_curve)

        assert '2024-01' in monthly_returns
        assert '2024-02' in monthly_returns

    def test_generate_report(self):
        """리포트 생성 테스트"""
        from src.core.backtesting import BacktestResult

        result = BacktestResult(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            trading_days=252,
            initial_capital=10_000_000,
            final_equity=12_500_000,
            total_return=25,
            annualized_return=25,
            monthly_return=2,
            total_trades=150,
            winning_trades=90,
            losing_trades=60,
            win_rate=60,
            avg_win=45000,
            avg_loss=-25000,
            profit_factor=2.7,
            avg_holding_period=1.5,
            max_drawdown=8,
            max_drawdown_duration=15,
            sharpe_ratio=1.5,
            sortino_ratio=2.1,
            calmar_ratio=3.1,
            monthly_returns={'2024-01': 3.5, '2024-02': 2.1},
            trade_distribution={'by_exit_reason': {'TAKE_PROFIT_1': 50}}
        )

        report = self.analyzer.generate_report(result)

        assert '백테스트 결과 보고서' in report
        assert '25' in report  # total return
        assert '60' in report  # win rate


class TestTradeDistributionAnalysis:
    """거래 분포 분석 테스트"""

    def setup_method(self):
        self.analyzer = ResultAnalyzer()

    def test_analyze_trade_distribution(self):
        """거래 분포 분석 테스트"""
        trade_history = [
            {'pnl_rate': 3.5, 'exit_reason': 'TAKE_PROFIT_1', 'exit_time': '2024-01-15T14:00:00'},
            {'pnl_rate': -1.2, 'exit_reason': 'STOP_LOSS', 'exit_time': '2024-01-16T11:00:00'},
            {'pnl_rate': 5.5, 'exit_reason': 'TAKE_PROFIT_2', 'exit_time': '2024-01-17T10:00:00'},
            {'pnl_rate': 2.1, 'exit_reason': 'TAKE_PROFIT_1', 'exit_time': '2024-01-18T15:00:00'},
            {'pnl_rate': -2.5, 'exit_reason': 'TRAILING_STOP', 'exit_time': '2024-01-19T13:00:00'},
        ]

        distribution = self.analyzer._analyze_trade_distribution(trade_history)

        assert 'by_exit_reason' in distribution
        assert 'by_pnl_range' in distribution
        assert 'by_weekday' in distribution

        # Exit reason counts
        assert distribution['by_exit_reason']['TAKE_PROFIT_1'] == 2
        assert distribution['by_exit_reason']['STOP_LOSS'] == 1

        # PnL range
        assert distribution['by_pnl_range']['big_profit'] == 1  # 5.5%
        assert distribution['by_pnl_range']['small_profit'] == 2  # 3.5%, 2.1%
        assert distribution['by_pnl_range']['small_loss'] == 2  # -1.2%, -2.5%


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
