"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Header,
  StockCard,
  PositionCard,
  SignalAlert,
  StatCard,
  TradePanel,
  AutoTraderPanel,
} from "@/components";
import { useWebSocket } from "@/hooks/useWebSocket";
import { stocksApi, portfolioApi, signalsApi, ordersApi } from "@/lib/api";
import { Quote, Position, SignalType, WSMessage } from "@/types";
import { OrderRequest } from "@/components/OrderModal";

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
  const [tradingStyle, setTradingStyle] = useState("DAYTRADING");
  const [selectedStock, setSelectedStock] = useState<Quote | null>(null);
  const [selectedSignal, setSelectedSignal] = useState<SignalType | undefined>(undefined);
  const [orderSuccess, setOrderSuccess] = useState<string | null>(null);
  const [balance, setBalance] = useState({
    total_asset: 10000000,
    available_cash: 5000000,
    total_pnl: 150000,
    total_pnl_rate: 1.5,
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
      setSignals((prev) =>
        [message as unknown as SignalData, ...prev].slice(0, 10)
      );
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
        const codes = response.data.items
          .slice(0, 12)
          .map((s: any) => s.stock_code);
        subscribe(codes);
      }
    } catch (error) {
      console.error("Failed to load stocks:", error);
      // Mock data for demo
      setStocks([
        {
          stock_code: "005930",
          name: "삼성전자",
          price: 72500,
          change: 1500,
          change_rate: 2.11,
          volume: 15234567,
          high: 73000,
          low: 71500,
          open: 71800,
          prev_close: 71000,
          timestamp: new Date().toISOString(),
        },
        {
          stock_code: "000660",
          name: "SK하이닉스",
          price: 178000,
          change: -2000,
          change_rate: -1.11,
          volume: 3456789,
          high: 180000,
          low: 176500,
          open: 179500,
          prev_close: 180000,
          timestamp: new Date().toISOString(),
        },
        {
          stock_code: "035720",
          name: "카카오",
          price: 52300,
          change: 800,
          change_rate: 1.55,
          volume: 2345678,
          high: 52800,
          low: 51200,
          open: 51500,
          prev_close: 51500,
          timestamp: new Date().toISOString(),
        },
        {
          stock_code: "035420",
          name: "NAVER",
          price: 215000,
          change: 3500,
          change_rate: 1.65,
          volume: 1234567,
          high: 216500,
          low: 212000,
          open: 212500,
          prev_close: 211500,
          timestamp: new Date().toISOString(),
        },
        {
          stock_code: "051910",
          name: "LG화학",
          price: 385000,
          change: -5000,
          change_rate: -1.28,
          volume: 567890,
          high: 390000,
          low: 383000,
          open: 389000,
          prev_close: 390000,
          timestamp: new Date().toISOString(),
        },
        {
          stock_code: "006400",
          name: "삼성SDI",
          price: 425000,
          change: 8000,
          change_rate: 1.92,
          volume: 456789,
          high: 428000,
          low: 418000,
          open: 419000,
          prev_close: 417000,
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  };

  const loadPositions = async () => {
    try {
      const response = await portfolioApi.getPositions();
      if (response.success) {
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
      // Mock data
      setPositions([
        {
          position_id: "1",
          stock_code: "005930",
          stock_name: "삼성전자",
          quantity: 50,
          entry_price: 71000,
          current_price: 72500,
          unrealized_pnl: 75000,
          unrealized_pnl_pct: 2.11,
          status: "OPEN",
        },
      ]);
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

  const loadSignals = async () => {
    try {
      const response = await signalsApi.getTopSignals(tradingStyle, 10);
      if (response.success && response.data) {
        const mappedSignals = response.data.map((s: any) => ({
          stock_code: s.stock_code,
          stock_name: s.stock_name,
          signal: s.signal as SignalType,
          score: s.total_score,
          reasons: s.reasons || [],
          timestamp: s.timestamp || new Date().toISOString(),
        }));
        setSignals(mappedSignals);
      }
    } catch (error) {
      console.error("Failed to load signals:", error);
      // Fallback demo signals
      setSignals([
        {
          stock_code: "005930",
          stock_name: "삼성전자",
          signal: "STRONG_BUY" as SignalType,
          score: 87.5,
          reasons: [
            "총점 87.5점 - 강력 매수 신호",
            "[거래량] 전일 대비 350% 폭발적 증가",
            "[체결강도] 145% 매수세 강함",
          ],
          timestamp: new Date().toISOString(),
        },
        {
          stock_code: "035420",
          stock_name: "NAVER",
          signal: "BUY" as SignalType,
          score: 75.2,
          reasons: [
            "총점 75.2점 - 매수 신호",
            "[VWAP] 상단 돌파",
            "[RSI] 55 중립권 상승 중",
          ],
          timestamp: new Date(Date.now() - 300000).toISOString(),
        },
      ]);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([loadStocks(), loadPositions(), loadBalance(), loadSignals()]);
      setLoading(false);
    };
    init();
  }, []);

  // Reload signals when trading style changes
  useEffect(() => {
    if (!loading) {
      loadSignals();
    }
  }, [tradingStyle]);

  // Handle stock selection
  const handleStockSelect = (stock: Quote) => {
    setSelectedStock(stock);
    // Find matching signal for this stock
    const matchingSignal = signals.find(s => s.stock_code === stock.stock_code);
    setSelectedSignal(matchingSignal?.signal);
  };

  // Handle order submission
  const handleOrderSubmit = async (side: "BUY" | "SELL", order: OrderRequest) => {
    try {
      const response = side === "BUY"
        ? await ordersApi.buy(order)
        : await ordersApi.sell(order);

      if (response.status === "FILLED" || response.status === "SUBMITTED") {
        setOrderSuccess(`${side === "BUY" ? "매수" : "매도"} 주문이 ${response.status === "FILLED" ? "체결" : "접수"}되었습니다`);
        // Reload positions and balance
        loadPositions();
        loadBalance();

        // Clear success message after 3 seconds
        setTimeout(() => setOrderSuccess(null), 3000);
      } else {
        throw new Error(response.message || "주문 처리 실패");
      }
    } catch (error) {
      throw error;
    }
  };

  const totalPnl = positions.reduce((sum, p) => sum + p.unrealized_pnl, 0);
  const openPositions = positions.filter((p) => p.status === "OPEN");

  if (loading) {
    return (
      <div className="min-h-screen gradient-mesh flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 animate-pulse" />
            <div className="absolute inset-0 w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 animate-ping opacity-20" />
          </div>
          <p className="mt-6 text-[var(--muted)] font-medium">로딩중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen gradient-mesh">
      <Header
        isConnected={isConnected}
        tradingStyle={tradingStyle}
        onStyleChange={setTradingStyle}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            title="총 자산"
            value={`${(balance.total_asset / 10000).toFixed(0)}만`}
            subValue="전일 대비"
            icon="💰"
            gradient="purple"
          />
          <StatCard
            title="가용 현금"
            value={`${(balance.available_cash / 10000).toFixed(0)}만`}
            subValue="투자 가능"
            icon="💵"
            gradient="blue"
          />
          <StatCard
            title="보유 포지션"
            value={openPositions.length}
            subValue={`${totalPnl >= 0 ? "+" : ""}${totalPnl.toLocaleString()}원`}
            trend={totalPnl >= 0 ? "up" : "down"}
            icon="📊"
            gradient="green"
          />
          <StatCard
            title="총 수익률"
            value={`${balance.total_pnl_rate >= 0 ? "+" : ""}${balance.total_pnl_rate.toFixed(2)}%`}
            subValue="누적 수익"
            trend={balance.total_pnl_rate >= 0 ? "up" : "down"}
            icon="📈"
            gradient={balance.total_pnl_rate >= 0 ? "green" : "pink"}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left - Stock List */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-xl font-bold text-[var(--foreground)]">
                  관심 종목
                </h2>
                <p className="text-sm text-[var(--muted)]">
                  실시간 시세를 확인하세요
                </p>
              </div>
              <button className="px-4 py-2 rounded-xl text-sm font-medium text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-500/10 transition-colors">
                전체보기 →
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {stocks.map((stock, idx) => {
                const stockSignal = signals.find(s => s.stock_code === stock.stock_code);
                return (
                  <div
                    key={stock.stock_code}
                    className={`animate-slide-up ${selectedStock?.stock_code === stock.stock_code ? 'ring-2 ring-violet-500 rounded-2xl' : ''}`}
                    style={{ animationDelay: `${idx * 50}ms` }}
                  >
                    <StockCard
                      quote={stock}
                      signal={stockSignal?.signal}
                      score={stockSignal?.score}
                      onClick={() => handleStockSelect(stock)}
                    />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right - Auto Trader, Trade Panel, Signals & Positions */}
          <div className="space-y-6">
            {/* Auto Trader Panel */}
            <AutoTraderPanel />

            {/* Trade Panel */}
            <TradePanel
              quote={selectedStock}
              signal={selectedSignal}
              score={signals.find(s => s.stock_code === selectedStock?.stock_code)?.score}
              onOrderSubmit={handleOrderSubmit}
            />
            {/* Signals */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-[var(--foreground)]">
                    매매 신호
                  </h2>
                  <p className="text-sm text-[var(--muted)]">
                    AI 분석 결과
                  </p>
                </div>
                {signals.length > 0 && (
                  <span className="px-2 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-500">
                    {signals.length}개
                  </span>
                )}
              </div>

              {signals.length > 0 ? (
                <div className="space-y-0">
                  {signals.map((signal, idx) => (
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
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-[var(--card)] rounded-2xl border border-[var(--border)]">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--secondary)] flex items-center justify-center">
                    <span className="text-3xl">📭</span>
                  </div>
                  <p className="text-[var(--muted)] font-medium">
                    새로운 신호가 없습니다
                  </p>
                  <p className="text-sm text-[var(--muted)] mt-1">
                    시장을 모니터링 중입니다
                  </p>
                </div>
              )}
            </div>

            {/* Positions */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-[var(--foreground)]">
                    보유 포지션
                  </h2>
                  <p className="text-sm text-[var(--muted)]">
                    실시간 손익 현황
                  </p>
                </div>
                {openPositions.length > 0 && (
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      totalPnl >= 0
                        ? "bg-emerald-500/10 text-emerald-500"
                        : "bg-rose-500/10 text-rose-500"
                    }`}
                  >
                    {totalPnl >= 0 ? "+" : ""}
                    {totalPnl.toLocaleString()}원
                  </span>
                )}
              </div>

              {openPositions.length > 0 ? (
                <div className="space-y-4">
                  {openPositions.map((position, idx) => (
                    <div
                      key={position.position_id}
                      className="animate-slide-up"
                      style={{ animationDelay: `${idx * 100}ms` }}
                    >
                      <PositionCard position={position} />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-[var(--card)] rounded-2xl border border-[var(--border)]">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--secondary)] flex items-center justify-center">
                    <span className="text-3xl">📋</span>
                  </div>
                  <p className="text-[var(--muted)] font-medium">
                    보유 포지션이 없습니다
                  </p>
                  <p className="text-sm text-[var(--muted)] mt-1">
                    신호를 확인하고 진입하세요
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Order Success Toast */}
      {orderSuccess && (
        <div className="fixed bottom-6 right-6 z-50 animate-slide-up">
          <div className="flex items-center gap-3 px-5 py-4 rounded-2xl bg-emerald-500 text-white shadow-lg shadow-emerald-500/30">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <span className="font-semibold">{orderSuccess}</span>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-[var(--border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-[var(--muted)]">
              © 2024 WeightedTrader. Smart Auto Trading System.
            </p>
            <div className="flex items-center gap-4">
              <span className="text-xs text-[var(--muted)]">
                Powered by AI
              </span>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-xs text-[var(--muted)]">
                  System Online
                </span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
