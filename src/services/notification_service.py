"""
텔레그램 알림 서비스
- 매매 신호 알림
- 거래 체결 알림
- 손익 리포트
"""
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import asyncio
import httpx

from ..config.constants import SignalType


class NotificationType(str, Enum):
    """알림 유형"""
    SIGNAL = "signal"           # 매매 신호
    ORDER_FILLED = "order"      # 주문 체결
    POSITION_OPEN = "position"  # 포지션 진입
    POSITION_CLOSE = "close"    # 포지션 청산
    STOP_LOSS = "stoploss"      # 손절
    TAKE_PROFIT = "takeprofit"  # 익절
    DAILY_REPORT = "report"     # 일일 리포트
    ERROR = "error"             # 에러


class TelegramNotificationService:
    """텔레그램 알림 서비스"""

    SIGNAL_EMOJI = {
        SignalType.STRONG_BUY: "🔥",
        SignalType.BUY: "📈",
        SignalType.WATCH: "👀",
        SignalType.HOLD: "⏸️",
        SignalType.SELL: "📉",
    }

    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        """
        Args:
            bot_token: 텔레그램 봇 토큰
            chat_id: 알림 받을 채팅방 ID
            enabled: 알림 활성화 여부
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self._client: Optional[httpx.AsyncClient] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def start(self):
        """알림 서비스 시작"""
        if not self.enabled:
            return

        self._client = httpx.AsyncClient(timeout=30.0)
        self._running = True
        asyncio.create_task(self._process_queue())

    async def stop(self):
        """알림 서비스 종료"""
        self._running = False
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _process_queue(self):
        """메시지 큐 처리"""
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                await self._send_message(message)
                await asyncio.sleep(0.1)  # Rate limit 방지
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"텔레그램 알림 오류: {e}")

    async def _send_message(self, text: str, parse_mode: str = "HTML"):
        """텔레그램 메시지 전송"""
        if not self._client or not self.enabled:
            return

        try:
            response = await self._client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True
                }
            )
            response.raise_for_status()
        except Exception as e:
            print(f"텔레그램 전송 실패: {e}")

    def queue_message(self, text: str):
        """메시지 큐에 추가"""
        if self.enabled:
            self._message_queue.put_nowait(text)

    # === 알림 메서드들 ===

    async def notify_signal(
        self,
        stock_code: str,
        stock_name: str,
        signal: SignalType,
        score: float,
        current_price: int,
        change_rate: float,
        reasons: List[str]
    ):
        """매매 신호 알림"""
        emoji = self.SIGNAL_EMOJI.get(signal, "📊")
        signal_text = {
            SignalType.STRONG_BUY: "강력 매수",
            SignalType.BUY: "매수",
            SignalType.WATCH: "관심",
            SignalType.HOLD: "대기",
            SignalType.SELL: "매도"
        }.get(signal, signal.value)

        change_emoji = "🔴" if change_rate >= 0 else "🔵"
        change_sign = "+" if change_rate >= 0 else ""

        reasons_text = "\n".join([f"  • {r}" for r in reasons[:3]])

        message = f"""
{emoji} <b>매매 신호 발생</b>

<b>{stock_name}</b> ({stock_code})
신호: <b>{signal_text}</b> | 점수: <b>{score:.1f}점</b>

💰 현재가: {current_price:,}원
{change_emoji} 등락: {change_sign}{change_rate:.2f}%

📋 분석 사유:
{reasons_text}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self.queue_message(message.strip())

    async def notify_order_filled(
        self,
        stock_code: str,
        stock_name: str,
        order_type: str,
        quantity: int,
        price: int,
        order_id: str
    ):
        """주문 체결 알림"""
        emoji = "🟢" if order_type == "BUY" else "🔵"
        type_text = "매수" if order_type == "BUY" else "매도"

        message = f"""
{emoji} <b>주문 체결</b>

<b>{stock_name}</b> ({stock_code})
{type_text} {quantity:,}주 @ {price:,}원
총액: {quantity * price:,}원

주문번호: {order_id}
⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self.queue_message(message.strip())

    async def notify_position_opened(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        entry_price: int,
        stop_loss: int,
        take_profit: int
    ):
        """포지션 진입 알림"""
        message = f"""
📊 <b>포지션 진입</b>

<b>{stock_name}</b> ({stock_code})
수량: {quantity:,}주
진입가: {entry_price:,}원
투자금액: {quantity * entry_price:,}원

🔴 손절가: {stop_loss:,}원 ({((stop_loss - entry_price) / entry_price * 100):.1f}%)
🟢 목표가: {take_profit:,}원 (+{((take_profit - entry_price) / entry_price * 100):.1f}%)

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self.queue_message(message.strip())

    async def notify_position_closed(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        entry_price: int,
        exit_price: int,
        pnl: int,
        pnl_rate: float,
        reason: str
    ):
        """포지션 청산 알림"""
        emoji = "🎉" if pnl >= 0 else "😢"
        pnl_sign = "+" if pnl >= 0 else ""
        pnl_color = "🟢" if pnl >= 0 else "🔴"

        message = f"""
{emoji} <b>포지션 청산</b>

<b>{stock_name}</b> ({stock_code})
수량: {quantity:,}주
진입가: {entry_price:,}원 → 청산가: {exit_price:,}원

{pnl_color} 손익: {pnl_sign}{pnl:,}원 ({pnl_sign}{pnl_rate:.2f}%)
청산 사유: {reason}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self.queue_message(message.strip())

    async def notify_stop_loss(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        entry_price: int,
        exit_price: int,
        loss: int,
        loss_rate: float
    ):
        """손절 알림"""
        message = f"""
