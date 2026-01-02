"use client";

import { useEffect, useRef, useState } from "react";
import { ChartData } from "@/types";

interface ChartProps {
  data: ChartData[];
  height?: number;
  showVolume?: boolean;
}

export function CandlestickChart({ data, height = 400, showVolume = true }: ChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredCandle, setHoveredCandle] = useState<ChartData | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!canvasRef.current || data.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const chartHeight = showVolume ? height * 0.7 : height;
    const volumeHeight = showVolume ? height * 0.25 : 0;
    const padding = { top: 20, right: 60, bottom: 30, left: 10 };

    // Clear canvas
    ctx.fillStyle = "var(--card)";
    ctx.fillRect(0, 0, width, height);

    // Calculate price range
    const prices = data.flatMap(d => [d.high, d.low]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 1;
    const pricePadding = priceRange * 0.1;

    // Calculate volume range
    const volumes = data.map(d => d.volume);
    const maxVolume = Math.max(...volumes) || 1;

    // Candle width
    const candleWidth = Math.max(2, (width - padding.left - padding.right) / data.length - 2);
    const candleSpacing = (width - padding.left - padding.right) / data.length;

    // Draw grid lines
    ctx.strokeStyle = "rgba(128, 128, 128, 0.1)";
    ctx.lineWidth = 1;

    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartHeight - padding.top - padding.bottom) * (i / 4);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      // Price labels
      const price = maxPrice + pricePadding - (priceRange + 2 * pricePadding) * (i / 4);
      ctx.fillStyle = "rgba(128, 128, 128, 0.7)";
      ctx.font = "11px sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(price.toLocaleString(), width - 5, y + 4);
    }

    // Draw candles
    data.forEach((candle, i) => {
      const x = padding.left + i * candleSpacing + candleSpacing / 2;
      const isUp = candle.close >= candle.open;

      // Calculate y positions
      const openY = padding.top + ((maxPrice + pricePadding - candle.open) / (priceRange + 2 * pricePadding)) * (chartHeight - padding.top - padding.bottom);
      const closeY = padding.top + ((maxPrice + pricePadding - candle.close) / (priceRange + 2 * pricePadding)) * (chartHeight - padding.top - padding.bottom);
      const highY = padding.top + ((maxPrice + pricePadding - candle.high) / (priceRange + 2 * pricePadding)) * (chartHeight - padding.top - padding.bottom);
      const lowY = padding.top + ((maxPrice + pricePadding - candle.low) / (priceRange + 2 * pricePadding)) * (chartHeight - padding.top - padding.bottom);

      const candleColor = isUp ? "#10b981" : "#ef4444";

      // Draw wick
      ctx.strokeStyle = candleColor;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, highY);
      ctx.lineTo(x, lowY);
      ctx.stroke();

      // Draw body
      ctx.fillStyle = candleColor;
      const bodyTop = Math.min(openY, closeY);
      const bodyHeight = Math.max(1, Math.abs(closeY - openY));
      ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);

      // Draw volume
      if (showVolume) {
        const volumeY = chartHeight + 10;
        const volumeBarHeight = (candle.volume / maxVolume) * volumeHeight;
        ctx.fillStyle = isUp ? "rgba(16, 185, 129, 0.5)" : "rgba(239, 68, 68, 0.5)";
        ctx.fillRect(
          x - candleWidth / 2,
          volumeY + volumeHeight - volumeBarHeight,
          candleWidth,
          volumeBarHeight
        );
      }
    });

    // Draw date labels
    ctx.fillStyle = "rgba(128, 128, 128, 0.7)";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    const labelInterval = Math.ceil(data.length / 6);
    data.forEach((candle, i) => {
      if (i % labelInterval === 0) {
        const x = padding.left + i * candleSpacing + candleSpacing / 2;
        const date = new Date(candle.timestamp);
        const label = `${date.getMonth() + 1}/${date.getDate()}`;
        ctx.fillText(label, x, height - 5);
      }
    });

  }, [data, height, showVolume]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || data.length === 0) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const padding = { left: 10, right: 60 };
    const candleSpacing = (rect.width - padding.left - padding.right) / data.length;
    const index = Math.floor((x - padding.left) / candleSpacing);

    if (index >= 0 && index < data.length) {
      setHoveredCandle(data[index]);
      setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    } else {
      setHoveredCandle(null);
    }
  };

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        style={{ width: "100%", height }}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoveredCandle(null)}
        className="cursor-crosshair"
      />
      {hoveredCandle && (
        <div
          className="absolute bg-[var(--card)] border border-[var(--border)] rounded-lg p-3 shadow-lg pointer-events-none z-10"
          style={{
            left: Math.min(mousePos.x + 10, (canvasRef.current?.clientWidth || 300) - 150),
            top: mousePos.y + 10,
          }}
        >
          <p className="text-xs text-[var(--muted)]">
            {new Date(hoveredCandle.timestamp).toLocaleDateString("ko-KR")}
          </p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-1 text-xs">
            <span className="text-[var(--muted)]">시가</span>
            <span className="text-[var(--foreground)] text-right">{hoveredCandle.open.toLocaleString()}</span>
            <span className="text-[var(--muted)]">고가</span>
            <span className="text-rose-500 text-right">{hoveredCandle.high.toLocaleString()}</span>
            <span className="text-[var(--muted)]">저가</span>
            <span className="text-blue-500 text-right">{hoveredCandle.low.toLocaleString()}</span>
            <span className="text-[var(--muted)]">종가</span>
            <span className="text-[var(--foreground)] text-right">{hoveredCandle.close.toLocaleString()}</span>
            <span className="text-[var(--muted)]">거래량</span>
            <span className="text-[var(--foreground)] text-right">{(hoveredCandle.volume / 1000).toFixed(0)}K</span>
          </div>
        </div>
      )}
    </div>
  );
}

// Simple line chart for quick view
export function MiniChart({ data, positive }: { data: number[]; positive: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || data.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = 60 * dpr;
    canvas.height = 24 * dpr;
    ctx.scale(dpr, dpr);

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    ctx.strokeStyle = positive ? "#10b981" : "#ef4444";
    ctx.lineWidth = 1.5;
    ctx.beginPath();

    data.forEach((value, i) => {
      const x = (i / (data.length - 1)) * 60;
      const y = 24 - ((value - min) / range) * 20 - 2;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.stroke();
  }, [data, positive]);

  return <canvas ref={canvasRef} style={{ width: 60, height: 24 }} />;
}
