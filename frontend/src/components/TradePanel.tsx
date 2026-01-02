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
      <div className="bg-white dark:bg-zinc-900 rounded-3xl border border-zinc-100 dark:border-zinc-800 p-8">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
            <svg className="w-7 h-7 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <p className="text-sm text-zinc-500">종목을 선택해주세요</p>
        </div>
      </div>
    );
  }

  const isPositive = quote.change_rate >= 0;

  return (
    <>
      <div className="bg-white dark:bg-zinc-900 rounded-3xl border border-zinc-100 dark:border-zinc-800 overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-zinc-100 dark:border-zinc-800">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className={`w-11 h-11 rounded-full p-[2px] bg-gradient-to-r ${
                isPositive ? "from-green-500 to-emerald-500" : "from-red-500 to-rose-500"
              }`}>
                <div className="w-full h-full rounded-full bg-white dark:bg-zinc-900 flex items-center justify-center font-bold text-sm text-zinc-700 dark:text-zinc-300">
                  {quote.name.charAt(0)}
                </div>
              </div>
              <div>
                <h3 className="font-bold text-zinc-900 dark:text-white">
                  {quote.name}
                </h3>
                <p className="text-xs text-zinc-400 font-mono">{quote.stock_code}</p>
              </div>
            </div>
            {signal && (
              <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold text-white bg-gradient-to-r ${
                signal === "STRONG_BUY" ? "from-rose-500 to-orange-500" :
                signal === "BUY" ? "from-orange-500 to-amber-500" :
                signal === "SELL" ? "from-blue-500 to-cyan-500" :
                "from-zinc-400 to-zinc-500"
              }`}>
                {signal.replace("_", " ")}
              </span>
            )}
          </div>

          {/* Price */}
          <div className="flex items-end justify-between">
            <div>
              <p className="text-2xl font-bold text-zinc-900 dark:text-white tabular-nums">
                {quote.price.toLocaleString()}
                <span className="text-sm font-normal text-zinc-400 ml-1">원</span>
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                  isPositive
                    ? "bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-400"
                    : "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400"
                }`}>
                  {isPositive ? "+" : ""}{quote.change.toLocaleString()}
                </span>
                <span className={`text-sm font-bold ${
                  isPositive ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                }`}>
                  {isPositive ? "+" : ""}{quote.change_rate.toFixed(2)}%
                </span>
              </div>
            </div>
            {score !== undefined && (
              <div className="text-right">
                <p className="text-[10px] text-zinc-400 uppercase tracking-wider">Score</p>
                <p className={`text-xl font-bold ${
                  score >= 80 ? "text-green-600 dark:text-green-400" :
                  score >= 60 ? "text-amber-600 dark:text-amber-400" :
                  "text-zinc-500"
                }`}>
                  {score.toFixed(0)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-4 divide-x divide-zinc-100 dark:divide-zinc-800 bg-zinc-50 dark:bg-zinc-800/30">
          <div className="p-3 text-center">
            <p className="text-[10px] text-zinc-400 uppercase">시가</p>
            <p className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 tabular-nums">
              {quote.open.toLocaleString()}
            </p>
          </div>
          <div className="p-3 text-center">
            <p className="text-[10px] text-zinc-400 uppercase">고가</p>
            <p className="text-sm font-semibold text-green-600 dark:text-green-400 tabular-nums">
              {quote.high.toLocaleString()}
            </p>
          </div>
          <div className="p-3 text-center">
            <p className="text-[10px] text-zinc-400 uppercase">저가</p>
            <p className="text-sm font-semibold text-red-600 dark:text-red-400 tabular-nums">
              {quote.low.toLocaleString()}
            </p>
          </div>
          <div className="p-3 text-center">
            <p className="text-[10px] text-zinc-400 uppercase">거래량</p>
            <p className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 tabular-nums">
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
              className="py-3.5 rounded-2xl font-bold text-white bg-gradient-to-r from-green-500 to-emerald-500 hover:opacity-90 transition-opacity active:scale-[0.98]"
            >
              <span className="flex items-center justify-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                매수
              </span>
            </button>
            <button
              onClick={() => handleOpenOrder("SELL")}
              className="py-3.5 rounded-2xl font-bold text-white bg-gradient-to-r from-rose-500 to-red-500 hover:opacity-90 transition-opacity active:scale-[0.98]"
            >
              <span className="flex items-center justify-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M20 12H4" />
                </svg>
                매도
              </span>
            </button>
          </div>

          {/* Quick Order Shortcuts */}
          <div className="mt-3 grid grid-cols-4 gap-2">
            {[
              { label: "1주", side: "BUY" as const },
              { label: "10주", side: "BUY" as const },
              { label: "1주", side: "SELL" as const },
              { label: "전량", side: "SELL" as const },
            ].map((shortcut, i) => (
              <button
                key={i}
                onClick={() => handleOpenOrder(shortcut.side)}
                className={`py-2 rounded-xl text-xs font-semibold transition-colors ${
                  shortcut.side === "BUY"
                    ? "bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-500/20"
                    : "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-500/20"
                }`}
              >
                {shortcut.label} {shortcut.side === "BUY" ? "매수" : "매도"}
              </button>
            ))}
          </div>
        </div>

        {/* Signal Recommendation */}
        {signal && (
          <div className="px-5 pb-5">
            <div className={`p-4 rounded-2xl ${
              signal === "STRONG_BUY" || signal === "BUY"
                ? "bg-green-50 dark:bg-green-500/5"
                : signal === "SELL"
                ? "bg-red-50 dark:bg-red-500/5"
                : "bg-amber-50 dark:bg-amber-500/5"
            }`}>
              <div className="flex items-start gap-3">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                  signal === "STRONG_BUY" || signal === "BUY"
                    ? "bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400"
                    : signal === "SELL"
                    ? "bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400"
                    : "bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400"
                }`}>
                  {signal === "STRONG_BUY" || signal === "BUY" ? "📈" :
                   signal === "SELL" ? "📉" : "👀"}
                </div>
                <div>
                  <p className={`text-sm font-bold ${
                    signal === "STRONG_BUY" || signal === "BUY"
                      ? "text-green-700 dark:text-green-400"
                      : signal === "SELL"
                      ? "text-red-700 dark:text-red-400"
                      : "text-amber-700 dark:text-amber-400"
                  }`}>
                    {signal === "STRONG_BUY" ? "강력 매수 추천" :
                     signal === "BUY" ? "매수 추천" :
                     signal === "SELL" ? "매도 추천" :
                     signal === "WATCH" ? "관심 종목" : "보유 유지"}
                  </p>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    {signal === "STRONG_BUY" ? "여러 지표가 강한 매수 신호를 보이고 있습니다" :
                     signal === "BUY" ? "긍정적인 신호가 감지되었습니다" :
                     signal === "SELL" ? "하락 신호가 감지되었습니다" :
                     signal === "WATCH" ? "진입 타이밍을 기다리세요" : "현재 포지션을 유지하세요"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

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
