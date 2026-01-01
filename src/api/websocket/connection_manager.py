"""
WebSocket 연결 관리자
- 클라이언트 연결 관리
- 브로드캐스트
- 구독 관리
"""
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
import json
import asyncio


class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # 활성 연결 목록
        self._connections: Dict[str, WebSocket] = {}
        # 종목별 구독자
        self._subscriptions: Dict[str, Set[str]] = {}
        # 채널별 구독자
        self._channel_subs: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """클라이언트 연결"""
        await websocket.accept()
        self._connections[client_id] = websocket
        await self._send_welcome(websocket, client_id)

    async def disconnect(self, client_id: str):
        """클라이언트 연결 해제"""
        if client_id in self._connections:
            del self._connections[client_id]

        # 구독 정리
        for stock_code in list(self._subscriptions.keys()):
            self._subscriptions[stock_code].discard(client_id)
            if not self._subscriptions[stock_code]:
                del self._subscriptions[stock_code]

        for channel in list(self._channel_subs.keys()):
            self._channel_subs[channel].discard(client_id)
            if not self._channel_subs[channel]:
                del self._channel_subs[channel]

    async def _send_welcome(self, websocket: WebSocket, client_id: str):
        """환영 메시지 전송"""
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "message": "WebSocket connected successfully"
        })

    async def send_personal(self, client_id: str, data: dict):
        """개인 메시지 전송"""
        if client_id in self._connections:
            try:
                await self._connections[client_id].send_json(data)
            except Exception:
                await self.disconnect(client_id)

    async def broadcast(self, data: dict, exclude: Optional[Set[str]] = None):
        """전체 브로드캐스트"""
        exclude = exclude or set()
        disconnected = []

        for client_id, websocket in self._connections.items():
            if client_id in exclude:
                continue
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected.append(client_id)

        for client_id in disconnected:
            await self.disconnect(client_id)

    async def broadcast_to_channel(self, channel: str, data: dict):
        """채널 브로드캐스트"""
        if channel not in self._channel_subs:
            return

        disconnected = []
        for client_id in self._channel_subs[channel]:
            if client_id in self._connections:
                try:
                    await self._connections[client_id].send_json(data)
                except Exception:
                    disconnected.append(client_id)

        for client_id in disconnected:
            await self.disconnect(client_id)

    async def broadcast_stock_update(self, stock_code: str, data: dict):
        """종목별 업데이트 브로드캐스트"""
        if stock_code not in self._subscriptions:
            return

        message = {
            "type": "stock_update",
            "stock_code": stock_code,
            "data": data
        }

        disconnected = []
        for client_id in self._subscriptions[stock_code]:
            if client_id in self._connections:
                try:
                    await self._connections[client_id].send_json(message)
                except Exception:
                    disconnected.append(client_id)

        for client_id in disconnected:
            await self.disconnect(client_id)

    def subscribe_stock(self, client_id: str, stock_code: str):
        """종목 구독"""
        if stock_code not in self._subscriptions:
            self._subscriptions[stock_code] = set()
        self._subscriptions[stock_code].add(client_id)

    def unsubscribe_stock(self, client_id: str, stock_code: str):
        """종목 구독 해제"""
        if stock_code in self._subscriptions:
            self._subscriptions[stock_code].discard(client_id)

    def subscribe_channel(self, client_id: str, channel: str):
        """채널 구독"""
        if channel not in self._channel_subs:
            self._channel_subs[channel] = set()
        self._channel_subs[channel].add(client_id)

    def unsubscribe_channel(self, client_id: str, channel: str):
        """채널 구독 해제"""
        if channel in self._channel_subs:
            self._channel_subs[channel].discard(client_id)

    def get_subscribed_stocks(self, client_id: str) -> List[str]:
        """클라이언트가 구독 중인 종목 목록"""
        return [
            stock_code
            for stock_code, clients in self._subscriptions.items()
            if client_id in clients
        ]

    def get_stock_subscribers(self, stock_code: str) -> Set[str]:
        """종목 구독자 목록"""
        return self._subscriptions.get(stock_code, set())

    def get_connection_count(self) -> int:
        """연결된 클라이언트 수"""
        return len(self._connections)

    def get_all_subscribed_stocks(self) -> List[str]:
        """구독 중인 모든 종목 목록"""
        return list(self._subscriptions.keys())
