"""
백테스팅 엔진
- 전략 시뮬레이션
- 포지션 관리
- 주문 실행
"""
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .data_loader import BacktestDataLoader, OHLCVData
from ...config.constants import TradingStyle, TRADE_PARAMS, SignalType


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class BacktestConfig:
    """백테스트 설정"""
    initial_capital: float = 10_000_000  # 초기 자본
    trading_style: TradingStyle = TradingStyle.DAYTRADING
    commission_rate: float = 0.00015  # 수수료율 (0.015%)
    slippage_rate: float = 0.001  # 슬리피지 (0.1%)
    max_position_size: float = 0.2  # 최대 포지션 크기 (자본의 20%)
    max_positions: int = 5  # 최대 동시 포지션
    use_trailing_stop: bool = True
    trailing_stop_pct: float = 0.02  # 트레일링 스탑 (2%)


@dataclass
class BacktestOrder:
    """백테스트 주문"""
    order_id: str
    stock_code: str
    side: OrderSide
    quantity: int
    price: float
    order_type: str = "MARKET"  # MARKET, LIMIT
    status: OrderStatus = OrderStatus.PENDING
    filled_price: float = 0
    filled_quantity: int = 0
    filled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BacktestPosition:
    """백테스트 포지션"""
    stock_code: str
    stock_name: str
    quantity: int
    entry_price: float
    entry_time: datetime
    current_price: float = 0
    highest_price: float = 0  # 최고가 (트레일링용)
    stop_loss: float = 0
    take_profit1: float = 0
    take_profit2: float = 0
    unrealized_pnl: float = 0
    realized_pnl: float = 0


@dataclass
class BacktestTrade:
    """백테스트 거래 기록"""
    trade_id: str
    stock_code: str
    stock_name: str
    side: OrderSide
    quantity: int
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_rate: float
    commission: float
    exit_reason: str


