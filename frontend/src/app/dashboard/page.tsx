"use client";
import { useQuery } from "@tanstack/react-query";
import AppLayout from "@/components/layout/AppLayout";
import KPICard from "@/components/ui/KPICard";
import { PageLoader } from "@/components/ui/LoadingSpinner";
import { SeverityBadge, StatusBadge } from "@/components/ui/Badge";
import { analyticsApi, riskApi, decisionsApi, auditApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Brain, Activity, AlertTriangle, CheckSquare } from "lucide-react";
import type { RiskAlert, Decision, AuditLog } from "@/types";

export default function DashboardPage() {
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: () => analyticsApi.getKPIs().then((r) => r.data) });
  const riskSummary = useQuery({ queryKey: ["risk-summary"], queryFn: () => riskApi.getSummary().then((r) => r.data) });
  const decisions = useQuery({ queryKey: ["decisions"], queryFn: () => decisionsApi.list().then((r) => r.data) });
  const auditStats = useQuery({ queryKey: ["audit-stats"], queryFn: () => auditApi.getStats().then((r) => r.data) });

  if (kpis.isLoading) return <AppLayout><PageLoader /></AppLayout>;

  const pendingDecisions = (decisions.data as Decision[] || []).filter((d) => d.status === "pending_approval");

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title flex items-center gap-2">
          <Brain className="h-7 w-7 text-brand-600" /> Dashboard
        </h1>
        <p className="page-subtitle">Enterprise-wide decision intelligence overview</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
        {(kpis.data || []).map((kpi: import("@/types").KPI) => <KPICard key={kpi.name} kpi={kpi} />)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            <h2 className="font-semibold text-gray-900">Risk Overview</h2>
          </div>
          {riskSummary.data ? (
            <div className="space-y-2">
              {(["critical", "high", "medium", "low"] as const).map((s) => (
                <div key={s} className="flex items-center justify-between">
                  <SeverityBadge severity={s} />
                  <span className="font-bold text-gray-700">{riskSummary.data[s]}</span>
                </div>
              ))}
              <div className="pt-2 border-t mt-2">
                <p className="text-sm text-gray-500">Open Alerts: <span className="font-bold text-gray-700">{riskSummary.data.open_alerts}</span></p>
              </div>
            </div>
          ) : <p className="text-sm text-gray-400">No data</p>}
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <CheckSquare className="h-5 w-5 text-brand-600" />
            <h2 className="font-semibold text-gray-900">Pending Approvals</h2>
          </div>
          <div className="space-y-2">
            {pendingDecisions.slice(0, 5).map((d) => (
              <div key={d.id} className="text-sm border rounded-lg p-2">
                <p className="font-medium text-gray-800 truncate">{d.title}</p>
                <p className="text-xs text-gray-500 mt-0.5">Confidence: {Math.round(d.confidence_score * 100)}%</p>
              </div>
            ))}
            {pendingDecisions.length === 0 && <p className="text-sm text-gray-400">No pending approvals</p>}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="h-5 w-5 text-green-500" />
            <h2 className="font-semibold text-gray-900">System Activity</h2>
          </div>
          {auditStats.data ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Total Events</span><span className="font-bold">{auditStats.data.total_events}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Decisions Approved</span><span className="font-bold text-green-600">{auditStats.data.decisions_approved}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Decisions Rejected</span><span className="font-bold text-red-600">{auditStats.data.decisions_rejected}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Risks Detected</span><span className="font-bold text-orange-600">{auditStats.data.risks_detected}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Queries Executed</span><span className="font-bold">{auditStats.data.queries_executed}</span></div>
            </div>
          ) : <p className="text-sm text-gray-400">No data</p>}
        </div>
      </div>

      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-4">Recent Decisions</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 pr-4 text-gray-500 font-medium">Title</th>
                <th className="text-left py-2 pr-4 text-gray-500 font-medium">Type</th>
                <th className="text-left py-2 pr-4 text-gray-500 font-medium">Status</th>
                <th className="text-left py-2 pr-4 text-gray-500 font-medium">Confidence</th>
                <th className="text-left py-2 text-gray-500 font-medium">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(decisions.data as Decision[] || []).slice(0, 10).map((d) => (
                <tr key={d.id} className="hover:bg-gray-50">
                  <td className="py-2 pr-4 font-medium text-gray-800 max-w-xs truncate">{d.title}</td>
                  <td className="py-2 pr-4 text-gray-500 capitalize">{d.decision_type}</td>
                  <td className="py-2 pr-4"><StatusBadge status={d.status} /></td>
                  <td className="py-2 pr-4">{Math.round(d.confidence_score * 100)}%</td>
                  <td className="py-2 text-gray-500">{formatDate(d.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {(!decisions.data || decisions.data.length === 0) && (
            <p className="text-center text-sm text-gray-400 py-6">No decisions yet. Use the Decisions page to run analyses.</p>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
