"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { 
  Plus, 
  Search, 
  Trash2, 
  Archive, 
  FolderOpen, 
  FileText,
  Sliders,
  AlertTriangle,
  RotateCcw,
  Sparkles
} from "lucide-react";

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
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [showArchived, setShowArchived] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, [showArchived]);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const endpoint = `/projects/?is_archived=${showArchived}`;
      const data = await apiFetch(endpoint);
      setProjects(data);
    } catch {
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Are you sure you want to delete project '${name}'?`)) return;
    try {
      await apiFetch(`/projects/${id}`, { method: "DELETE" });
      setProjects(prev => prev.filter(p => p.id !== id));
    } catch {
      // Ignore project deletion errors in this UI flow.
    }
  };

  const handleArchive = async (id: number) => {
    try {
      await apiFetch(`/projects/${id}/archive`, { method: "POST" });
      setProjects(prev => prev.filter(p => p.id !== id));
    } catch {
      // Ignore archive failures in this UI flow.
    }
  };

  const handleUnarchive = async (id: number) => {
    try {
      await apiFetch(`/projects/${id}/unarchive`, { method: "POST" });
      setProjects(prev => prev.filter(p => p.id !== id));
    } catch {
      // Ignore restore failures in this UI flow.
    }
  };

  // Client-side quick filter
  const filteredProjects = projects.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) || 
                          (p.company_name && p.company_name.toLowerCase().includes(search.toLowerCase()));
    const matchesRisk = riskFilter === "" || p.risk_level === riskFilter;
    const matchesType = typeFilter === "" || p.project_type === typeFilter;
    return matchesSearch && matchesRisk && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Project Workspace</span>
          <h2 className="text-xl font-bold text-slate-100 mt-1">
            {showArchived ? "Archived Projects" : "Active Projects"} ({filteredProjects.length})
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowArchived(!showArchived)}
            className="px-4 py-2 bg-slate-900 border border-slate-800 text-slate-300 hover:text-white rounded-lg text-xs font-semibold cursor-pointer"
          >
            {showArchived ? "Show Active Projects" : "Show Archived"}
          </button>
          
          {!showArchived && (
            <Link
              href="/projects/new"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold cursor-pointer flex items-center gap-1.5"
            >
              <Plus size={14} />
              Add Project
            </Link>
          )}
        </div>
      </div>

      {/* Filters Toolbar */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
        {/* Search */}
        <div className="relative col-span-1 md:col-span-2">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
          <input 
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or company..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg py-1.5 pl-10 pr-4 text-xs text-slate-300 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        {/* Risk Level */}
        <div>
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg py-1.5 px-3 text-xs text-slate-300 focus:outline-none focus:border-blue-500 transition-colors"
          >
            <option value="">All Risk Levels</option>
            <option value="Low">Low Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="High">High Risk</option>
          </select>
        </div>

        {/* Project Type */}
        <div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg py-1.5 px-3 text-xs text-slate-300 focus:outline-none focus:border-blue-500 transition-colors"
          >
            <option value="">All Project Types</option>
            <option value="Web">Web Apps</option>
            <option value="Mobile">Mobile Apps</option>
            <option value="AI/ML">AI/ML Models</option>
            <option value="Cloud">Cloud Migration</option>
            <option value="DevOps">DevOps Pipeline</option>
            <option value="Security">Security Audit</option>
          </select>
        </div>
      </div>

      {/* Projects Table */}
      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="w-8 h-8 rounded-full border-2 border-blue-500/20 border-t-blue-500 animate-spin mx-auto mb-4" />
            <p className="text-slate-400 text-xs font-mono">LOADING PROJECTS TABLE...</p>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">
            No projects found matching current filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 font-semibold uppercase tracking-wider bg-slate-900/30">
                  <th className="p-4">Project Name</th>
                  <th className="p-4">Company</th>
                  <th className="p-4">Type</th>
                  <th className="p-4">Budget</th>
                  <th className="p-4">Test Cover</th>
                  <th className="p-4">Bugs</th>
                  <th className="p-4">Sprint Delays</th>
                  <th className="p-4 font-bold text-blue-400">Success Prob</th>
                  <th className="p-4">Risk Level</th>
                  <th className="p-4">Health</th>
                  <th className="p-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {filteredProjects.map((project) => (
                  <tr key={project.id} className="text-slate-300 hover:bg-slate-900/20 transition-colors">
                    <td className="p-4 font-semibold text-slate-100">
                      <Link href={`/predictions?project_id=${project.id}`} className="hover:text-blue-400 hover:underline">
                        {project.name}
                      </Link>
                    </td>
                    <td className="p-4 text-slate-400">{project.company_name || "N/A"}</td>
                    <td className="p-4">{project.project_type}</td>
                    <td className="p-4 font-mono">${project.budget?.toLocaleString(undefined, { minimumFractionDigits: 0 })}</td>
                    <td className="p-4 font-mono">{project.testing_coverage?.toFixed(1)}%</td>
                    <td className="p-4 font-mono text-red-400">{project.bug_count}</td>
                    <td className="p-4 font-mono text-red-400">{project.sprint_delays}</td>
                    <td className="p-4 font-mono font-bold text-blue-400">
                      {project.success_probability ? `${(project.success_probability * 100).toFixed(1)}%` : "N/A"}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        project.risk_level === "High" ? "bg-red-950/40 text-red-400 border border-red-500/20" :
                        project.risk_level === "Medium" ? "bg-amber-950/40 text-amber-400 border border-amber-500/20" :
                        "bg-emerald-950/40 text-emerald-400 border border-emerald-500/20"
                      }`}>
                        {project.risk_level}
                      </span>
                    </td>
                    <td className="p-4 font-mono font-semibold">{project.health_score?.toFixed(1) || "100.0"}/100</td>
                    <td className="p-4">
                      <div className="flex items-center justify-center gap-2">
                        {/* Predict Link */}
                        <Link
                          href={`/predictions?project_id=${project.id}`}
                          className="p-1.5 bg-blue-950/40 border border-blue-500/20 text-blue-400 hover:bg-blue-600 hover:text-white rounded-md transition-colors"
                          title="Evaluate Risk & XAI"
                        >
                          <Sparkles size={13} />
                        </Link>
                        
                        {/* What-If Simulator */}
                        <Link
                          href={`/predictions/what-if?project_id=${project.id}`}
                          className="p-1.5 bg-slate-800 border border-slate-700 text-slate-300 hover:bg-blue-600 hover:text-white rounded-md transition-colors"
                          title="What-If Simulation"
                        >
                          <Sliders size={13} />
                        </Link>

                        {/* Edit Link */}
                        <Link
                          href={`/projects/${project.id}/edit`}
                          className="p-1.5 bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 rounded-md transition-colors"
                          title="Edit Parameters"
                        >
                          <FolderOpen size={13} />
                        </Link>

                        {/* Archive / Restore Button */}
                        {showArchived ? (
                          <button
                            onClick={() => handleUnarchive(project.id)}
                            className="p-1.5 bg-slate-800 border border-slate-700 text-slate-300 hover:bg-emerald-600 hover:text-white rounded-md transition-colors cursor-pointer"
                            title="Restore Project"
                          >
                            <RotateCcw size={13} />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleArchive(project.id)}
                            className="p-1.5 bg-slate-800 border border-slate-700 text-slate-300 hover:bg-amber-600 hover:text-white rounded-md transition-colors cursor-pointer"
                            title="Archive Project"
                          >
                            <Archive size={13} />
                          </button>
                        )}

                        {/* Delete Button */}
                        <button
                          onClick={() => handleDelete(project.id, project.name)}
                          className="p-1.5 bg-red-950/20 border border-red-500/10 text-red-400 hover:bg-red-600 hover:text-white rounded-md transition-colors cursor-pointer"
                          title="Delete Project"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
