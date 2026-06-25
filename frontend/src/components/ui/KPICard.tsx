import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn, formatNumber } from "@/lib/utils";
import type { KPI } from "@/types";

export default function KPICard({ kpi }: { kpi: KPI }) {
  const isUp = kpi.trend === "up";
  const isDown = kpi.trend === "down";
  return (
    <div className="card">
      <p className="text-sm font-medium text-gray-500">{kpi.name}</p>
      <div className="mt-2 flex items-baseline justify-between">
        <p className="text-3xl font-bold text-gray-900">
          {kpi.unit === "USD" ? "$" : ""}{formatNumber(kpi.value)}{kpi.unit === "ratio" ? "x" : ""}
        </p>
        <span className={cn("flex items-center gap-1 text-sm font-medium",
          isUp ? "text-green-600" : isDown ? "text-red-600" : "text-gray-500")}>
          {isUp ? <TrendingUp className="h-4 w-4" /> : isDown ? <TrendingDown className="h-4 w-4" /> : <Minus className="h-4 w-4" />}
          {Math.abs(kpi.change_pct).toFixed(1)}%
        </span>
      </div>
      <p className="text-xs text-gray-400 mt-1">{kpi.period}</p>
    </div>
  );
}
