"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import AppLayout from "@/components/layout/AppLayout";
import LineChart from "@/components/charts/LineChart";
import { PageLoader } from "@/components/ui/LoadingSpinner";
import { forecastApi } from "@/lib/api";
import { TrendingUp } from "lucide-react";
import toast from "react-hot-toast";
import type { ForecastResult } from "@/types";

const METRICS = ["revenue", "customers", "orders", "profit", "expenses"];
const HORIZONS = [7, 14, 30, 60, 90];

export default function ForecastingPage() {
  const [metric, setMetric] = useState("revenue");
  const [horizon, setHorizon] = useState(30);
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(false);

  const history = useQuery({ queryKey: ["forecast-history"], queryFn: () => forecastApi.getHistory().then((r) => r.data as ForecastResult[]) });

  const runForecast = async () => {
    setLoading(true);
    try {
      const res = await forecastApi.runForecast(metric, horizon);
      setResult(res.data);
      toast.success("Forecast completed");
    } catch {
      toast.error("Forecast failed");
    } finally {
      setLoading(false);
    }
  };

  const chartData = result ? [
    ...result.forecast_data.historical_dates.slice(-60).map((d, i) => ({
      date: d, historical: result.forecast_data.historical_values[result.forecast_data.historical_dates.length - 60 + i]
    })),
    ...result.forecast_data.dates.map((d, i) => ({
      date: d, forecast: result.forecast_data.values[i],
      lower: result.forecast_data.lower[i], upper: result.forecast_data.upper[i]
    })),
  ] : [];

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title flex items-center gap-2"><TrendingUp className="h-7 w-7 text-brand-600" /> Forecasting</h1>
        <p className="page-subtitle">AI-powered time-series forecasting with Prophet</p>
      </div>

      <div className="card mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Metric</label>
            <select className="input w-40" value={metric} onChange={(e) => setMetric(e.target.value)}>
              {METRICS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Horizon (days)</label>
            <select className="input w-32" value={horizon} onChange={(e) => setHorizon(Number(e.target.value))}>
              {HORIZONS.map((h) => <option key={h} value={h}>{h} days</option>)}
            </select>
          </div>
          <button onClick={runForecast} className="btn-primary mt-5" disabled={loading}>
            {loading ? "Running..." : "Run Forecast"}
          </button>
        </div>
      </div>

      {loading && <PageLoader />}
      {result && !loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <div className="card"><p className="text-xs text-gray-500">RMSE</p><p className="text-xl font-bold">{result.accuracy_metrics.rmse?.toFixed(2) ?? "N/A"}</p></div>
            <div className="card"><p className="text-xs text-gray-500">MAPE (%)</p><p className="text-xl font-bold">{result.accuracy_metrics.mape?.toFixed(2) ?? "N/A"}%</p></div>
            <div className="card"><p className="text-xs text-gray-500">Model</p><p className="text-xl font-bold capitalize">{result.model_type}</p></div>
          </div>

          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-4 capitalize">{metric} Forecast — {horizon}-Day Horizon</h2>
            <LineChart data={chartData} xKey="date"
              lines={[
                { key: "historical", color: "#6b7280", label: "Historical" },
                { key: "forecast", color: "#3b82f6", label: "Forecast" },
                { key: "upper", color: "#93c5fd", label: "Upper Bound", dashed: true },
                { key: "lower", color: "#93c5fd", label: "Lower Bound", dashed: true },
              ]} height={350} />
          </div>

          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-2">Explanation</h2>
            <p className="text-sm text-gray-700">{result.explanation}</p>
          </div>
        </div>
      )}

      <div className="card mt-8">
        <h2 className="font-semibold text-gray-900 mb-4">Recent Forecasts</h2>
        {history.isLoading ? <PageLoader /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b"><th className="text-left py-2 pr-4 text-gray-500">Metric</th><th className="text-left py-2 pr-4 text-gray-500">Model</th><th className="text-left py-2 pr-4 text-gray-500">Horizon</th><th className="text-left py-2 pr-4 text-gray-500">RMSE</th><th className="text-left py-2 text-gray-500">MAPE</th></tr></thead>
              <tbody className="divide-y divide-gray-50">
                {(history.data || []).map((r: ForecastResult) => (
                  <tr key={r.id}><td className="py-2 pr-4 capitalize">{r.metric_name}</td><td className="py-2 pr-4 capitalize">{r.model_type}</td><td className="py-2 pr-4">{r.horizon_days}d</td><td className="py-2 pr-4">{r.accuracy_metrics.rmse?.toFixed(2)}</td><td className="py-2">{r.accuracy_metrics.mape?.toFixed(2)}%</td></tr>
                ))}
              </tbody>
            </table>
            {(!history.data || history.data.length === 0) && <p className="text-center text-sm text-gray-400 py-6">No forecasts yet.</p>}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
