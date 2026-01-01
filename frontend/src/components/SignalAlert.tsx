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
}

const signalStyles: Record<
  SignalType,
  { bg: string; border: string; icon: string }
> = {
  STRONG_BUY: {
    bg: "bg-red-50 dark:bg-red-900/20",
    border: "border-red-400",
    icon: "🔥",
  },
  BUY: {
    bg: "bg-orange-50 dark:bg-orange-900/20",
    border: "border-orange-400",
    icon: "📈",
  },
  WATCH: {
    bg: "bg-yellow-50 dark:bg-yellow-900/20",
    border: "border-yellow-400",
    icon: "👀",
  },
  HOLD: {
    bg: "bg-gray-50 dark:bg-gray-900/20",
    border: "border-gray-400",
    icon: "⏸️",
  },
  SELL: {
    bg: "bg-blue-50 dark:bg-blue-900/20",
    border: "border-blue-400",
    icon: "📉",
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
}: SignalAlertProps) {
  const style = signalStyles[signal];

  return (
    <div
      className={`${style.bg} border-l-4 ${style.border} p-4 rounded-r-lg mb-3`}
    >
      <div className="flex justify-between items-start">
        <div className="flex items-start gap-3">
          <span className="text-2xl">{style.icon}</span>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-gray-900 dark:text-white">
                {stockName}
              </h4>
              <span className="text-xs text-gray-500">{stockCode}</span>
            </div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              점수: {score.toFixed(1)}점
            </p>
            <ul className="mt-1 text-xs text-gray-600 dark:text-gray-400">
              {reasons.slice(0, 3).map((reason, i) => (
                <li key={i}>• {reason}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <span className="text-xs text-gray-500">
            {new Date(timestamp).toLocaleTimeString()}
          </span>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
