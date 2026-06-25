"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import AppLayout from "@/components/layout/AppLayout";
import ConfidenceMeter from "@/components/ui/ConfidenceMeter";
import { StatusBadge } from "@/components/ui/Badge";
import { PageLoader } from "@/components/ui/LoadingSpinner";
import SHAPChart from "@/components/ui/SHAPChart";
import { decisionsApi } from "@/lib/api";
import { CheckSquare, Send, CheckCircle, XCircle, Clock } from "lucide-react";
import { formatDate } from "@/lib/utils";
import toast from "react-hot-toast";
import type { Decision } from "@/types";

export default function DecisionsPage() {
  const qc = useQueryClient();
  const [query, setQuery] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [latestAnalysis, setLatestAnalysis] = useState<Record<string, unknown> | null>(null);
  const [scenarioMode, setScenarioMode] = useState(false);
  const [scenarioName, setScenarioName] = useState("");
  const [approvalNotes, setApprovalNotes] = useState<Record<number, string>>({});

  const decisions = useQuery({ queryKey: ["decisions"], queryFn: () => decisionsApi.list().then((r) => r.data as Decision[]) });

  const runAnalysis = async () => {
    if (!query.trim()) return;
    setAnalyzing(true);
    try {
      const res = await decisionsApi.analyze(query);
      setLatestAnalysis(res.data);
      qc.invalidateQueries({ queryKey: ["decisions"] });
      toast.success("Analysis complete — review and approve");
    } catch { toast.error("Analysis failed"); } finally { setAnalyzing(false); }
  };

  const handleApproval = async (id: number, action: string) => {
    try {
      await decisionsApi.approve(id, action, approvalNotes[id]);
      toast.success(`Decision ${action}`);
      qc.invalidateQueries({ queryKey: ["decisions"] });
    } catch { toast.error("Action failed"); }
  };

  const simScenario = async () => {
    if (!scenarioName.trim()) return;
    try {
      const res = await decisionsApi.simulate({ scenario_name: scenarioName, description: query || "Scenario analysis", parameters: { revenue_trend: 0.5, payment_delay_days: 0.2, order_volume_change: 0.3, customer_churn_rate: 0.1, inventory_turnover: 0.4, debt_ratio: 0.2 } });
      setLatestAnalysis(res.data);
      toast.success("Scenario simulated");
    } catch { toast.error("Simulation failed"); }
  };

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title flex items-center gap-2"><CheckSquare className="h-7 w-7 text-brand-600" /> Decision Intelligence</h1>
        <p className="page-subtitle">AI-driven recommendations with human-in-the-loop approval</p>
      </div>

      <div className="card mb-6">
        <div className="flex gap-2 mb-4">
          <button onClick={() => setScenarioMode(false)} className={`px-3 py-1.5 rounded-lg text-sm font-medium ${!scenarioMode ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-600"}`}>Analysis Query</button>
          <button onClick={() => setScenarioMode(true)} className={`px-3 py-1.5 rounded-lg text-sm font-medium ${scenarioMode ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-600"}`}>Scenario Simulation</button>
        </div>
        {!scenarioMode ? (
          <div className="flex gap-3">
            <input className="input flex-1" placeholder="What strategic decision do you need support for?" value={query} onChange={(e) => setQuery(e.target.value)} />
            <button onClick={runAnalysis} className="btn-primary flex items-center gap-2" disabled={analyzing || !query.trim()}>
              <Send className="h-4 w-4" />{analyzing ? "Analyzing..." : "Analyze"}
            </button>
          </div>
        ) : (
          <div className="flex gap-3">
            <input className="input w-64" placeholder="Scenario name" value={scenarioName} onChange={(e) => setScenarioName(e.target.value)} />
            <input className="input flex-1" placeholder="Description" value={query} onChange={(e) => setQuery(e.target.value)} />
            <button onClick={simScenario} className="btn-primary">Simulate</button>
          </div>
        )}
      </div>

      {latestAnalysis && (
        <div className="card mb-6 border-brand-200 bg-brand-50">
          <h2 className="font-semibold text-gray-900 mb-3">Latest Analysis Result</h2>
          <p className="text-sm text-gray-700 mb-3">{(latestAnalysis.recommendation as string) || (latestAnalysis as any).recommendations?.join(" ")}</p>
          {(latestAnalysis.confidence as number) && <ConfidenceMeter score={latestAnalysis.confidence as number} />}
          {(latestAnalysis as any).explanation?.top_features && (
            <div className="mt-3">
              <p className="text-xs font-medium text-gray-500 mb-2">Key Drivers</p>
              <SHAPChart shap_values={Object.fromEntries(((latestAnalysis as any).explanation.top_features as any[]).map((f: any) => [f.name, f.impact]))} />
            </div>
          )}
        </div>
      )}

      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-4">Decision Queue ({(decisions.data || []).filter((d: Decision) => d.status === "pending_approval").length} pending)</h2>
        {decisions.isLoading ? <PageLoader /> : (
          <div className="space-y-4">
            {(decisions.data || []).map((d: Decision) => (
              <div key={d.id} className="border rounded-xl p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <StatusBadge status={d.status} />
                      <span className="text-xs text-gray-400 capitalize">{d.decision_type}</span>
                      <span className="text-xs text-gray-400">{formatDate(d.created_at)}</span>
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-2">{d.title}</h3>
                    <p className="text-sm text-gray-600 line-clamp-3">{d.recommendation}</p>
                    <div className="mt-3 max-w-xs"><ConfidenceMeter score={d.confidence_score} /></div>
                  </div>
                </div>
                {d.status === "pending_approval" && (
                  <div className="mt-4 pt-4 border-t flex items-center gap-3 flex-wrap">
                    <input className="input flex-1 text-sm" placeholder="Optional notes..." value={approvalNotes[d.id] || ""} onChange={(e) => setApprovalNotes((p) => ({ ...p, [d.id]: e.target.value }))} />
                    <button onClick={() => handleApproval(d.id, "approved")} className="flex items-center gap-1 px-3 py-2 rounded-lg bg-green-600 text-white text-sm hover:bg-green-700">
                      <CheckCircle className="h-4 w-4" /> Approve
                    </button>
                    <button onClick={() => handleApproval(d.id, "deferred")} className="flex items-center gap-1 px-3 py-2 rounded-lg bg-yellow-500 text-white text-sm hover:bg-yellow-600">
                      <Clock className="h-4 w-4" /> Defer
                    </button>
                    <button onClick={() => handleApproval(d.id, "rejected")} className="flex items-center gap-1 px-3 py-2 rounded-lg bg-red-600 text-white text-sm hover:bg-red-700">
                      <XCircle className="h-4 w-4" /> Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
            {(!decisions.data || decisions.data.length === 0) && (
              <p className="text-center text-sm text-gray-400 py-8">No decisions yet. Run an analysis above.</p>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
