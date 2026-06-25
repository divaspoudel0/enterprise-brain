"use client";
import { useState } from "react";
import AppLayout from "@/components/layout/AppLayout";
import ConfidenceMeter from "@/components/ui/ConfidenceMeter";
import { dataApi } from "@/lib/api";
import { Search, Send, Network } from "lucide-react";
import toast from "react-hot-toast";
import type { QueryResponse } from "@/types";

const EXAMPLE_QUERIES = [
  "What are the top revenue drivers this quarter?",
  "Which customers have the highest churn risk?",
  "Show me sales performance trends for the last 90 days",
  "What are the main operational bottlenecks?",
];

export default function QueryPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await dataApi.query(query);
      setResult(res.data);
    } catch {
      toast.error("Query failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title flex items-center gap-2"><Search className="h-7 w-7 text-brand-600" /> Natural Language Query</h1>
        <p className="page-subtitle">Ask questions about your enterprise data in plain English</p>
      </div>

      <div className="card mb-6">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            className="input flex-1 text-base"
            placeholder="Ask anything about your enterprise data..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="btn-primary flex items-center gap-2" disabled={loading || !query.trim()}>
            <Send className="h-4 w-4" /> {loading ? "Thinking..." : "Ask"}
          </button>
        </form>
        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((q) => (
            <button key={q} onClick={() => setQuery(q)} className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-full transition-colors">
              {q}
            </button>
          ))}
        </div>
      </div>

      {result && (
        <div className="space-y-4">
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-3">Answer</h2>
            <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">{result.answer}</div>
            <div className="mt-4">
              <ConfidenceMeter score={result.confidence} />
            </div>
          </div>

          {result.sources.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-gray-900 mb-3">Evidence Sources ({result.sources.length})</h2>
              <div className="space-y-3">
                {result.sources.map((s, i) => (
                  <div key={i} className="border rounded-lg p-3 bg-gray-50">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-brand-600">{s.source_name || "Unknown source"}</span>
                      <span className="text-xs text-gray-400">Relevance: {(s.score * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-3">{s.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.graph_context && result.graph_context.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <Network className="h-5 w-5 text-brand-600" />
                <h2 className="font-semibold text-gray-900">Knowledge Graph Matches ({result.graph_context.length})</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {result.graph_context.slice(0, 6).map((node, i) => {
                  const n = node.n as Record<string, unknown> | undefined;
                  const props = n ? Object.entries(n).filter(([k]) => k !== "elementId" && k !== "identity") : [];
                  return (
                    <div key={i} className="border rounded-lg p-3 bg-gray-50 text-xs">
                      {props.map(([k, v]) => (
                        <div key={k} className="flex gap-2">
                          <span className="text-gray-400 font-medium w-20 shrink-0">{k}:</span>
                          <span className="text-gray-700 truncate">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {result.agent_trace.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-gray-900 mb-3">Agent Trace</h2>
              <div className="space-y-2">
                {result.agent_trace.map((step, i) => (
                  <div key={i} className="flex items-center gap-3 text-sm">
                    <span className="h-6 w-6 rounded-full bg-brand-100 text-brand-700 text-xs flex items-center justify-center font-bold">{i + 1}</span>
                    <span className="font-medium text-gray-700 capitalize">{step.step?.replace(/_/g, " ")}</span>
                    <span className="text-gray-400 text-xs">{JSON.stringify(Object.fromEntries(Object.entries(step).filter(([k]) => k !== "step")))}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}
