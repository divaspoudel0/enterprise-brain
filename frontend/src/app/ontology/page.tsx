"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import AppLayout from "@/components/layout/AppLayout";
import { PageLoader } from "@/components/ui/LoadingSpinner";
import { ontologyApi } from "@/lib/api";
import { Network, Plus, GitBranch, Search } from "lucide-react";
import toast from "react-hot-toast";

interface GraphStats {
  nodes: Array<{ label: string; count: number }>;
  relationships: Array<{ type: string; count: number }>;
}

interface CypherResult {
  results: Array<Record<string, unknown>>;
  count: number;
}

export default function OntologyPage() {
  const qc = useQueryClient();
  const [cypherQuery, setCypherQuery] = useState(
    "MATCH (n) RETURN labels(n)[0] as type, n.name as name, n.id as id LIMIT 20"
  );
  const [cypherResult, setCypherResult] = useState<CypherResult | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);

  // Entity form
  const [entityLabel, setEntityLabel] = useState("Customer");
  const [entityId, setEntityId] = useState("");
  const [entityProps, setEntityProps] = useState('{"name": "", "industry": ""}');

  // Relationship form
  const [relFromLabel, setRelFromLabel] = useState("Customer");
  const [relFromId, setRelFromId] = useState("");
  const [relToLabel, setRelToLabel] = useState("Product");
  const [relToId, setRelToId] = useState("");
  const [relType, setRelType] = useState("PURCHASED");

  const stats = useQuery<GraphStats>({
    queryKey: ["ontology-stats"],
    queryFn: () => ontologyApi.getStats().then((r) => r.data),
  });

  const runCypher = async () => {
    if (!cypherQuery.trim()) return;
    setQueryLoading(true);
    try {
      const res = await ontologyApi.queryGraph(cypherQuery);
      setCypherResult(res.data);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Query failed";
      toast.error(msg);
    } finally {
      setQueryLoading(false);
    }
  };

  const addEntity = async () => {
    if (!entityId.trim()) return toast.error("Entity ID required");
    try {
      const props = JSON.parse(entityProps);
      await ontologyApi.queryGraph(
        `MERGE (n:${entityLabel} {id: $id}) SET n += $props RETURN n`,
        { id: entityId, props }
      );
      toast.success(`${entityLabel} created`);
      qc.invalidateQueries({ queryKey: ["ontology-stats"] });
    } catch {
      toast.error("Failed to create entity. Check JSON syntax.");
    }
  };

  const addRelationship = async () => {
    if (!relFromId.trim() || !relToId.trim()) return toast.error("Both IDs required");
    try {
      await ontologyApi.queryGraph(
        `MATCH (a {id: $from_id}), (b {id: $to_id}) MERGE (a)-[:${relType}]->(b)`,
        { from_id: relFromId, to_id: relToId }
      );
      toast.success(`${relType} relationship created`);
      qc.invalidateQueries({ queryKey: ["ontology-stats"] });
    } catch {
      toast.error("Failed to create relationship");
    }
  };

  const EXAMPLE_QUERIES = [
    { label: "All nodes (20)", cypher: "MATCH (n) RETURN labels(n)[0] as type, n.name as name, n.id as id LIMIT 20" },
    { label: "Customers", cypher: "MATCH (c:Customer) RETURN c.id as id, c.name as name, c.industry as industry, c.revenue as revenue" },
    { label: "Products", cypher: "MATCH (p:Product) RETURN p.id as id, p.name as name, p.category as category, p.price as price" },
    { label: "Purchases", cypher: "MATCH (c:Customer)-[r:PURCHASED]->(p:Product) RETURN c.name as customer, p.name as product, r.amount as amount" },
    { label: "Risk Exposure", cypher: "MATCH (rf:RiskFactor)-[r:AFFECTS]->(n) RETURN rf.name as risk, labels(n)[0]+': '+n.name as affected, r.severity as severity" },
    { label: "Suppliers → Assets", cypher: "MATCH (s:Supplier)-[r:PROVIDES]->(a:Asset) RETURN s.name as supplier, a.name as asset, r.sla as sla" },
  ];

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="page-title flex items-center gap-2">
          <Network className="h-7 w-7 text-brand-600" /> Knowledge Graph
        </h1>
        <p className="page-subtitle">Enterprise ontology — entities, relationships, and graph exploration</p>
      </div>

      {/* Stats Overview */}
      {stats.isLoading ? (
        <PageLoader />
      ) : stats.data ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <div className="h-8 w-8 rounded-lg bg-brand-100 flex items-center justify-center">
                <Network className="h-4 w-4 text-brand-600" />
              </div>
              <h2 className="font-semibold text-gray-900">Node Counts</h2>
            </div>
            {stats.data.nodes.length === 0 ? (
              <p className="text-sm text-gray-400">No nodes. Run seed script or add entities below.</p>
            ) : (
              <div className="space-y-2">
                {stats.data.nodes.map((n) => (
                  <div key={n.label} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 bg-gray-100 px-2 py-0.5 rounded">
                      {n.label || "Unknown"}
                    </span>
                    <span className="text-sm font-bold text-gray-900">{n.count}</span>
                  </div>
                ))}
                <div className="pt-2 border-t mt-2 flex justify-between text-sm">
                  <span className="text-gray-500 font-medium">Total nodes</span>
                  <span className="font-bold text-brand-600">
                    {stats.data.nodes.reduce((s, n) => s + n.count, 0)}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <div className="h-8 w-8 rounded-lg bg-green-100 flex items-center justify-center">
                <GitBranch className="h-4 w-4 text-green-600" />
              </div>
              <h2 className="font-semibold text-gray-900">Relationship Types</h2>
            </div>
            {stats.data.relationships.length === 0 ? (
              <p className="text-sm text-gray-400">No relationships yet.</p>
            ) : (
              <div className="space-y-2">
                {stats.data.relationships.map((r) => (
                  <div key={r.type} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 font-mono bg-blue-50 px-2 py-0.5 rounded">
                      {r.type}
                    </span>
                    <span className="text-sm font-bold text-gray-900">{r.count}</span>
                  </div>
                ))}
                <div className="pt-2 border-t mt-2 flex justify-between text-sm">
                  <span className="text-gray-500 font-medium">Total edges</span>
                  <span className="font-bold text-green-600">
                    {stats.data.relationships.reduce((s, r) => s + r.count, 0)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}

      {/* Cypher Query Explorer */}
      <div className="card mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Search className="h-5 w-5 text-brand-600" />
          <h2 className="font-semibold text-gray-900">Cypher Query Explorer</h2>
        </div>
        <div className="flex flex-wrap gap-2 mb-3">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q.label}
              onClick={() => setCypherQuery(q.cypher)}
              className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-full transition-colors"
            >
              {q.label}
            </button>
          ))}
        </div>
        <div className="flex gap-3">
          <textarea
            className="input flex-1 font-mono text-sm resize-none"
            rows={3}
            value={cypherQuery}
            onChange={(e) => setCypherQuery(e.target.value)}
            placeholder="MATCH (n) RETURN n LIMIT 10"
          />
          <button
            onClick={runCypher}
            className="btn-primary self-start flex items-center gap-2"
            disabled={queryLoading}
          >
            <Search className="h-4 w-4" /> {queryLoading ? "Running..." : "Execute"}
          </button>
        </div>
        {cypherResult && (
          <div className="mt-4">
            <p className="text-xs text-gray-500 mb-2 font-medium">{cypherResult.count} result(s)</p>
            {cypherResult.results.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm border rounded-lg overflow-hidden">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(cypherResult.results[0]).map((k) => (
                        <th key={k} className="text-left px-3 py-2 text-gray-600 font-medium border-b">{k}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {cypherResult.results.map((row, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        {Object.values(row).map((v, j) => (
                          <td key={j} className="px-3 py-2 text-gray-700 font-mono text-xs max-w-xs truncate">
                            {v === null || v === undefined ? (
                              <span className="text-gray-300 italic">null</span>
                            ) : typeof v === "object" ? (
                              JSON.stringify(v)
                            ) : (
                              String(v)
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-4">No results</p>
            )}
          </div>
        )}
      </div>

      {/* Add Entities / Relationships */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Plus className="h-5 w-5 text-brand-600" />
            <h2 className="font-semibold text-gray-900">Add Entity</h2>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">Label</label>
                <select className="input w-full" value={entityLabel} onChange={(e) => setEntityLabel(e.target.value)}>
                  {["Customer", "Product", "Supplier", "Asset", "Order", "RiskFactor"].map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">Entity ID</label>
                <input className="input w-full" value={entityId} onChange={(e) => setEntityId(e.target.value)} placeholder="CUST-005" />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 block mb-1">Properties (JSON)</label>
              <textarea
                className="input w-full font-mono text-xs resize-none"
                rows={3}
                value={entityProps}
                onChange={(e) => setEntityProps(e.target.value)}
              />
            </div>
            <button onClick={addEntity} className="btn-primary w-full">Add Entity</button>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <GitBranch className="h-5 w-5 text-green-600" />
            <h2 className="font-semibold text-gray-900">Add Relationship</h2>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">From Label</label>
                <select className="input w-full" value={relFromLabel} onChange={(e) => setRelFromLabel(e.target.value)}>
                  {["Customer", "Product", "Supplier", "Asset", "Order", "RiskFactor"].map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">From ID</label>
                <input className="input w-full" value={relFromId} onChange={(e) => setRelFromId(e.target.value)} placeholder="CUST-001" />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 block mb-1">Relationship Type</label>
              <select className="input w-full" value={relType} onChange={(e) => setRelType(e.target.value)}>
                {["PURCHASED", "SUPPLIES", "PROVIDES", "AFFECTS", "BELONGS_TO", "RELATED_TO"].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">To Label</label>
                <select className="input w-full" value={relToLabel} onChange={(e) => setRelToLabel(e.target.value)}>
                  {["Customer", "Product", "Supplier", "Asset", "Order", "RiskFactor"].map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 block mb-1">To ID</label>
                <input className="input w-full" value={relToId} onChange={(e) => setRelToId(e.target.value)} placeholder="PROD-001" />
              </div>
            </div>
            <button onClick={addRelationship} className="btn-primary w-full">Add Relationship</button>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
