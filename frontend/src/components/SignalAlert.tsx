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
  {
    gradient: string;
    bgGradient: string;
    borderColor: string;
    icon: string;
    label: string;
  }
> = {
  STRONG_BUY: {
    gradient: "from-rose-500 to-orange-500",
    bgGradient: "from-rose-500/10 to-orange-500/10",
    borderColor: "border-rose-500/30",
    icon: "🔥",
    label: "강력 매수",
  },
  BUY: {
    gradient: "from-orange-500 to-amber-500",
    bgGradient: "from-orange-500/10 to-amber-500/10",
    borderColor: "border-orange-500/30",
    icon: "📈",
    label: "매수",
  },
  WATCH: {
    gradient: "from-amber-500 to-yellow-500",
    bgGradient: "from-amber-500/10 to-yellow-500/10",
    borderColor: "border-amber-500/30",
    icon: "👀",
    label: "관심",
  },
  HOLD: {
    gradient: "from-slate-400 to-slate-500",
    bgGradient: "from-slate-400/10 to-slate-500/10",
    borderColor: "border-slate-400/30",
    icon: "⏸️",
    label: "대기",
  },
  SELL: {
    gradient: "from-blue-500 to-cyan-500",
    bgGradient: "from-blue-500/10 to-cyan-500/10",
    borderColor: "border-blue-500/30",
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
      className={`relative overflow-hidden bg-[var(--card)] rounded-2xl border ${config.borderColor} mb-3 cursor-pointer card-hover animate-slide-up`}
    >
      {/* Gradient background */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${config.bgGradient} opacity-50`}
      />

      {/* Left accent bar */}
      <div
        className={`absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b ${config.gradient}`}
      />

      <div className="relative p-4 pl-5">
        <div className="flex items-start justify-between">
          {/* Left content */}
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div
              className={`w-12 h-12 rounded-xl bg-gradient-to-br ${config.gradient} flex items-center justify-center shadow-lg flex-shrink-0`}
            >
              <span className="text-2xl">{config.icon}</span>
            </div>

            {/* Info */}
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-bold text-[var(--foreground)] truncate">
                  {stockName}
                </h4>
                <span className="text-xs text-[var(--muted)] font-mono flex-shrink-0">
                  {stockCode}
                </span>
              </div>

              {/* Signal badge & score */}
              <div className="flex items-center gap-2 mb-2">
                <span
                  className={`px-2 py-0.5 rounded-md text-xs font-semibold text-white bg-gradient-to-r ${config.gradient}`}
                >
                  {config.label}
                </span>
                <span className="text-sm font-bold text-[var(--foreground)]">
                  {score.toFixed(0)}점
                </span>
              </div>

              {/* Reasons */}
              <div className="space-y-0.5">
                {reasons.slice(0, 2).map((reason, i) => (
                  <p
                    key={i}
                    className="text-xs text-[var(--muted)] truncate max-w-[280px]"
                  >
                    • {reason}
                  </p>
                ))}
              </div>
            </div>
          </div>

          {/* Right - time & dismiss */}
          <div className="flex flex-col items-end gap-2 flex-shrink-0 ml-2">
            <span className="text-xs text-[var(--muted)] tabular-nums">
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
                className="p-1.5 rounded-lg hover:bg-[var(--secondary)] transition-colors"
              >
                <svg
                  className="w-4 h-4 text-[var(--muted)]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
