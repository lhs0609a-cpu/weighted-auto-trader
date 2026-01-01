"use client";

import { Quote, SignalType } from "@/types";

interface StockCardProps {
  quote: Quote;
  signal?: SignalType;
  score?: number;
  onClick?: () => void;
}

const signalColors: Record<SignalType, string> = {
  STRONG_BUY: "bg-red-500 text-white",
  BUY: "bg-orange-500 text-white",
  WATCH: "bg-yellow-500 text-black",
  HOLD: "bg-gray-400 text-white",
  SELL: "bg-blue-500 text-white",
};

const signalLabels: Record<SignalType, string> = {
  STRONG_BUY: "강력매수",
  BUY: "매수",
  WATCH: "관심",
  HOLD: "대기",
  SELL: "매도",
};

export default function StockCard({
  quote,
  signal,
  score,
  onClick,
}: StockCardProps) {
  const isPositive = quote.change_rate >= 0;

  return (
    <div
      onClick={onClick}
      className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-lg transition-shadow cursor-pointer"
    >
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-white">
            {quote.name}
          </h3>
          <p className="text-xs text-gray-500">{quote.stock_code}</p>
        </div>
        {signal && (
          <span
            className={`px-2 py-0.5 rounded text-xs font-medium ${signalColors[signal]}`}
          >
            {signalLabels[signal]}
          </span>
        )}
      </div>

      <div className="flex justify-between items-end">
        <div>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            {quote.price.toLocaleString()}원
          </p>
          <p
            className={`text-sm font-medium ${
              isPositive ? "text-red-500" : "text-blue-500"
            }`}
          >
            {isPositive ? "+" : ""}
            {quote.change.toLocaleString()} ({isPositive ? "+" : ""}
            {quote.change_rate.toFixed(2)}%)
          </p>
        </div>

        {score !== undefined && (
          <div className="text-right">
            <p className="text-xs text-gray-500">점수</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white">
              {score.toFixed(1)}
            </p>
          </div>
        )}
      </div>

      <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
        <p className="text-xs text-gray-500">
          거래량 {(quote.volume / 1000).toFixed(0)}K
        </p>
      </div>
    </div>
  );
}
