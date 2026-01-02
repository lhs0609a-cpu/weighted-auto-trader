"use client";

import { SignalType } from "@/types";

interface SignalAlertProps {
  stockCode: string;
  stockName: string;
  signal: SignalType;
  score: number;
  reasons: string[];
  timestamp: string;
  onDismiss?: () => void;
  onClick?: () => void;
}

const signalConfig: Record<
  SignalType,
  { gradient: string; bg: string; icon: string; label: string }
> = {
  STRONG_BUY: {
    gradient: "from-rose-500 to-orange-500",
    bg: "bg-rose-50 dark:bg-rose-500/10",
    icon: "🔥",
    label: "강력 매수",
  },
  BUY: {
    gradient: "from-orange-500 to-amber-500",
    bg: "bg-orange-50 dark:bg-orange-500/10",
    icon: "📈",
    label: "매수",
  },
  WATCH: {
    gradient: "from-amber-500 to-yellow-500",
    bg: "bg-amber-50 dark:bg-amber-500/10",
    icon: "👀",
    label: "관심",
  },
  HOLD: {
    gradient: "from-zinc-400 to-zinc-500",
    bg: "bg-zinc-50 dark:bg-zinc-500/10",
    icon: "✋",
    label: "대기",
  },
  SELL: {
    gradient: "from-blue-500 to-cyan-500",
    bg: "bg-blue-50 dark:bg-blue-500/10",
    icon: "📉",
    label: "매도",
  },
};

export default function SignalAlert({
  stockCode,
  stockName,
  signal,
  score,
  reasons,
  timestamp,
  onDismiss,
  onClick,
}: SignalAlertProps) {
  const config = signalConfig[signal];

  return (
    <div
      onClick={onClick}
      className={`relative ${config.bg} rounded-2xl p-4 cursor-pointer hover:scale-[1.02] transition-transform`}
    >
      <div className="flex items-start gap-3">
        {/* Instagram Story Ring */}
        <div className={`w-11 h-11 rounded-full p-[2px] bg-gradient-to-r ${config.gradient} flex-shrink-0`}>
          <div className="w-full h-full rounded-full bg-white dark:bg-zinc-900 flex items-center justify-center">
            <span className="text-lg">{config.icon}</span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-bold text-zinc-900 dark:text-white text-sm truncate">
              {stockName}
            </h4>
            <span className="text-[10px] text-zinc-400 font-mono flex-shrink-0">
              {stockCode}
            </span>
          </div>

          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold text-white bg-gradient-to-r ${config.gradient}`}>
              {config.label}
            </span>
            <span className="text-xs font-bold text-zinc-700 dark:text-zinc-300">
              {score.toFixed(0)}점
            </span>
          </div>

          {reasons.length > 0 && (
            <p className="text-xs text-zinc-500 truncate">
              {reasons[0]}
            </p>
          )}
        </div>

        {/* Right side */}
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span className="text-[10px] text-zinc-400 tabular-nums">
            {new Date(timestamp).toLocaleTimeString("ko-KR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
          {onDismiss && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDismiss();
              }}
              className="p-1 rounded-full hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
            >
              <svg className="w-3.5 h-3.5 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
