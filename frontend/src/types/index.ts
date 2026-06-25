export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface DataSource {
  id: number;
  name: string;
  source_type: string;
  status: string;
  last_ingested_at: string | null;
  record_count: number;
  error_message: string | null;
  created_at: string;
}

export interface KPI {
  name: string;
  value: number;
  unit: string;
  change_pct: number;
  trend: "up" | "down" | "stable";
  period: string;
}

export interface ForecastResult {
  id: number;
  metric_name: string;
  model_type: string;
  horizon_days: number;
  forecast_data: {
    dates: string[];
    values: number[];
    lower: number[];
    upper: number[];
    historical_dates: string[];
    historical_values: number[];
    rmse: number;
    mape: number;
  };
  accuracy_metrics: { rmse?: number; mape?: number };
  feature_importance: Record<string, number>;
  explanation: string;
  created_at: string;
}

export interface RiskAlert {
  id: number;
  title: string;
  description: string;
  severity: "low" | "medium" | "high" | "critical";
  risk_score: number;
  risk_category: string;
  status: string;
  affected_entities: Record<string, unknown>;
  evidence: Record<string, unknown>;
  shap_values: Record<string, number>;
  created_at: string;
}

export interface RiskSummary {
  total_alerts: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  open_alerts: number;
  top_risks: Array<{ id: number; title: string; severity: string; risk_score: number }>;
}

export interface Decision {
  id: number;
  title: string;
  description: string;
  decision_type: string;
  status: string;
  recommendation: string;
  confidence_score: number;
  evidence: Record<string, unknown>;
  explanation: Record<string, unknown>;
  source_data: Record<string, unknown>;
  created_by_agent: string;
  created_at: string;
  resolved_at: string | null;
}

export interface AuditLog {
  id: number;
  event_type: string;
  entity_type: string;
  entity_id: number | null;
  actor_id: number | null;
  actor_type: string;
  description: string;
  metadata: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export interface AnalyticsData {
  metric: string;
  data: Array<{ date: string; value: number }>;
  summary: { mean: number; max: number; min: number; std: number };
  insights: string[];
  anomalies: Array<{ date: string; value: number; score: number }>;
}

export interface GraphNode {
  n?: { id?: string; name?: string; [key: string]: unknown };
  [key: string]: unknown;
}

export interface QueryResponse {
  answer: string;
  sources: Array<{ score: number; source_name: string; text: string }>;
  confidence: number;
  graph_context: GraphNode[] | null;
  agent_trace: Array<{ step: string; [key: string]: unknown }>;
}

export interface ScenarioResponse {
  scenario_name: string;
  description: string;
  simulated_outcomes: Record<string, unknown>;
  risk_delta: number;
  confidence: number;
  recommendations: string[];
}
