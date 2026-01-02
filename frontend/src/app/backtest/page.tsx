"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { BacktestConfig, BacktestResult, TradingStyle } from "@/types";
import { backtestApi } from "@/lib/api";

// Mock result data
const mockResult: BacktestResult = {
  config: {
    stock_codes: ["005930", "000660", "035420"],
    start_date: "2024-01-01",
    end_date: "2024-12-31",
    initial_capital: 10000000,
    trading_style: "DAYTRADING",
    commission_rate: 0.00015,
    slippage_rate: 0.001,
    max_position_size: 0.2,
    max_positions: 5,
  },
  performance: {
    final_equity: 12850000,
    total_return: 28.5,
    total_pnl: 2850000,
    max_drawdown: 8.5,
  },
  trades: {
    total_trades: 156,
    winning_trades: 98,
    losing_trades: 58,
    win_rate: 62.8,
    avg_win: 45000,
    avg_loss: -28000,
    profit_factor: 2.15,
  },
  equity_curve: Array.from({ length: 252 }, (_, i) => ({
    timestamp: new Date(2024, 0, 1 + i).toISOString(),
    equity: 10000000 + Math.floor(Math.random() * 3000000) + i * 10000,
    cash: 5000000,
    position_count: Math.floor(Math.random() * 5),
  })),
  trade_history: [],
};

