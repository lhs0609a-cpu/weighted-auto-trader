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

  useEffect(() => {
    setIsMenuOpen(false);
  }, [pathname]);

  const styles = [
    { value: "SCALPING", label: "Scalping", icon: "bolt", emoji: "⚡" },
    { value: "DAYTRADING", label: "Day", icon: "sun", emoji: "☀️" },
    { value: "SWING", label: "Swing", icon: "wave", emoji: "🌊" },
  ];

  const navItems = [
    { href: "/", label: "Home", icon: "home" },
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
        className={`sticky top-0 z-50 transition-all duration-300 ${
          scrolled
            ? "bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border-b border-zinc-200/50 dark:border-zinc-800/50"
            : "bg-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 group">
              <div className="relative">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#833AB4] via-[#E1306C] to-[#F77737] p-[2px] group-hover:scale-105 transition-transform">
                  <div className="w-full h-full rounded-[14px] bg-white dark:bg-zinc-900 flex items-center justify-center">
                    <svg
                      className="w-5 h-5 text-transparent bg-clip-text bg-gradient-to-br from-[#833AB4] via-[#E1306C] to-[#F77737]"
                      fill="url(#logoGradient)"
                      viewBox="0 0 24 24"
                    >
                      <defs>
                        <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#833AB4" />
                          <stop offset="50%" stopColor="#E1306C" />
                          <stop offset="100%" stopColor="#F77737" />
                        </linearGradient>
                      </defs>
                      <path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" stroke="url(#logoGradient)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                    </svg>
                  </div>
                </div>
                {/* Connection status */}
                <div
                  className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white dark:border-zinc-900 ${
                    isConnected ? "bg-green-500" : "bg-red-500"
                  }`}
                >
                  {isConnected && (
                    <span className="absolute inset-0 rounded-full bg-green-400 animate-ping opacity-60" />
                  )}
                </div>
              </div>
              <div className="hidden sm:block">
                <h1 className="text-lg font-bold bg-gradient-to-r from-[#833AB4] via-[#E1306C] to-[#F77737] bg-clip-text text-transparent">
                  WeightedTrader
                </h1>
                <p className="text-[10px] text-zinc-400 dark:text-zinc-500 font-medium tracking-widest uppercase">
                  Smart Trading
                </p>
              </div>
            </Link>

            {/* Center - Trading Style Pills */}
            <div className="hidden md:flex items-center">
              <div className="flex items-center p-1 rounded-full bg-zinc-100 dark:bg-zinc-800/50">
                {styles.map((style) => (
                  <button
                    key={style.value}
                    onClick={() => onStyleChange?.(style.value)}
                    className={`relative px-4 py-2 rounded-full text-sm font-semibold transition-all duration-300 ${
                      tradingStyle === style.value
                        ? "text-white"
                        : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
                    }`}
                  >
                    {tradingStyle === style.value && (
                      <span className="absolute inset-0 rounded-full bg-gradient-to-r from-[#833AB4] via-[#E1306C] to-[#F77737] animate-gradient-shift" />
                    )}
                    <span className="relative flex items-center gap-1.5">
                      <span className="text-base">{style.emoji}</span>
                      {style.label}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Right - Actions */}
            <div className="flex items-center gap-1">
              {/* Live Badge */}
              <div
                className={`hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold ${
                  isConnected
                    ? "bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-400"
                    : "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400"
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"} animate-pulse`} />
                {isConnected ? "LIVE" : "OFFLINE"}
              </div>

              {/* Time */}
              <div className="hidden lg:block px-3 py-1.5 rounded-full bg-zinc-100 dark:bg-zinc-800/50">
                <CurrentTime />
              </div>

              {/* Notifications */}
              <button className="relative p-2.5 rounded-full text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800/50 transition-colors">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
                </svg>
                {notifications > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-gradient-to-r from-[#E1306C] to-[#F77737] text-[10px] font-bold text-white flex items-center justify-center">
                    {notifications}
                  </span>
                )}
              </button>

              {/* Direct Message */}
              <button className="hidden sm:flex p-2.5 rounded-full text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800/50 transition-colors">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                </svg>
              </button>

              {/* Desktop Navigation */}
              <nav className="hidden lg:flex items-center ml-2 border-l border-zinc-200 dark:border-zinc-700 pl-3">
                {navItems.slice(1).map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`p-2.5 rounded-full transition-all ${
                      isActive(item.href)
                        ? "text-zinc-900 dark:text-white bg-zinc-100 dark:bg-zinc-800"
                        : "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                    }`}
                    title={item.label}
                  >
                    <NavIcon type={item.icon} />
                  </Link>
                ))}
              </nav>

              {/* Profile */}
              <button className="hidden lg:flex items-center ml-2 p-0.5 rounded-full bg-gradient-to-r from-[#833AB4] via-[#E1306C] to-[#F77737] hover:scale-105 transition-transform">
                <div className="w-8 h-8 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center text-sm font-bold text-zinc-600 dark:text-zinc-300">
                  W
                </div>
              </button>

              {/* Mobile Menu Toggle */}
              <button
                className="lg:hidden p-2.5 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800/50 transition-colors"
                onClick={() => setIsMenuOpen(!isMenuOpen)}
              >
                <svg className="w-6 h-6 text-zinc-600 dark:text-zinc-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d={isMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"}
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setIsMenuOpen(false)}
          />
          <div className="fixed top-16 left-0 right-0 z-40 lg:hidden p-4">
            <div className="bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden">
              {/* Status Bar */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-100 dark:border-zinc-800">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"} animate-pulse`} />
                  <span className={`text-sm font-semibold ${isConnected ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
                    {isConnected ? "Live" : "Offline"}
                  </span>
                </div>
                <CurrentTime />
              </div>

              {/* Trading Style */}
              <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800">
                <p className="text-xs text-zinc-400 dark:text-zinc-500 uppercase tracking-wider font-semibold mb-3">
                  Trading Style
                </p>
                <div className="flex gap-2">
                  {styles.map((style) => (
                    <button
                      key={style.value}
                      onClick={() => onStyleChange?.(style.value)}
                      className={`flex-1 py-3 rounded-2xl text-sm font-semibold transition-all ${
                        tradingStyle === style.value
                          ? "text-white bg-gradient-to-r from-[#833AB4] via-[#E1306C] to-[#F77737]"
                          : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300"
                      }`}
                    >
                      <span className="text-lg">{style.emoji}</span>
                      <span className="ml-1">{style.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Navigation */}
              <nav className="py-2">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsMenuOpen(false)}
                    className={`flex items-center gap-4 px-5 py-3.5 transition-all ${
                      isActive(item.href)
                        ? "bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-500/10 dark:to-pink-500/10"
                        : "hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                    }`}
                  >
                    <div className={`${isActive(item.href) ? "text-[#E1306C]" : "text-zinc-400"}`}>
                      <NavIcon type={item.icon} />
                    </div>
                    <span className={`font-semibold ${isActive(item.href) ? "text-zinc-900 dark:text-white" : "text-zinc-600 dark:text-zinc-300"}`}>
                      {item.label}
                    </span>
                    {isActive(item.href) && (
                      <div className="ml-auto w-1.5 h-1.5 rounded-full bg-gradient-to-r from-[#833AB4] to-[#E1306C]" />
                    )}
                  </Link>
                ))}
              </nav>

              {/* Profile Section */}
              <div className="px-5 py-4 border-t border-zinc-100 dark:border-zinc-800">
                <button className="w-full flex items-center gap-3 p-3 rounded-2xl hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-all">
                  <div className="w-12 h-12 rounded-full p-0.5 bg-gradient-to-r from-[#833AB4] via-[#E1306C] to-[#F77737]">
                    <div className="w-full h-full rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center text-lg font-bold text-zinc-600 dark:text-zinc-300">
                      W
                    </div>
                  </div>
                  <div className="flex-1 text-left">
                    <p className="font-bold text-zinc-900 dark:text-white">Trader</p>
                    <p className="text-sm text-zinc-400">View Profile</p>
                  </div>
                  <svg className="w-5 h-5 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}

function NavIcon({ type }: { type: string }) {
  const icons: Record<string, React.ReactNode> = {
    home: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
      </svg>
    ),
    clock: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    chart: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
    cog: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
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
    <span className="text-sm font-mono text-zinc-400 dark:text-zinc-500 tabular-nums">{time}</span>
  );
}
