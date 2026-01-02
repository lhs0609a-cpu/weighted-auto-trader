"use client";

interface StatCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  trend?: "up" | "down" | "neutral";
  icon?: string;
  gradient?: "purple" | "blue" | "green" | "orange" | "pink";
}

const gradientConfig = {
  purple: {
    border: "from-[#833AB4] via-[#E1306C] to-[#F77737]",
    bg: "bg-purple-50 dark:bg-purple-500/5",
  },
  blue: {
    border: "from-blue-500 via-cyan-500 to-teal-500",
    bg: "bg-blue-50 dark:bg-blue-500/5",
  },
  green: {
    border: "from-emerald-500 via-green-500 to-teal-500",
    bg: "bg-green-50 dark:bg-green-500/5",
  },
  orange: {
    border: "from-orange-500 via-amber-500 to-yellow-500",
    bg: "bg-orange-50 dark:bg-orange-500/5",
  },
  pink: {
    border: "from-pink-500 via-rose-500 to-red-500",
    bg: "bg-pink-50 dark:bg-pink-500/5",
  },
};

export default function StatCard({
  title,
  value,
  subValue,
  trend,
  icon,
  gradient = "purple",
}: StatCardProps) {
  const config = gradientConfig[gradient];

  return (
    <div className="flex-shrink-0 w-44">
      {/* Instagram Story-like ring */}
      <div className={`p-[2px] rounded-3xl bg-gradient-to-r ${config.border}`}>
        <div className={`${config.bg} bg-white dark:bg-zinc-900 rounded-[22px] p-4`}>
          {/* Icon */}
          {icon && (
            <div className="w-10 h-10 rounded-2xl bg-white dark:bg-zinc-800 shadow-sm flex items-center justify-center mb-3">
              <span className="text-xl">{icon}</span>
            </div>
          )}

          {/* Title */}
          <p className="text-xs text-zinc-400 font-medium mb-1">{title}</p>

          {/* Value */}
          <p className="text-2xl font-bold text-zinc-900 dark:text-white tracking-tight">
            {typeof value === "number" ? value.toLocaleString() : value}
          </p>

          {/* Sub value with trend */}
          {subValue && (
            <div className="flex items-center gap-1.5 mt-2">
              {trend && trend !== "neutral" && (
                <span
                  className={`w-4 h-4 rounded-full flex items-center justify-center ${
                    trend === "up"
                      ? "bg-green-100 dark:bg-green-500/20 text-green-600 dark:text-green-400"
                      : "bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400"
                  }`}
                >
                  {trend === "up" ? (
                    <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 15l7-7 7 7" />
                    </svg>
                  ) : (
                    <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </span>
              )}
              <p
                className={`text-xs font-medium ${
                  trend === "up"
                    ? "text-green-600 dark:text-green-400"
                    : trend === "down"
                    ? "text-red-600 dark:text-red-400"
                    : "text-zinc-400"
                }`}
              >
                {subValue}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
