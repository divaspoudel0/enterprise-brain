import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info";
  className?: string;
}

const variants = {
  default: "bg-gray-100 text-gray-800",
  success: "bg-green-100 text-green-800",
  warning: "bg-yellow-100 text-yellow-800",
  danger: "bg-red-100 text-red-800",
  info: "bg-blue-100 text-blue-800",
};

export default function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span className={cn("badge", variants[variant], className)}>{children}</span>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, BadgeProps["variant"]> = { critical: "danger", high: "warning", medium: "info", low: "success" };
  return <Badge variant={map[severity] ?? "default"}>{severity}</Badge>;
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeProps["variant"]> = {
    active: "success",
    approved: "success",
    resolved: "success",
    pending_approval: "warning",
    pending: "warning",
    acknowledged: "warning",
    deferred: "info",
    rejected: "danger",
    error: "danger",
    open: "danger",
  };
  return <Badge variant={map[status] ?? "default"}>{status.replace(/_/g, " ")}</Badge>;
}
