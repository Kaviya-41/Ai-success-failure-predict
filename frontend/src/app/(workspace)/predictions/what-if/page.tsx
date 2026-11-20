"use client";

import React, { useState, useEffect, use, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { 
  Sliders, 
  HelpCircle, 
  ArrowLeft,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Activity,
  Zap
} from "lucide-react";
import Link from "next/link";

interface Project {
  id: number;
  name: string;
}

interface PredictionResponse {
  is_successful_prediction: boolean;
  success_probability: number;
  failure_probability: number;
  risk_score: number;
  risk_level: string;
  health_score: number;
  confidence_score: number;
  model_algorithm: string;
  top_risk_factors: string[];
  top_success_factors: string[];
}

function WhatIfContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectIdParam = searchParams.get("project_id");

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  
  // Simulation Values State
  const [simValues, setSimValues] = useState({
    budget: 50000,
    duration_days: 90,
    team_size: 5,
    team_experience_years: 5.0,
    project_complexity: 3,
    requirement_changes: 0,
    sprint_delays: 0,
    bug_count: 0,
    testing_coverage: 70.0,
    client_involvement: 3,
    resource_availability: 100.0,
    customer_satisfaction: 3,
    project_type: "Web"
  });

  // Predictions State
  const [basePrediction, setBasePrediction] = useState<PredictionResponse | null>(null);
  const [simPrediction, setSimPrediction] = useState<PredictionResponse | null>(null);

  // 1. Load Projects List
  useEffect(() => {
    async function loadProjects() {
      try {
        const data = await apiFetch("/projects/");
        setProjects(data);
        if (data.length > 0 && !projectIdParam) {
          setSelectedProjectId(data[0].id.toString());
        }
      } catch {
        setProjects([]);
      }
    }
    loadProjects();
  }, [projectIdParam]);

  // 2. Respond to project changes and load base details
  useEffect(() => {
    if (projectIdParam) {
      setSelectedProjectId(projectIdParam);
      loadBaseProjectDetails(projectIdParam);
    } else if (selectedProjectId) {
      loadBaseProjectDetails(selectedProjectId);
    }
  }, [projectIdParam, selectedProjectId]);

  // 3. Trigger simulation recalculation when inputs change
  useEffect(() => {
    if (selectedProjectId) {
      runSimulation();
    }
  }, [simValues]);

  const loadBaseProjectDetails = async (id: string) => {
    setLoading(true);
    try {
      const project = await apiFetch(`/projects/${id}`);
      const initialMetrics = {
        name: project.name,
        company_name: project.company_name || "",
        project_type: project.project_type || "Web",
        budget: project.budget || 50000,
        duration_days: project.duration_days || 90,
        team_size: project.team_size || 5,
        team_experience_years: project.team_experience_years || 5.0,
        project_complexity: project.project_complexity || 3,
        requirement_changes: project.requirement_changes || 0,
        sprint_delays: project.sprint_delays || 0,
        bug_count: project.bug_count || 0,
        testing_coverage: project.testing_coverage || 70.0,
        client_involvement: project.client_involvement || 3,
        resource_availability: project.resource_availability || 100.0,
        customer_satisfaction: project.customer_satisfaction || 3
      };
      
      setSimValues(initialMetrics);
    } catch {
      setLoading(false);
      return;
    } finally {
      setLoading(false);
    }
  };

  const handleProjectSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedProjectId(val);
    router.push(`/predictions/what-if?project_id=${val}`);
  };

  const handleSliderChange = (name: string, val: number) => {
    setSimValues(prev => ({
      ...prev,
      [name]: val
    }));
  };

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setSimValues(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const runSimulation = async () => {
    try {
      const payload = {
        project_id: selectedProjectId ? parseInt(selectedProjectId) : null,
        current_values: simValues
      };
      
      const res = await apiFetch("/predictions/what-if", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setBasePrediction(res.base_prediction);
      setSimPrediction(res.simulated_prediction);
    } catch {
      setBasePrediction(null);
      setSimPrediction(null);
    }
  };

  const getDeltaSuccess = () => {
    if (!basePrediction || !simPrediction) return 0;
    return (simPrediction.success_probability - basePrediction.success_probability) * 100;
  };

  const delta = getDeltaSuccess();

  return (
    <div className="space-y-6">
      {/* Header toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link 
            href="/projects" 
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={16} />
          </Link>
          <div>
            <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Prediction Sandbox</span>
            <h2 className="text-xl font-bold text-slate-100 mt-1">What-If Analysis Simulator</h2>
          </div>
        </div>

        {/* Project Selector dropdown */}
        <div className="w-full sm:w-64">
          <select
            value={selectedProjectId}
            onChange={handleProjectSelect}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg py-1.5 px-3 text-xs text-slate-300 focus:outline-none focus:border-blue-500 transition-colors"
          >
            <option value="" disabled>Choose a project...</option>
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Sliders Panel (col-span-2) */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 lg:col-span-2 space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Sliders className="w-5 h-5 text-blue-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Simulated Parameter Controls</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5">
            {/* Planning parameters */}
            <div className="space-y-4">
              <h4 className="text-[10px] font-extrabold text-blue-500 uppercase tracking-widest border-l-2 border-blue-500 pl-2">Planning & Team Metrics</h4>
              
              {/* Budget */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Budget ($ USD)</span>
                  <span className="font-mono text-slate-200">${simValues.budget.toLocaleString()}</span>
                </div>
                <input 
                  type="range" min="10000" max="1000000" step="10000"
                  value={simValues.budget}
                  onChange={(e) => handleSliderChange("budget", parseInt(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {/* Duration */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Duration (Days)</span>
                  <span className="font-mono text-slate-200">{simValues.duration_days} days</span>
                </div>
                <input 
                  type="range" min="15" max="365" step="5"
                  value={simValues.duration_days}
                  onChange={(e) => handleSliderChange("duration_days", parseInt(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {/* Team Size */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Team Size</span>
                  <span className="font-mono text-slate-200">{simValues.team_size} members</span>
                </div>
                <input 
                  type="range" min="1" max="50" step="1"
                  value={simValues.team_size}
                  onChange={(e) => handleSliderChange("team_size", parseInt(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {/* Team Experience */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Team Experience (Yrs)</span>
                  <span className="font-mono text-slate-200">{simValues.team_experience_years.toFixed(1)} yrs</span>
                </div>
                <input 
                  type="range" min="0.5" max="15.0" step="0.5"
                  value={simValues.team_experience_years}
                  onChange={(e) => handleSliderChange("team_experience_years", parseFloat(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {/* Resource Availability */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Resource Availability</span>
                  <span className="font-mono text-slate-200">{simValues.resource_availability}%</span>
                </div>
                <input 
                  type="range" min="10" max="100" step="5"
                  value={simValues.resource_availability}
                  onChange={(e) => handleSliderChange("resource_availability", parseFloat(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>
            </div>

            {/* Risk / Execution Metrics */}
            <div className="space-y-4">
              <h4 className="text-[10px] font-extrabold text-red-500 uppercase tracking-widest border-l-2 border-red-500 pl-2">Risk & Execution Metrics</h4>

              {/* Testing Coverage */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Testing Coverage</span>
                  <span className="font-mono text-slate-200">{simValues.testing_coverage}%</span>
                </div>
                <input 
                  type="range" min="0" max="100" step="2"
                  value={simValues.testing_coverage}
                  onChange={(e) => handleSliderChange("testing_coverage", parseFloat(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {/* Bug count */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Active Bug Backlog</span>
                  <span className="font-mono text-slate-200">{simValues.bug_count} bugs</span>
                </div>
                <input 
                  type="range" min="0" max="100" step="1"
                  value={simValues.bug_count}
                  onChange={(e) => handleSliderChange("bug_count", parseInt(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {/* Sprint delays */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Sprint Delays</span>
                  <span className="font-mono text-slate-200">{simValues.sprint_delays} delays</span>
                </div>
                <input 
                  type="range" min="0" max="15" step="1"
                  value={simValues.sprint_delays}
                  onChange={(e) => handleSliderChange("sprint_delays", parseInt(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {/* Requirement changes */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Requirement changes</span>
                  <span className="font-mono text-slate-200">{simValues.requirement_changes} scope adjustments</span>
                </div>
                <input 
                  type="range" min="0" max="15" step="1"
                  value={simValues.requirement_changes}
                  onChange={(e) => handleSliderChange("requirement_changes", parseInt(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {/* Client involvement */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Client Connection Rating</span>
                  <span className="font-mono text-slate-200">{simValues.client_involvement}/5</span>
                </div>
                <input 
                  type="range" min="1" max="5" step="1"
                  value={simValues.client_involvement}
                  onChange={(e) => handleSliderChange("client_involvement", parseInt(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Real-time output feedback */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 flex flex-col justify-between space-y-6">
          <div>
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4">
              <Zap className="w-5 h-5 text-indigo-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Simulated Prediction</h3>
            </div>

            {simPrediction ? (
              <div className="space-y-6">
                {/* Result outcome banner */}
                <div className="text-center p-4 bg-slate-950/60 rounded-xl border border-slate-800 flex flex-col items-center">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Simulated Outcome</span>
                  <span className={`text-xl font-black mt-1 ${
                    simPrediction.is_successful_prediction ? "text-blue-500" : "text-red-500"
                  }`}>
                    {simPrediction.is_successful_prediction ? "✅ SUCCESS" : "❌ FAILURE"}
                  </span>
                  
                  {/* Delta indicator compared to baseline */}
                  {basePrediction && delta !== 0 && (
                    <span className={`inline-flex items-center mt-2 px-2 py-0.5 rounded text-[10px] font-bold ${
                      delta > 0 ? "bg-emerald-950/30 text-emerald-400 border border-emerald-500/20" : "bg-red-950/30 text-red-400 border border-red-500/20"
                    }`}>
                      {delta > 0 ? <TrendingUp size={10} className="mr-1" /> : <TrendingDown size={10} className="mr-1" />}
                      {delta > 0 ? "+" : ""}{delta.toFixed(1)}% vs Baseline
                    </span>
                  )}
                </div>

                {/* Probability bar */}
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-slate-400">Success Probability</span>
                    <span className="text-blue-400 font-bold font-mono">{(simPrediction.success_probability * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2.5 bg-slate-950 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-linear-to-r from-blue-600 to-indigo-500 transition-all duration-300"
                      style={{ width: `${simPrediction.success_probability * 100}%` }}
                    />
                  </div>
                </div>

                {/* Metrics boxes */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-900 text-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Health Rating</span>
                    <span className="text-md font-bold text-slate-200 mt-1 block font-mono">
                      {simPrediction.health_score.toFixed(1)}/100
                    </span>
                  </div>
                  
                  <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-900 text-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Risk Level</span>
                    <span className={`text-xs font-black mt-1.5 inline-block px-2 py-0.5 rounded ${
                      simPrediction.risk_level === "High" ? "bg-red-950/40 text-red-400 border border-red-500/20" :
                      simPrediction.risk_level === "Medium" ? "bg-amber-950/40 text-amber-400 border border-amber-500/20" :
                      "bg-emerald-950/40 text-emerald-400 border border-emerald-500/20"
                    }`}>
                      {simPrediction.risk_level}
                    </span>
                  </div>
                </div>

                {/* Baseline comparison boxes */}
                {basePrediction && (
                  <div className="border-t border-slate-800/80 pt-4 space-y-2">
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider block">Baseline Project Context</span>
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Baseline Success Probability:</span>
                      <span className="font-mono text-slate-300">{(basePrediction.success_probability * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Baseline Risk Level:</span>
                      <span className="font-semibold text-slate-300">{basePrediction.risk_level}</span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-xs text-slate-500">
                Awaiting simulation parameters...
              </div>
            )}
          </div>
          
          <div className="bg-slate-900/30 border border-slate-850 p-4 rounded-xl text-xs text-slate-400 flex items-start gap-2.5">
            <HelpCircle size={16} className="text-blue-500 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <strong>Tip:</strong> Drag the <strong>Code Test Coverage</strong> slider up or the <strong>Active Bug Backlog</strong> slider down to see how code quality immediately alters the project's success probability.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function WhatIfPage() {
  return (
    <Suspense fallback={
      <div className="h-96 flex flex-col items-center justify-center">
        <Zap className="w-8 h-8 text-blue-500 animate-spin mb-3" />
        <p className="text-slate-400 text-xs font-mono tracking-widest animate-pulse font-bold">LOADING WHAT-IF ENGINE...</p>
      </div>
    }>
      <WhatIfContent />
    </Suspense>
  );
}
