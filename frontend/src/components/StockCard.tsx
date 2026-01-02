"use client";

import { Quote, SignalType } from "@/types";
import { useMemo } from "react";

interface StockCardProps {
  quote: Quote;
  signal?: SignalType;
  score?: number;
  onClick?: () => void;
}

const signalConfig: Record<
  SignalType,
  { gradient: string; glow: string; label: string; textColor: string }
> = {
  STRONG_BUY: {
    gradient: "from-rose-500 to-orange-500",
    glow: "shadow-rose-500/50",
    label: "STRONG BUY",
    textColor: "text-rose-400",
  },
  BUY: {
    gradient: "from-orange-500 to-amber-500",
    glow: "shadow-orange-500/50",
    label: "BUY",
    textColor: "text-orange-400",
  },
  WATCH: {
    gradient: "from-amber-500 to-yellow-500",
    glow: "shadow-amber-500/50",
    label: "WATCH",
    textColor: "text-amber-400",
  },
  HOLD: {
    gradient: "from-slate-400 to-slate-500",
    glow: "shadow-slate-500/50",
    label: "HOLD",
    textColor: "text-slate-400",
  },
  SELL: {
    gradient: "from-cyan-500 to-blue-500",
    glow: "shadow-cyan-500/50",
    label: "SELL",
    textColor: "text-cyan-400",
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

  // Generate mini sparkline data
  const sparklineData = useMemo(() => {
    const points: number[] = [];
    const base = quote.prev_close || quote.price;
    const range = Math.abs(quote.high - quote.low) || base * 0.02;

    for (let i = 0; i < 12; i++) {
      const progress = i / 11;
      const noise = (Math.random() - 0.5) * range * 0.5;
      const trend = (quote.price - base) * progress;
      points.push(base + trend + noise);
    }
    points[points.length - 1] = quote.price;
    return points;
  }, [quote.price, quote.prev_close, quote.high, quote.low]);

  const sparklinePath = useMemo(() => {
    const min = Math.min(...sparklineData);
    const max = Math.max(...sparklineData);
    const range = max - min || 1;
    const width = 80;
    const height = 32;

    return sparklineData
      .map((value, index) => {
        const x = (index / (sparklineData.length - 1)) * width;
        const y = height - ((value - min) / range) * height;
        return `${index === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");
  }, [sparklineData]);

  return (
    <div
      onClick={onClick}
      className="group relative glass-card p-5 cursor-pointer overflow-hidden"
    >
      {/* Gradient border on hover */}
      <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-500">
        <div className="absolute inset-0 rounded-lg p-[1px] bg-gradient-to-r from-violet-500 via-fuchsia-500 to-cyan-500">
          <div className="w-full h-full rounded-lg bg-[var(--card)]" />
        </div>
      </div>

      {/* Background gradient effect on hover */}
      <div
        className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${
          isPositive
            ? "bg-gradient-to-br from-emerald-500/5 via-transparent to-cyan-500/5"
            : "bg-gradient-to-br from-rose-500/5 via-transparent to-orange-500/5"
        }`}
      />

      {/* Top glow effect */}
      <div
        className={`absolute -top-20 -right-20 w-40 h-40 rounded-full blur-3xl opacity-0 group-hover:opacity-30 transition-opacity duration-500 ${
          isPositive ? "bg-emerald-500" : "bg-rose-500"
        }`}
      />

      {/* Content */}
      <div className="relative z-10">
        {/* Header - Name & Signal */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-bold text-[var(--foreground)] text-lg truncate group-hover:text-gradient transition-all duration-300">
                {quote.name}
              </h3>
              {/* Live indicator */}
              <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <p className="text-xs text-muted font-mono tracking-wider">
              {quote.stock_code}
            </p>
          </div>

          {/* Signal badge */}
          {config && (
            <div
              className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider text-white bg-gradient-to-r ${config.gradient} shadow-lg ${config.glow}`}
            >
              {config.label}
            </div>
          )}
        </div>

        {/* Price Section */}
        <div className="flex items-end justify-between mb-4">
          <div>
            <p className="text-3xl font-bold text-[var(--foreground)] tracking-tight tabular-nums">
              {quote.price.toLocaleString()}
              <span className="text-sm font-medium text-muted ml-1">원</span>
            </p>
            <div className="flex items-center gap-2 mt-2">
              {/* Change badge */}
              <span
                className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold ${
                  isPositive
                    ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20"
                    : "bg-rose-500/15 text-rose-400 border border-rose-500/20"
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
              {/* Percentage */}
              <span
                className={`text-sm font-bold tabular-nums ${
                  isPositive ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {isPositive ? "+" : ""}
                {quote.change_rate.toFixed(2)}%
              </span>
            </div>
          </div>

          {/* Mini Sparkline Chart */}
          <div className="relative w-20 h-10">
            <svg
              className="w-full h-full"
              viewBox="0 0 80 32"
              preserveAspectRatio="none"
            >
              {/* Gradient fill under the line */}
              <defs>
                <linearGradient
                  id={`gradient-${quote.stock_code}`}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor={isPositive ? "#10b981" : "#f43f5e"}
                    stopOpacity="0.3"
                  />
                  <stop
                    offset="100%"
                    stopColor={isPositive ? "#10b981" : "#f43f5e"}
                    stopOpacity="0"
                  />
                </linearGradient>
              </defs>
              {/* Fill area */}
              <path
                d={`${sparklinePath} L 80 32 L 0 32 Z`}
                fill={`url(#gradient-${quote.stock_code})`}
              />
              {/* Line */}
              <path
                d={sparklinePath}
                fill="none"
                stroke={isPositive ? "#10b981" : "#f43f5e"}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="drop-shadow-sm"
              />
              {/* Current price dot */}
              <circle
                cx="80"
                cy={sparklineData.length > 0 ? 32 - ((quote.price - Math.min(...sparklineData)) / (Math.max(...sparklineData) - Math.min(...sparklineData) || 1)) * 32 : 16}
                r="3"
                fill={isPositive ? "#10b981" : "#f43f5e"}
                className="animate-pulse"
              />
            </svg>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-3 pt-4 border-t border-[var(--card-border)]">
          <div className="text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider mb-1">
              Vol
            </p>
            <p className="text-sm font-semibold text-[var(--foreground)] tabular-nums">
              {quote.volume >= 1000000
                ? `${(quote.volume / 1000000).toFixed(1)}M`
                : `${(quote.volume / 1000).toFixed(0)}K`}
            </p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider mb-1">
              High
            </p>
            <p className="text-sm font-semibold text-emerald-400 tabular-nums">
              {quote.high.toLocaleString()}
            </p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider mb-1">
              Low
            </p>
            <p className="text-sm font-semibold text-rose-400 tabular-nums">
              {quote.low.toLocaleString()}
            </p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider mb-1">
              {score !== undefined ? "Score" : "Open"}
            </p>
            {score !== undefined ? (
              <p
                className={`text-sm font-bold tabular-nums ${
                  score >= 80
                    ? "text-emerald-400"
                    : score >= 60
                    ? "text-amber-400"
                    : "text-muted"
                }`}
              >
                {score.toFixed(0)}
              </p>
            ) : (
              <p className="text-sm font-semibold text-[var(--foreground)] tabular-nums">
                {quote.open.toLocaleString()}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Bottom gradient line on hover */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 overflow-hidden">
        <div
          className={`h-full transform -translate-x-full group-hover:translate-x-0 transition-transform duration-500 ease-out ${
            isPositive
              ? "bg-gradient-to-r from-emerald-500 via-cyan-500 to-emerald-500"
              : "bg-gradient-to-r from-rose-500 via-orange-500 to-rose-500"
          }`}
        />
      </div>

      {/* Corner accent */}
      <div
        className={`absolute top-0 right-0 w-16 h-16 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${
          isPositive
            ? "bg-gradient-to-bl from-emerald-500/20 to-transparent"
            : "bg-gradient-to-bl from-rose-500/20 to-transparent"
        }`}
      />
    </div>
  );
}