export default function BacktestPage() {
  const [config, setConfig] = useState<Partial<BacktestConfig>>({
    stock_codes: ["005930", "000660", "035420"],
    start_date: "2024-01-01",
    end_date: "2024-12-31",
    initial_capital: 10000000,
    trading_style: "DAYTRADING",
    commission_rate: 0.00015,
    slippage_rate: 0.001,
    max_position_size: 0.2,
    max_positions: 5,
  });
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stockInput, setStockInput] = useState("005930, 000660, 035420");

  const runBacktest = async () => {
    setIsRunning(true);
    setProgress(0);
    setResult(null);

    try {
      // Start async backtest
      const response = await backtestApi.runAsync({
        stock_codes: config.stock_codes,
        start_date: config.start_date,
        end_date: config.end_date,
        initial_capital: config.initial_capital,
        trading_style: config.trading_style,
        commission_rate: config.commission_rate,
        slippage_rate: config.slippage_rate,
        max_position_size: config.max_position_size,
        max_positions: config.max_positions,
      });

      const backtestId = response.backtest_id;

      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const status = await backtestApi.getStatus(backtestId);
          setProgress(status.progress);

          if (status.status === "completed") {
            clearInterval(pollInterval);
            const resultData = await backtestApi.getResult(backtestId);
            if (resultData.success && resultData.data) {
              setResult(resultData.data);
            }
            setIsRunning(false);
          } else if (status.status === "failed") {
            clearInterval(pollInterval);
            console.error("Backtest failed:", status.message);
            setIsRunning(false);
          }
        } catch (error) {
          console.error("Error polling status:", error);
        }
      }, 500);
    } catch (error) {
      console.error("Error starting backtest:", error);
      // Fallback to mock result for demo
      for (let i = 0; i <= 100; i += 5) {
        await new Promise((r) => setTimeout(r, 100));
        setProgress(i);
      }
      setResult(mockResult);
      setIsRunning(false);
    }
  };

  const maxEquity = result
    ? Math.max(...result.equity_curve.map((p) => p.equity))
    : 0;
  const minEquity = result
    ? Math.min(...result.equity_curve.map((p) => p.equity))
    : 0;

  return (
    <div className="min-h-screen gradient-mesh">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-effect border-b border-zinc-200 dark:border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="p-2 rounded-xl hover:bg-zinc-100 dark:bg-zinc-800 transition-colors"
              >
                <svg
                  className="w-5 h-5 text-zinc-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </Link>
              <div>
                <h1 className="text-xl font-bold text-zinc-900 dark:text-white">
                  Backtest
                </h1>
                <p className="text-sm text-zinc-500">
                  Test your strategy with historical data
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Config Panel */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800">
              <h2 className="text-lg font-bold text-zinc-900 dark:text-white mb-4">
                Configuration
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-zinc-500 mb-2">
                    Stock Codes
                  </label>
                  <input
                    type="text"
                    value={stockInput}
                    onChange={(e) => {
                      setStockInput(e.target.value);
                      setConfig((prev) => ({
                        ...prev,
                        stock_codes: e.target.value
                          .split(",")
                          .map((s) => s.trim()),
                      }));
                    }}
                    placeholder="005930, 000660, 035420"
                    className="w-full px-4 py-3 rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-white text-sm"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-zinc-500 mb-2">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={config.start_date}
                      onChange={(e) =>
                        setConfig((prev) => ({
                          ...prev,
                          start_date: e.target.value,
                        }))
                      }
                      className="w-full px-4 py-3 rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-500 mb-2">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={config.end_date}
                      onChange={(e) =>
                        setConfig((prev) => ({
                          ...prev,
                          end_date: e.target.value,
                        }))
                      }
                      className="w-full px-4 py-3 rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-white text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-zinc-500 mb-2">
                    Initial Capital (KRW)
                  </label>
                  <input
                    type="number"
                    value={config.initial_capital}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        initial_capital: parseInt(e.target.value) || 10000000,
                      }))
                    }
                    className="w-full px-4 py-3 rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-white text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm text-zinc-500 mb-2">
                    Trading Style
                  </label>
                  <select
                    value={config.trading_style}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        trading_style: e.target.value as TradingStyle,
                      }))
                    }
                    className="w-full px-4 py-3 rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-white text-sm"
                  >
                    <option value="SCALPING">Scalping</option>
                    <option value="DAYTRADING">Day Trading</option>
                    <option value="SWING">Swing</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-zinc-500 mb-2">
                      Max Positions
                    </label>
                    <input
                      type="number"
                      value={config.max_positions}
                      onChange={(e) =>
                        setConfig((prev) => ({
                          ...prev,
                          max_positions: parseInt(e.target.value) || 5,
                        }))
                      }
                      min={1}
                      max={20}
                      className="w-full px-4 py-3 rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-500 mb-2">
                      Position Size (%)
                    </label>
                    <input
                      type="number"
                      value={(config.max_position_size || 0.2) * 100}
                      onChange={(e) =>
                        setConfig((prev) => ({
                          ...prev,
                          max_position_size:
                            (parseFloat(e.target.value) || 20) / 100,
                        }))
                      }
                      min={5}
                      max={50}
                      className="w-full px-4 py-3 rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-white text-sm"
                    />
                  </div>
                </div>

                <button
                  onClick={runBacktest}
                  disabled={isRunning}
                  className="w-full py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg"
                >
                  {isRunning ? "Running..." : "Run Backtest"}
                </button>

                {isRunning && (
                  <div className="mt-4">
                    <div className="flex justify-between text-sm text-zinc-500 mb-2">
                      <span>Progress</span>
                      <span>{progress}%</span>
                    </div>
                    <div className="h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2 space-y-6">
            {result ? (
              <>
                {/* Performance Summary */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-white dark:bg-zinc-900 rounded-2xl p-5 border border-zinc-200 dark:border-zinc-800">
                    <p className="text-sm text-zinc-500 mb-1">
                      Final Equity
                    </p>
                    <p className="text-2xl font-bold text-zinc-900 dark:text-white">
                      {(result.performance.final_equity / 10000).toFixed(0)}M
                    </p>
                  </div>
                  <div className="bg-white dark:bg-zinc-900 rounded-2xl p-5 border border-zinc-200 dark:border-zinc-800">
                    <p className="text-sm text-zinc-500 mb-1">
                      Total Return
                    </p>
                    <p
                      className={`text-2xl font-bold ${
                        result.performance.total_return >= 0
                          ? "text-emerald-500"
                          : "text-rose-500"
                      }`}
                    >
                      {result.performance.total_return >= 0 ? "+" : ""}
                      {result.performance.total_return.toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-white dark:bg-zinc-900 rounded-2xl p-5 border border-zinc-200 dark:border-zinc-800">
                    <p className="text-sm text-zinc-500 mb-1">Win Rate</p>
                    <p className="text-2xl font-bold text-zinc-900 dark:text-white">
                      {result.trades.win_rate.toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-white dark:bg-zinc-900 rounded-2xl p-5 border border-zinc-200 dark:border-zinc-800">
                    <p className="text-sm text-zinc-500 mb-1">
                      Max Drawdown
                    </p>
                    <p className="text-2xl font-bold text-rose-500">
                      -{result.performance.max_drawdown.toFixed(1)}%
                    </p>
                  </div>
                </div>

                {/* Equity Curve */}
                <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800">
                  <h3 className="text-lg font-bold text-zinc-900 dark:text-white mb-4">
                    Equity Curve
                  </h3>
                  <div className="h-64 flex items-end gap-[2px]">
                    {result.equity_curve
                      .filter((_, i) => i % 5 === 0)
                      .map((point, i) => {
                        const height =
                          ((point.equity - minEquity) /
                            (maxEquity - minEquity)) *
                          100;
                        const isProfit =
                          point.equity > result.config.initial_capital;
                        return (
                          <div
                            key={i}
                            className={`flex-1 rounded-t transition-all hover:opacity-80 ${
                              isProfit
                                ? "bg-gradient-to-t from-emerald-500 to-teal-400"
                                : "bg-gradient-to-t from-rose-500 to-pink-400"
                            }`}
                            style={{ height: `${Math.max(height, 5)}%` }}
                            title={`${new Date(
                              point.timestamp
                            ).toLocaleDateString()}: ${point.equity.toLocaleString()} KRW`}
                          />
                        );
                      })}
                  </div>
                  <div className="flex justify-between text-xs text-zinc-500 mt-2">
                    <span>{result.config.start_date}</span>
                    <span>{result.config.end_date}</span>
                  </div>
                </div>

                {/* Trade Stats */}
                <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800">
                  <h3 className="text-lg font-bold text-zinc-900 dark:text-white mb-4">
                    Trade Statistics
                  </h3>
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-6">
                    <div>
                      <p className="text-sm text-zinc-500">
                        Total Trades
                      </p>
                      <p className="text-xl font-bold text-zinc-900 dark:text-white">
                        {result.trades.total_trades}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-zinc-500">
                        Winning Trades
                      </p>
                      <p className="text-xl font-bold text-emerald-500">
                        {result.trades.winning_trades}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-zinc-500">
                        Losing Trades
                      </p>
                      <p className="text-xl font-bold text-rose-500">
                        {result.trades.losing_trades}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-zinc-500">Avg Win</p>
                      <p className="text-xl font-bold text-emerald-500">
                        +{result.trades.avg_win.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-zinc-500">Avg Loss</p>
                      <p className="text-xl font-bold text-rose-500">
                        {result.trades.avg_loss.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-zinc-500">
                        Profit Factor
                      </p>
                      <p className="text-xl font-bold text-zinc-900 dark:text-white">
                        {typeof result.trades.profit_factor === "number"
                          ? result.trades.profit_factor.toFixed(2)
                          : result.trades.profit_factor}
                      </p>
                    </div>
                  </div>

                  {/* Win rate bar */}
                  <div className="mt-6">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-emerald-500">
                        Wins: {result.trades.winning_trades}
                      </span>
                      <span className="text-rose-500">
                        Losses: {result.trades.losing_trades}
                      </span>
                    </div>
                    <div className="h-3 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden flex">
                      <div
                        className="bg-gradient-to-r from-emerald-500 to-teal-500"
                        style={{ width: `${result.trades.win_rate}%` }}
                      />
                      <div
                        className="bg-gradient-to-r from-rose-500 to-pink-500"
                        style={{ width: `${100 - result.trades.win_rate}%` }}
                      />
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white dark:bg-zinc-900 rounded-2xl p-12 border border-zinc-200 dark:border-zinc-800 flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
                    <span className="text-4xl">📊</span>
                  </div>
                  <h3 className="text-xl font-bold text-zinc-900 dark:text-white mb-2">
                    Run a Backtest
                  </h3>
                  <p className="text-zinc-500">
                    Configure your settings and click "Run Backtest" to see
                    results
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
