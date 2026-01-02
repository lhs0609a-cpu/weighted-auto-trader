"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Trade, Statistics } from "@/types";
import { tradesApi } from "@/lib/api";

// Mock trade data
const mockTrades: Trade[] = [
  {
    trade_id: "T001",
    stock_code: "005930",
    stock_name: "Samsung Electronics",
    side: "SELL",
    quantity: 50,
    entry_price: 71000,
    exit_price: 72500,
    pnl: 75000,
    pnl_rate: 2.11,
    commission: 108,
    exit_reason: "TAKE_PROFIT_1",
    entry_time: "2024-01-15T09:30:00",
    exit_time: "2024-01-15T14:25:00",
  },
  {
    trade_id: "T002",
    stock_code: "000660",
    stock_name: "SK Hynix",
    side: "SELL",
    quantity: 20,
    entry_price: 180000,
    exit_price: 176000,
    pnl: -80000,
    pnl_rate: -2.22,
    commission: 534,
    exit_reason: "STOP_LOSS",
    entry_time: "2024-01-15T10:15:00",
    exit_time: "2024-01-15T11:30:00",
  },
  {
    trade_id: "T003",
    stock_code: "035420",
    stock_name: "NAVER",
    side: "SELL",
    quantity: 30,
    entry_price: 210000,
    exit_price: 218000,
    pnl: 240000,
    pnl_rate: 3.81,
    commission: 642,
    exit_reason: "TAKE_PROFIT_2",
    entry_time: "2024-01-14T09:45:00",
    exit_time: "2024-01-15T10:00:00",
  },
  {
    trade_id: "T004",
    stock_code: "035720",
    stock_name: "Kakao",
    side: "SELL",
    quantity: 100,
    entry_price: 52000,
    exit_price: 51500,
    pnl: -50000,
    pnl_rate: -0.96,
    commission: 78,
    exit_reason: "TRAILING_STOP",
    entry_time: "2024-01-14T13:00:00",
    exit_time: "2024-01-14T15:15:00",
  },
  {
    trade_id: "T005",
    stock_code: "051910",
    stock_name: "LG Chem",
    side: "SELL",
    quantity: 10,
    entry_price: 385000,
    exit_price: 395000,
    pnl: 100000,
    pnl_rate: 2.6,
    commission: 585,
    exit_reason: "TAKE_PROFIT_1",
    entry_time: "2024-01-13T10:30:00",
    exit_time: "2024-01-14T11:00:00",
  },
];

const mockStats: Statistics = {
  total_trades: 25,
  winning_trades: 16,
  losing_trades: 9,
  win_rate: 64,
  total_pnl: 850000,
  avg_pnl: 34000,
  max_profit: 240000,
  max_loss: -80000,
};

