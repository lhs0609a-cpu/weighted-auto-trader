"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { WSMessage } from "@/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws";

interface UseWebSocketOptions {
  onMessage?: (message: WSMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoConnect?: boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { onMessage, onConnect, onDisconnect, autoConnect = true } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      setIsConnected(true);
      onConnect?.();
    };

    ws.onclose = () => {
      setIsConnected(false);
      onDisconnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSMessage;
        setLastMessage(message);
        onMessage?.(message);
      } catch (e) {
        console.error("WebSocket message parse error:", e);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    wsRef.current = ws;
  }, [onMessage, onConnect, onDisconnect]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const subscribe = useCallback(
    (stockCodes: string | string[]) => {
      sendMessage({
        type: "subscribe",
        stock_codes: Array.isArray(stockCodes) ? stockCodes : [stockCodes],
      });
    },
    [sendMessage]
  );

  const unsubscribe = useCallback(
    (stockCodes: string | string[]) => {
      sendMessage({
        type: "unsubscribe",
        stock_codes: Array.isArray(stockCodes) ? stockCodes : [stockCodes],
      });
    },
    [sendMessage]
  );

  const subscribeChannel = useCallback(
    (channels: string | string[]) => {
      sendMessage({
        type: "subscribe_channel",
        channels: Array.isArray(channels) ? channels : [channels],
      });
    },
    [sendMessage]
  );

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    connect,
    disconnect,
    sendMessage,
    subscribe,
    unsubscribe,
    subscribeChannel,
  };
}
