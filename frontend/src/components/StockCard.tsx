"use client";

import { Quote, SignalType } from "@/types";

interface StockCardProps {
  quote: Quote;
  signal?: SignalType;
  score?: number;
  onClick?: () => void;
}

const signalConfig: Record<
  SignalType,
  { gradient: string; glow: string; label: string; icon: string }
> = {
  STRONG_BUY: {
    gradient: "from-rose-500 to-orange-500",
    glow: "shadow-rose-500/30",
    label: "강력매수",
    icon: "🔥",
  },
  BUY: {
    gradient: "from-orange-500 to-amber-500",
    glow: "shadow-orange-500/30",
    label: "매수",
    icon: "📈",
  },
  WATCH: {
    gradient: "from-amber-500 to-yellow-500",
    glow: "shadow-amber-500/30",
    label: "관심",
    icon: "👀",
  },
  HOLD: {
    gradient: "from-slate-400 to-slate-500",
    glow: "shadow-slate-500/30",
    label: "대기",
    icon: "⏸️",
  },
  SELL: {
    gradient: "from-blue-500 to-cyan-500",
    glow: "shadow-blue-500/30",
    label: "매도",
    icon: "📉",
  },
};

export default function StockCard({
  quote,
  signal,
  score,
  onClick,
}: StockCardProps) {
  const isPositive = quote.change_rate >= 0;
  const config = signal ? signalConfig[signal] : null;

  return (
    <div
      onClick={onClick}
      className="group relative bg-[var(--card)] rounded-2xl p-5 card-hover cursor-pointer overflow-hidden border border-[var(--border)]"
    >
      {/* Background gradient effect on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      {/* Signal badge */}
      {config && (
        <div className="absolute top-3 right-3">
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold text-white bg-gradient-to-r ${config.gradient} shadow-lg ${config.glow}`}
          >
            <span>{config.icon}</span>
            <span>{config.label}</span>
          </span>
        </div>
      )}

      {/* Stock info */}
      <div className="relative">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-bold text-[var(--foreground)] text-lg group-hover:text-indigo-600 transition-colors">
              {quote.name}
            </h3>
            <p className="text-xs text-[var(--muted)] font-mono">
              {quote.stock_code}
            </p>
          </div>
        </div>

        {/* Price */}
        <div className="mb-4">
          <p className="text-2xl font-bold text-[var(--foreground)] tracking-tight">
            {quote.price.toLocaleString()}
            <span className="text-sm font-normal text-[var(--muted)] ml-1">
              원
            </span>
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-md text-sm font-semibold ${
                isPositive
                  ? "bg-rose-500/10 text-rose-500"
                  : "bg-blue-500/10 text-blue-500"
              }`}
            >
              {isPositive ? "▲" : "▼"} {Math.abs(quote.change).toLocaleString()}
            </span>
            <span
              className={`text-sm font-bold ${
                isPositive ? "text-rose-500" : "text-blue-500"
              }`}
            >
              {isPositive ? "+" : ""}
              {quote.change_rate.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between pt-3 border-t border-[var(--border)]">
          <div className="flex items-center gap-4">
            <div>
              <p className="text-xs text-[var(--muted)]">거래량</p>
              <p className="text-sm font-semibold text-[var(--foreground)]">
                {(quote.volume / 1000).toFixed(0)}K
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--muted)]">고가</p>
              <p className="text-sm font-semibold text-rose-500">
                {quote.high.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--muted)]">저가</p>
              <p className="text-sm font-semibold text-blue-500">
                {quote.low.toLocaleString()}
              </p>
            </div>
          </div>

          {score !== undefined && (
            <div className="text-right">
              <p className="text-xs text-[var(--muted)]">점수</p>
              <p
                className={`text-lg font-bold ${
                  score >= 80
                    ? "text-rose-500"
                    : score >= 60
                    ? "text-amber-500"
                    : "text-[var(--muted)]"
                }`}
              >
                {score.toFixed(0)}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Hover indicator */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
    </div>
  );
}
