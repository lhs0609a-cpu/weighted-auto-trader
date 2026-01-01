"use client";

import { useState } from "react";

interface HeaderProps {
  isConnected: boolean;
  tradingStyle?: string;
  onStyleChange?: (style: string) => void;
}

export default function Header({
  isConnected,
  tradingStyle = "DAYTRADING",
  onStyleChange,
}: HeaderProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const styles = [
    { value: "SCALPING", label: "스캘핑", desc: "초단타" },
    { value: "DAYTRADING", label: "단타", desc: "당일매매" },
    { value: "SWING", label: "스윙", desc: "수일보유" },
  ];

  return (
    <header className="sticky top-0 z-50 glass-card border-b border-[var(--border)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                  />
                </svg>
              </div>
              <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white dark:border-gray-800" />
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                WeightedTrader
              </h1>
              <p className="text-xs text-[var(--muted)] -mt-0.5">
                Smart Auto Trading
              </p>
            </div>
          </div>

          {/* Center - Trading Style */}
          <div className="hidden md:flex items-center gap-1 p-1 bg-[var(--secondary)] rounded-xl">
            {styles.map((style) => (
              <button
                key={style.value}
                onClick={() => onStyleChange?.(style.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  tradingStyle === style.value
                    ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-md"
                    : "text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-[var(--card)]"
                }`}
              >
                <span>{style.label}</span>
                <span className="hidden lg:inline text-xs ml-1 opacity-70">
                  {style.desc}
                </span>
              </button>
            ))}
          </div>

          {/* Right - Status & Menu */}
          <div className="flex items-center gap-4">
            {/* Connection Status */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--secondary)]">
              <span className="relative flex h-2.5 w-2.5">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    isConnected ? "bg-green-400" : "bg-red-400"
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                    isConnected ? "bg-green-500" : "bg-red-500"
                  }`}
                />
              </span>
              <span className="text-xs font-medium text-[var(--muted)]">
                {isConnected ? "Live" : "Offline"}
              </span>
            </div>

            {/* Time */}
            <div className="hidden sm:block text-sm font-mono text-[var(--muted)]">
              <CurrentTime />
            </div>

            {/* Settings Button */}
            <button className="p-2 rounded-xl hover:bg-[var(--secondary)] transition-colors">
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
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </button>

            {/* Mobile Menu */}
            <button
              className="md:hidden p-2 rounded-xl hover:bg-[var(--secondary)] transition-colors"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={isMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16m-7 6h7"}
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {isMenuOpen && (
          <div className="md:hidden py-3 border-t border-[var(--border)] animate-slide-up">
            <div className="flex flex-col gap-1">
              {styles.map((style) => (
                <button
                  key={style.value}
                  onClick={() => {
                    onStyleChange?.(style.value);
                    setIsMenuOpen(false);
                  }}
                  className={`px-4 py-2.5 rounded-lg text-left transition-all ${
                    tradingStyle === style.value
                      ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white"
                      : "hover:bg-[var(--secondary)]"
                  }`}
                >
                  <span className="font-medium">{style.label}</span>
                  <span className="text-sm ml-2 opacity-70">{style.desc}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

function CurrentTime() {
  const [time, setTime] = useState(new Date());

  if (typeof window !== "undefined") {
    setTimeout(() => setTime(new Date()), 1000);
  }

  return (
    <span>
      {time.toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })}
    </span>
  );
}
