"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Header,
  StockCard,
  PositionCard,
  SignalAlert,
  StatCard,
} from "@/components";
import { useWebSocket } from "@/hooks/useWebSocket";
import { stocksApi, portfolioApi } from "@/lib/api";
import { Quote, Position, SignalType, WSMessage } from "@/types";

interface SignalData {
  stock_code: string;
  stock_name: string;
  signal: SignalType;
  score: number;
  reasons: string[];
  timestamp: string;
}

export default function Dashboard() {
  const [stocks, setStocks] = useState<Quote[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [signals, setSignals] = useState<SignalData[]>([]);
  const [balance, setBalance] = useState({
    total_asset: 0,
    available_cash: 0,
    total_pnl: 0,
    total_pnl_rate: 0,
  });
  const [loading, setLoading] = useState(true);

  const handleMessage = useCallback((message: WSMessage) => {
    if (message.type === "stock_update") {
      setStocks((prev) => {
        const idx = prev.findIndex(
          (s) => s.stock_code === message.data.stock_code
        );
        if (idx >= 0) {
          const updated = [...prev];
          updated[idx] = { ...updated[idx], ...message.data };
          return updated;
        }
        return prev;
      });
    } else if (message.type === "signal_alert") {
      setSignals((prev) => [message as unknown as SignalData, ...prev].slice(0, 10));
    } else if (message.type === "position_update") {
      loadPositions();
    }
  }, []);

  const { isConnected, subscribe, subscribeChannel } = useWebSocket({
    onMessage: handleMessage,
    onConnect: () => {
      subscribeChannel(["signals", "positions"]);
    },
  });

  const loadStocks = async () => {
    try {
      const response = await stocksApi.getAll();
      if (response.success) {
        setStocks(response.data.items.slice(0, 12));
        // 종목 구독
        const codes = response.data.items.slice(0, 12).map((s: any) => s.stock_code);
        subscribe(codes);
      }
    } catch (error) {
      console.error("Failed to load stocks:", error);
    }
  };

  const loadPositions = async () => {
    try {
      const response = await portfolioApi.getPositions();
      if (response.success) {
        // API 응답을 Position 타입에 맞게 매핑
        const mappedPositions = (response.data.items || []).map((p: any) => ({
          position_id: p.stock_code,
          stock_code: p.stock_code,
          stock_name: p.stock_name,
          quantity: p.quantity,
          entry_price: p.avg_price,
          current_price: p.current_price,
          unrealized_pnl: p.pnl,
          unrealized_pnl_pct: p.pnl_rate,
          status: "OPEN",
        }));
        setPositions(mappedPositions);
      }
    } catch (error) {
      console.error("Failed to load positions:", error);
    }
  };

  const loadBalance = async () => {
    try {
      const response = await portfolioApi.getBalance();
      if (response.success) {
        setBalance(response.data);
      }
    } catch (error) {
      console.error("Failed to load balance:", error);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([loadStocks(), loadPositions(), loadBalance()]);
      setLoading(false);
    };
    init();
  }, []);

  const totalPnl = positions.reduce((sum, p) => sum + p.unrealized_pnl, 0);
  const openPositions = positions.filter((p) => p.status === "OPEN");

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">로딩중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header isConnected={isConnected} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 통계 카드 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="총 자산"
            value={`${(balance.total_asset / 10000).toFixed(0)}만원`}
            icon="💰"
          />
          <StatCard
            title="가용 현금"
            value={`${(balance.available_cash / 10000).toFixed(0)}만원`}
            icon="💵"
          />
          <StatCard
            title="보유 포지션"
            value={openPositions.length}
            subValue={`미실현 손익: ${totalPnl.toLocaleString()}원`}
            trend={totalPnl >= 0 ? "up" : "down"}
            icon="📊"
          />
          <StatCard
            title="총 수익률"
            value={`${balance.total_pnl_rate >= 0 ? "+" : ""}${balance.total_pnl_rate.toFixed(2)}%`}
            trend={balance.total_pnl_rate >= 0 ? "up" : "down"}
            icon="📈"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 왼쪽: 종목 목록 */}
          <div className="lg:col-span-2">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                관심 종목
              </h2>
              <button className="text-sm text-blue-500 hover:text-blue-600">
                더보기 →
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {stocks.map((stock) => (
                <StockCard
                  key={stock.stock_code}
                  quote={stock}
                  onClick={() => console.log("Stock clicked:", stock.stock_code)}
                />
              ))}
            </div>
          </div>

          {/* 오른쪽: 신호 알림 & 포지션 */}
          <div className="space-y-6">
            {/* 신호 알림 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                매매 신호
              </h2>
              {signals.length > 0 ? (
                signals.map((signal, idx) => (
                  <SignalAlert
                    key={`${signal.stock_code}-${idx}`}
                    stockCode={signal.stock_code}
                    stockName={signal.stock_name}
                    signal={signal.signal}
                    score={signal.score}
                    reasons={signal.reasons}
                    timestamp={signal.timestamp}
                    onDismiss={() =>
                      setSignals((prev) => prev.filter((_, i) => i !== idx))
                    }
                  />
                ))
              ) : (
                <div className="text-center py-8 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <p className="text-gray-500">새로운 신호가 없습니다</p>
                </div>
              )}
            </div>

            {/* 보유 포지션 */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                보유 포지션
              </h2>
              {openPositions.length > 0 ? (
                <div className="space-y-3">
                  {openPositions.map((position) => (
                    <PositionCard
                      key={position.position_id}
                      position={position}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <p className="text-gray-500">보유 포지션이 없습니다</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