export default function HistoryPage() {
  const [trades, setTrades] = useState<Trade[]>(mockTrades);
  const [stats, setStats] = useState<Statistics>(mockStats);
  const [filter, setFilter] = useState<"all" | "win" | "loss">("all");
  const [sortBy, setSortBy] = useState<"date" | "pnl" | "pnl_rate">("date");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [tradesData, statsData] = await Promise.all([
          tradesApi.getAll({ limit: 50 }),
          tradesApi.getStatistics("all"),
        ]);
        if (tradesData) setTrades(tradesData);
        if (statsData) setStats(statsData);
      } catch (error) {
        console.error("Error fetching trades:", error);
        // Keep mock data on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredTrades = trades
    .filter((t) => {
      if (filter === "win") return t.pnl > 0;
      if (filter === "loss") return t.pnl <= 0;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "pnl") return b.pnl - a.pnl;
      if (sortBy === "pnl_rate") return b.pnl_rate - a.pnl_rate;
      return (
        new Date(b.exit_time).getTime() - new Date(a.exit_time).getTime()
      );
    });

  const exitReasonLabels: Record<string, string> = {
    TAKE_PROFIT_1: "TP1",
    TAKE_PROFIT_2: "TP2",
    STOP_LOSS: "S/L",
    TRAILING_STOP: "Trail",
    SELL_SIGNAL: "Signal",
    MANUAL: "Manual",
  };

  return (
    <div className="min-h-screen gradient-mesh">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-effect border-b border-[var(--border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="p-2 rounded-xl hover:bg-[var(--secondary)] transition-colors"
              >
                <svg
                  className="w-5 h-5 text-[var(--muted)]"
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
                <h1 className="text-xl font-bold text-[var(--foreground)]">
                  Trade History
                </h1>
                <p className="text-sm text-[var(--muted)]">
                  View all your trading activity
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-[var(--card)] rounded-2xl p-5 border border-[var(--border)]">
            <p className="text-sm text-[var(--muted)] mb-1">Total Trades</p>
            <p className="text-3xl font-bold text-[var(--foreground)]">
              {stats.total_trades}
            </p>
            <p className="text-xs text-[var(--muted)] mt-1">
              {stats.winning_trades}W / {stats.losing_trades}L
            </p>
          </div>
          <div className="bg-[var(--card)] rounded-2xl p-5 border border-[var(--border)]">
            <p className="text-sm text-[var(--muted)] mb-1">Win Rate</p>
            <p className="text-3xl font-bold text-emerald-500">
              {stats.win_rate}%
            </p>
            <div className="mt-2 h-1.5 bg-[var(--secondary)] rounded-full">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full"
                style={{ width: `${stats.win_rate}%` }}
              />
            </div>
          </div>
          <div className="bg-[var(--card)] rounded-2xl p-5 border border-[var(--border)]">
            <p className="text-sm text-[var(--muted)] mb-1">Total P&L</p>
            <p
              className={`text-3xl font-bold ${
                stats.total_pnl >= 0 ? "text-emerald-500" : "text-rose-500"
              }`}
            >
              {stats.total_pnl >= 0 ? "+" : ""}
              {stats.total_pnl.toLocaleString()}
            </p>
            <p className="text-xs text-[var(--muted)] mt-1">KRW</p>
          </div>
          <div className="bg-[var(--card)] rounded-2xl p-5 border border-[var(--border)]">
            <p className="text-sm text-[var(--muted)] mb-1">Avg P&L</p>
            <p
              className={`text-3xl font-bold ${
                stats.avg_pnl >= 0 ? "text-emerald-500" : "text-rose-500"
              }`}
            >
              {stats.avg_pnl >= 0 ? "+" : ""}
              {stats.avg_pnl.toLocaleString()}
            </p>
            <p className="text-xs text-[var(--muted)] mt-1">per trade</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="flex gap-2">
            {(["all", "win", "loss"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  filter === f
                    ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white"
                    : "bg-[var(--secondary)] text-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
              >
                {f === "all" ? "All" : f === "win" ? "Wins" : "Losses"}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <span className="text-sm text-[var(--muted)]">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) =>
                setSortBy(e.target.value as "date" | "pnl" | "pnl_rate")
              }
              className="bg-[var(--secondary)] border border-[var(--border)] rounded-xl px-3 py-2 text-sm text-[var(--foreground)]"
            >
              <option value="date">Date</option>
              <option value="pnl">P&L Amount</option>
              <option value="pnl_rate">P&L %</option>
            </select>
          </div>
        </div>

        {/* Trade List */}
        <div className="space-y-3">
          {filteredTrades.map((trade) => {
            const isProfit = trade.pnl > 0;
            return (
              <div
                key={trade.trade_id}
                className="bg-[var(--card)] rounded-2xl p-5 border border-[var(--border)] card-hover"
              >
                <div className="flex items-center justify-between">
                  {/* Left - Stock Info */}
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold ${
                        isProfit
                          ? "bg-gradient-to-br from-emerald-500 to-teal-500"
                          : "bg-gradient-to-br from-rose-500 to-pink-500"
                      }`}
                    >
                      {trade.stock_name.charAt(0)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-[var(--foreground)]">
                          {trade.stock_name}
                        </h3>
                        <span className="text-xs text-[var(--muted)] font-mono">
                          {trade.stock_code}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-sm text-[var(--muted)]">
                          {trade.quantity} shares
                        </span>
                        <span className="text-sm text-[var(--muted)]">
                          {trade.entry_price.toLocaleString()} &rarr;{" "}
                          {trade.exit_price.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right - P&L */}
                  <div className="text-right">
                    <p
                      className={`text-xl font-bold ${
                        isProfit ? "text-emerald-500" : "text-rose-500"
                      }`}
                    >
                      {isProfit ? "+" : ""}
                      {trade.pnl.toLocaleString()} KRW
                    </p>
                    <div className="flex items-center justify-end gap-2 mt-1">
                      <span
                        className={`text-sm font-semibold ${
                          isProfit ? "text-emerald-500" : "text-rose-500"
                        }`}
                      >
                        {isProfit ? "+" : ""}
                        {trade.pnl_rate.toFixed(2)}%
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-lg text-xs font-medium ${
                          trade.exit_reason.includes("PROFIT")
                            ? "bg-emerald-500/10 text-emerald-500"
                            : trade.exit_reason.includes("STOP") ||
                              trade.exit_reason.includes("LOSS")
                            ? "bg-rose-500/10 text-rose-500"
                            : "bg-amber-500/10 text-amber-500"
                        }`}
                      >
                        {exitReasonLabels[trade.exit_reason] ||
                          trade.exit_reason}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Bottom - Time Info */}
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--border)]">
                  <div className="flex items-center gap-4 text-xs text-[var(--muted)]">
                    <span>
                      Entry:{" "}
                      {new Date(trade.entry_time).toLocaleString("ko-KR", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                    <span>
                      Exit:{" "}
                      {new Date(trade.exit_time).toLocaleString("ko-KR", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                  <span className="text-xs text-[var(--muted)]">
                    Fee: {trade.commission.toLocaleString()} KRW
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {filteredTrades.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--secondary)] flex items-center justify-center">
              <span className="text-3xl">📋</span>
            </div>
            <p className="text-[var(--muted)] font-medium">No trades found</p>
          </div>
        )}
      </main>
    </div>
  );
}
