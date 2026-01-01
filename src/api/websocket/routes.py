"""
WebSocket 라우터
- WebSocket 엔드포인트
- 메시지 핸들링
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
import uuid
import json

from .connection_manager import ConnectionManager
from .realtime_streamer import RealtimeStreamer
from ...core.broker import MockBrokerClient

router = APIRouter()

# 전역 인스턴스
manager = ConnectionManager()
_streamer: Optional[RealtimeStreamer] = None


def get_streamer() -> RealtimeStreamer:
    """스트리머 인스턴스 가져오기"""
    global _streamer
    if _streamer is None:
        broker = MockBrokerClient()
        _streamer = RealtimeStreamer(broker, manager)
    return _streamer


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 메인 엔드포인트"""
    client_id = str(uuid.uuid4())

    await manager.connect(websocket, client_id)

    # 스트리머 시작
    streamer = get_streamer()
    if not streamer._running:
        await streamer.start()

    try:
        while True:
            data = await websocket.receive_text()
            await handle_message(client_id, data)
    except WebSocketDisconnect:
        await manager.disconnect(client_id)


async def handle_message(client_id: str, message: str):
    """메시지 핸들링"""
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        await manager.send_personal(client_id, {
            "type": "error",
            "message": "Invalid JSON format"
        })
        return

    msg_type = data.get("type", "")

    if msg_type == "subscribe":
        await handle_subscribe(client_id, data)

    elif msg_type == "unsubscribe":
        await handle_unsubscribe(client_id, data)

    elif msg_type == "subscribe_channel":
        await handle_channel_subscribe(client_id, data)

    elif msg_type == "unsubscribe_channel":
        await handle_channel_unsubscribe(client_id, data)

    elif msg_type == "ping":
        await manager.send_personal(client_id, {"type": "pong"})

    elif msg_type == "get_subscriptions":
        stocks = manager.get_subscribed_stocks(client_id)
        await manager.send_personal(client_id, {
            "type": "subscriptions",
            "stocks": stocks
        })

    else:
        await manager.send_personal(client_id, {
            "type": "error",
            "message": f"Unknown message type: {msg_type}"
        })


async def handle_subscribe(client_id: str, data: dict):
    """종목 구독 처리"""
    stock_codes = data.get("stock_codes", [])
    if isinstance(stock_codes, str):
        stock_codes = [stock_codes]

    for stock_code in stock_codes:
        manager.subscribe_stock(client_id, stock_code)

    await manager.send_personal(client_id, {
        "type": "subscribed",
        "stock_codes": stock_codes,
        "message": f"Subscribed to {len(stock_codes)} stocks"
    })


async def handle_unsubscribe(client_id: str, data: dict):
    """종목 구독 해제 처리"""
    stock_codes = data.get("stock_codes", [])
    if isinstance(stock_codes, str):
        stock_codes = [stock_codes]

    for stock_code in stock_codes:
        manager.unsubscribe_stock(client_id, stock_code)

    await manager.send_personal(client_id, {
        "type": "unsubscribed",
        "stock_codes": stock_codes
    })


async def handle_channel_subscribe(client_id: str, data: dict):
    """채널 구독 처리"""
    channels = data.get("channels", [])
    if isinstance(channels, str):
        channels = [channels]

    valid_channels = ["signals", "positions", "orders", "market"]

    for channel in channels:
        if channel in valid_channels:
            manager.subscribe_channel(client_id, channel)

    await manager.send_personal(client_id, {
        "type": "channel_subscribed",
        "channels": [c for c in channels if c in valid_channels]
    })


async def handle_channel_unsubscribe(client_id: str, data: dict):
    """채널 구독 해제 처리"""
    channels = data.get("channels", [])
    if isinstance(channels, str):
        channels = [channels]

    for channel in channels:
        manager.unsubscribe_channel(client_id, channel)

    await manager.send_personal(client_id, {
        "type": "channel_unsubscribed",
        "channels": channels
    })


# 상태 조회용 HTTP 엔드포인트
@router.get("/ws/status")
async def get_websocket_status():
    """WebSocket 상태 조회"""
    return {
        "connected_clients": manager.get_connection_count(),
        "subscribed_stocks": manager.get_all_subscribed_stocks()
    }
