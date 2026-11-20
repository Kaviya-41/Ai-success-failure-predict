"use client";

import React, { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/context/auth-context";
import { 
  Users, 
  Activity, 
  ShieldCheck, 
  Settings, 
  UserCheck, 
  AlertCircle,
  Clock
} from "lucide-react";

interface UserInfo {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
}

interface ActivityLog {
  id: number;
  action: string;
  details: string;
  timestamp: string;
  user_email: string;
}

interface SystemAnalytics {
  total_users: number;
  total_projects: number;
  active_projects: number;
  high_risk_projects: number;
  med_risk_projects: number;
  low_risk_projects: number;
  predicted_success_count: number;
  predicted_failure_count: number;
  active_model_name: string;
  active_model_accuracy: number;
}

export default function AdminPage() {
  const { user: currentUser } = useAuth();
  
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);

  const [loading, setLoading] = useState(true);
  const [updatingRole, setUpdatingRole] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [activeTab, setActiveTab] = useState<"users" | "logs" | "analytics">("analytics");

  useEffect(() => {
    if (currentUser?.role === "admin") {
      loadAdminData();
    } else {
      setError("Unauthorized access. Admin permissions required.");
      setLoading(false);
    }
  }, [currentUser]);

  const loadAdminData = async () => {
    setLoading(true);
    setError("");
    try {
      const stats = await apiFetch("/admin/system-analytics");
      setAnalytics(stats);
      
      const userList = await apiFetch("/admin/users");
      setUsers(userList);
      
      const logList = await apiFetch("/admin/activity-logs");
      setLogs(logList);
    } catch (e: any) {
      setError(e.message || "Failed to load administrative logs.");
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    setError("");
    setSuccess("");
    setUpdatingRole(userId);
    try {
      const res = await apiFetch(`/admin/users/${userId}/role?role=${newRole}`, {
        method: "PUT"
      });
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: newRole } : u));
      setSuccess(`User '${res.email}' role updated to '${newRole}'.`);
    } catch (e: any) {
      setError(e.message || "Failed to update role.");
    } finally {
      setUpdatingRole(null);
    }
  };

  if (currentUser?.role !== "admin") {
    return (
      <div className="bg-red-950/20 border border-red-500/20 p-6 rounded-xl flex items-center justify-center gap-3 text-red-400">
        <AlertCircle size={20} />
        <span className="text-sm font-semibold">Access Denied: Administrative permissions required to view this panel.</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Navigation tabs */}
      <div className="flex border-b border-slate-800 gap-6">
        <button
          onClick={() => setActiveTab("analytics")}
          className={`pb-2.5 text-xs font-bold uppercase tracking-wider cursor-pointer transition-colors ${
            activeTab === "analytics"
              ? "text-blue-500 border-b-2 border-blue-500"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          System Statistics
        </button>
        <button
          onClick={() => setActiveTab("users")}
          className={`pb-2.5 text-xs font-bold uppercase tracking-wider cursor-pointer transition-colors ${
            activeTab === "users"
              ? "text-blue-500 border-b-2 border-blue-500"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          User Management
        </button>
        <button
          onClick={() => setActiveTab("logs")}
          className={`pb-2.5 text-xs font-bold uppercase tracking-wider cursor-pointer transition-colors ${
            activeTab === "logs"
              ? "text-blue-500 border-b-2 border-blue-500"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Audit Logs
        </button>
      </div>

      {/* Alert panels */}
      {error && (
        <div className="bg-red-950/20 border border-red-500/30 p-3 rounded-lg text-xs text-red-400">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-emerald-950/20 border border-emerald-500/30 p-3 rounded-lg text-xs text-emerald-400">
          {success}
        </div>
      )}

      {loading ? (
        <div className="h-96 flex flex-col items-center justify-center">
          <ShieldCheck className="w-8 h-8 text-blue-500 animate-spin mb-2" />
          <p className="text-slate-500 text-xs font-mono">LOADING CONTROL MATRIX...</p>
        </div>
      ) : (
        <div>
          {/* Tab 1: Analytics */}
          {activeTab === "analytics" && analytics && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="glass-panel p-5 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold block">Registered Users</span>
                <span className="text-2xl font-black mt-1 text-slate-200 font-mono block">{analytics.total_users}</span>
              </div>
              <div className="glass-panel p-5 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold block">Evaluated Projects</span>
                <span className="text-2xl font-black mt-1 text-slate-200 font-mono block">{analytics.total_projects}</span>
              </div>
              <div className="glass-panel p-5 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold block">Active Model</span>
                <span className="text-sm font-extrabold mt-2.5 text-blue-400 block uppercase tracking-wider">{analytics.active_model_name}</span>
              </div>
              <div className="glass-panel p-5 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold block">Model Validation Accuracy</span>
                <span className="text-2xl font-black mt-1 text-purple-400 font-mono block">{(analytics.active_model_accuracy * 100).toFixed(1)}%</span>
              </div>

              {/* Detailed Breakdown Card */}
              <div className="glass-panel p-6 rounded-xl border border-slate-800 md:col-span-2 space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Risk Profile Summary</h4>
                <div className="space-y-3.5">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Low Risk Portfolio:</span>
                      <span className="font-semibold text-emerald-400 font-mono">{analytics.low_risk_projects} projects</span>
                    </div>
                    <div className="h-1.5 bg-slate-950 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500" style={{ width: `${analytics.total_projects > 0 ? (analytics.low_risk_projects / analytics.total_projects) * 100 : 0}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Medium Risk Portfolio:</span>
                      <span className="font-semibold text-amber-400 font-mono">{analytics.med_risk_projects} projects</span>
                    </div>
                    <div className="h-1.5 bg-slate-950 rounded-full overflow-hidden">
                      <div className="h-full bg-amber-500" style={{ width: `${analytics.total_projects > 0 ? (analytics.med_risk_projects / analytics.total_projects) * 100 : 0}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">High Risk Portfolio:</span>
                      <span className="font-semibold text-red-500 font-mono">{analytics.high_risk_projects} projects</span>
                    </div>
                    <div className="h-1.5 bg-slate-950 rounded-full overflow-hidden">
                      <div className="h-full bg-red-500" style={{ width: `${analytics.total_projects > 0 ? (analytics.high_risk_projects / analytics.total_projects) * 100 : 0}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: User management */}
          {activeTab === "users" && (
            <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-500 font-semibold uppercase tracking-wider bg-slate-900/30">
                      <th className="p-4">Full Name</th>
                      <th className="p-4">Email</th>
                      <th className="p-4">System Role</th>
                      <th className="p-4">Active</th>
                      <th className="p-4 text-center">Change Role</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {users.map(u => (
                      <tr key={u.id} className="text-slate-300 hover:bg-slate-900/20 transition-colors">
                        <td className="p-4 font-semibold text-slate-100 flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-blue-600/10 border border-blue-500/20 text-blue-400 flex items-center justify-center font-bold">
                            {u.full_name?.charAt(0).toUpperCase() || u.email.charAt(0).toUpperCase()}
                          </div>
                          {u.full_name || "N/A"}
                        </td>
                        <td className="p-4 text-slate-400">{u.email}</td>
                        <td className="p-4">
                          <span className="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-[10px] capitalize font-mono font-semibold">
                            {u.role}
                          </span>
                        </td>
                        <td className="p-4">
                          <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${u.is_active ? "bg-emerald-950/40 text-emerald-400" : "bg-red-950/40 text-red-400"}`}>
                            {u.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                        <td className="p-4">
                          <div className="flex justify-center gap-1.5">
                            {["member", "manager", "admin"].map(roleOption => (
                              <button
                                key={roleOption}
                                disabled={updatingRole === u.id || u.role === roleOption}
                                onClick={() => handleRoleChange(u.id, roleOption)}
                                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase transition-colors cursor-pointer disabled:opacity-40 ${
                                  u.role === roleOption
                                    ? "bg-blue-600 text-white"
                                    : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                                }`}
                              >
                                {roleOption === "admin" ? "Admin" : roleOption === "manager" ? "Manager" : "Member"}
                              </button>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 3: Audit Logs */}
          {activeTab === "logs" && (
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Activity size={16} className="text-blue-500" />
                Security Audit Log
              </h3>
              
              <div className="space-y-3.5 max-h-96 overflow-y-auto pr-1">
                {logs.map(log => (
                  <div key={log.id} className="p-3 bg-slate-950/40 border border-slate-900 rounded-lg flex items-start justify-between gap-4 text-xs">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200 uppercase tracking-wide text-[10px] bg-slate-850 px-1.5 py-0.5 rounded">
                          {log.action}
                        </span>
                        <span className="text-slate-400 font-bold">{log.user_email}</span>
                      </div>
                      <p className="text-slate-400">{log.details}</p>
                    </div>
                    
                    <span className="text-[10px] text-slate-600 flex items-center gap-1 shrink-0 mt-0.5">
                      <Clock size={12} />
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                ))}
                {logs.length === 0 && (
                  <p className="text-center text-xs text-slate-500 py-6">No logs generated yet.</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
