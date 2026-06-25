import axios, { AxiosInstance } from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      const refresh = Cookies.get("refresh_token");
      if (refresh) {
        try {
          const res = await axios.post(`${API_URL}/api/v1/auth/refresh`, null, { params: { refresh_token: refresh } });
          Cookies.set("access_token", res.data.access_token, { secure: true, sameSite: "strict" });
          err.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(err.config);
        } catch {
          Cookies.remove("access_token");
          Cookies.remove("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(err);
  }
);

export const authApi = {
  login: (email: string, password: string) => api.post("/auth/login", { email, password }),
  register: (data: { email: string; full_name: string; password: string; role?: string }) => api.post("/auth/register", data),
  me: () => api.get("/auth/me"),
};

export const dataApi = {
  listSources: () => api.get("/data/sources"),
  createSource: (data: { name: string; source_type: string; connection_config?: object }) => api.post("/data/sources", data),
  getSource: (id: number) => api.get(`/data/sources/${id}`),
  uploadFile: (sourceId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post(`/data/sources/${sourceId}/upload`, form, { headers: { "Content-Type": "multipart/form-data" } });
  },
  query: (query: string, sourceIds?: number[]) => api.post("/data/query", { query, data_source_ids: sourceIds }),
};

export const analyticsApi = {
  getKPIs: () => api.get("/analytics/kpis"),
  runAnalytics: (metric: string, filters?: object) => api.post("/analytics/query", { metric, ...filters }),
};

export const forecastApi = {
  runForecast: (metric: string, horizonDays?: number) => api.post("/forecast/run", { metric, horizon_days: horizonDays || 30 }),
  getHistory: () => api.get("/forecast/history"),
};

export const riskApi = {
  listAlerts: () => api.get("/risk/alerts"),
  getSummary: () => api.get("/risk/summary"),
  scanRisks: () => api.post("/risk/scan"),
  acknowledgeAlert: (id: number) => api.patch(`/risk/alerts/${id}/acknowledge`),
};

export const decisionsApi = {
  analyze: (query: string) => api.post("/decisions/analyze", null, { params: { query } }),
  list: () => api.get("/decisions/"),
  get: (id: number) => api.get(`/decisions/${id}`),
  approve: (id: number, action: string, notes?: string) => api.post(`/decisions/${id}/approve`, { action, notes }),
  simulate: (data: { scenario_name: string; parameters: object; description: string }) => api.post("/decisions/scenario/simulate", data),
};

export const ontologyApi = {
  getStats: () => api.get("/ontology/stats"),
  queryGraph: (cypher: string, params?: object) => api.post("/ontology/query", { cypher, params }),
  getNeighborhood: (entityId: string, depth?: number) => api.get(`/ontology/entities/${entityId}/neighborhood`, { params: { depth } }),
};

export const auditApi = {
  getLogs: (params?: { event_type?: string; entity_type?: string; limit?: number; offset?: number }) => api.get("/audit/logs", { params }),
  getStats: () => api.get("/audit/stats"),
};
