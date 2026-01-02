"use client";

import { useState } from "react";
import { Quote, SignalType } from "@/types";
import OrderModal, { OrderRequest } from "./OrderModal";

interface TradePanelProps {
  quote: Quote | null;
  signal?: SignalType;
  score?: number;
  onOrderSubmit?: (side: "BUY" | "SELL", order: OrderRequest) => Promise<void>;
}

export default function TradePanel({
  quote,
  signal,
  score,
  onOrderSubmit,
}: TradePanelProps) {
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [orderSide, setOrderSide] = useState<"BUY" | "SELL">("BUY");

  const handleOpenOrder = (side: "BUY" | "SELL") => {
    setOrderSide(side);
    setShowOrderModal(true);
  };

  const handleOrderSubmit = async (order: OrderRequest) => {
    if (onOrderSubmit) {
      await onOrderSubmit(orderSide, order);
    }
  };

  if (!quote) {
    return (
      <div className="glass-card p-6">
        <div className="text-center text-muted">
          <svg
            className="w-12 h-12 mx-auto mb-3 opacity-50"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
            />
          </svg>
          <p className="text-sm">종목을 선택해주세요</p>
        </div>
      </div>
    );
  }

  const isPositive = quote.change_rate >= 0;
  const signalColors: Record<SignalType, string> = {
    STRONG_BUY: "from-rose-500 to-orange-500",
    BUY: "from-orange-500 to-amber-500",
    WATCH: "from-amber-500 to-yellow-500",
    HOLD: "from-slate-400 to-slate-500",
    SELL: "from-cyan-500 to-blue-500",
  };

  return (
    <>
      <div className="glass-card overflow-hidden">
        {/* Header with stock info */}
        <div className="p-5 border-b border-[var(--card-border)]">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-xl font-bold text-[var(--foreground)]">
                {quote.name}
              </h3>
              <p className="text-sm text-muted font-mono">{quote.stock_code}</p>
            </div>
            {signal && (
              <div
                className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase text-white bg-gradient-to-r ${signalColors[signal]} shadow-lg`}
              >
                {signal.replace("_", " ")}
              </div>
            )}
          </div>

          {/* Price */}
          <div className="flex items-end justify-between">
            <div>
              <p className="text-3xl font-bold text-[var(--foreground)] tabular-nums">
                {quote.price.toLocaleString()}
                <span className="text-sm font-medium text-muted ml-1">원</span>
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-sm font-bold ${
                    isPositive
                      ? "bg-emerald-500/15 text-emerald-400"
                      : "bg-rose-500/15 text-rose-400"
                  }`}
                >
                  <svg
                    className={`w-3 h-3 ${isPositive ? "" : "rotate-180"}`}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  {Math.abs(quote.change).toLocaleString()}
                </span>
                <span
                  className={`text-sm font-bold ${
                    isPositive ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {quote.change_rate.toFixed(2)}%
                </span>
              </div>
            </div>

            {score !== undefined && (
              <div className="text-right">
                <p className="text-xs text-muted uppercase tracking-wider">
                  Score
                </p>
                <p
                  className={`text-2xl font-bold tabular-nums ${
                    score >= 80
                      ? "text-emerald-400"
                      : score >= 60
                      ? "text-amber-400"
                      : "text-muted"
                  }`}
                >
                  {score.toFixed(0)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-px bg-[var(--card-border)]">
          <div className="bg-[var(--card)] p-3 text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              시가
            </p>
            <p className="text-sm font-semibold text-[var(--foreground)] tabular-nums">
              {quote.open.toLocaleString()}
            </p>
          </div>
          <div className="bg-[var(--card)] p-3 text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              고가
            </p>
            <p className="text-sm font-semibold text-emerald-400 tabular-nums">
              {quote.high.toLocaleString()}
            </p>
          </div>
          <div className="bg-[var(--card)] p-3 text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              저가
            </p>
            <p className="text-sm font-semibold text-rose-400 tabular-nums">
              {quote.low.toLocaleString()}
            </p>
          </div>
          <div className="bg-[var(--card)] p-3 text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              거래량
            </p>
            <p className="text-sm font-semibold text-[var(--foreground)] tabular-nums">
              {quote.volume >= 1000000
                ? `${(quote.volume / 1000000).toFixed(1)}M`
                : `${(quote.volume / 1000).toFixed(0)}K`}
            </p>
          </div>
        </div>

        {/* Order Buttons */}
        <div className="p-5">
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => handleOpenOrder("BUY")}
              className="group relative py-4 rounded-xl font-bold text-white overflow-hidden transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              {/* Background */}
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500 to-cyan-500" />
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />

              {/* Glow */}
              <div className="absolute inset-0 shadow-lg shadow-emerald-500/30 group-hover:shadow-emerald-500/50 transition-shadow" />

              {/* Content */}
              <span className="relative flex items-center justify-center gap-2">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2.5}
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                  />
                </svg>
                매수
              </span>
            </button>

            <button
              onClick={() => handleOpenOrder("SELL")}
              className="group relative py-4 rounded-xl font-bold text-white overflow-hidden transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              {/* Background */}
              <div className="absolute inset-0 bg-gradient-to-r from-rose-500 to-orange-500" />
              <div className="absolute inset-0 bg-gradient-to-r from-rose-400 to-orange-400 opacity-0 group-hover:opacity-100 transition-opacity" />

              {/* Glow */}
              <div className="absolute inset-0 shadow-lg shadow-rose-500/30 group-hover:shadow-rose-500/50 transition-shadow" />

              {/* Content */}
              <span className="relative flex items-center justify-center gap-2">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2.5}
                    d="M20 12H4"
                  />
                </svg>
                매도
              </span>
            </button>
          </div>

          {/* Quick order shortcuts */}
          <div className="mt-3 grid grid-cols-4 gap-2">
            {[
              { label: "1주 매수", qty: 1, side: "BUY" as const },
              { label: "10주 매수", qty: 10, side: "BUY" as const },
              { label: "1주 매도", qty: 1, side: "SELL" as const },
              { label: "전량 매도", qty: -1, side: "SELL" as const },
            ].map((shortcut, i) => (
              <button
                key={i}
                onClick={() => handleOpenOrder(shortcut.side)}
                className={`py-2 px-2 rounded-lg text-[10px] font-semibold transition-all ${
                  shortcut.side === "BUY"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20"
                    : "bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20"
                }`}
              >
                {shortcut.label}
              </button>
            ))}
          </div>
        </div>

        {/* Signal Recommendation */}
        {signal && (
          <div className="px-5 pb-5">
            <div
              className={`p-4 rounded-xl border ${
                signal === "STRONG_BUY" || signal === "BUY"
                  ? "bg-emerald-500/5 border-emerald-500/20"
                  : signal === "SELL"
                  ? "bg-rose-500/5 border-rose-500/20"
                  : "bg-amber-500/5 border-amber-500/20"
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    signal === "STRONG_BUY" || signal === "BUY"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : signal === "SELL"
                      ? "bg-rose-500/20 text-rose-400"
                      : "bg-amber-500/20 text-amber-400"
                  }`}
                >
                  {signal === "STRONG_BUY" || signal === "BUY" ? (
                    <svg
                      className="w-4 h-4"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : signal === "SELL" ? (
                    <svg
                      className="w-4 h-4"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M12 13a1 1 0 100 2h5a1 1 0 001-1V9a1 1 0 10-2 0v2.586l-4.293-4.293a1 1 0 00-1.414 0L8 9.586 3.707 5.293a1 1 0 00-1.414 1.414l5 5a1 1 0 001.414 0L11 9.414 14.586 13H12z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="w-4 h-4"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
                <div>
                  <p
                    className={`text-sm font-semibold ${
                      signal === "STRONG_BUY" || signal === "BUY"
                        ? "text-emerald-400"
                        : signal === "SELL"
                        ? "text-rose-400"
                        : "text-amber-400"
                    }`}
                  >
                    {signal === "STRONG_BUY"
                      ? "강력 매수 추천"
                      : signal === "BUY"
                      ? "매수 추천"
                      : signal === "SELL"
                      ? "매도 추천"
                      : signal === "WATCH"
                      ? "관심 종목"
                      : "보유 유지"}
                  </p>
                  <p className="text-xs text-muted mt-0.5">
                    {signal === "STRONG_BUY"
                      ? "여러 지표가 강한 매수 신호를 보이고 있습니다"
                      : signal === "BUY"
                      ? "긍정적인 신호가 감지되었습니다"
                      : signal === "SELL"
                      ? "하락 신호가 감지되어 매도를 고려하세요"
                      : signal === "WATCH"
                      ? "주시하며 진입 타이밍을 기다리세요"
                      : "현재 포지션을 유지하세요"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Order Modal */}
      <OrderModal
        isOpen={showOrderModal}
        onClose={() => setShowOrderModal(false)}
        quote={quote}
        side={orderSide}
        onSubmit={handleOrderSubmit}
      />
    </>
  );
}
