"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import AppLayout from "@/components/layout/AppLayout";
import { SeverityBadge, StatusBadge } from "@/components/ui/Badge";
import SHAPChart from "@/components/ui/SHAPChart";
import RiskGauge from "@/components/charts/RiskGauge";
import { PageLoader } from "@/components/ui/LoadingSpinner";
import { riskApi } from "@/lib/api";
import { AlertTriangle, RefreshCw, CheckCircle } from "lucide-react";
import { formatDate } from "@/lib/utils";
import toast from "react-hot-toast";
import type { RiskAlert, RiskSummary } from "@/types";

export default function RisksPage() {
  const qc = useQueryClient();
  const alerts = useQuery({ queryKey: ["risk-alerts"], queryFn: () => riskApi.listAlerts().then((r) => r.data as RiskAlert[]) });
  const summary = useQuery({ queryKey: ["risk-summary"], queryFn: () => riskApi.getSummary().then((r) => r.data as RiskSummary) });

  const scan = async () => {
    try {
      const res = await riskApi.scanRisks();
      toast.success(`Scan complete: ${res.data.alerts_created} new alerts`);
      qc.invalidateQueries({ queryKey: ["risk-alerts"] });
      qc.invalidateQueries({ queryKey: ["risk-summary"] });
    } catch { toast.error("Scan failed"); }
  };

  const acknowledge = async (id: number) => {
    try {
      await riskApi.acknowledgeAlert(id);
      toast.success("Alert acknowledged");
      qc.invalidateQueries({ queryKey: ["risk-alerts"] });
    } catch { toast.error("Failed"); }
  };

  return (
    <AppLayout>
      <div className="flex items-start justify-between page-header">
        <div>
          <h1 className="page-title flex items-center gap-2"><AlertTriangle className="h-7 w-7 text-orange-500" /> Risk Detection</h1>
          <p className="page-subtitle">Proactive risk monitoring with XAI explanations</p>
        </div>
        <button onClick={scan} className="btn-primary flex items-center gap-2">
          <RefreshCw className="h-4 w-4" /> Run Scan
        </button>
      </div>

      {summary.data && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-6">
          {(["critical", "high", "medium", "low"] as const).map((s) => (
            <div key={s} className="card text-center py-4">
              <p className="text-2xl font-bold text-gray-900">{summary.data![s]}</p>
              <SeverityBadge severity={s} />
            </div>
          ))}
          <div className="card text-center py-4">
            <p className="text-2xl font-bold text-orange-600">{summary.data.open_alerts}</p>
            <p className="text-xs text-gray-500 mt-1">Open Alerts</p>
          </div>
        </div>
      )}

      {alerts.isLoading ? <PageLoader /> : (
        <div className="space-y-4">
          {(alerts.data || []).map((alert: RiskAlert) => (
            <div key={alert.id} className="card">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <SeverityBadge severity={alert.severity} />
                    <StatusBadge status={alert.status} />
                    <span className="text-xs text-gray-400">{formatDate(alert.created_at)}</span>
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-1">{alert.title}</h3>
                  <p className="text-sm text-gray-600">{alert.description}</p>
                  <div className="mt-3 flex items-center gap-4 text-sm">
                    <span className="text-gray-500">Risk Score: <span className="font-bold text-gray-800">{(alert.risk_score * 100).toFixed(0)}</span></span>
                    <span className="text-gray-500">Category: <span className="font-medium capitalize">{alert.risk_category}</span></span>
                  </div>
                </div>
                <div className="flex-shrink-0 w-32">
                  <RiskGauge score={alert.risk_score} />
                </div>
              </div>
              {Object.keys(alert.shap_values).length > 0 && (
                <div className="mt-4 border-t pt-4">
                  <p className="text-xs font-medium text-gray-500 mb-2">Feature Impact (SHAP)</p>
                  <SHAPChart shap_values={alert.shap_values} />
                </div>
              )}
              {alert.status === "open" && (
                <div className="mt-4 flex gap-2">
                  <button onClick={() => acknowledge(alert.id)} className="btn-secondary flex items-center gap-1 text-sm">
                    <CheckCircle className="h-4 w-4" /> Acknowledge
                  </button>
                </div>
              )}
            </div>
          ))}
          {(!alerts.data || alerts.data.length === 0) && (
            <div className="card text-center py-12">
              <AlertTriangle className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No risk alerts. Click "Run Scan" to detect risks.</p>
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}
