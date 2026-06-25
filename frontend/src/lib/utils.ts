import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number, decimals = 0): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toFixed(decimals);
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function severityColor(severity: string): string {
  return { critical: "red", high: "orange", medium: "yellow", low: "green" }[severity] ?? "gray";
}

export function severityBadgeClass(severity: string): string {
  const map: Record<string, string> = {
    critical: "bg-red-100 text-red-800",
    high: "bg-orange-100 text-orange-800",
    medium: "bg-yellow-100 text-yellow-800",
    low: "bg-green-100 text-green-800",
  };
  return map[severity] ?? "bg-gray-100 text-gray-800";
}

export function confidenceLabel(score: number): string {
  if (score >= 0.85) return "High";
  if (score >= 0.65) return "Medium";
  return "Low";
}

export function confidenceBadgeClass(score: number): string {
  if (score >= 0.85) return "bg-green-100 text-green-800";
  if (score >= 0.65) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}
