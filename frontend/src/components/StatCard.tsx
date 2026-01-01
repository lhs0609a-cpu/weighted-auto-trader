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
    bg: "from-indigo-500/10 to-purple-500/10",
    icon: "from-indigo-500 to-purple-500",
    border: "border-indigo-500/20",
  },
  blue: {
    bg: "from-blue-500/10 to-cyan-500/10",
    icon: "from-blue-500 to-cyan-500",
    border: "border-blue-500/20",
  },
  green: {
    bg: "from-emerald-500/10 to-teal-500/10",
    icon: "from-emerald-500 to-teal-500",
    border: "border-emerald-500/20",
  },
  orange: {
    bg: "from-orange-500/10 to-amber-500/10",
    icon: "from-orange-500 to-amber-500",
    border: "border-orange-500/20",
  },
  pink: {
    bg: "from-pink-500/10 to-rose-500/10",
    icon: "from-pink-500 to-rose-500",
    border: "border-pink-500/20",
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
    <div
      className={`relative overflow-hidden bg-[var(--card)] rounded-2xl p-5 border ${config.border} card-hover`}
    >
      {/* Background gradient */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${config.bg} opacity-50`}
      />

      <div className="relative">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium text-[var(--muted)]">{title}</p>
          {icon && (
            <div
              className={`w-10 h-10 rounded-xl bg-gradient-to-br ${config.icon} flex items-center justify-center shadow-lg`}
            >
              <span className="text-lg">{icon}</span>
            </div>
          )}
        </div>

        {/* Value */}
        <p className="text-3xl font-bold text-[var(--foreground)] tracking-tight">
          {typeof value === "number" ? value.toLocaleString() : value}
        </p>

        {/* Sub value with trend */}
        {subValue && (
          <div className="flex items-center gap-2 mt-2">
            {trend && trend !== "neutral" && (
              <span
                className={`inline-flex items-center justify-center w-5 h-5 rounded-full ${
                  trend === "up"
                    ? "bg-emerald-500/20 text-emerald-500"
                    : "bg-rose-500/20 text-rose-500"
                }`}
              >
                {trend === "up" ? (
                  <svg
                    className="w-3 h-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={3}
                      d="M5 15l7-7 7 7"
                    />
                  </svg>
                ) : (
                  <svg
                    className="w-3 h-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={3}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                )}
              </span>
            )}
            <p
              className={`text-sm font-medium ${
                trend === "up"
                  ? "text-emerald-500"
                  : trend === "down"
                  ? "text-rose-500"
                  : "text-[var(--muted)]"
              }`}
            >
              {subValue}
            </p>
          </div>
        )}
      </div>

      {/* Decorative element */}
      <div
        className={`absolute -right-4 -bottom-4 w-24 h-24 rounded-full bg-gradient-to-br ${config.icon} opacity-10 blur-2xl`}
      />
    </div>
  );
}
