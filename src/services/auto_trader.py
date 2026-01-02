"""
자동매매 서비스
- 시장 시간에 맞춰 자동 실행
- 신호 감지 → 주문 실행
- 포지션 모니터링 (손절/익절)
- 텔레그램 알림
"""
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
import asyncio
import pytz

from ..config.constants import TradingStyle, SignalType, ExitReason
from ..config.settings import get_settings
from ..core.broker import IBrokerClient, create_broker_from_settings
from ..core.trading import TradingEngine, TradingConfig, TradeDecision
from .analysis_service import AnalysisService
from .screening_service import ScreeningService
from .notification_service import NotificationManager, NotificationType


class AutoTraderStatus(str, Enum):
    """자동매매 상태"""
    STOPPED = "stopped"
    WAITING = "waiting"      # 장 시작 대기
    RUNNING = "running"      # 자동매매 실행 중
    PAUSED = "paused"        # 일시 정지
    MARKET_CLOSED = "closed" # 장 마감


@dataclass
class AutoTraderConfig:
    """자동매매 설정"""
    enabled: bool = False
    trading_style: TradingStyle = TradingStyle.DAYTRADING

    # 시장 시간 (한국 시간)
    market_open: time = time(9, 0)      # 09:00
    market_close: time = time(15, 30)   # 15:30
    pre_market_start: time = time(8, 30)  # 08:30 사전준비

    # 스크리닝 간격 (초)
    screening_interval: int = 60
    position_check_interval: int = 10

    # 매매 설정
    max_positions: int = 5
    max_daily_trades: int = 20
    max_position_pct: float = 20.0
    total_capital: float = 10_000_000

    # 손익 제한
    daily_loss_limit_pct: float = -2.0
    daily_profit_target_pct: float = 5.0

    # 자동 매매 모드
    auto_buy_enabled: bool = True
    auto_sell_enabled: bool = True

    # 필터
    min_score: float = 70.0
    signal_types: List[str] = None

    def __post_init__(self):
        if self.signal_types is None:
            self.signal_types = ["STRONG_BUY", "BUY"]


