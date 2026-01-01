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
    <div className="relative bg-[var(--card)] rounded-2xl overflow-hidden border border-[var(--border)] card-hover">
      {/* Profit/Loss indicator bar */}
      <div
        className={`absolute top-0 left-0 right-0 h-1 ${
          isProfit
            ? "bg-gradient-to-r from-emerald-500 to-teal-500"
            : "bg-gradient-to-r from-rose-500 to-pink-500"
        }`}
      />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center text-white text-lg font-bold ${
                isProfit
                  ? "bg-gradient-to-br from-emerald-500 to-teal-500"
                  : "bg-gradient-to-br from-rose-500 to-pink-500"
              }`}
            >
              {position.stock_name.charAt(0)}
            </div>
            <div>
              <h3 className="font-bold text-[var(--foreground)]">
                {position.stock_name}
              </h3>
              <p className="text-xs text-[var(--muted)] font-mono">
                {position.stock_code}
              </p>
            </div>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              position.status === "OPEN"
                ? "bg-emerald-500/10 text-emerald-500"
                : "bg-slate-500/10 text-slate-500"
            }`}
          >
            {position.status === "OPEN" ? "보유중" : "청산"}
          </span>
        </div>

        {/* PnL Display */}
        <div
          className={`p-4 rounded-xl mb-4 ${
            isProfit ? "bg-emerald-500/5" : "bg-rose-500/5"
          }`}
        >
          <div className="flex items-end justify-between">
            <div>
              <p className="text-xs text-[var(--muted)] mb-1">평가손익</p>
              <p
                className={`text-2xl font-bold ${
                  isProfit ? "text-emerald-500" : "text-rose-500"
                }`}
              >
                {isProfit ? "+" : ""}
                {position.unrealized_pnl.toLocaleString()}
                <span className="text-sm ml-1">원</span>
              </p>
            </div>
            <div
              className={`text-right px-3 py-1.5 rounded-lg ${
                isProfit ? "bg-emerald-500/10" : "bg-rose-500/10"
              }`}
            >
              <span
                className={`text-lg font-bold ${
                  isProfit ? "text-emerald-500" : "text-rose-500"
                }`}
              >
                {isProfit ? "+" : "-"}
                {profitPercent.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-[var(--secondary)] rounded-xl p-3">
            <p className="text-xs text-[var(--muted)] mb-1">보유수량</p>
            <p className="font-bold text-[var(--foreground)]">
              {position.quantity.toLocaleString()}
              <span className="text-sm font-normal text-[var(--muted)] ml-1">
                주
              </span>
            </p>
          </div>
          <div className="bg-[var(--secondary)] rounded-xl p-3">
            <p className="text-xs text-[var(--muted)] mb-1">평균단가</p>
            <p className="font-bold text-[var(--foreground)]">
              {position.entry_price.toLocaleString()}
              <span className="text-sm font-normal text-[var(--muted)] ml-1">
                원
              </span>
            </p>
          </div>
          <div className="bg-[var(--secondary)] rounded-xl p-3">
            <p className="text-xs text-[var(--muted)] mb-1">현재가</p>
            <p className="font-bold text-[var(--foreground)]">
              {position.current_price.toLocaleString()}
              <span className="text-sm font-normal text-[var(--muted)] ml-1">
                원
              </span>
            </p>
          </div>
          <div className="bg-[var(--secondary)] rounded-xl p-3">
            <p className="text-xs text-[var(--muted)] mb-1">평가금액</p>
            <p className="font-bold text-[var(--foreground)]">
              {(position.current_price * position.quantity).toLocaleString()}
              <span className="text-sm font-normal text-[var(--muted)] ml-1">
                원
              </span>
            </p>
          </div>
        </div>

        {/* Close button */}
        {onClose && position.status === "OPEN" && (
          <button
            onClick={onClose}
            className="mt-4 w-full py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 transition-all duration-200 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40"
          >
            청산하기
          </button>
        )}
      </div>
    </div>
  );
}
