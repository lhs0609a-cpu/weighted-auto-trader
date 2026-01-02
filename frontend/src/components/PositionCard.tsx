"use client";

import { Position } from "@/types";

interface PositionCardProps {
  position: Position;
  onClose?: () => void;
}

export default function PositionCard({ position, onClose }: PositionCardProps) {
  const isProfit = position.unrealized_pnl >= 0;
  const profitPercent = Math.abs(position.unrealized_pnl_pct);

  return (
    <div className={`relative rounded-2xl p-4 ${
      isProfit
        ? "bg-green-50 dark:bg-green-500/5"
        : "bg-red-50 dark:bg-red-500/5"
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Avatar with gradient ring */}
          <div className={`w-10 h-10 rounded-full p-[2px] bg-gradient-to-r ${
            isProfit
              ? "from-emerald-500 to-teal-500"
              : "from-rose-500 to-red-500"
          }`}>
            <div className="w-full h-full rounded-full bg-white dark:bg-zinc-900 flex items-center justify-center font-bold text-sm text-zinc-700 dark:text-zinc-300">
              {position.stock_name.charAt(0)}
            </div>
          </div>
          <div>
            <h3 className="font-bold text-zinc-900 dark:text-white text-sm">
              {position.stock_name}
            </h3>
            <p className="text-[10px] text-zinc-400 font-mono">
              {position.stock_code}
            </p>
          </div>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
          position.status === "OPEN"
            ? "bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400"
            : "bg-zinc-100 dark:bg-zinc-500/20 text-zinc-600 dark:text-zinc-400"
        }`}>
          {position.status === "OPEN" ? "보유" : "청산"}
        </span>
      </div>

      {/* PnL */}
      <div className="flex items-end justify-between mb-3">
        <div>
          <p className="text-[10px] text-zinc-400 uppercase tracking-wider mb-0.5">
            손익
          </p>
          <p className={`text-xl font-bold ${
            isProfit ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
          }`}>
            {isProfit ? "+" : ""}{position.unrealized_pnl.toLocaleString()}원
          </p>
        </div>
        <div className={`px-2.5 py-1 rounded-xl ${
          isProfit
            ? "bg-green-100 dark:bg-green-500/20"
            : "bg-red-100 dark:bg-red-500/20"
        }`}>
          <span className={`text-sm font-bold ${
            isProfit ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
          }`}>
            {isProfit ? "+" : "-"}{profitPercent.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-white dark:bg-zinc-800/50 rounded-xl py-2">
          <p className="text-[10px] text-zinc-400 mb-0.5">수량</p>
          <p className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
            {position.quantity}주
          </p>
        </div>
        <div className="bg-white dark:bg-zinc-800/50 rounded-xl py-2">
          <p className="text-[10px] text-zinc-400 mb-0.5">평단가</p>
          <p className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
            {position.entry_price.toLocaleString()}
          </p>
        </div>
        <div className="bg-white dark:bg-zinc-800/50 rounded-xl py-2">
          <p className="text-[10px] text-zinc-400 mb-0.5">현재가</p>
          <p className={`text-sm font-semibold ${
            isProfit ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
          }`}>
            {position.current_price.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Close button */}
      {onClose && position.status === "OPEN" && (
        <button
          onClick={onClose}
          className="mt-3 w-full py-2.5 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-[#833AB4] via-[#E1306C] to-[#F77737] hover:opacity-90 transition-opacity"
        >
          청산하기
        </button>
      )}
    </div>
  );
}
