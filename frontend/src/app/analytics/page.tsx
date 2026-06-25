"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import AppLayout from "@/components/layout/AppLayout";
import LineChart from "@/components/charts/LineChart";
import { PageLoader } from "@/components/ui/LoadingSpinner";
import { analyticsApi } from "@/lib/api";
import { BarChart2, AlertCircle } from "lucide-react";
import type { AnalyticsData } from "@/types";

const METRICS = ["revenue", "customers", "orders", "inventory", "expenses", "profit"];

export default function AnalyticsPage() {
  const [metric, setMetric] = useState("revenue");
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["analytics", metric],
    queryFn: () => analyticsApi.runAnalytics(metric).then((r) => r.data as AnalyticsData),
  });

  const chartData = data?.data?.slice(-60).map((d) => ({ date: d.date, value: d.value })) || [];

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title flex items-center gap-2"><BarChart2 className="h-7 w-7 text-brand-600" /> Analytics</h1>
        <p className="page-subtitle">Explore enterprise metrics, trends, and anomalies</p>
      </div>

      <div className="card mb-6">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-sm font-medium text-gray-700">Metric:</span>
          {METRICS.map((m) => (
            <button key={m} onClick={() => setMetric(m)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors capitalize ${metric === m ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
              {m}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? <PageLoader /> : data ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: "Mean", value: data.summary.mean.toLocaleString(undefined, { maximumFractionDigits: 0 }) },
              { label: "Max", value: data.summary.max.toLocaleString(undefined, { maximumFractionDigits: 0 }) },
              { label: "Min", value: data.summary.min.toLocaleString(undefined, { maximumFractionDigits: 0 }) },
              { label: "Std Dev", value: data.summary.std.toLocaleString(undefined, { maximumFractionDigits: 0 }) },
            ].map(({ label, value }) => (
              <div key={label} className="card py-4">
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{value}</p>
              </div>
            ))}
          </div>

          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-4 capitalize">{metric} Trend (Last 60 Days)</h2>
            <LineChart data={chartData} xKey="date"
              lines={[{ key: "value", color: "#3b82f6", label: metric }]} height={320} />
          </div>

          {data.anomalies.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <AlertCircle className="h-5 w-5 text-orange-500" />
                <h2 className="font-semibold text-gray-900">Anomalies Detected ({data.anomalies.length})</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b"><th className="text-left py-2 pr-4 text-gray-500">Date</th><th className="text-left py-2 pr-4 text-gray-500">Value</th><th className="text-left py-2 text-gray-500">Anomaly Score</th></tr></thead>
                  <tbody className="divide-y divide-gray-50">
                    {data.anomalies.map((a, i) => (
                      <tr key={i}><td className="py-2 pr-4">{a.date}</td><td className="py-2 pr-4 font-medium">{a.value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td><td className="py-2">{a.score.toFixed(4)}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-3">AI Insights</h2>
            <ul className="space-y-2">
              {data.insights.map((ins, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="h-5 w-5 rounded-full bg-brand-100 text-brand-700 text-xs flex items-center justify-center flex-shrink-0 mt-0.5">{i + 1}</span>
                  {ins}
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </AppLayout>
  );
}
