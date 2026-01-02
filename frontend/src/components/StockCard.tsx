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
  { bg: string; text: string; label: string; emoji: string }
> = {
  STRONG_BUY: {
    bg: "bg-gradient-to-r from-rose-500 to-orange-500",
    text: "text-rose-500",
    label: "STRONG BUY",
    emoji: "🔥",
  },
  BUY: {
    bg: "bg-gradient-to-r from-orange-500 to-amber-500",
    text: "text-orange-500",
    label: "BUY",
    emoji: "📈",
  },
  WATCH: {
    bg: "bg-gradient-to-r from-amber-500 to-yellow-500",
    text: "text-amber-500",
    label: "WATCH",
    emoji: "👀",
  },
  HOLD: {
    bg: "bg-zinc-400",
    text: "text-zinc-500",
    label: "HOLD",
    emoji: "✋",
  },
  SELL: {
    bg: "bg-gradient-to-r from-blue-500 to-cyan-500",
    text: "text-blue-500",
    label: "SELL",
    emoji: "📉",
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
      className="group relative bg-white dark:bg-zinc-900 rounded-3xl p-5 cursor-pointer border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-xl hover:shadow-zinc-200/50 dark:hover:shadow-zinc-900/50 transition-all duration-300"
    >
      {/* Instagram-style story ring for signals */}
      {config && (
        <div className="absolute -top-1 -right-1 w-7 h-7 rounded-full p-[2px] bg-gradient-to-r from-[#833AB4] via-[#E1306C] to-[#F77737]">
          <div className="w-full h-full rounded-full bg-white dark:bg-zinc-900 flex items-center justify-center text-xs">
            {config.emoji}
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Stock Avatar */}
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-zinc-100 to-zinc-200 dark:from-zinc-800 dark:to-zinc-700 flex items-center justify-center font-bold text-zinc-600 dark:text-zinc-300 text-sm">
            {quote.name.charAt(0)}
          </div>
          <div>
            <h3 className="font-bold text-zinc-900 dark:text-white text-base">
              {quote.name}
            </h3>
            <p className="text-xs text-zinc-400 font-mono">
              {quote.stock_code}
            </p>
          </div>
        </div>

        {/* Live dot */}
        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
      </div>

      {/* Price */}
      <div className="mb-4">
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-zinc-900 dark:text-white tabular-nums">
            {quote.price.toLocaleString()}
          </span>
          <span className="text-sm text-zinc-400">원</span>
        </div>

        {/* Change */}
        <div className="flex items-center gap-2 mt-1">
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
              isPositive
                ? "bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-400"
                : "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400"
            }`}
          >
            {isPositive ? "+" : ""}{quote.change.toLocaleString()}
          </span>
          <span
            className={`text-sm font-semibold tabular-nums ${
              isPositive ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
            }`}
          >
            {isPositive ? "+" : ""}{quote.change_rate.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Sparkline */}
      <div className="relative h-12 mb-4 -mx-1">
        <svg
          className="w-full h-full"
          viewBox="0 0 80 32"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient
              id={`fill-${quote.stock_code}`}
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="0%"
                stopColor={isPositive ? "#22c55e" : "#ef4444"}
                stopOpacity="0.2"
              />
              <stop
                offset="100%"
                stopColor={isPositive ? "#22c55e" : "#ef4444"}
                stopOpacity="0"
              />
            </linearGradient>
          </defs>
          <path
            d={`${sparklinePath} L 80 32 L 0 32 Z`}
            fill={`url(#fill-${quote.stock_code})`}
          />
          <path
            d={sparklinePath}
            fill="none"
            stroke={isPositive ? "#22c55e" : "#ef4444"}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle
            cx="80"
            cy={sparklineData.length > 0 ? 32 - ((quote.price - Math.min(...sparklineData)) / (Math.max(...sparklineData) - Math.min(...sparklineData) || 1)) * 32 : 16}
            r="3"
            fill={isPositive ? "#22c55e" : "#ef4444"}
            className="animate-pulse"
          />
        </svg>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800">
        <div className="text-center">
          <p className="text-[10px] text-zinc-400 uppercase tracking-wider">High</p>
          <p className="text-sm font-semibold text-green-600 dark:text-green-400 tabular-nums">
            {quote.high.toLocaleString()}
          </p>
        </div>
        <div className="text-center">
          <p className="text-[10px] text-zinc-400 uppercase tracking-wider">Low</p>
          <p className="text-sm font-semibold text-red-600 dark:text-red-400 tabular-nums">
            {quote.low.toLocaleString()}
          </p>
        </div>
        <div className="text-center">
          <p className="text-[10px] text-zinc-400 uppercase tracking-wider">Vol</p>
          <p className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 tabular-nums">
            {quote.volume >= 1000000
              ? `${(quote.volume / 1000000).toFixed(1)}M`
              : `${(quote.volume / 1000).toFixed(0)}K`}
          </p>
        </div>
        {score !== undefined ? (
          <div className="text-center">
            <p className="text-[10px] text-zinc-400 uppercase tracking-wider">Score</p>
            <p className={`text-sm font-bold tabular-nums ${
              score >= 80 ? "text-green-600 dark:text-green-400" :
              score >= 60 ? "text-amber-600 dark:text-amber-400" :
              "text-zinc-500"
            }`}>
              {score.toFixed(0)}
            </p>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-[10px] text-zinc-400 uppercase tracking-wider">Open</p>
            <p className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 tabular-nums">
              {quote.open.toLocaleString()}
            </p>
          </div>
        )}
      </div>

      {/* Signal Badge */}
      {config && (
        <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800">
          <div className={`text-center py-2 rounded-xl ${config.bg} text-white text-xs font-bold tracking-wider`}>
            {config.label}
          </div>
        </div>
      )}

      {/* Hover Effect */}
      <div className="absolute inset-0 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        <div className="absolute inset-0 rounded-3xl ring-2 ring-inset ring-zinc-200 dark:ring-zinc-700" />
      </div>
    </div>
  );
}
