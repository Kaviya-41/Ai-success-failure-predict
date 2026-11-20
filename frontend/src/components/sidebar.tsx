"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import {
  LayoutDashboard,
  FolderKanban,
  BrainCircuit,
  Database,
  FileBarChart,
  GitBranch,
  ShieldAlert,
  LogOut,
  ChevronLeft,
  ChevronRight,
  User,
  Settings,
  Sparkles,
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  const isAuthPage = pathname === "/" || pathname === "/login" || pathname === "/register";
  if (isAuthPage) return null;

  const links = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard, roles: ["admin", "manager", "member"] },
    { name: "Projects", href: "/projects", icon: FolderKanban, roles: ["admin", "manager", "member"] },
    { name: "AI Predictions", href: "/predictions", icon: BrainCircuit, roles: ["admin", "manager", "member"] },
    { name: "GitHub Analysis", href: "/github-analysis", icon: GitBranch, roles: ["admin", "manager", "member"] },
    { name: "Dataset Manager", href: "/datasets", icon: Database, roles: ["admin", "manager"] },
    { name: "System Reports", href: "/reports", icon: FileBarChart, roles: ["admin", "manager", "member"] },
    { name: "Admin Panel", href: "/admin", icon: ShieldAlert, roles: ["admin"] },
  ];

  const filteredLinks = links.filter((link) => !user || link.roles.includes(user.role));

  return (
    <aside
      className={`sticky top-0 h-screen border-r border-slate-200 bg-slate-50/90 backdrop-blur-sm transition-all duration-200 ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center justify-between border-b border-slate-200 px-4">
          <Link href="/dashboard" className="flex items-center gap-2 overflow-hidden whitespace-nowrap text-slate-900">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-100 text-blue-700">
              <Sparkles className="h-4 w-4" />
            </div>
            {!collapsed && (
              <span className="text-base font-semibold tracking-tight text-slate-900">RiskPilot</span>
            )}
          </Link>

          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            className="hidden h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 md:flex"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {filteredLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname.startsWith(link.href);

            return (
              <Link
                key={link.name}
                href={link.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-600 hover:bg-slate-200 hover:text-slate-900"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span>{link.name}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-200 p-3">
          {!collapsed && user && (
            <div className="mb-3 rounded-lg border border-slate-200 bg-white p-3">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
                  {user.full_name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-800">{user.full_name}</p>
                  <p className="truncate text-[11px] text-slate-500">{user.email}</p>
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-600">
                  {user.role}
                </span>
                <Link
                  href="/projects"
                  className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-[10px] font-medium text-slate-600 hover:bg-slate-100"
                >
                  <Settings size={12} />
                  Settings
                </Link>
              </div>
            </div>
          )}

          <div className="space-y-2">
            {!collapsed && user && (
              <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-200">
                <User size={15} />
                <span>User profile</span>
              </div>
            )}

            <button
              type="button"
              onClick={logout}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-700 hover:bg-red-50 hover:text-red-700"
            >
              <LogOut className="h-4 w-4" />
              {!collapsed && <span>Sign Out</span>}
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
