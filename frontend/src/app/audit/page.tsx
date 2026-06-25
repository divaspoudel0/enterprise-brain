"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import AppLayout from "@/components/layout/AppLayout";
import { PageLoader } from "@/components/ui/LoadingSpinner";
import { auditApi } from "@/lib/api";
import { FileText, Filter } from "lucide-react";
import { formatDate } from "@/lib/utils";
import type { AuditLog } from "@/types";

const EVENT_TYPES = ["", "decision.created", "decision.approved", "decision.rejected", "risk.detected", "query.executed", "data.ingested", "forecast.created"];

export default function AuditPage() {
  const [eventType, setEventType] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const logs = useQuery({
    queryKey: ["audit-logs", eventType, page],
    queryFn: () => auditApi.getLogs({ event_type: eventType || undefined, limit, offset: page * limit }).then((r) => r.data as AuditLog[]),
  });
  const stats = useQuery({ queryKey: ["audit-stats"], queryFn: () => auditApi.getStats().then((r) => r.data) });

  const actorIcon = (type: string) => type === "agent" ? "🤖" : type === "system" ? "⚙️" : "👤";

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title flex items-center gap-2"><FileText className="h-7 w-7 text-brand-600" /> Audit Trail</h1>
        <p className="page-subtitle">Complete decision traceability and governance log</p>
      </div>

      {stats.data && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-6">
          <div className="card"><p className="text-xs text-gray-500">Total Events</p><p className="text-2xl font-bold">{stats.data.total_events}</p></div>
          <div className="card"><p className="text-xs text-gray-500">Approved</p><p className="text-2xl font-bold text-green-600">{stats.data.decisions_approved}</p></div>
          <div className="card"><p className="text-xs text-gray-500">Rejected</p><p className="text-2xl font-bold text-red-600">{stats.data.decisions_rejected}</p></div>
          <div className="card"><p className="text-xs text-gray-500">Risks Found</p><p className="text-2xl font-bold text-orange-600">{stats.data.risks_detected}</p></div>
          <div className="card"><p className="text-xs text-gray-500">Queries</p><p className="text-2xl font-bold">{stats.data.queries_executed}</p></div>
        </div>
      )}

      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Filter className="h-4 w-4 text-gray-500" />
          <select className="input w-56 text-sm" value={eventType} onChange={(e) => { setEventType(e.target.value); setPage(0); }}>
            {EVENT_TYPES.map((t) => <option key={t} value={t}>{t || "All events"}</option>)}
          </select>
        </div>
        {logs.isLoading ? <PageLoader /> : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="border-b">
                  <th className="text-left py-2 pr-3 text-gray-500">Time</th>
                  <th className="text-left py-2 pr-3 text-gray-500">Event</th>
                  <th className="text-left py-2 pr-3 text-gray-500">Entity</th>
                  <th className="text-left py-2 pr-3 text-gray-500">Actor</th>
                  <th className="text-left py-2 text-gray-500">Description</th>
                </tr></thead>
                <tbody className="divide-y divide-gray-50">
                  {(logs.data || []).map((log: AuditLog) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="py-2 pr-3 text-gray-400 whitespace-nowrap">{formatDate(log.created_at)}</td>
                      <td className="py-2 pr-3"><span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">{log.event_type}</span></td>
                      <td className="py-2 pr-3 text-gray-600">{log.entity_type}{log.entity_id ? ` #${log.entity_id}` : ""}</td>
                      <td className="py-2 pr-3"><span title={log.actor_type}>{actorIcon(log.actor_type)} {log.actor_id ? `#${log.actor_id}` : ""}</span></td>
                      <td className="py-2 text-gray-700 max-w-sm truncate">{log.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(!logs.data || logs.data.length === 0) && <p className="text-center text-sm text-gray-400 py-8">No audit logs found.</p>}
            </div>
            <div className="flex items-center justify-between mt-4 text-sm">
              <span className="text-gray-500">Page {page + 1}</span>
              <div className="flex gap-2">
                <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0} className="btn-secondary py-1 px-3 text-xs">Previous</button>
                <button onClick={() => setPage((p) => p + 1)} disabled={(logs.data || []).length < limit} className="btn-secondary py-1 px-3 text-xs">Next</button>
              </div>
            </div>
          </>
        )}
      </div>
    </AppLayout>
  );
}
