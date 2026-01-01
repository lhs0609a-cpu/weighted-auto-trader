"use client";

interface StatCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  trend?: "up" | "down" | "neutral";
  icon?: string;
}

export default function StatCard({
  title,
  value,
  subValue,
  trend,
  icon,
}: StatCardProps) {
  const trendColors = {
    up: "text-red-500",
    down: "text-blue-500",
    neutral: "text-gray-500",
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex justify-between items-start">
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
      {subValue && (
        <p className={`mt-1 text-sm ${trend ? trendColors[trend] : "text-gray-500"}`}>
          {subValue}
        </p>
      )}
    </div>
  );
}
