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
    if (!status) return "bg-zinc-400";
    switch (status.status) {
      case "running": return "bg-green-500";
      case "waiting": return "bg-amber-500";
      case "paused": return "bg-yellow-500";
      case "closed": return "bg-blue-500";
      default: return "bg-zinc-400";
    }
  };

  const getStatusText = () => {
    if (!status) return "Loading...";
    switch (status.status) {
      case "running": return "Running";
      case "waiting": return "Waiting";
      case "paused": return "Paused";
      case "closed": return "Market Closed";
      case "stopped": return "Stopped";
      default: return status.status;
    }
  };

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-3xl border border-zinc-100 dark:border-zinc-800 overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-zinc-100 dark:border-zinc-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full p-[2px] bg-gradient-to-r from-[#833AB4] via-[#E1306C] to-[#F77737]">
              <div className="w-full h-full rounded-full bg-white dark:bg-zinc-900 flex items-center justify-center">
                <span className="text-lg">🤖</span>
              </div>
            </div>
            <div>
              <h3 className="font-bold text-zinc-900 dark:text-white">
                Auto Trader
              </h3>
              <div className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${getStatusColor()} animate-pulse`} />
                <span className="text-xs text-zinc-400">{getStatusText()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      {status && (
        <div className="grid grid-cols-3 divide-x divide-zinc-100 dark:divide-zinc-800 bg-zinc-50 dark:bg-zinc-800/30">
          <div className="p-3 text-center">
            <p className="text-[10px] text-zinc-400 uppercase tracking-wider mb-0.5">Trades</p>
            <p className="text-lg font-bold text-zinc-900 dark:text-white tabular-nums">
              {status.today_trades}
            </p>
          </div>
          <div className="p-3 text-center">
            <p className="text-[10px] text-zinc-400 uppercase tracking-wider mb-0.5">P&L</p>
            <p className={`text-lg font-bold tabular-nums ${
              status.today_pnl >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
            }`}>
              {status.today_pnl >= 0 ? "+" : ""}{status.today_pnl.toLocaleString()}
            </p>
          </div>
          <div className="p-3 text-center">
            <p className="text-[10px] text-zinc-400 uppercase tracking-wider mb-0.5">Watching</p>
            <p className="text-lg font-bold text-zinc-900 dark:text-white tabular-nums">
              {status.watched_stocks}
            </p>
          </div>
        </div>
      )}

      {/* Position Summary */}
      {status?.positions && (
        <div className="px-5 py-3 border-t border-zinc-100 dark:border-zinc-800">
          <div className="flex items-center justify-between text-sm">
            <span className="text-zinc-400">Open Positions</span>
            <span className="font-semibold text-zinc-700 dark:text-zinc-300">
              {status.positions.open_positions} / {status.config?.max_positions || 5}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm mt-2">
            <span className="text-zinc-400">Unrealized P&L</span>
            <span className={`font-semibold ${
              status.positions.total_unrealized_pnl >= 0
                ? "text-green-600 dark:text-green-400"
                : "text-red-600 dark:text-red-400"
            }`}>
              {status.positions.total_unrealized_pnl >= 0 ? "+" : ""}
              {status.positions.total_unrealized_pnl.toLocaleString()}
            </span>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="px-5 py-2 bg-red-50 dark:bg-red-500/10">
          <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Controls */}
      <div className="p-4 border-t border-zinc-100 dark:border-zinc-800">
        <div className="grid grid-cols-2 gap-2">
          {!status?.is_running ? (
            <button
              onClick={handleStart}
              disabled={loading}
              className="col-span-2 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-[#833AB4] via-[#E1306C] to-[#F77737] hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Starting...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
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
                  className="py-3 rounded-xl font-bold text-white bg-gradient-to-r from-amber-500 to-orange-500 hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  Resume
                </button>
              ) : (
                <button
                  onClick={handlePause}
                  disabled={loading}
                  className="py-3 rounded-xl font-bold text-white bg-gradient-to-r from-amber-500 to-yellow-500 hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  Pause
                </button>
              )}
              <button
                onClick={handleStop}
                disabled={loading}
                className="py-3 rounded-xl font-bold text-white bg-gradient-to-r from-rose-500 to-red-500 hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                Stop
              </button>
            </>
          )}
        </div>

        {/* Toggle Switches */}
        {status && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-500">Auto Buy</span>
              <button
                className={`w-11 h-6 rounded-full relative transition-colors ${
                  status.auto_buy_enabled ? "bg-green-500" : "bg-zinc-300 dark:bg-zinc-600"
                }`}
                onClick={async () => {
                  try {
                    await autoTraderApi.updateConfig({ auto_buy_enabled: !status.auto_buy_enabled });
                    await fetchStatus();
                  } catch (err) { console.error(err); }
                }}
              >
                <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${
                  status.auto_buy_enabled ? "translate-x-[22px]" : "translate-x-0.5"
                }`} />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-500">Auto Sell</span>
              <button
                className={`w-11 h-6 rounded-full relative transition-colors ${
                  status.auto_sell_enabled ? "bg-green-500" : "bg-zinc-300 dark:bg-zinc-600"
                }`}
                onClick={async () => {
                  try {
                    await autoTraderApi.updateConfig({ auto_sell_enabled: !status.auto_sell_enabled });
                    await fetchStatus();
                  } catch (err) { console.error(err); }
                }}
              >
                <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${
                  status.auto_sell_enabled ? "translate-x-[22px]" : "translate-x-0.5"
                }`} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Market Hours */}
      <div className="px-4 py-3 bg-zinc-50 dark:bg-zinc-800/30 border-t border-zinc-100 dark:border-zinc-800">
        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>09:00 - 15:30 KST</span>
          {status?.is_market_hours && (
            <span className="ml-auto px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400 font-bold">
              OPEN
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
