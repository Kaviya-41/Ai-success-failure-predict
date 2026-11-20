"use client";

import React, { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import {
  Folder,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Activity,
  ArrowRight,
  ClipboardList,
  Search,
  Users,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  AreaChart,
  Area,
  ComposedChart,
  Line,
} from "recharts";
import Link from "next/link";

interface Project {
  id: number;
  name: string;
  company_name: string;
  project_type: string;
  budget: number;
  duration_days: number;
  team_size: number;
  team_experience_years: number;
  testing_coverage: number;
  bug_count: number;
  sprint_delays: number;
  requirement_changes: number;
  success_probability: number;
  failure_probability: number;
  risk_score: number;
  risk_level: string;
  health_score: number;
  is_successful_prediction: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  description?: string | null;
}

interface Workspace {
  id: number;
  name: string;
  role: string;
  can_manage_members: boolean;
}

interface GitHubReport {
  id: number;
  repository_url: string;
  repository_name: string;
  repository_owner: string;
  prediction: string;
  health_score: number;
  risk_score: number;
  risk_level: string;
  created_at: string;
}

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [githubReports, setGithubReports] = useState<GitHubReport[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
  const [loading, setLoading] = useState(true);
  const [workspaceError, setWorkspaceError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [historySearch, setHistorySearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [predictionFilter, setPredictionFilter] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"member" | "manager">("member");
  const [inviteMessage, setInviteMessage] = useState("");

  useEffect(() => {
    apiFetch("/workspaces/")
      .then((data) => {
        const available: Workspace[] = Array.isArray(data.workspaces) ? data.workspaces : [];
        setWorkspaces(available);
        const savedId = localStorage.getItem("selected_workspace_id");
        const active = available.find((workspace) => String(workspace.id) === savedId) ?? available[0];
        if (active) {
          localStorage.setItem("selected_workspace_id", String(active.id));
          setSelectedWorkspaceId(String(active.id));
        } else {
          setWorkspaceError("This account is not associated with a workspace. Contact an administrator.");
          setLoading(false);
        }
      })
      .catch((err) => {
        setWorkspaceError(err instanceof Error ? err.message : "Workspaces could not be loaded.");
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selectedWorkspaceId) return;
    setLoading(true);
    setHistoryError("");
    Promise.all([
      apiFetch("/projects/?is_archived=false&limit=100"),
      apiFetch("/github/reports?limit=100"),
    ])
      .then(([projectData, reportData]) => {
        setProjects(Array.isArray(projectData) ? projectData : []);
        setGithubReports(Array.isArray(reportData.reports) ? reportData.reports : []);
      })
      .catch((err) => {
        setHistoryError(err instanceof Error ? err.message : "Workspace history could not be loaded.");
        setProjects([]);
        setGithubReports([]);
      })
      .finally(() => setLoading(false));
  }, [selectedWorkspaceId]);

  const selectWorkspace = (workspaceId: string) => {
    localStorage.setItem("selected_workspace_id", workspaceId);
    setSelectedWorkspaceId(workspaceId);
  };

  const handleInvite = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setInviteMessage("");
    try {
      await apiFetch("/workspaces/members", {
        method: "POST",
        body: JSON.stringify({ email: inviteEmail.trim(), role: inviteRole }),
      });
      setInviteEmail("");
      setInviteMessage("Workspace member added.");
    } catch (err) {
      setInviteMessage(err instanceof Error ? err.message : "Member could not be added.");
    }
  };

  const matchesHistoryFilter = (date: string, prediction?: boolean | string | null) => {
    const day = date.slice(0, 10);
    const result = typeof prediction === "boolean"
      ? prediction ? "SUCCESS" : "FAILURE"
      : prediction?.toUpperCase() ?? "";
    return (
      (!dateFrom || day >= dateFrom)
      && (!dateTo || day <= dateTo)
      && (!predictionFilter || result === predictionFilter)
    );
  };

  const filteredProjects = projects.filter((project) => (
    (!historySearch || project.name.toLowerCase().includes(historySearch.toLowerCase())
      || (project.company_name || "").toLowerCase().includes(historySearch.toLowerCase()))
    && matchesHistoryFilter(project.created_at, project.is_successful_prediction)
  ));
  const filteredGithubReports = githubReports.filter((report) => (
    (!historySearch || report.repository_name.toLowerCase().includes(historySearch.toLowerCase())
      || report.repository_url.toLowerCase().includes(historySearch.toLowerCase()))
    && matchesHistoryFilter(report.created_at, report.prediction)
  ));
  const activeWorkspace = workspaces.find(
    (workspace) => String(workspace.id) === selectedWorkspaceId
  );

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 rounded-xl border border-slate-200 bg-white" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="h-72 rounded-xl border border-slate-200 bg-white" />
          <div className="h-72 rounded-xl border border-slate-200 bg-white" />
        </div>
      </div>
    );
  }

  const total = projects.length;
  const active = projects.filter((p) => !p.is_archived).length;
  const highRisk = projects.filter((p) => p.risk_level === "High" && !p.is_archived).length;
  const successCount = projects.filter((p) => p.is_successful_prediction && !p.is_archived).length;
  const failureCount = projects.filter((p) => !p.is_successful_prediction && !p.is_archived).length;
  const successRate = total > 0 ? (projects.filter((p) => p.is_successful_prediction).length / total) * 100 : 0;
  const lowRiskCount = projects.filter((p) => p.risk_level === "Low" && !p.is_archived).length;
  const medRiskCount = projects.filter((p) => p.risk_level === "Medium" && !p.is_archived).length;

  const summaryCards = [
    {
      label: "Total projects",
      value: total,
      detail: `Active ${active} • Archived ${Math.max(total - active, 0)}`,
      tone: "blue",
      icon: Folder,
    },
    {
      label: "Successful projects",
      value: successCount,
      detail: `${successRate.toFixed(1)}% portfolio success rate`,
      tone: "green",
      icon: CheckCircle,
    },
    {
      label: "At-risk projects",
      value: highRisk,
      detail: "Require attention this week",
      tone: "amber",
      icon: AlertTriangle,
    },
    {
      label: "Failed projects",
      value: failureCount,
      detail: "Needs corrective action",
      tone: "red",
      icon: TrendingUp,
    },
  ];

  const successVsFailureData = [
    { name: "Predicted success", value: successCount, color: "#2563eb" },
    { name: "Predicted failure", value: failureCount, color: "#dc2626" },
  ];

  const riskData = [
    { name: "Low risk", count: lowRiskCount, color: "#16a34a" },
    { name: "Medium risk", count: medRiskCount, color: "#d97706" },
    { name: "High risk", count: highRisk, color: "#dc2626" },
  ];

  const budgetDelayData = projects.slice(0, 6).map((p) => ({
    name: p.name.length > 16 ? `${p.name.substring(0, 16)}...` : p.name,
    budget: p.budget / 1000,
    delays: p.sprint_delays,
  }));

  const projectTypesData = ["Web", "Mobile", "AI/ML", "Cloud", "DevOps", "Security"].map((type) => {
    const typeProjects = projects.filter((p) => p.project_type === type);
    const avgRisk = typeProjects.length > 0 ? typeProjects.reduce((sum, p) => sum + p.risk_score, 0) / typeProjects.length : 0;
    return { name: type, avgRisk: Math.round(avgRisk) };
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="section-label">Portfolio overview</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">Project Risk Overview</h2>
        </div>
        <p className="text-sm text-slate-500">Monitor project health and identify potential delivery risks.</p>
      </div>

      {workspaceError && (
        <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {workspaceError}
        </p>
      )}
      {workspaces.length > 0 && (
        <div className="surface-panel flex flex-col gap-4 p-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-60">
            <label htmlFor="active-workspace" className="mb-2 block text-sm font-medium text-slate-700">Active workspace</label>
            <select
              id="active-workspace"
              value={selectedWorkspaceId}
              onChange={(event) => selectWorkspace(event.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
            >
              {workspaces.map((workspace) => (
                <option key={workspace.id} value={workspace.id}>{workspace.name} · {workspace.role}</option>
              ))}
            </select>
          </div>
          {activeWorkspace?.can_manage_members && (
            <form onSubmit={handleInvite} className="flex flex-col gap-2 sm:flex-row sm:items-end">
              <div>
                <label htmlFor="workspace-member-email" className="mb-2 block text-sm font-medium text-slate-700">Add existing account</label>
                <input
                  id="workspace-member-email"
                  type="email"
                  required
                  value={inviteEmail}
                  onChange={(event) => setInviteEmail(event.target.value)}
                  placeholder="colleague@example.com"
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
                />
              </div>
              {activeWorkspace.role === "owner" && (
                <select
                  aria-label="Workspace role"
                  value={inviteRole}
                  onChange={(event) => setInviteRole(event.target.value as "manager" | "member")}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
                >
                  <option value="member">Member</option>
                  <option value="manager">Manager</option>
                </select>
              )}
              <button type="submit" className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">
                <Users size={16} /> Add member
              </button>
              {inviteMessage && <span role="status" className="text-xs text-slate-600">{inviteMessage}</span>}
            </form>
          )}
        </div>
      )}

      <div className="surface-panel grid grid-cols-1 gap-3 p-4 md:grid-cols-4">
        <label className="relative md:col-span-2">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <span className="sr-only">Search project and repository history</span>
          <input
            value={historySearch}
            onChange={(event) => setHistorySearch(event.target.value)}
            placeholder="Search projects or repositories"
            className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-slate-800"
          />
        </label>
        <label>
          <span className="sr-only">Filter history from date</span>
          <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800" />
        </label>
        <div className="flex gap-3">
          <label className="min-w-0 flex-1">
            <span className="sr-only">Filter history to date</span>
            <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800" />
          </label>
          <select
            aria-label="Filter by prediction result"
            value={predictionFilter}
            onChange={(event) => setPredictionFilter(event.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
          >
            <option value="">All results</option>
            <option value="SUCCESS">Success</option>
            <option value="FAILURE">Failure</option>
          </select>
        </div>
      </div>
      {dateFrom && dateTo && dateFrom > dateTo && (
        <p role="alert" className="text-sm text-red-700">Start date must be on or before end date.</p>
      )}
      {historyError && (
        <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{historyError}</p>
      )}

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        {summaryCards.map(({ label, value, detail, tone, icon: Icon }) => (
          <div key={label} className="kpi-card p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">{label}</p>
                <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>
                <p className="mt-2 text-xs text-slate-500">{detail}</p>
              </div>
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-lg ${
                  tone === "blue"
                    ? "bg-blue-100 text-blue-700"
                    : tone === "green"
                      ? "bg-emerald-100 text-emerald-700"
                      : tone === "amber"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-red-100 text-red-700"
                }`}
              >
                <Icon size={20} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="surface-panel p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="section-label">Signal review</p>
            <h3 className="mt-1 text-lg font-semibold text-slate-900">Project Risk Distribution</h3>
          </div>
          <div className="rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">Portfolio view</div>
        </div>
        <div className="h-72">
          {total === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-slate-500">No project data available</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData} margin={{ top: 10, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#fff", borderColor: "#e2e8f0", borderRadius: "10px" }}
                  itemStyle={{ color: "#0f172a", fontSize: "12px" }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {riskData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="surface-panel p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="section-label">Current activity</p>
              <h3 className="mt-1 text-lg font-semibold text-slate-900">Recent Projects</h3>
            </div>
            <Link href="/projects" className="inline-flex items-center gap-1 text-sm font-medium text-blue-700 hover:text-blue-800">
              View all
              <ArrowRight size={14} />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="data-table w-full min-w-180 text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="pb-3 pr-3 font-medium">Project</th>
                  <th className="pb-3 pr-3 font-medium">Company</th>
                  <th className="pb-3 pr-3 font-medium">Type</th>
                  <th className="pb-3 pr-3 font-medium">Risk Level</th>
                  <th className="pb-3 pr-3 font-medium">Health Score</th>
                  <th className="pb-3 pr-3 font-medium">Prediction</th>
                  <th className="pb-3 font-medium">Updated</th>
                </tr>
              </thead>
              <tbody>
                {projects.slice(0, 6).map((project) => (
                  <tr key={project.id} className="border-b border-slate-100 text-slate-700">
                    <td className="py-3 pr-3 font-semibold text-slate-900">
                      <Link href={`/projects/${project.id}/edit`} className="hover:text-blue-700 hover:underline">{project.name}</Link>
                    </td>
                    <td className="py-3 pr-3 text-slate-600">{project.company_name || "N/A"}</td>
                    <td className="py-3 pr-3">{project.project_type}</td>
                    <td className="py-3 pr-3">
                      <span className={`status-badge ${project.risk_level === "Low" ? "status-low" : project.risk_level === "Medium" ? "status-medium" : "status-high"}`}>
                        {project.risk_level}
                      </span>
                    </td>
                    <td className="py-3 pr-3 font-medium">{project.health_score?.toFixed(1) || "100.0"}/100</td>
                    <td className="py-3 pr-3">
                      {project.is_successful_prediction === true ? (
                        <span className="font-medium text-emerald-700">Success</span>
                      ) : project.is_successful_prediction === false ? (
                        <span className="font-medium text-red-700">Failure</span>
                      ) : (
                        <span className="text-slate-500">Not predicted</span>
                      )}
                    </td>
                    <td className="py-3">{new Date(project.updated_at || project.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="surface-panel p-5">
          <div className="mb-4">
            <p className="section-label">Risk drivers</p>
            <h3 className="mt-1 text-lg font-semibold text-slate-900">Risk Factors</h3>
          </div>

          <div className="space-y-4">
            {projects.length > 0 ? (
              [
                { label: "Sprint delays", value: Math.max(...projects.map((p) => p.sprint_delays), 0), unit: "avg. days" },
                { label: "Testing coverage", value: Math.round(projects.reduce((sum, p) => sum + (p.testing_coverage || 0), 0) / Math.max(projects.length, 1)), unit: "%" },
                { label: "Requirement changes", value: Math.round(projects.reduce((sum, p) => sum + (p.requirement_changes || 0), 0) / Math.max(projects.length, 1)), unit: "changes" },
                { label: "Bug volume", value: Math.round(projects.reduce((sum, p) => sum + (p.bug_count || 0), 0) / Math.max(projects.length, 1)), unit: "bugs" },
              ].map((metric) => (
                <div key={metric.label} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-medium text-slate-700">{metric.label}</span>
                    <span className="text-sm font-semibold text-slate-900">{metric.value}{metric.unit}</span>
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-slate-200">
                    <div
                      className="h-2 rounded-full bg-blue-600"
                      style={{ width: `${Math.min(100, ((metric.value || 0) / (metric.unit === "%" ? 100 : 20)) * 100)}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <ClipboardList size={28} className="text-slate-400" />
                <p className="font-medium text-slate-700">No projects available</p>
                <p>Register a project to begin risk analysis.</p>
                <Link href="/projects/new" className="primary-button">Register project</Link>
              </div>
            )}
          </div>
        </div>
      </div>

      <section className="surface-panel p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <p className="section-label">Workspace records</p>
            <h3 className="mt-1 text-lg font-semibold text-slate-900">Project History</h3>
          </div>
          <Link href="/projects" className="text-sm font-medium text-blue-700 hover:text-blue-800">All projects</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full min-w-180 text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="pb-3 pr-3 font-medium">Project</th>
                <th className="pb-3 pr-3 font-medium">Created</th>
                <th className="pb-3 pr-3 font-medium">Last updated</th>
                <th className="pb-3 pr-3 font-medium">Prediction status</th>
                <th className="pb-3 pr-3 font-medium">Result</th>
                <th className="pb-3 font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {filteredProjects.map((project) => (
                <tr key={project.id} className="border-b border-slate-100 text-slate-700">
                  <td className="py-3 pr-3 font-medium text-slate-900">{project.name}</td>
                  <td className="py-3 pr-3">{new Date(project.created_at).toLocaleString()}</td>
                  <td className="py-3 pr-3">{new Date(project.updated_at || project.created_at).toLocaleString()}</td>
                  <td className="py-3 pr-3">{project.is_successful_prediction == null ? "Pending" : "Predicted"}</td>
                  <td className="py-3 pr-3">
                    {project.is_successful_prediction === true ? "Success" : project.is_successful_prediction === false ? "Failure" : "—"}
                  </td>
                  <td className="py-3"><Link href={`/projects/${project.id}/edit`} className="font-medium text-blue-700 hover:underline">View details</Link></td>
                </tr>
              ))}
              {filteredProjects.length === 0 && (
                <tr><td colSpan={6} className="py-6 text-center text-sm text-slate-500">No projects match these filters.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="surface-panel p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <p className="section-label">Repository intelligence</p>
            <h3 className="mt-1 text-lg font-semibold text-slate-900">GitHub Analysis History</h3>
          </div>
          <Link href="/github-analysis" className="text-sm font-medium text-blue-700 hover:text-blue-800">Analyse repository</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table w-full min-w-180 text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="pb-3 pr-3 font-medium">Repository</th>
                <th className="pb-3 pr-3 font-medium">GitHub URL</th>
                <th className="pb-3 pr-3 font-medium">Analysed</th>
                <th className="pb-3 pr-3 font-medium">Health</th>
                <th className="pb-3 pr-3 font-medium">Risk</th>
                <th className="pb-3 pr-3 font-medium">Prediction</th>
                <th className="pb-3 font-medium">Report</th>
              </tr>
            </thead>
            <tbody>
              {filteredGithubReports.map((report) => (
                <tr key={report.id} className="border-b border-slate-100 text-slate-700">
                  <td className="py-3 pr-3 font-medium text-slate-900">{report.repository_name}</td>
                  <td className="max-w-64 truncate py-3 pr-3">
                    <a href={report.repository_url} target="_blank" rel="noreferrer" className="text-blue-700 hover:underline">{report.repository_url}</a>
                  </td>
                  <td className="py-3 pr-3">{new Date(report.created_at).toLocaleString()}</td>
                  <td className="py-3 pr-3">{report.health_score.toFixed(1)}/100</td>
                  <td className="py-3 pr-3">{report.risk_level} · {report.risk_score.toFixed(1)}</td>
                  <td className="py-3 pr-3">{report.prediction}</td>
                  <td className="py-3"><Link href={`/github-analysis/reports/${report.id}`} className="font-medium text-blue-700 hover:underline">View previous report</Link></td>
                </tr>
              ))}
              {filteredGithubReports.length === 0 && (
                <tr><td colSpan={7} className="py-6 text-center text-sm text-slate-500">No GitHub reports match these filters.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
