"use client";

import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Bell, Search, Check, AlertTriangle, AlertCircle, Info } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/context/auth-context";

interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export default function Navbar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  const isAuthPage = pathname === "/" || pathname === "/login" || pathname === "/register";

  useEffect(() => {
    if (isAuthPage || !user) return;

    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [pathname, user]);

  const fetchNotifications = async () => {
    try {
      const data = await apiFetch("/notifications/");
      setNotifications(data);
    } catch (e) {
      // Quietly ignore background network failures.
    }
  };

  const markAsRead = async (id: number) => {
    try {
      await apiFetch(`/notifications/read/${id}`, { method: "POST" });
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    } catch {
      // Ignore notification update failures.
    }
  };

  const markAllRead = async () => {
    try {
      await apiFetch("/notifications/read-all", { method: "POST" });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      // Ignore notification update failures.
    }
  };

  if (isAuthPage) return null;

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const getPageTitle = () => {
    if (pathname.startsWith("/dashboard")) return "Dashboard";
    if (pathname.startsWith("/projects")) return "Projects";
    if (pathname.startsWith("/predictions")) return "AI Predictions";
    if (pathname.startsWith("/datasets")) return "Dataset Manager";
    if (pathname.startsWith("/reports")) return "System Reports";
    if (pathname.startsWith("/admin")) return "Administration";
    return "Project Risk Workspace";
  };

  const getPageDescription = () => {
    if (pathname.startsWith("/dashboard")) return "Monitor project health and identify delivery risk.";
    if (pathname.startsWith("/projects")) return "Manage project records and active portfolio health.";
    if (pathname.startsWith("/predictions")) return "Evaluate risk, review conditions, and act on recommendations.";
    if (pathname.startsWith("/datasets")) return "Upload and maintain structured training datasets.";
    if (pathname.startsWith("/reports")) return "Review summary reporting and export portfolio data.";
    return "Operational risk overview";
  };

  return (
    <header className="sticky top-0 z-40 h-20 w-full border-b border-slate-200 bg-white/80 backdrop-blur-sm">
      <div className="flex h-full items-center justify-between gap-4 px-6">
        <div>
          <p className="section-label mb-1">Portfolio management</p>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">{getPageTitle()}</h1>
        </div>

        <div className="flex items-center gap-4">
          <div className="relative hidden w-72 md:block">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search workspace"
              className="form-field h-10 bg-slate-50 pl-9 text-sm text-slate-700 placeholder:text-slate-400"
              aria-label="Search workspace"
            />
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => setIsOpen(!isOpen)}
              className="relative flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-100"
              aria-label="Notifications"
            >
              <Bell size={16} />
              {unreadCount > 0 && (
                <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white animate-pulse-ring">
                  {unreadCount}
                </span>
              )}
            </button>

            {isOpen && (
              <div className="absolute right-0 mt-3 w-80 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
                <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
                  <span className="text-sm font-semibold text-slate-800">Notifications ({unreadCount} new)</span>
                  {unreadCount > 0 && (
                    <button
                      type="button"
                      onClick={markAllRead}
                      className="text-xs font-medium text-blue-700 hover:text-blue-800"
                    >
                      Mark all read
                    </button>
                  )}
                </div>

                <div className="max-h-72 overflow-y-auto divide-y divide-slate-200">
                  {notifications.length === 0 ? (
                    <div className="p-4 text-center text-sm text-slate-500">No alerts or notifications</div>
                  ) : (
                    notifications.map((notif) => (
                      <div key={notif.id} className={`flex gap-3 p-3 ${!notif.is_read ? "bg-blue-50" : "bg-white"}`}>
                        <div className="mt-0.5 shrink-0">
                          {notif.type === "danger" ? (
                            <AlertCircle className="h-4 w-4 text-red-500" />
                          ) : notif.type === "warning" ? (
                            <AlertTriangle className="h-4 w-4 text-amber-500" />
                          ) : (
                            <Info className="h-4 w-4 text-blue-500" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-semibold text-slate-800">{notif.title}</p>
                          <p className="mt-1 text-xs text-slate-500">{notif.message}</p>
                          <span className="mt-1 block text-[10px] text-slate-400">
                            {new Date(notif.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </div>
                        {!notif.is_read && (
                          <button
                            type="button"
                            onClick={() => markAsRead(notif.id)}
                            className="self-center rounded-md p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700"
                            title="Mark as read"
                          >
                            <Check size={12} />
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {user && (
            <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                {user.full_name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
              </div>
              <div className="hidden text-left sm:block">
                <p className="text-sm font-semibold text-slate-800">{user.full_name}</p>
                <p className="text-[11px] capitalize text-slate-500">{user.role}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
