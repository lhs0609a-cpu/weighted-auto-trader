"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Settings, TradingStyle } from "@/types";
import { settingsApi } from "@/lib/api";

const defaultSettings: Settings = {
  trading_style: "DAYTRADING",
  auto_trade_enabled: false,
  telegram_enabled: false,
  telegram_bot_token: "",
  telegram_chat_id: "",
  max_positions: 5,
  max_position_size_pct: 20,
  stop_loss_pct: 1.5,
  take_profit1_pct: 2.0,
  take_profit2_pct: 3.0,
  trailing_stop_pct: 1.0,
  indicator_weights: {
    volume: 25,
    order_book: 20,
    vwap: 18,
    rsi: 12,
    macd: 10,
    ma: 8,
    bollinger: 5,
    obv: 2,
  },
};

const indicatorInfo: Record<string, { name: string; description: string }> = {
  volume: { name: "Volume", description: "Trading volume analysis" },
  order_book: { name: "Order Book", description: "Bid/Ask strength ratio" },
  vwap: { name: "VWAP", description: "Volume Weighted Average Price" },
  rsi: { name: "RSI", description: "Relative Strength Index" },
  macd: { name: "MACD", description: "Moving Average Convergence Divergence" },
  ma: { name: "Moving Average", description: "Price trend direction" },
  bollinger: { name: "Bollinger Bands", description: "Volatility indicator" },
  obv: { name: "OBV", description: "On-Balance Volume" },
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>(defaultSettings);
  const [activeTab, setActiveTab] = useState<
    "trading" | "notifications" | "weights"
  >("trading");
  const [saved, setSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchSettings = async () => {
      setIsLoading(true);
      try {
        const data = await settingsApi.getAll();
        if (data) {
          setSettings({
            trading_style: data.trading?.trading_style || "DAYTRADING",
            auto_trade_enabled: data.trading?.auto_trade_enabled || false,
            telegram_enabled: data.notifications?.telegram_enabled || false,
            telegram_bot_token: data.notifications?.telegram_bot_token || "",
            telegram_chat_id: data.notifications?.telegram_chat_id || "",
            max_positions: data.trading?.max_positions || 5,
            max_position_size_pct: data.trading?.max_position_size_pct || 20,
            stop_loss_pct: data.trading?.stop_loss_pct || 1.5,
            take_profit1_pct: data.trading?.take_profit1_pct || 2.0,
            take_profit2_pct: data.trading?.take_profit2_pct || 3.0,
            trailing_stop_pct: data.trading?.trailing_stop_pct || 1.0,
            indicator_weights: data.indicator_weights || defaultSettings.indicator_weights,
          });
        }
      } catch (err) {
        console.error("Error fetching settings:", err);
        // Keep default settings on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      await settingsApi.updateAll({
        trading: {
          trading_style: settings.trading_style,
          auto_trade_enabled: settings.auto_trade_enabled,
          max_positions: settings.max_positions,
          max_position_size_pct: settings.max_position_size_pct,
          stop_loss_pct: settings.stop_loss_pct,
          take_profit1_pct: settings.take_profit1_pct,
          take_profit2_pct: settings.take_profit2_pct,
          trailing_stop_pct: settings.trailing_stop_pct,
        },
        notifications: {
          telegram_enabled: settings.telegram_enabled,
          telegram_bot_token: settings.telegram_bot_token,
          telegram_chat_id: settings.telegram_chat_id,
        },
        indicator_weights: settings.indicator_weights,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err: any) {
      setError(err.message || "Failed to save settings");
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestTelegram = async () => {
    try {
      await settingsApi.testTelegram();
      alert("Test message sent successfully!");
    } catch (err: any) {
      alert(err.message || "Failed to send test message");
    }
  };

  const updateWeight = (key: string, value: number) => {
    setSettings((prev) => ({
      ...prev,
      indicator_weights: {
        ...prev.indicator_weights,
        [key]: value,
      },
    }));
  };

  const totalWeight = Object.values(settings.indicator_weights).reduce(
    (sum, w) => sum + w,
    0
  );

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
                  Settings
                </h1>
                <p className="text-sm text-[var(--muted)]">
                  Configure your trading preferences
                </p>
              </div>
            </div>

            <button
              onClick={handleSave}
              disabled={isSaving}
              className={`px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all ${
                saved
                  ? "bg-emerald-500"
                  : "bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600"
              } ${isSaving ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {isSaving ? "Saving..." : saved ? "Saved!" : "Save Changes"}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {(["trading", "notifications", "weights"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                activeTab === tab
                  ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg"
                  : "bg-[var(--secondary)] text-[var(--muted)] hover:text-[var(--foreground)]"
              }`}
            >
              {tab === "trading"
                ? "Trading"
                : tab === "notifications"
                ? "Notifications"
                : "Indicator Weights"}
            </button>
          ))}
        </div>

        {/* Trading Settings */}
        {activeTab === "trading" && (
          <div className="space-y-6">
            {/* Trading Style */}
            <div className="bg-[var(--card)] rounded-2xl p-6 border border-[var(--border)]">
              <h2 className="text-lg font-bold text-[var(--foreground)] mb-4">
                Trading Style
              </h2>
              <div className="grid grid-cols-3 gap-4">
                {(["SCALPING", "DAYTRADING", "SWING"] as TradingStyle[]).map(
                  (style) => (
                    <button
                      key={style}
                      onClick={() =>
                        setSettings((prev) => ({
                          ...prev,
                          trading_style: style,
                        }))
                      }
                      className={`p-4 rounded-xl border-2 transition-all ${
                        settings.trading_style === style
                          ? "border-indigo-500 bg-indigo-500/10"
                          : "border-[var(--border)] hover:border-indigo-500/50"
                      }`}
                    >
                      <p className="font-semibold text-[var(--foreground)]">
                        {style === "SCALPING"
                          ? "Scalping"
                          : style === "DAYTRADING"
                          ? "Day Trading"
                          : "Swing"}
                      </p>
                      <p className="text-xs text-[var(--muted)] mt-1">
                        {style === "SCALPING"
                          ? "Quick trades, small profits"
                          : style === "DAYTRADING"
                          ? "Intraday positions"
                          : "Multi-day holds"}
                      </p>
                    </button>
                  )
                )}
              </div>
            </div>

            {/* Auto Trade */}
            <div className="bg-[var(--card)] rounded-2xl p-6 border border-[var(--border)]">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-[var(--foreground)]">
                    Auto Trading
                  </h2>
                  <p className="text-sm text-[var(--muted)]">
                    Automatically execute trades based on signals
                  </p>
                </div>
                <button
                  onClick={() =>
                    setSettings((prev) => ({
                      ...prev,
                      auto_trade_enabled: !prev.auto_trade_enabled,
                    }))
                  }
                  className={`relative w-14 h-7 rounded-full transition-colors ${
                    settings.auto_trade_enabled
                      ? "bg-indigo-500"
                      : "bg-[var(--secondary)]"
                  }`}
                >
                  <div
                    className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                      settings.auto_trade_enabled
                        ? "translate-x-8"
                        : "translate-x-1"
                    }`}
                  />
                </button>
              </div>
            </div>

            {/* Position Settings */}
            <div className="bg-[var(--card)] rounded-2xl p-6 border border-[var(--border)]">
              <h2 className="text-lg font-bold text-[var(--foreground)] mb-4">
                Position Settings
              </h2>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm text-[var(--muted)] mb-2">
                    Max Positions
                  </label>
                  <input
                    type="number"
                    value={settings.max_positions}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        max_positions: parseInt(e.target.value) || 1,
                      }))
                    }
                    min={1}
                    max={20}
                    className="w-full px-4 py-3 rounded-xl bg-[var(--secondary)] border border-[var(--border)] text-[var(--foreground)]"
                  />
                </div>
                <div>
                  <label className="block text-sm text-[var(--muted)] mb-2">
                    Max Position Size (%)
                  </label>
                  <input
                    type="number"
                    value={settings.max_position_size_pct}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        max_position_size_pct: parseFloat(e.target.value) || 10,
                      }))
                    }
                    min={5}
                    max={50}
                    step={5}
                    className="w-full px-4 py-3 rounded-xl bg-[var(--secondary)] border border-[var(--border)] text-[var(--foreground)]"
                  />
                </div>
              </div>
            </div>

            {/* Risk Settings */}
            <div className="bg-[var(--card)] rounded-2xl p-6 border border-[var(--border)]">
              <h2 className="text-lg font-bold text-[var(--foreground)] mb-4">
                Risk Management
              </h2>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm text-[var(--muted)] mb-2">
                    Stop Loss (%)
                  </label>
                  <input
                    type="number"
                    value={settings.stop_loss_pct}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        stop_loss_pct: parseFloat(e.target.value) || 1,
                      }))
                    }
                    min={0.5}
                    max={10}
                    step={0.5}
                    className="w-full px-4 py-3 rounded-xl bg-[var(--secondary)] border border-[var(--border)] text-[var(--foreground)]"
                  />
                </div>
                <div>
                  <label className="block text-sm text-[var(--muted)] mb-2">
                    Trailing Stop (%)
                  </label>
                  <input
                    type="number"
                    value={settings.trailing_stop_pct}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        trailing_stop_pct: parseFloat(e.target.value) || 1,
                      }))
                    }
                    min={0.5}
                    max={5}
                    step={0.5}
                    className="w-full px-4 py-3 rounded-xl bg-[var(--secondary)] border border-[var(--border)] text-[var(--foreground)]"
                  />
                </div>
                <div>
                  <label className="block text-sm text-[var(--muted)] mb-2">
                    Take Profit 1 (%)
                  </label>
                  <input
                    type="number"
                    value={settings.take_profit1_pct}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        take_profit1_pct: parseFloat(e.target.value) || 2,
                      }))
                    }
                    min={1}
                    max={20}
                    step={0.5}
                    className="w-full px-4 py-3 rounded-xl bg-[var(--secondary)] border border-[var(--border)] text-[var(--foreground)]"
                  />
                </div>
                <div>
                  <label className="block text-sm text-[var(--muted)] mb-2">
                    Take Profit 2 (%)
                  </label>
                  <input
                    type="number"
                    value={settings.take_profit2_pct}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        take_profit2_pct: parseFloat(e.target.value) || 3,
                      }))
                    }
                    min={2}
                    max={30}
                    step={0.5}
                    className="w-full px-4 py-3 rounded-xl bg-[var(--secondary)] border border-[var(--border)] text-[var(--foreground)]"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Notification Settings */}
        {activeTab === "notifications" && (
          <div className="space-y-6">
            <div className="bg-[var(--card)] rounded-2xl p-6 border border-[var(--border)]">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-bold text-[var(--foreground)]">
                    Telegram Notifications
                  </h2>
                  <p className="text-sm text-[var(--muted)]">
                    Receive alerts via Telegram bot
                  </p>
                </div>
                <button
                  onClick={() =>
                    setSettings((prev) => ({
                      ...prev,
                      telegram_enabled: !prev.telegram_enabled,
                    }))
                  }
                  className={`relative w-14 h-7 rounded-full transition-colors ${
                    settings.telegram_enabled
                      ? "bg-indigo-500"
                      : "bg-[var(--secondary)]"
                  }`}
                >
                  <div
                    className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                      settings.telegram_enabled
                        ? "translate-x-8"
                        : "translate-x-1"
                    }`}
                  />
                </button>
              </div>

              {settings.telegram_enabled && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-[var(--muted)] mb-2">
                      Bot Token
                    </label>
                    <input
                      type="password"
                      value={settings.telegram_bot_token}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          telegram_bot_token: e.target.value,
                        }))
                      }
                      placeholder="Enter your Telegram bot token"
                      className="w-full px-4 py-3 rounded-xl bg-[var(--secondary)] border border-[var(--border)] text-[var(--foreground)]"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-[var(--muted)] mb-2">
                      Chat ID
                    </label>
                    <input
                      type="text"
                      value={settings.telegram_chat_id}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          telegram_chat_id: e.target.value,
                        }))
                      }
                      placeholder="Enter your chat ID"
                      className="w-full px-4 py-3 rounded-xl bg-[var(--secondary)] border border-[var(--border)] text-[var(--foreground)]"
                    />
                  </div>
                  <button
                    onClick={handleTestTelegram}
                    className="px-4 py-2 rounded-xl bg-[var(--secondary)] text-[var(--foreground)] text-sm font-medium hover:bg-[var(--border)] transition-colors"
                  >
                    Send Test Message
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Indicator Weights */}
        {activeTab === "weights" && (
          <div className="space-y-6">
            <div className="bg-[var(--card)] rounded-2xl p-6 border border-[var(--border)]">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-bold text-[var(--foreground)]">
                    Indicator Weights
                  </h2>
                  <p className="text-sm text-[var(--muted)]">
                    Adjust the importance of each indicator
                  </p>
                </div>
                <div
                  className={`px-3 py-1 rounded-lg text-sm font-semibold ${
                    totalWeight === 100
                      ? "bg-emerald-500/10 text-emerald-500"
                      : "bg-rose-500/10 text-rose-500"
                  }`}
                >
                  Total: {totalWeight}%
                </div>
              </div>

              <div className="space-y-6">
                {Object.entries(settings.indicator_weights).map(
                  ([key, value]) => (
                    <div key={key}>
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <span className="font-medium text-[var(--foreground)]">
                            {indicatorInfo[key]?.name || key}
                          </span>
                          <p className="text-xs text-[var(--muted)]">
                            {indicatorInfo[key]?.description}
                          </p>
                        </div>
                        <span className="font-semibold text-[var(--foreground)]">
                          {value}%
                        </span>
                      </div>
                      <input
                        type="range"
                        min={0}
                        max={50}
                        value={value}
                        onChange={(e) =>
                          updateWeight(key, parseInt(e.target.value))
                        }
                        className="w-full h-2 bg-[var(--secondary)] rounded-full appearance-none cursor-pointer accent-indigo-500"
                      />
                    </div>
                  )
                )}
              </div>

              {totalWeight !== 100 && (
                <div className="mt-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30">
                  <p className="text-sm text-rose-500">
                    Total weight must equal 100%. Current: {totalWeight}%
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
