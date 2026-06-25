"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, LayoutDashboard, BarChart2, TrendingUp, AlertTriangle, CheckSquare, FileText, Database, Search, LogOut, Network } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/query", label: "NL Query", icon: Search },
  { href: "/analytics", label: "Analytics", icon: BarChart2 },
  { href: "/forecasting", label: "Forecasting", icon: TrendingUp },
  { href: "/risks", label: "Risk Detection", icon: AlertTriangle },
  { href: "/decisions", label: "Decisions", icon: CheckSquare },
  { href: "/ontology", label: "Knowledge Graph", icon: Network },
  { href: "/audit", label: "Audit Trail", icon: FileText },
  { href: "/data-sources", label: "Data Sources", icon: Database },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-screen sticky top-0">
      <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-700">
        <Brain className="h-7 w-7 text-brand-400" />
        <div>
          <p className="font-bold text-sm">Enterprise Brain</p>
          <p className="text-xs text-gray-400">Decision Intelligence</p>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              pathname === href || pathname.startsWith(href + "/")
                ? "bg-brand-600 text-white"
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            )}
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            {label}
          </Link>
        ))}
      </nav>
      {user && (
        <div className="px-3 py-4 border-t border-gray-700">
          <div className="flex items-center gap-3 px-3 py-2 mb-1">
            <div className="h-8 w-8 rounded-full bg-brand-600 flex items-center justify-center text-xs font-bold">
              {user.full_name.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.full_name}</p>
              <p className="text-xs text-gray-400 capitalize">{user.role}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white w-full transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}
