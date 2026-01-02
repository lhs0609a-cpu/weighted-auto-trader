"use client";

import { useState, useEffect } from "react";
import { Quote } from "@/types";

interface OrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  quote: Quote | null;
  side: "BUY" | "SELL";
  onSubmit: (order: OrderRequest) => Promise<void>;
}

export interface OrderRequest {
  stock_code: string;
  quantity: number;
  price: number | null;
  order_type: "MARKET" | "LIMIT";
}

export default function OrderModal({
  isOpen,
  onClose,
  quote,
  side,
  onSubmit,
}: OrderModalProps) {
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [quantity, setQuantity] = useState<number>(1);
  const [price, setPrice] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen && quote) {
      setQuantity(1);
      setPrice(quote.price);
      setOrderType("MARKET");
      setError(null);
    }
  }, [isOpen, quote]);

  // Close on escape key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  if (!isOpen || !quote) return null;

  const isBuy = side === "BUY";
  const estimatedAmount =
    orderType === "MARKET" ? quote.price * quantity : price * quantity;

  const handleSubmit = async () => {
    if (quantity <= 0) {
      setError("수량을 입력해주세요");
      return;
    }
    if (orderType === "LIMIT" && price <= 0) {
      setError("가격을 입력해주세요");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onSubmit({
        stock_code: quote.stock_code,
        quantity,
        price: orderType === "LIMIT" ? price : null,
        order_type: orderType,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "주문 실패");
    } finally {
      setIsSubmitting(false);
    }
  };

  const quickQuantities = [1, 5, 10, 50, 100];

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 animate-fade-in"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div
          className="w-full max-w-md pointer-events-auto animate-scale-in"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="glass rounded-2xl border border-[var(--glass-border)] overflow-hidden shadow-2xl">
            {/* Header */}
            <div
              className={`px-6 py-4 border-b border-[var(--card-border)] ${
                isBuy
                  ? "bg-gradient-to-r from-emerald-500/20 to-cyan-500/20"
                  : "bg-gradient-to-r from-rose-500/20 to-orange-500/20"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      isBuy
                        ? "bg-emerald-500 shadow-lg shadow-emerald-500/30"
                        : "bg-rose-500 shadow-lg shadow-rose-500/30"
                    }`}
                  >
                    {isBuy ? (
                      <svg
                        className="w-5 h-5 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                        />
                      </svg>
                    ) : (
                      <svg
                        className="w-5 h-5 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M20 12H4"
                        />
                      </svg>
                    )}
                  </div>
                  <div>
                    <h2
                      className={`text-xl font-bold ${
                        isBuy ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {isBuy ? "매수" : "매도"} 주문
                    </h2>
                    <p className="text-sm text-muted">{quote.name}</p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <svg
                    className="w-5 h-5 text-muted"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>

            {/* Body */}
            <div className="p-6 space-y-5">
              {/* Current Price */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
                <span className="text-sm text-muted">현재가</span>
                <div className="text-right">
                  <span className="text-2xl font-bold text-[var(--foreground)] tabular-nums">
                    {quote.price.toLocaleString()}
                  </span>
                  <span className="text-sm text-muted ml-1">원</span>
                  <span
                    className={`ml-2 text-sm font-semibold ${
                      quote.change_rate >= 0
                        ? "text-emerald-400"
                        : "text-rose-400"
                    }`}
                  >
                    {quote.change_rate >= 0 ? "+" : ""}
                    {quote.change_rate.toFixed(2)}%
                  </span>
                </div>
              </div>

              {/* Order Type */}
              <div>
                <label className="block text-sm font-medium text-muted mb-2">
                  주문 유형
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setOrderType("MARKET")}
                    className={`py-3 px-4 rounded-xl font-semibold transition-all ${
                      orderType === "MARKET"
                        ? "bg-violet-500 text-white shadow-lg shadow-violet-500/30"
                        : "bg-[var(--card)] text-muted border border-[var(--card-border)] hover:border-violet-500/50"
                    }`}
                  >
                    시장가
                  </button>
                  <button
                    onClick={() => setOrderType("LIMIT")}
                    className={`py-3 px-4 rounded-xl font-semibold transition-all ${
                      orderType === "LIMIT"
                        ? "bg-violet-500 text-white shadow-lg shadow-violet-500/30"
                        : "bg-[var(--card)] text-muted border border-[var(--card-border)] hover:border-violet-500/50"
                    }`}
                  >
                    지정가
                  </button>
                </div>
              </div>

              {/* Price Input (for LIMIT orders) */}
              {orderType === "LIMIT" && (
                <div>
                  <label className="block text-sm font-medium text-muted mb-2">
                    주문 가격
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      value={price}
                      onChange={(e) => setPrice(Number(e.target.value))}
                      className="w-full px-4 py-3 pr-12 rounded-xl bg-[var(--card)] border border-[var(--card-border)] text-[var(--foreground)] font-semibold text-lg tabular-nums focus:outline-none focus:border-violet-500 transition-colors"
                    />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-muted">
                      원
                    </span>
                  </div>
                  <div className="flex gap-2 mt-2">
                    {[-2, -1, 0, 1, 2].map((pct) => (
                      <button
                        key={pct}
                        onClick={() =>
                          setPrice(
                            Math.round(quote.price * (1 + pct / 100))
                          )
                        }
                        className="flex-1 py-1.5 text-xs rounded-lg bg-[var(--card)] border border-[var(--card-border)] text-muted hover:border-violet-500/50 hover:text-[var(--foreground)] transition-colors"
                      >
                        {pct >= 0 ? "+" : ""}
                        {pct}%
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Quantity */}
              <div>
                <label className="block text-sm font-medium text-muted mb-2">
                  수량
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    min={1}
                    className="w-full px-4 py-3 pr-12 rounded-xl bg-[var(--card)] border border-[var(--card-border)] text-[var(--foreground)] font-semibold text-lg tabular-nums focus:outline-none focus:border-violet-500 transition-colors"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-muted">
                    주
                  </span>
                </div>
                <div className="flex gap-2 mt-2">
                  {quickQuantities.map((qty) => (
                    <button
                      key={qty}
                      onClick={() => setQuantity(qty)}
                      className={`flex-1 py-1.5 text-xs rounded-lg transition-colors ${
                        quantity === qty
                          ? "bg-violet-500/20 border border-violet-500/50 text-violet-400"
                          : "bg-[var(--card)] border border-[var(--card-border)] text-muted hover:border-violet-500/50"
                      }`}
                    >
                      {qty}
                    </button>
                  ))}
                </div>
              </div>

              {/* Estimated Amount */}
              <div className="p-4 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted">예상 금액</span>
                  <div>
                    <span className="text-xl font-bold text-[var(--foreground)] tabular-nums">
                      {estimatedAmount.toLocaleString()}
                    </span>
                    <span className="text-sm text-muted ml-1">원</span>
                  </div>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
                  {error}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-[var(--card-border)] flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 py-3 rounded-xl font-semibold bg-[var(--card)] border border-[var(--card-border)] text-muted hover:text-[var(--foreground)] transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className={`flex-1 py-3 rounded-xl font-semibold text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                  isBuy
                    ? "bg-gradient-to-r from-emerald-500 to-cyan-500 shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50"
                    : "bg-gradient-to-r from-rose-500 to-orange-500 shadow-lg shadow-rose-500/30 hover:shadow-rose-500/50"
                }`}
              >
                {isSubmitting ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="w-4 h-4 animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    처리 중...
                  </span>
                ) : (
                  `${isBuy ? "매수" : "매도"} 주문`
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
