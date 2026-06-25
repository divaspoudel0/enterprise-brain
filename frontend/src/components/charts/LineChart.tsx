"use client";
import { ResponsiveContainer, LineChart as ReLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

interface LineChartProps {
  data: Array<Record<string, unknown>>;
  xKey: string;
  lines: Array<{ key: string; color: string; label: string; dashed?: boolean }>;
  height?: number;
}

export default function LineChart({ data, xKey, lines, height = 300 }: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ReLineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey={xKey} tick={{ fontSize: 11 }} tickLine={false} />
        <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {lines.map(({ key, color, label, dashed }) => (
          <Line key={key} type="monotone" dataKey={key} name={label} stroke={color} strokeWidth={2}
            strokeDasharray={dashed ? "5 5" : undefined} dot={false} />
        ))}
      </ReLineChart>
    </ResponsiveContainer>
  );
}
