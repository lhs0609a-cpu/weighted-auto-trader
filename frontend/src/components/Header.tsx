"use client";

interface HeaderProps {
  isConnected: boolean;
}

export default function Header({ isConnected }: HeaderProps) {
  return (
    <header className="bg-white dark:bg-gray-800 shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              WeightedAutoTrader
            </h1>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              가중치 기반 자동매매
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? "bg-green-500" : "bg-red-500"
                }`}
              />
              <span className="text-sm text-gray-600 dark:text-gray-300">
                {isConnected ? "연결됨" : "연결 끊김"}
              </span>
            </div>

            <select className="bg-gray-100 dark:bg-gray-700 border-0 rounded-md px-3 py-1.5 text-sm">
              <option value="SCALPING">스캘핑</option>
              <option value="DAYTRADING">단타</option>
              <option value="SWING">스윙</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
}
