"use client";
import { useState, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import AppLayout from "@/components/layout/AppLayout";
import { StatusBadge } from "@/components/ui/Badge";
import { PageLoader } from "@/components/ui/LoadingSpinner";
import { dataApi } from "@/lib/api";
import { Database, Upload, Plus, File } from "lucide-react";
import { formatDate } from "@/lib/utils";
import toast from "react-hot-toast";
import type { DataSource } from "@/types";

export default function DataSourcesPage() {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedSource, setSelectedSource] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [type, setType] = useState("csv");
  const [uploading, setUploading] = useState(false);

  const sources = useQuery({ queryKey: ["data-sources"], queryFn: () => dataApi.listSources().then((r) => r.data as DataSource[]) });

  const createSource = async () => {
    if (!name.trim()) return;
    try {
      await dataApi.createSource({ name, source_type: type });
      toast.success("Data source created");
      setShowCreate(false); setName(""); setType("csv");
      qc.invalidateQueries({ queryKey: ["data-sources"] });
    } catch { toast.error("Failed to create source"); }
  };

  const handleUpload = async (file: File) => {
    if (!selectedSource) return;
    setUploading(true);
    try {
      const res = await dataApi.uploadFile(selectedSource, file);
      toast.success(res.data.message);
      qc.invalidateQueries({ queryKey: ["data-sources"] });
    } catch { toast.error("Upload failed"); } finally { setUploading(false); }
  };

  return (
    <AppLayout>
      <div className="flex items-start justify-between page-header">
        <div>
          <h1 className="page-title flex items-center gap-2"><Database className="h-7 w-7 text-brand-600" /> Data Sources</h1>
          <p className="page-subtitle">Connect and manage enterprise data integrations</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="h-4 w-4" /> Add Source
        </button>
      </div>

      {showCreate && (
        <div className="card mb-6 border-brand-200">
          <h2 className="font-semibold text-gray-900 mb-4">New Data Source</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Name</label>
              <input className="input" placeholder="e.g. Sales Database" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Type</label>
              <select className="input" value={type} onChange={(e) => setType(e.target.value)}>
                <option value="csv">CSV</option><option value="excel">Excel</option>
                <option value="pdf">PDF</option><option value="postgresql">PostgreSQL</option><option value="api">External API</option>
              </select>
            </div>
            <div className="flex items-end gap-2">
              <button onClick={createSource} className="btn-primary">Create</button>
              <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}

      <input ref={fileRef} type="file" className="hidden" accept=".csv,.xlsx,.xls,.pdf"
        onChange={(e) => { if (e.target.files?.[0]) handleUpload(e.target.files[0]); }} />

      {sources.isLoading ? <PageLoader /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {(sources.data || []).map((s: DataSource) => (
            <div key={s.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-brand-600" />
                  <h3 className="font-semibold text-gray-900">{s.name}</h3>
                </div>
                <StatusBadge status={s.status} />
              </div>
              <div className="space-y-1 text-sm text-gray-600 mb-4">
                <p>Type: <span className="font-medium uppercase">{s.source_type}</span></p>
                <p>Records: <span className="font-medium">{s.record_count.toLocaleString()}</span></p>
                {s.last_ingested_at && <p>Last synced: {formatDate(s.last_ingested_at)}</p>}
                {s.error_message && <p className="text-red-500 text-xs">{s.error_message}</p>}
                <p className="text-gray-400 text-xs">Created {formatDate(s.created_at)}</p>
              </div>
              {["csv", "excel", "pdf"].includes(s.source_type) && (
                <button
                  onClick={() => { setSelectedSource(s.id); fileRef.current?.click(); }}
                  disabled={uploading}
                  className="btn-secondary text-sm flex items-center gap-2 w-full justify-center"
                >
                  <Upload className="h-4 w-4" />{uploading && selectedSource === s.id ? "Uploading..." : "Upload File"}
                </button>
              )}
            </div>
          ))}
          {(!sources.data || sources.data.length === 0) && (
            <div className="col-span-3 card text-center py-16">
              <Database className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 mb-3">No data sources yet</p>
              <button onClick={() => setShowCreate(true)} className="btn-primary">Add First Source</button>
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}
