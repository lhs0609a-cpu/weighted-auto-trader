"use client";

import { useState, useEffect, useCallback } from "react";
import { autoTraderApi, AutoTraderStatus } from "@/lib/api";

interface AutoTraderPanelProps {
  onStatusChange?: (status: AutoTraderStatus) => void;
}

export default function AutoTraderPanel({ onStatusChange }: AutoTraderPanelProps) {
  const [status, setStatus] = useState<AutoTraderStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await autoTraderApi.getStatus();
      if (response.success) {
        setStatus(response.data);
        onStatusChange?.(response.data);
      }
    } catch (err) {
      console.error("Failed to fetch auto-trader status:", err);
    }
  }, [onStatusChange]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await autoTraderApi.start();
      if (response.success && response.data) {
        setStatus(response.data);
      }
    } catch (err: any) {
      setError(err.message || "Failed to start auto-trader");
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    setError(null);
    try {
      await autoTraderApi.stop();
      await fetchStatus();
    } catch (err: any) {
      setError(err.message || "Failed to stop auto-trader");
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    setLoading(true);
    try {
      await autoTraderApi.pause();
      await fetchStatus();
    } catch (err: any) {
      setError(err.message || "Failed to pause auto-trader");
    } finally {
      setLoading(false);
    }
  };

  const handleResume = async () => {
    setLoading(true);
    try {
      await autoTraderApi.resume();
      await fetchStatus();
    } catch (err: any) {
      setError(err.message || "Failed to resume auto-trader");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = () => {
    if (!status) return "bg-slate-500";
    switch (status.status) {
      case "running":
        return "bg-emerald-500";
      case "waiting":
        return "bg-amber-500";
      case "paused":
        return "bg-yellow-500";
      case "closed":
        return "bg-blue-500";
      default:
        return "bg-slate-500";
    }
  };

  const getStatusText = () => {
    if (!status) return "Loading...";
    switch (status.status) {
      case "running":
        return "Running";
      case "waiting":
        return "Waiting";
      case "paused":
        return "Paused";
      case "closed":
        return "Market Closed";
      case "stopped":
        return "Stopped";
      default:
        return status.status;
    }
  };

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-[var(--card-border)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()} animate-pulse`} />
            <h3 className="text-lg font-bold text-[var(--foreground)]">
              Auto Trader
            </h3>
          </div>
          <span className="px-2 py-1 text-xs font-semibold rounded-lg bg-[var(--card-border)] text-muted">
            {getStatusText()}
          </span>
        </div>
      </div>

      {/* Stats */}
      {status && (
        <div className="grid grid-cols-3 gap-px bg-[var(--card-border)]">
          <div className="bg-[var(--card)] p-3 text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              Trades
            </p>
            <p className="text-lg font-bold text-[var(--foreground)] tabular-nums">
              {status.today_trades}
            </p>
          </div>
          <div className="bg-[var(--card)] p-3 text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              P&L
            </p>
            <p
              className={`text-lg font-bold tabular-nums ${
                status.today_pnl >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {status.today_pnl >= 0 ? "+" : ""}
              {status.today_pnl.toLocaleString()}
            </p>
          </div>
          <div className="bg-[var(--card)] p-3 text-center">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              Watching
            </p>
            <p className="text-lg font-bold text-[var(--foreground)] tabular-nums">
              {status.watched_stocks}
            </p>
          </div>
        </div>
      )}

      {/* Position Summary */}
      {status?.positions && (
        <div className="p-4 border-t border-[var(--card-border)]">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted">Open Positions</span>
            <span className="font-semibold text-[var(--foreground)]">
              {status.positions.open_positions} / {status.config?.max_positions || 5}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm mt-2">
            <span className="text-muted">Unrealized P&L</span>
            <span
              className={`font-semibold ${
                status.positions.total_unrealized_pnl >= 0
                  ? "text-emerald-400"
                  : "text-rose-400"
              }`}
            >
              {status.positions.total_unrealized_pnl >= 0 ? "+" : ""}
              {status.positions.total_unrealized_pnl.toLocaleString()}
            </span>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="px-4 py-2 bg-rose-500/10 border-t border-rose-500/20">
          <p className="text-xs text-rose-400">{error}</p>
        </div>
      )}

      {/* Controls */}
      <div className="p-4 border-t border-[var(--card-border)]">
        <div className="grid grid-cols-2 gap-2">
          {!status?.is_running ? (
            <button
              onClick={handleStart}
              disabled={loading}
              className="col-span-2 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Starting...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Start Auto Trading
                </span>
              )}
            </button>
          ) : (
            <>
              {status.is_paused ? (
                <button
                  onClick={handleResume}
                  disabled={loading}
                  className="py-3 rounded-xl font-bold text-white bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 transition-all disabled:opacity-50"
                >
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Resume
                  </span>
                </button>
              ) : (
                <button
                  onClick={handlePause}
                  disabled={loading}
                  className="py-3 rounded-xl font-bold text-white bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 transition-all disabled:opacity-50"
                >
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Pause
                  </span>
                </button>
              )}
              <button
                onClick={handleStop}
                disabled={loading}
                className="py-3 rounded-xl font-bold text-white bg-gradient-to-r from-rose-500 to-red-500 hover:from-rose-400 hover:to-red-400 transition-all disabled:opacity-50"
              >
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Stop
                </span>
              </button>
            </>
          )}
        </div>

        {/* Quick Settings */}
        {status && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted">Auto Buy</span>
              <div
                className={`w-10 h-5 rounded-full relative cursor-pointer transition-colors ${
                  status.auto_buy_enabled ? "bg-emerald-500" : "bg-slate-600"
                }`}
                onClick={async () => {
                  try {
                    await autoTraderApi.updateConfig({
                      auto_buy_enabled: !status.auto_buy_enabled,
                    });
                    await fetchStatus();
                  } catch (err) {
                    console.error(err);
                  }
                }}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                    status.auto_buy_enabled ? "translate-x-5" : "translate-x-0.5"
                  }`}
                />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted">Auto Sell</span>
              <div
                className={`w-10 h-5 rounded-full relative cursor-pointer transition-colors ${
                  status.auto_sell_enabled ? "bg-emerald-500" : "bg-slate-600"
                }`}
                onClick={async () => {
                  try {
                    await autoTraderApi.updateConfig({
                      auto_sell_enabled: !status.auto_sell_enabled,
                    });
                    await fetchStatus();
                  } catch (err) {
                    console.error(err);
                  }
                }}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                    status.auto_sell_enabled ? "translate-x-5" : "translate-x-0.5"
                  }`}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Market Hours Indicator */}
      <div className="px-4 py-3 bg-[var(--card-hover)] border-t border-[var(--card-border)]">
        <div className="flex items-center gap-2 text-xs text-muted">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>
            Market Hours: 09:00 - 15:30 KST
          </span>
          {status?.is_market_hours && (
            <span className="ml-auto px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold">
              OPEN
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
