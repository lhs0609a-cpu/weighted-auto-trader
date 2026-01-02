"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

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
  const [scrolled, setScrolled] = useState(false);
  const [notifications, setNotifications] = useState(3);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close menu on route change
  useEffect(() => {
    setIsMenuOpen(false);
  }, [pathname]);

  const styles = [
    { value: "SCALPING", label: "Scalping", icon: "bolt", color: "cyan" },
    { value: "DAYTRADING", label: "Day Trade", icon: "sun", color: "purple" },
    { value: "SWING", label: "Swing", icon: "wave", color: "pink" },
  ];

  const navItems = [
    { href: "/", label: "Dashboard", icon: "grid" },
    { href: "/history", label: "History", icon: "clock" },
    { href: "/backtest", label: "Backtest", icon: "chart" },
    { href: "/settings", label: "Settings", icon: "cog" },
  ];

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <>
      <header
        className={`sticky top-0 z-50 transition-all duration-500 ${
          scrolled
            ? "glass border-b border-[var(--glass-border)] shadow-lg shadow-black/5"
            : "bg-transparent"
        }`}
      >
        <div className="container-app">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 group">
              <div className="relative">
                {/* Animated gradient border */}
                <div className="absolute -inset-0.5 rounded-xl bg-gradient-to-r from-violet-500 via-fuchsia-500 to-cyan-500 opacity-70 blur-sm group-hover:opacity-100 transition-opacity animate-gradient-shift" />
                <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 flex items-center justify-center shadow-lg">
                  <svg
                    className="w-5 h-5 text-white drop-shadow-sm"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2.5}
                      d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                    />
                  </svg>
                </div>
                {/* Status indicator with pulse */}
                <div
                  className={`absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-[var(--background)] ${
                    isConnected ? "bg-emerald-400" : "bg-red-400"
                  }`}
                >
                  {isConnected && (
                    <span className="absolute inset-0 rounded-full bg-emerald-400 animate-ping opacity-75" />
                  )}
                </div>
              </div>
              <div className="hidden sm:block">
                <h1 className="text-lg font-bold text-gradient">
                  WeightedTrader
                </h1>
                <p className="text-[10px] text-muted -mt-0.5 font-medium tracking-wide uppercase">
                  Smart Trading
                </p>
              </div>
            </Link>

            {/* Center - Trading Style Selector */}
            <div className="hidden md:flex items-center">
              <div className="relative flex items-center p-1 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] shadow-lg shadow-black/10">
                {/* Background indicator */}
                <div
                  className={`absolute h-[calc(100%-8px)] rounded-xl transition-all duration-300 ease-out ${
                    tradingStyle === "SCALPING"
                      ? "left-1 w-[calc(33.333%-2px)] bg-gradient-to-r from-cyan-500 to-cyan-400"
                      : tradingStyle === "DAYTRADING"
                      ? "left-[calc(33.333%+1px)] w-[calc(33.333%-2px)] bg-gradient-to-r from-violet-500 to-fuchsia-500"
                      : "left-[calc(66.666%+1px)] w-[calc(33.333%-4px)] bg-gradient-to-r from-pink-500 to-rose-500"
                  }`}
                  style={{
                    boxShadow:
                      tradingStyle === "SCALPING"
                        ? "0 4px 20px -5px rgba(6, 182, 212, 0.5)"
                        : tradingStyle === "DAYTRADING"
                        ? "0 4px 20px -5px rgba(139, 92, 246, 0.5)"
                        : "0 4px 20px -5px rgba(236, 72, 153, 0.5)",
                  }}
                />
                {styles.map((style) => (
                  <button
                    key={style.value}
                    onClick={() => onStyleChange?.(style.value)}
                    className={`relative px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
                      tradingStyle === style.value
                        ? "text-white"
                        : "text-muted hover:text-[var(--foreground)]"
                    }`}
                  >
                    <span className="relative flex items-center gap-2">
                      <StyleIcon type={style.icon} />
                      {style.label}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Right - Status & Actions */}
            <div className="flex items-center gap-2">
              {/* Live Status Badge */}
              <div
                className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full transition-all duration-300 ${
                  isConnected
                    ? "border border-emerald-500/30 bg-emerald-500/10 shadow-lg shadow-emerald-500/10"
                    : "border border-red-500/30 bg-red-500/10 shadow-lg shadow-red-500/10"
                }`}
              >
                <span
                  className={`status-dot ${
                    isConnected ? "status-online" : "status-offline"
                  }`}
                />
                <span
                  className={`text-xs font-bold tracking-wide ${
                    isConnected ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {isConnected ? "LIVE" : "OFFLINE"}
                </span>
              </div>

              {/* Time Display */}
              <div className="hidden lg:flex items-center px-3 py-1.5 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
                <CurrentTime />
              </div>

              {/* Notifications */}
              <button className="relative p-2.5 rounded-xl text-muted hover:text-[var(--foreground)] hover:bg-[var(--card)] transition-all group">
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
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                {notifications > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-gradient-to-r from-rose-500 to-pink-500 text-[10px] font-bold text-white flex items-center justify-center shadow-lg shadow-rose-500/50 group-hover:scale-110 transition-transform">
                    {notifications > 9 ? "9+" : notifications}
                  </span>
                )}
              </button>

              {/* Desktop Navigation */}
              <nav className="hidden lg:flex items-center gap-1 ml-2">
                {navItems.slice(1).map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`relative p-2.5 rounded-xl transition-all group ${
                      isActive(item.href)
                        ? "text-[var(--foreground)] bg-[var(--card)]"
                        : "text-muted hover:text-[var(--foreground)] hover:bg-[var(--card)]"
                    }`}
                    title={item.label}
                  >
                    <NavIcon type={item.icon} />
                    {isActive(item.href) && (
                      <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-violet-500" />
                    )}
                  </Link>
                ))}
              </nav>

              {/* User Profile */}
              <button className="hidden lg:flex items-center gap-2 p-1 pr-3 rounded-full bg-[var(--card)] border border-[var(--card-border)] hover:border-violet-500/30 transition-all group">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white text-sm font-bold shadow-lg group-hover:shadow-violet-500/30 transition-shadow">
                  W
                </div>
                <svg
                  className="w-4 h-4 text-muted group-hover:text-[var(--foreground)] transition-colors"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              {/* Mobile Menu Toggle */}
              <button
                className="lg:hidden p-2.5 rounded-xl hover:bg-[var(--card)] transition-all"
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
                    d={
                      isMenuOpen
                        ? "M6 18L18 6M6 6l12 12"
                        : "M4 6h16M4 12h16M4 18h16"
                    }
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {isMenuOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden animate-fade-in"
            onClick={() => setIsMenuOpen(false)}
          />

          {/* Menu Panel */}
          <div className="fixed top-16 left-0 right-0 z-40 lg:hidden animate-slide-down">
            <div className="container-app">
              <div className="glass rounded-2xl border border-[var(--glass-border)] p-4 shadow-2xl mt-2">
                {/* Mobile Status */}
                <div className="flex items-center justify-between mb-4 pb-4 border-b border-[var(--card-border)]">
                  <div className="flex items-center gap-2">
                    <span
                      className={`status-dot ${
                        isConnected ? "status-online" : "status-offline"
                      }`}
                    />
                    <span
                      className={`text-sm font-semibold ${
                        isConnected ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {isConnected ? "Connected" : "Disconnected"}
                    </span>
                  </div>
                  <CurrentTime />
                </div>

                {/* Trading Style */}
                <div className="mb-4">
                  <p className="text-xs text-muted uppercase tracking-wider mb-3 font-semibold">
                    Trading Style
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    {styles.map((style) => (
                      <button
                        key={style.value}
                        onClick={() => {
                          onStyleChange?.(style.value);
                        }}
                        className={`relative p-3 rounded-xl text-sm font-semibold transition-all overflow-hidden ${
                          tradingStyle === style.value
                            ? "text-white"
                            : "bg-[var(--card)] text-muted border border-[var(--card-border)] hover:border-violet-500/30"
                        }`}
                      >
                        {tradingStyle === style.value && (
                          <span
                            className={`absolute inset-0 ${
                              style.color === "cyan"
                                ? "bg-gradient-to-br from-cyan-500 to-cyan-400"
                                : style.color === "purple"
                                ? "bg-gradient-to-br from-violet-500 to-fuchsia-500"
                                : "bg-gradient-to-br from-pink-500 to-rose-500"
                            }`}
                          />
                        )}
                        <span className="relative flex flex-col items-center gap-1">
                          <StyleIcon type={style.icon} />
                          <span>{style.label}</span>
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Navigation */}
                <nav className="space-y-1">
                  {navItems.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setIsMenuOpen(false)}
                      className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                        isActive(item.href)
                          ? "bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 text-[var(--foreground)] border border-violet-500/30"
                          : "hover:bg-[var(--card)] text-muted hover:text-[var(--foreground)]"
                      }`}
                    >
                      <NavIcon type={item.icon} />
                      <span className="font-medium">{item.label}</span>
                      {isActive(item.href) && (
                        <span className="ml-auto w-1.5 h-1.5 rounded-full bg-violet-500" />
                      )}
                    </Link>
                  ))}
                </nav>

                {/* User Section */}
                <div className="mt-4 pt-4 border-t border-[var(--card-border)]">
                  <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-[var(--card)] transition-all">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-bold shadow-lg">
                      W
                    </div>
                    <div className="flex-1 text-left">
                      <p className="font-semibold text-sm">Trader</p>
                      <p className="text-xs text-muted">View Profile</p>
                    </div>
                    <svg
                      className="w-4 h-4 text-muted"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}

function StyleIcon({ type }: { type: string }) {
  const icons: Record<string, React.ReactNode> = {
    bolt: (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
          clipRule="evenodd"
        />
      </svg>
    ),
    sun: (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
          clipRule="evenodd"
        />
      </svg>
    ),
    wave: (
      <svg
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"
        />
      </svg>
    ),
  };
  return icons[type] || null;
}

function NavIcon({ type }: { type: string }) {
  const icons: Record<string, React.ReactNode> = {
    grid: (
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
          d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
        />
      </svg>
    ),
    clock: (
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
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
    chart: (
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
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
    ),
    cog: (
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
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
    ),
  };
  return icons[type] || null;
}

function CurrentTime() {
  const [time, setTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      setTime(
        new Date().toLocaleTimeString("ko-KR", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <span className="text-sm font-mono text-muted tabular-nums">{time}</span>
  );
}
