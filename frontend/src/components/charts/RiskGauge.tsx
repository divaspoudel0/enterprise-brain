"use client";
import { RadialBarChart, RadialBar, ResponsiveContainer } from "recharts";
import { cn } from "@/lib/utils";

export default function RiskGauge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score > 0.7 ? "#ef4444" : score > 0.5 ? "#f97316" : score > 0.3 ? "#eab308" : "#22c55e";
  const label = score > 0.7 ? "Critical" : score > 0.5 ? "High" : score > 0.3 ? "Medium" : "Low";
  const data = [{ value: pct, fill: color }, { value: 100 - pct, fill: "#f3f4f6" }];
  return (
    <div className="flex flex-col items-center">
      <ResponsiveContainer width={120} height={120}>
        <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="80%" startAngle={90} endAngle={-270} data={data}>
          <RadialBar dataKey="value" cornerRadius={4} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="text-center -mt-2">
        <p className="text-2xl font-bold" style={{ color }}>{pct}</p>
        <p className="text-xs font-medium" style={{ color }}>{label} Risk</p>
      </div>
    </div>
  );
}