🚨 <b>손절 실행</b>

<b>{stock_name}</b> ({stock_code})
수량: {quantity:,}주
진입가: {entry_price:,}원 → 손절가: {exit_price:,}원

🔴 손실: {loss:,}원 ({loss_rate:.2f}%)

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self.queue_message(message.strip())

    async def notify_take_profit(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        entry_price: int,
        exit_price: int,
        profit: int,
        profit_rate: float,
        tp_level: int
    ):
        """익절 알림"""
        message = f"""
💰 <b>익절 실행 (TP{tp_level})</b>

<b>{stock_name}</b> ({stock_code})
수량: {quantity:,}주
진입가: {entry_price:,}원 → 익절가: {exit_price:,}원

🟢 수익: +{profit:,}원 (+{profit_rate:.2f}%)

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self.queue_message(message.strip())

    async def notify_daily_report(
        self,
        date: str,
        total_trades: int,
        win_count: int,
        loss_count: int,
        total_pnl: int,
        total_pnl_rate: float,
        best_trade: Optional[Dict],
        worst_trade: Optional[Dict]
    ):
        """일일 리포트 알림"""
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        pnl_emoji = "📈" if total_pnl >= 0 else "📉"
        pnl_sign = "+" if total_pnl >= 0 else ""

        best_text = ""
        if best_trade:
            best_text = f"\n🏆 최고 수익: {best_trade['stock_name']} (+{best_trade['pnl']:,}원)"

        worst_text = ""
        if worst_trade:
            worst_text = f"\n💔 최대 손실: {worst_trade['stock_name']} ({worst_trade['pnl']:,}원)"

        message = f"""
📊 <b>일일 거래 리포트</b>
📅 {date}

거래 횟수: {total_trades}회
승률: {win_rate:.1f}% ({win_count}승 / {loss_count}패)

{pnl_emoji} 총 손익: {pnl_sign}{total_pnl:,}원 ({pnl_sign}{total_pnl_rate:.2f}%)
{best_text}{worst_text}

Good trading! 🚀
"""
        self.queue_message(message.strip())

    async def notify_error(self, error_type: str, message: str, details: str = ""):
        """에러 알림"""
        error_message = f"""
⚠️ <b>시스템 에러</b>

유형: {error_type}
메시지: {message}
{f'상세: {details}' if details else ''}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self.queue_message(error_message.strip())

    async def notify_system_status(self, status: str, details: Dict):
        """시스템 상태 알림"""
        status_emoji = {
            "started": "🟢",
            "stopped": "🔴",
            "paused": "🟡",
            "resumed": "🟢"
        }.get(status, "⚪")

        message = f"""
{status_emoji} <b>시스템 상태</b>

상태: {status.upper()}
매매 스타일: {details.get('trading_style', 'N/A')}
모니터링 종목: {details.get('stock_count', 0)}개
자동매매: {'ON' if details.get('auto_trade', False) else 'OFF'}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        self.queue_message(message.strip())


class NotificationManager:
    """알림 관리자 - 여러 채널 통합"""

    def __init__(self):
        self.telegram: Optional[TelegramNotificationService] = None
        self._enabled = True

    def configure_telegram(self, bot_token: str, chat_id: str, enabled: bool = True):
        """텔레그램 설정"""
        self.telegram = TelegramNotificationService(bot_token, chat_id, enabled)

    async def start(self):
        """알림 서비스 시작"""
        if self.telegram:
            await self.telegram.start()

    async def stop(self):
        """알림 서비스 종료"""
        if self.telegram:
            await self.telegram.stop()

    def set_enabled(self, enabled: bool):
        """알림 활성화/비활성화"""
        self._enabled = enabled
        if self.telegram:
            self.telegram.enabled = enabled

    async def notify(self, notification_type: NotificationType, **kwargs):
        """통합 알림 전송"""
        if not self._enabled:
            return

        if self.telegram:
            try:
                if notification_type == NotificationType.SIGNAL:
                    await self.telegram.notify_signal(**kwargs)
                elif notification_type == NotificationType.ORDER_FILLED:
                    await self.telegram.notify_order_filled(**kwargs)
                elif notification_type == NotificationType.POSITION_OPEN:
                    await self.telegram.notify_position_opened(**kwargs)
                elif notification_type == NotificationType.POSITION_CLOSE:
                    await self.telegram.notify_position_closed(**kwargs)
                elif notification_type == NotificationType.STOP_LOSS:
                    await self.telegram.notify_stop_loss(**kwargs)
                elif notification_type == NotificationType.TAKE_PROFIT:
                    await self.telegram.notify_take_profit(**kwargs)
                elif notification_type == NotificationType.DAILY_REPORT:
                    await self.telegram.notify_daily_report(**kwargs)
                elif notification_type == NotificationType.ERROR:
                    await self.telegram.notify_error(**kwargs)
            except Exception as e:
                print(f"알림 전송 실패: {e}")
