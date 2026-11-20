"use client";

import React, { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { 
  FileText, 
  FileSpreadsheet, 
  Download, 
  AlertTriangle, 
  FileCheck,
  Cpu
} from "lucide-react";

interface Project {
  id: number;
  name: string;
  company_name: string;
  project_type: string;
  risk_level: string;
  risk_score: number;
  is_successful_prediction: boolean;
  created_at: string;
}

export default function ReportsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState<number | null>(null);
  const [downloadingExcel, setDownloadingExcel] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const data = await apiFetch("/projects/");
      setProjects(data);
    } catch {
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async (projectId: number, projectName: string) => {
    setDownloadingPdf(projectId);
    try {
      const blob = await apiFetch(`/reports/pdf/${projectId}`);
      // Create local URL and trigger download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `Risk_Assessment_${projectName.replace(/\s+/g, "_")}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch {
      // Ignore PDF export failures in this UI flow.
    } finally {
      setDownloadingPdf(null);
    }
  };

  const handleDownloadExcel = async () => {
    setDownloadingExcel(true);
    try {
      const blob = await apiFetch("/reports/excel");
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `Projects_Portfolio_Summary.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch {
      // Ignore Excel export failures in this UI flow.
    } finally {
      setDownloadingExcel(false);
    }
  };

  const highRiskCount = projects.filter(p => p.risk_level === "High").length;

  return (
    <div className="space-y-6">
      {/* Overview Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Reports */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Compiled Reports</span>
            <span className="text-2xl font-black mt-1 text-slate-200 block font-mono">{projects.length}</span>
            <span className="text-[10px] text-slate-500 mt-0.5 block">Ready for executive export</span>
          </div>
          <div className="w-12 h-12 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-500">
            <FileCheck size={24} />
          </div>
        </div>

        {/* High Risk Flags */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">High Risk Flags</span>
            <span className="text-2xl font-black mt-1 text-red-500 block font-mono">{highRiskCount}</span>
            <span className="text-[10px] text-slate-500 mt-0.5 block">Require immediate audit</span>
          </div>
          <div className="w-12 h-12 rounded-lg bg-red-600/10 border border-red-500/20 flex items-center justify-center text-red-500">
            <AlertTriangle size={24} />
          </div>
        </div>

        {/* Excel Export Card */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Portfolio Export</span>
            <span className="text-xs text-slate-400 mt-1.5 block">Download all projects details in a clean spreadsheet</span>
          </div>
          
          <button
            onClick={handleDownloadExcel}
            disabled={downloadingExcel || projects.length === 0}
            className="w-full mt-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg py-2 px-4 text-xs font-bold transition-colors cursor-pointer flex items-center justify-center gap-1.5 disabled:opacity-50"
          >
            <FileSpreadsheet size={14} />
            {downloadingExcel ? "Exporting Spreadsheet..." : "Download Portfolio Excel"}
          </button>
        </div>
      </div>

      {/* Reports Table */}
      <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-2">
          Project Evaluation Log
        </h3>

        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 rounded-full border-2 border-blue-500/20 border-t-blue-500 animate-spin mx-auto mb-3" />
            <p className="text-slate-500 text-xs font-mono">LOADING REPORT LOGS...</p>
          </div>
        ) : projects.length === 0 ? (
          <p className="text-xs text-slate-500 py-8 text-center">No projects found to compile reports for.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 font-semibold uppercase tracking-wider bg-slate-900/30">
                  <th className="p-4">Project Name</th>
                  <th className="p-4">Client Company</th>
                  <th className="p-4">Category</th>
                  <th className="p-4">Risk Level</th>
                  <th className="p-4">Outcome</th>
                  <th className="p-4">Assessment Date</th>
                  <th className="p-4 text-center">Export</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40">
                {projects.map((project) => (
                  <tr key={project.id} className="text-slate-300 hover:bg-slate-900/20 transition-colors">
                    <td className="p-4 font-semibold text-slate-100">{project.name}</td>
                    <td className="p-4 text-slate-400">{project.company_name || "N/A"}</td>
                    <td className="p-4">{project.project_type}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        project.risk_level === "High" ? "bg-red-950/40 text-red-400 border border-red-500/20" :
                        project.risk_level === "Medium" ? "bg-amber-950/40 text-amber-400 border border-amber-500/20" :
                        "bg-emerald-950/40 text-emerald-400 border border-emerald-500/20"
                      }`}>
                        {project.risk_level} ({project.risk_score?.toFixed(1) || 0})
                      </span>
                    </td>
                    <td className="p-4 font-semibold">
                      {project.is_successful_prediction ? (
                        <span className="text-blue-400">Success</span>
                      ) : (
                        <span className="text-red-400">Failure</span>
                      )}
                    </td>
                    <td className="p-4 text-slate-500">
                      {new Date(project.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                    </td>
                    <td className="p-4">
                      <div className="flex justify-center">
                        <button
                          onClick={() => handleDownloadPdf(project.id, project.name)}
                          disabled={downloadingPdf !== null}
                          className="px-3 py-1 bg-slate-800 hover:bg-blue-600 text-slate-300 hover:text-white rounded-sm text-[10px] font-bold transition-all cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                        >
                          <Download size={12} className={downloadingPdf === project.id ? "animate-bounce" : ""} />
                          {downloadingPdf === project.id ? "Downloading..." : "Download PDF"}
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
