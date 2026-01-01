"""
실시간 데이터 스트리머
- 주기적 시세 업데이트
- 신호 알림
- 포지션 업데이트
"""
from typing import Dict, List, Optional, Callable, Awaitable
from datetime import datetime
import asyncio

from ...core.broker.interfaces import IBrokerClient
from ...services import AnalysisService
from ...config.constants import TradingStyle
from .connection_manager import ConnectionManager


class RealtimeStreamer:
    """실시간 데이터 스트리머"""

    def __init__(
        self,
        broker: IBrokerClient,
        connection_manager: ConnectionManager
    ):
        self.broker = broker
        self.manager = connection_manager
        self.analysis_service = AnalysisService(broker)

        self._running = False
        self._update_interval = 1.0  # 초 단위
        self._signal_check_interval = 5.0  # 신호 체크 간격

        self._price_cache: Dict[str, Dict] = {}
        self._tasks: List[asyncio.Task] = []

    async def start(self):
        """스트리머 시작"""
        if self._running:
            return

        self._running = True
        await self.broker.connect()

        # 백그라운드 태스크 시작
        self._tasks.append(asyncio.create_task(self._price_update_loop()))
        self._tasks.append(asyncio.create_task(self._signal_check_loop()))

    async def stop(self):
        """스트리머 중지"""
        self._running = False

        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._tasks.clear()

    async def _price_update_loop(self):
        """가격 업데이트 루프"""
        while self._running:
            try:
                await self._update_subscribed_stocks()
                await asyncio.sleep(self._update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Price update error: {e}")
                await asyncio.sleep(1)

    async def _signal_check_loop(self):
        """신호 체크 루프"""
        while self._running:
            try:
                await self._check_signals()
                await asyncio.sleep(self._signal_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Signal check error: {e}")
                await asyncio.sleep(1)

    async def _update_subscribed_stocks(self):
        """구독 종목 업데이트"""
        subscribed_stocks = self.manager.get_all_subscribed_stocks()
        if not subscribed_stocks:
            return

        for stock_code in subscribed_stocks:
            try:
                quote = await self.broker.get_quote(stock_code)

                data = {
                    "stock_code": quote.stock_code,
                    "name": quote.name,
                    "price": quote.price,
                    "change": quote.change,
                    "change_rate": quote.change_rate,
                    "volume": quote.volume,
                    "high": quote.high,
                    "low": quote.low,
                    "timestamp": datetime.now().isoformat()
                }

                # 캐시 업데이트
                self._price_cache[stock_code] = data

                # 브로드캐스트
                await self.manager.broadcast_stock_update(stock_code, data)

            except Exception as e:
                print(f"Stock update error ({stock_code}): {e}")

    async def _check_signals(self):
        """신호 체크"""
        subscribed_stocks = self.manager.get_all_subscribed_stocks()
        if not subscribed_stocks:
            return

        for stock_code in subscribed_stocks:
            try:
                # 분석 수행
                result = await self.analysis_service.analyze_stock(
                    stock_code,
                    TradingStyle.DAYTRADING
                )

                signal = result.get('signal', 'HOLD')

                # BUY/STRONG_BUY 신호인 경우 알림
                if signal in ['BUY', 'STRONG_BUY']:
                    await self.manager.broadcast_to_channel('signals', {
                        "type": "signal_alert",
                        "stock_code": stock_code,
                        "stock_name": result.get('stock_name', ''),
                        "signal": signal,
                        "score": result.get('total_score', 0),
                        "confidence": result.get('confidence', 0),
                        "reasons": result.get('reasons', []),
                        "timestamp": datetime.now().isoformat()
                    })

            except Exception as e:
                print(f"Signal check error ({stock_code}): {e}")

    async def send_position_update(self, position_data: Dict):
        """포지션 업데이트 전송"""
        await self.manager.broadcast_to_channel('positions', {
            "type": "position_update",
            "data": position_data,
            "timestamp": datetime.now().isoformat()
        })

    async def send_order_update(self, order_data: Dict):
        """주문 업데이트 전송"""
        await self.manager.broadcast_to_channel('orders', {
            "type": "order_update",
            "data": order_data,
            "timestamp": datetime.now().isoformat()
        })

    async def send_trade_alert(self, trade_data: Dict):
        """매매 알림 전송"""
        await self.manager.broadcast({
            "type": "trade_alert",
            "data": trade_data,
            "timestamp": datetime.now().isoformat()
        })

    def get_cached_price(self, stock_code: str) -> Optional[Dict]:
        """캐시된 가격 조회"""
        return self._price_cache.get(stock_code)

    def set_update_interval(self, seconds: float):
        """업데이트 간격 설정"""
        self._update_interval = max(0.5, seconds)

    def set_signal_check_interval(self, seconds: float):
        """신호 체크 간격 설정"""
        self._signal_check_interval = max(1.0, seconds)