class BacktestEngine:
    """백테스팅 엔진"""

    def __init__(
        self,
        config: BacktestConfig,
        data_loader: BacktestDataLoader,
        signal_generator: Optional[Callable] = None
    ):
        self.config = config
        self.data_loader = data_loader
        self.signal_generator = signal_generator

        # 상태
        self.capital = config.initial_capital
        self.available_cash = config.initial_capital
        self.positions: Dict[str, BacktestPosition] = {}
        self.orders: List[BacktestOrder] = []
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Dict] = []

        # 카운터
        self._order_counter = 0
        self._trade_counter = 0

        # 매매 파라미터
        self.trade_params = TRADE_PARAMS.get(
            config.trading_style,
            TRADE_PARAMS[TradingStyle.DAYTRADING]
        )

    def reset(self):
        """엔진 초기화"""
        self.capital = self.config.initial_capital
        self.available_cash = self.config.initial_capital
        self.positions.clear()
        self.orders.clear()
        self.trades.clear()
        self.equity_curve.clear()
        self._order_counter = 0
        self._trade_counter = 0

    async def run(
        self,
        stock_codes: List[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """백테스트 실행"""
        self.reset()

        # 데이터 로드
        all_data: Dict[str, List[OHLCVData]] = {}
        for code in stock_codes:
            data = self.data_loader.load_ohlcv(code, start_date, end_date, timeframe)
            if data:
                all_data[code] = data

        if not all_data:
            return {"error": "No data available"}

        # 날짜별 시뮬레이션
        all_dates = set()
        for data in all_data.values():
            for bar in data:
                all_dates.add(bar.timestamp.date())

        sorted_dates = sorted(all_dates)
        total_days = len(sorted_dates)

        for i, date in enumerate(sorted_dates):
            current_datetime = datetime.combine(date, datetime.min.time())

            # 각 종목 처리
            for stock_code, data in all_data.items():
                # 해당 날짜 데이터 찾기
                bar = next(
                    (b for b in data if b.timestamp.date() == date),
                    None
                )
                if not bar:
                    continue

                # 포지션 업데이트
                await self._update_position(stock_code, bar, current_datetime)

                # 신호 생성 및 매매
                if self.signal_generator:
                    signal = await self._generate_signal(stock_code, data, bar)
                    await self._process_signal(stock_code, signal, bar, current_datetime)

            # 일일 자산 기록
            self._record_equity(current_datetime)

            # 진행률 콜백
            if progress_callback:
                await progress_callback({
                    'progress': (i + 1) / total_days,
                    'date': str(date),
                    'equity': self._calculate_total_equity()
                })

        # 남은 포지션 청산
        for stock_code in list(self.positions.keys()):
            if stock_code in all_data and all_data[stock_code]:
                last_bar = all_data[stock_code][-1]
                await self._close_position(
                    stock_code,
                    last_bar.close,
                    last_bar.timestamp,
                    "BACKTEST_END"
                )

        return self._generate_result()

    async def _update_position(
        self,
        stock_code: str,
        bar: OHLCVData,
        current_time: datetime
    ):
        """포지션 업데이트"""
        if stock_code not in self.positions:
            return

        position = self.positions[stock_code]
        position.current_price = bar.close

        # 최고가 업데이트 (트레일링 스탑용)
        if bar.high > position.highest_price:
            position.highest_price = bar.high

        # 손익 계산
        position.unrealized_pnl = (
            (bar.close - position.entry_price) * position.quantity
        )

        # 손절 체크
        if bar.low <= position.stop_loss:
            await self._close_position(
                stock_code,
                position.stop_loss,
                current_time,
                "STOP_LOSS"
            )
            return

        # 트레일링 스탑 체크
        if self.config.use_trailing_stop:
            trailing_stop = position.highest_price * (1 - self.config.trailing_stop_pct)
            if bar.low <= trailing_stop and trailing_stop > position.entry_price:
                await self._close_position(
                    stock_code,
                    trailing_stop,
                    current_time,
                    "TRAILING_STOP"
                )
                return

        # 익절 체크 (TP2)
        if bar.high >= position.take_profit2:
            await self._close_position(
                stock_code,
                position.take_profit2,
                current_time,
                "TAKE_PROFIT_2"
            )
            return

        # 부분 익절 (TP1) - 50% 청산
        if bar.high >= position.take_profit1 and position.quantity > 1:
            partial_qty = position.quantity // 2
            if partial_qty > 0:
                await self._partial_close(
                    stock_code,
                    partial_qty,
                    position.take_profit1,
                    current_time,
                    "TAKE_PROFIT_1"
                )

    async def _generate_signal(
        self,
        stock_code: str,
        historical_data: List[OHLCVData],
        current_bar: OHLCVData
    ) -> Optional[SignalType]:
        """신호 생성"""
        if not self.signal_generator:
            return None

        try:
            # 현재 바까지의 데이터만 전달
            bar_index = next(
                (i for i, b in enumerate(historical_data) if b.timestamp == current_bar.timestamp),
                -1
            )
            if bar_index < 0:
                return None

            lookback_data = historical_data[:bar_index + 1]
            return await self.signal_generator(stock_code, lookback_data, current_bar)
        except Exception as e:
            print(f"신호 생성 오류: {e}")
            return None

    async def _process_signal(
        self,
        stock_code: str,
        signal: Optional[SignalType],
        bar: OHLCVData,
        current_time: datetime
    ):
        """신호 처리"""
        if not signal:
            return

        # 매수 신호
        if signal in [SignalType.STRONG_BUY, SignalType.BUY]:
            if stock_code not in self.positions:
                if len(self.positions) < self.config.max_positions:
                    await self._open_position(stock_code, bar, current_time)

        # 매도 신호
        elif signal == SignalType.SELL:
            if stock_code in self.positions:
                await self._close_position(
                    stock_code,
                    bar.close,
                    current_time,
                    "SELL_SIGNAL"
                )

    async def _open_position(
        self,
        stock_code: str,
        bar: OHLCVData,
        current_time: datetime
    ):
        """포지션 진입"""
        # 포지션 크기 계산
        max_amount = self.available_cash * self.config.max_position_size
        price_with_slippage = bar.close * (1 + self.config.slippage_rate)
        quantity = int(max_amount / price_with_slippage)

        if quantity <= 0:
            return

        # 수수료 계산
        commission = price_with_slippage * quantity * self.config.commission_rate
        total_cost = price_with_slippage * quantity + commission

        if total_cost > self.available_cash:
            return

        # 손절/익절가 계산
        stop_loss = price_with_slippage * (1 + self.trade_params['stop_loss_pct'])
        take_profit1 = price_with_slippage * (1 + self.trade_params['take_profit1_pct'])
        take_profit2 = price_with_slippage * (1 + self.trade_params['take_profit2_pct'])

        # 포지션 생성
        position = BacktestPosition(
            stock_code=stock_code,
            stock_name=stock_code,  # 실제로는 이름 필요
            quantity=quantity,
            entry_price=price_with_slippage,
            entry_time=current_time,
            current_price=bar.close,
            highest_price=bar.high,
            stop_loss=stop_loss,
            take_profit1=take_profit1,
            take_profit2=take_profit2
        )

        self.positions[stock_code] = position
        self.available_cash -= total_cost

        # 주문 기록
        self._order_counter += 1
        order = BacktestOrder(
            order_id=f"O{self._order_counter:06d}",
            stock_code=stock_code,
            side=OrderSide.BUY,
            quantity=quantity,
            price=bar.close,
            status=OrderStatus.FILLED,
            filled_price=price_with_slippage,
            filled_quantity=quantity,
            filled_at=current_time
        )
        self.orders.append(order)

    async def _close_position(
        self,
        stock_code: str,
        exit_price: float,
        current_time: datetime,
        reason: str
    ):
        """포지션 청산"""
        if stock_code not in self.positions:
            return

        position = self.positions[stock_code]
        price_with_slippage = exit_price * (1 - self.config.slippage_rate)

        # 손익 계산
        gross_pnl = (price_with_slippage - position.entry_price) * position.quantity
        commission = (
            position.entry_price * position.quantity * self.config.commission_rate +
            price_with_slippage * position.quantity * self.config.commission_rate
        )
        net_pnl = gross_pnl - commission
        pnl_rate = (price_with_slippage / position.entry_price - 1) * 100

        # 거래 기록
        self._trade_counter += 1
        trade = BacktestTrade(
            trade_id=f"T{self._trade_counter:06d}",
            stock_code=stock_code,
            stock_name=position.stock_name,
            side=OrderSide.SELL,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=price_with_slippage,
            entry_time=position.entry_time,
            exit_time=current_time,
            pnl=net_pnl,
            pnl_rate=pnl_rate,
            commission=commission,
            exit_reason=reason
        )
        self.trades.append(trade)

        # 자금 반환
        self.available_cash += price_with_slippage * position.quantity - commission

        # 포지션 삭제
        del self.positions[stock_code]

        # 주문 기록
        self._order_counter += 1
        order = BacktestOrder(
            order_id=f"O{self._order_counter:06d}",
            stock_code=stock_code,
            side=OrderSide.SELL,
            quantity=position.quantity,
            price=exit_price,
            status=OrderStatus.FILLED,
            filled_price=price_with_slippage,
            filled_quantity=position.quantity,
            filled_at=current_time
        )
        self.orders.append(order)

    async def _partial_close(
        self,
        stock_code: str,
        quantity: int,
        exit_price: float,
        current_time: datetime,
        reason: str
    ):
        """부분 청산"""
        if stock_code not in self.positions:
            return

        position = self.positions[stock_code]
        price_with_slippage = exit_price * (1 - self.config.slippage_rate)

        # 손익 계산
        gross_pnl = (price_with_slippage - position.entry_price) * quantity
        commission = price_with_slippage * quantity * self.config.commission_rate
        net_pnl = gross_pnl - commission
        pnl_rate = (price_with_slippage / position.entry_price - 1) * 100

        # 거래 기록
        self._trade_counter += 1
        trade = BacktestTrade(
            trade_id=f"T{self._trade_counter:06d}",
            stock_code=stock_code,
            stock_name=position.stock_name,
            side=OrderSide.SELL,
            quantity=quantity,
            entry_price=position.entry_price,
            exit_price=price_with_slippage,
            entry_time=position.entry_time,
            exit_time=current_time,
            pnl=net_pnl,
            pnl_rate=pnl_rate,
            commission=commission,
            exit_reason=reason
        )
        self.trades.append(trade)

        # 자금 반환
        self.available_cash += price_with_slippage * quantity - commission

        # 포지션 업데이트
        position.quantity -= quantity
        position.realized_pnl += net_pnl

    def _calculate_total_equity(self) -> float:
        """총 자산 계산"""
        position_value = sum(
            p.current_price * p.quantity for p in self.positions.values()
        )
        return self.available_cash + position_value

    def _record_equity(self, timestamp: datetime):
        """자산 기록"""
        equity = self._calculate_total_equity()
        self.equity_curve.append({
            'timestamp': timestamp.isoformat(),
            'equity': equity,
            'cash': self.available_cash,
            'position_count': len(self.positions)
        })

    def _generate_result(self) -> Dict:
        """결과 생성"""
        final_equity = self._calculate_total_equity()
        total_return = (final_equity / self.config.initial_capital - 1) * 100

        # 거래 통계
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]

        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0

        profit_factor = abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades and sum(t.pnl for t in losing_trades) != 0 else float('inf')

        # 최대 낙폭 계산
        max_drawdown = self._calculate_max_drawdown()

        return {
            'config': {
                'initial_capital': self.config.initial_capital,
                'trading_style': self.config.trading_style.value,
                'commission_rate': self.config.commission_rate,
                'slippage_rate': self.config.slippage_rate
            },
            'performance': {
                'final_equity': final_equity,
                'total_return': round(total_return, 2),
                'total_pnl': round(final_equity - self.config.initial_capital, 0),
                'max_drawdown': round(max_drawdown, 2)
            },
            'trades': {
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': round(win_rate, 2),
                'avg_win': round(avg_win, 0),
                'avg_loss': round(avg_loss, 0),
                'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 'N/A'
            },
            'equity_curve': self.equity_curve,
            'trade_history': [
                {
                    'trade_id': t.trade_id,
                    'stock_code': t.stock_code,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'quantity': t.quantity,
                    'pnl': t.pnl,
                    'pnl_rate': t.pnl_rate,
                    'exit_reason': t.exit_reason,
                    'entry_time': t.entry_time.isoformat(),
                    'exit_time': t.exit_time.isoformat()
                }
                for t in self.trades
            ]
        }

    def _calculate_max_drawdown(self) -> float:
        """최대 낙폭 계산"""
        if not self.equity_curve:
            return 0

        peak = self.equity_curve[0]['equity']
        max_dd = 0

        for point in self.equity_curve:
            equity = point['equity']
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_dd:
                max_dd = drawdown

        return max_dd