class AutoTrader:
    """자동매매 서비스"""

    KST = pytz.timezone('Asia/Seoul')

    def __init__(
        self,
        broker: Optional[IBrokerClient] = None,
        config: Optional[AutoTraderConfig] = None,
        notification_manager: Optional[NotificationManager] = None
    ):
        """
        Args:
            broker: 브로커 클라이언트 (None이면 설정에서 생성)
            config: 자동매매 설정
            notification_manager: 알림 관리자
        """
        self.broker = broker or create_broker_from_settings()
        self.config = config or AutoTraderConfig()
        self.notification = notification_manager or NotificationManager()

        # 서비스 초기화
        self.analysis_service = AnalysisService(self.broker)
        self.screening_service = ScreeningService(self.broker)

        # 트레이딩 엔진 초기화
        trading_config = TradingConfig(
            style=self.config.trading_style,
            max_positions=self.config.max_positions,
            max_position_pct=self.config.max_position_pct,
            total_capital=self.config.total_capital,
            enable_auto_trade=self.config.enabled,
            enable_partial_close=True
        )
        self.trading_engine = TradingEngine(self.broker, trading_config)

        # 상태
        self._status = AutoTraderStatus.STOPPED
        self._running = False
        self._paused = False

        # 통계
        self._today_trades = 0
        self._today_pnl = 0.0
        self._start_balance = 0.0

        # 모니터링
        self._watched_stocks: Set[str] = set()
        self._last_prices: Dict[str, float] = {}

        # 태스크
        self._main_task: Optional[asyncio.Task] = None
        self._position_task: Optional[asyncio.Task] = None

        # 콜백
        self._status_callbacks: List[Callable] = []

        # 트레이딩 엔진 콜백 등록
        self.trading_engine.register_trade_callback(self._on_trade_executed)

    @property
    def status(self) -> AutoTraderStatus:
        return self._status

    @property
    def is_running(self) -> bool:
        return self._running and not self._paused

    def _now_kst(self) -> datetime:
        """현재 한국 시간"""
        return datetime.now(self.KST)

    def _is_market_hours(self) -> bool:
        """장 시간 여부"""
        now = self._now_kst()
        current_time = now.time()

        # 주말 제외
        if now.weekday() >= 5:
            return False

        return self.config.market_open <= current_time <= self.config.market_close

    def _is_pre_market(self) -> bool:
        """사전 준비 시간 여부"""
        now = self._now_kst()
        current_time = now.time()

        if now.weekday() >= 5:
            return False

        return self.config.pre_market_start <= current_time < self.config.market_open

    def _seconds_until_market_open(self) -> int:
        """장 시작까지 남은 초"""
        now = self._now_kst()
        today_open = now.replace(
            hour=self.config.market_open.hour,
            minute=self.config.market_open.minute,
            second=0,
            microsecond=0
        )

        if now.time() >= self.config.market_open:
            # 내일 장 시작
            today_open += timedelta(days=1)
            # 주말 건너뛰기
            while today_open.weekday() >= 5:
                today_open += timedelta(days=1)

        return int((today_open - now).total_seconds())

    async def start(self):
        """자동매매 시작"""
        if self._running:
            return

        self._running = True
        self._paused = False

        # 브로커 연결
        await self.broker.connect()
        await self.trading_engine.start()

        # 알림 서비스 시작
        settings = get_settings()
        if settings.telegram_bot_token and settings.telegram_chat_id:
            self.notification.configure_telegram(
                settings.telegram_bot_token,
                settings.telegram_chat_id,
                enabled=True
            )
            await self.notification.start()

        # 초기 잔고 기록
        try:
            balance = await self.broker.get_balance()
            self._start_balance = balance.total_balance
        except:
            self._start_balance = self.config.total_capital

        # 메인 루프 시작
        self._main_task = asyncio.create_task(self._main_loop())
        self._position_task = asyncio.create_task(self._position_monitor_loop())

        await self._update_status(AutoTraderStatus.WAITING)
        await self._notify_system_status("started")

        print(f"[AutoTrader] 시작됨 - 스타일: {self.config.trading_style.value}")

    async def stop(self):
        """자동매매 중지"""
        if not self._running:
            return

        self._running = False

        # 태스크 취소
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass

        if self._position_task:
            self._position_task.cancel()
            try:
                await self._position_task
            except asyncio.CancelledError:
                pass

        # 일일 리포트 전송
        await self._send_daily_report()

        # 서비스 종료
        await self.trading_engine.stop()
        await self.broker.disconnect()
        await self.notification.stop()

        await self._update_status(AutoTraderStatus.STOPPED)
        await self._notify_system_status("stopped")

        print("[AutoTrader] 중지됨")

    def pause(self):
        """일시 정지"""
        self._paused = True
        asyncio.create_task(self._update_status(AutoTraderStatus.PAUSED))
        print("[AutoTrader] 일시 정지")

    def resume(self):
        """재개"""
        self._paused = False
        asyncio.create_task(self._update_status(AutoTraderStatus.RUNNING))
        print("[AutoTrader] 재개")

    async def _main_loop(self):
        """메인 자동매매 루프"""
        print("[AutoTrader] 메인 루프 시작")

        while self._running:
            try:
                if self._paused:
                    await asyncio.sleep(1)
                    continue

                if self._is_market_hours():
                    await self._update_status(AutoTraderStatus.RUNNING)
                    await self._trading_cycle()
                    await asyncio.sleep(self.config.screening_interval)

                elif self._is_pre_market():
                    await self._update_status(AutoTraderStatus.WAITING)
                    await self._pre_market_preparation()
                    await asyncio.sleep(30)

                else:
                    await self._update_status(AutoTraderStatus.MARKET_CLOSED)

                    # 장 마감 후 일일 리포트
                    now = self._now_kst()
                    if now.time() > self.config.market_close and self._today_trades > 0:
                        await self._send_daily_report()
                        self._reset_daily_stats()

                    # 장 시작 대기
                    wait_seconds = min(self._seconds_until_market_open(), 300)
                    await asyncio.sleep(wait_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[AutoTrader] 메인 루프 오류: {e}")
                await self.notification.notify(
                    NotificationType.ERROR,
                    error_type="MainLoopError",
                    message=str(e)
                )
                await asyncio.sleep(5)

    async def _pre_market_preparation(self):
        """장 시작 전 준비"""
        print("[AutoTrader] 사전 준비 중...")

        # 관심종목 스크리닝
        try:
            discovered = await self.screening_service.auto_discover(
                self.config.trading_style,
                max_stocks=20
            )

            self._watched_stocks = set(s['stock_code'] for s in discovered)
            print(f"[AutoTrader] 관심종목 {len(self._watched_stocks)}개 발굴")

            # 상위 신호 종목 알림
            top_stocks = discovered[:5]
            for stock in top_stocks:
                if stock['signal'] in self.config.signal_types:
                    await self.notification.notify(
                        NotificationType.SIGNAL,
                        stock_code=stock['stock_code'],
                        stock_name=stock['stock_name'],
                        signal=SignalType(stock['signal']),
                        score=stock['total_score'],
                        current_price=int(stock['current_price']),
                        change_rate=stock['change_rate'],
                        reasons=["사전 스크리닝 발굴"]
                    )

        except Exception as e:
            print(f"[AutoTrader] 사전 준비 오류: {e}")

    async def _trading_cycle(self):
        """매매 사이클"""
        # 일일 제한 체크
        if not self._check_daily_limits():
            return

        try:
            # 1. 관심종목 분석 및 신호 감지
            await self._analyze_and_trade()

            # 2. 새 종목 발굴 (5분마다)
            now = self._now_kst()
            if now.minute % 5 == 0:
                await self._discover_new_stocks()

        except Exception as e:
            print(f"[AutoTrader] 매매 사이클 오류: {e}")

    async def _analyze_and_trade(self):
        """종목 분석 및 매매"""
        if not self._watched_stocks:
            return

        for stock_code in list(self._watched_stocks):
            try:
                # 분석
                analysis = await self.analysis_service.analyze_stock(
                    stock_code,
                    self.config.trading_style
                )

                # 가격 업데이트
                self._last_prices[stock_code] = analysis['current_price']

                # 신호 확인
                signal = analysis.get('signal', 'HOLD')
                score = analysis.get('total_score', 0)

                if signal in self.config.signal_types and score >= self.config.min_score:
                    # 매수 신호
                    if self.config.auto_buy_enabled:
                        decision = await self.trading_engine.analyze_stock(
                            stock_code,
                            analysis.get('indicators', {}),
                            analysis['current_price']
                        )

                        if decision.action == "BUY":
                            await self._execute_buy(decision, analysis)

                elif signal == "SELL":
                    # 매도 신호
                    if self.config.auto_sell_enabled:
                        decision = await self.trading_engine.analyze_stock(
                            stock_code,
                            analysis.get('indicators', {}),
                            analysis['current_price']
                        )

                        if decision.action == "SELL":
                            await self._execute_sell(decision, analysis)

            except Exception as e:
                print(f"[AutoTrader] 종목 분석 오류 ({stock_code}): {e}")

    async def _execute_buy(self, decision: TradeDecision, analysis: Dict):
        """매수 실행"""
        # 일일 거래 수 체크
        if self._today_trades >= self.config.max_daily_trades:
            return

        order = await self.trading_engine.execute_decision(decision)

        if order:
            self._today_trades += 1
            print(f"[AutoTrader] 매수 실행: {decision.stock_name} {decision.quantity}주 @ {decision.price:,}원")

            # 알림
            await self.notification.notify(
                NotificationType.ORDER_FILLED,
                stock_code=decision.stock_code,
                stock_name=decision.stock_name,
                order_type="BUY",
                quantity=decision.quantity,
                price=int(decision.price),
                order_id=order.order_id
            )

    async def _execute_sell(self, decision: TradeDecision, analysis: Dict):
        """매도 실행"""
        order = await self.trading_engine.execute_decision(decision)

        if order:
            self._today_trades += 1
            print(f"[AutoTrader] 매도 실행: {decision.stock_name} {decision.quantity}주 @ {decision.price:,}원")

            # 알림
            await self.notification.notify(
                NotificationType.ORDER_FILLED,
                stock_code=decision.stock_code,
                stock_name=decision.stock_name,
                order_type="SELL",
                quantity=decision.quantity,
                price=int(decision.price),
                order_id=order.order_id
            )

    async def _discover_new_stocks(self):
        """새 종목 발굴"""
        try:
            top_signals = await self.screening_service.get_top_signals(
                self.config.trading_style,
                signal_types=self.config.signal_types,
                limit=10
            )

            for stock in top_signals:
                if stock['stock_code'] not in self._watched_stocks:
                    self._watched_stocks.add(stock['stock_code'])

                    # 새 신호 알림
                    if stock['total_score'] >= self.config.min_score:
                        await self.notification.notify(
                            NotificationType.SIGNAL,
                            stock_code=stock['stock_code'],
                            stock_name=stock['stock_name'],
                            signal=SignalType(stock['signal']),
                            score=stock['total_score'],
                            current_price=int(stock['current_price']),
                            change_rate=stock['change_rate'],
                            reasons=["실시간 스크리닝 발굴"]
                        )

        except Exception as e:
            print(f"[AutoTrader] 종목 발굴 오류: {e}")

    async def _position_monitor_loop(self):
        """포지션 모니터링 루프"""
        print("[AutoTrader] 포지션 모니터링 시작")

        while self._running:
            try:
                if self._paused or not self._is_market_hours():
                    await asyncio.sleep(1)
                    continue

                # 오픈 포지션 가격 업데이트
                open_positions = self.trading_engine.position_manager.get_open_positions()

                if open_positions:
                    # 실시간 가격 조회
                    prices = {}
                    for pos in open_positions:
                        try:
                            quote = await self.broker.get_quote(pos.stock_code)
                            prices[pos.stock_code] = quote.price
                            self._last_prices[pos.stock_code] = quote.price
                        except:
                            if pos.stock_code in self._last_prices:
                                prices[pos.stock_code] = self._last_prices[pos.stock_code]

                    # 포지션 업데이트 (손절/익절 체크)
                    await self.trading_engine.update_positions(prices)

                await asyncio.sleep(self.config.position_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[AutoTrader] 포지션 모니터링 오류: {e}")
                await asyncio.sleep(5)

    async def _on_trade_executed(self, decision: TradeDecision):
        """매매 실행 콜백"""
        # PnL 업데이트는 포지션 청산 시 처리
        pass

    def _check_daily_limits(self) -> bool:
        """일일 제한 체크"""
        # 일일 손실 제한
        if self._start_balance > 0:
            current_pnl_pct = (self._today_pnl / self._start_balance) * 100

            if current_pnl_pct <= self.config.daily_loss_limit_pct:
                print(f"[AutoTrader] 일일 손실 제한 도달: {current_pnl_pct:.2f}%")
                return False

            if current_pnl_pct >= self.config.daily_profit_target_pct:
                print(f"[AutoTrader] 일일 목표 수익 도달: {current_pnl_pct:.2f}%")
                return False

        # 일일 거래 수 제한
        if self._today_trades >= self.config.max_daily_trades:
            print(f"[AutoTrader] 일일 거래 제한 도달: {self._today_trades}회")
            return False

        return True

    def _reset_daily_stats(self):
        """일일 통계 초기화"""
        self._today_trades = 0
        self._today_pnl = 0.0

    async def _send_daily_report(self):
        """일일 리포트 전송"""
        try:
            position_summary = self.trading_engine.position_manager.get_position_summary()

            await self.notification.notify(
                NotificationType.DAILY_REPORT,
                date=self._now_kst().strftime('%Y-%m-%d'),
                total_trades=self._today_trades,
                win_count=0,  # TODO: 실제 승패 집계
                loss_count=0,
                total_pnl=int(position_summary['total_realized_pnl']),
                total_pnl_rate=(position_summary['total_realized_pnl'] / self._start_balance * 100) if self._start_balance > 0 else 0,
                best_trade=None,
                worst_trade=None
            )
        except Exception as e:
            print(f"[AutoTrader] 일일 리포트 오류: {e}")

    async def _update_status(self, status: AutoTraderStatus):
        """상태 업데이트"""
        if self._status != status:
            self._status = status

            for callback in self._status_callbacks:
                try:
                    await callback(status)
                except Exception as e:
                    print(f"[AutoTrader] 상태 콜백 오류: {e}")

    async def _notify_system_status(self, status: str):
        """시스템 상태 알림"""
        if self.notification.telegram:
            await self.notification.telegram.notify_system_status(
                status,
                {
                    'trading_style': self.config.trading_style.value,
                    'stock_count': len(self._watched_stocks),
                    'auto_trade': self.config.enabled
                }
            )

    def register_status_callback(self, callback: Callable):
        """상태 콜백 등록"""
        self._status_callbacks.append(callback)

    def get_status_info(self) -> Dict:
        """상태 정보 조회"""
        return {
            'status': self._status.value,
            'is_running': self._running,
            'is_paused': self._paused,
            'is_market_hours': self._is_market_hours(),
            'trading_style': self.config.trading_style.value,
            'auto_buy_enabled': self.config.auto_buy_enabled,
            'auto_sell_enabled': self.config.auto_sell_enabled,
            'watched_stocks': len(self._watched_stocks),
            'today_trades': self._today_trades,
            'today_pnl': self._today_pnl,
            'positions': self.trading_engine.position_manager.get_position_summary(),
            'config': {
                'max_positions': self.config.max_positions,
                'max_daily_trades': self.config.max_daily_trades,
                'daily_loss_limit_pct': self.config.daily_loss_limit_pct,
                'daily_profit_target_pct': self.config.daily_profit_target_pct,
                'min_score': self.config.min_score,
                'signal_types': self.config.signal_types,
            }
        }

    def update_config(self, **kwargs):
        """설정 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # 트레이딩 엔진 설정도 업데이트
        self.trading_engine.update_config(
            enable_auto_trade=self.config.enabled
        )

    def add_watch_stock(self, stock_code: str):
        """관심종목 추가"""
        self._watched_stocks.add(stock_code)

    def remove_watch_stock(self, stock_code: str):
        """관심종목 제거"""
        self._watched_stocks.discard(stock_code)

    def get_watched_stocks(self) -> List[str]:
        """관심종목 목록"""
        return list(self._watched_stocks)


# 싱글톤 인스턴스
_auto_trader_instance: Optional[AutoTrader] = None


def get_auto_trader() -> AutoTrader:
    """AutoTrader 싱글톤 인스턴스 반환"""
    global _auto_trader_instance
    if _auto_trader_instance is None:
        settings = get_settings()

        config = AutoTraderConfig(
            enabled=settings.auto_trade_enabled,
            trading_style=TradingStyle(settings.default_trading_style),
            max_positions=settings.max_positions,
            daily_loss_limit_pct=settings.daily_loss_limit_pct,
            max_position_pct=settings.position_size_pct,
        )

        _auto_trader_instance = AutoTrader(config=config)

    return _auto_trader_instance


async def start_auto_trader():
    """자동매매 시작 (헬퍼 함수)"""
    trader = get_auto_trader()
    await trader.start()


async def stop_auto_trader():
    """자동매매 중지 (헬퍼 함수)"""
    global _auto_trader_instance
    if _auto_trader_instance:
        await _auto_trader_instance.stop()
