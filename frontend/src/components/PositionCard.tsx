"use client";

import { Position } from "@/types";

interface PositionCardProps {
  position: Position;
  onClose?: () => void;
}

export default function PositionCard({ position, onClose }: PositionCardProps) {
  const isProfit = position.unrealized_pnl >= 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-white">
            {position.stock_name}
          </h3>
          <p className="text-xs text-gray-500">{position.stock_code}</p>
        </div>
        <span
          className={`px-2 py-0.5 rounded text-xs font-medium ${
            position.status === "OPEN"
              ? "bg-green-100 text-green-800"
              : "bg-gray-100 text-gray-800"
          }`}
        >
          {position.status === "OPEN" ? "보유중" : "청산"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-gray-500">수량</p>
          <p className="font-medium text-gray-900 dark:text-white">
            {position.quantity}주
          </p>
        </div>
        <div>
          <p className="text-gray-500">평균단가</p>
          <p className="font-medium text-gray-900 dark:text-white">
            {position.entry_price.toLocaleString()}원
          </p>
        </div>
        <div>
          <p className="text-gray-500">현재가</p>
          <p className="font-medium text-gray-900 dark:text-white">
            {position.current_price.toLocaleString()}원
          </p>
        </div>
        <div>
          <p className="text-gray-500">손익</p>
          <p
            className={`font-medium ${
              isProfit ? "text-red-500" : "text-blue-500"
            }`}
          >
            {isProfit ? "+" : ""}
            {position.unrealized_pnl.toLocaleString()}원
            <span className="text-xs ml-1">
              ({isProfit ? "+" : ""}
              {position.unrealized_pnl_pct.toFixed(2)}%)
            </span>
          </p>
        </div>
      </div>

      {onClose && position.status === "OPEN" && (
        <button
          onClick={onClose}
          className="mt-3 w-full py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md text-sm font-medium transition-colors"
        >
          청산하기
        </button>
      )}
    </div>
  );
}
