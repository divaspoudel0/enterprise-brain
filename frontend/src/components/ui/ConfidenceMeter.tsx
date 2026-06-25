import { cn, confidenceLabel, confidenceBadgeClass } from "@/lib/utils";

export default function ConfidenceMeter({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.85 ? "bg-green-500" : score >= 0.65 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-500">Confidence</span>
        <span className={cn("badge text-xs", confidenceBadgeClass(score))}>{confidenceLabel(score)} ({pct}%)</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
