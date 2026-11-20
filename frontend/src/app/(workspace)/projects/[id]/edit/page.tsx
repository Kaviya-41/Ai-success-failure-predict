"use client";

import React, { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { ArrowLeft, Save, Loader2 } from "lucide-react";
import Link from "next/link";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function EditProjectPage({ params }: PageProps) {
  const router = useRouter();
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    company_name: "",
    project_type: "Web",
    budget: 0,
    duration_days: 0,
    team_size: 0,
    team_experience_years: 0.0,
    tech_stack: "",
    requirement_changes: 0,
    sprint_delays: 0,
    bug_count: 0,
    testing_coverage: 0.0,
    client_involvement: 3,
    resource_availability: 100.0,
    customer_satisfaction: 3,
    project_complexity: 3
  });

  useEffect(() => {
    fetchProjectDetails();
  }, [projectId]);

  const fetchProjectDetails = async () => {
    try {
      const data = await apiFetch(`/projects/${projectId}`);
      setFormData({
        name: data.name,
        description: data.description || "",
        company_name: data.company_name || "",
        project_type: data.project_type || "Web",
        budget: data.budget || 0,
        duration_days: data.duration_days || 0,
        team_size: data.team_size || 0,
        team_experience_years: data.team_experience_years || 0.0,
        tech_stack: data.tech_stack || "",
        requirement_changes: data.requirement_changes || 0,
        sprint_delays: data.sprint_delays || 0,
        bug_count: data.bug_count || 0,
        testing_coverage: data.testing_coverage || 0.0,
        client_involvement: data.client_involvement || 3,
        resource_availability: data.resource_availability || 100.0,
        customer_satisfaction: data.customer_satisfaction || 3,
        project_complexity: data.project_complexity || 3
      });
    } catch (err: any) {
      setError("Failed to load project details.");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === "number" || name === "testing_coverage" || name === "resource_availability" || name === "team_experience_years"
        ? parseFloat(value) || 0
        : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await apiFetch(`/projects/${projectId}`, {
        method: "PUT",
        body: JSON.stringify(formData),
      });
      router.push("/projects");
    } catch (err: any) {
      setError(err.message || "Failed to update project");
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-2" />
        <p className="text-slate-500 text-xs font-mono">LOADING PROJECT CONFIGURATION...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back Header */}
      <div className="flex items-center gap-3">
        <Link 
          href="/projects" 
          className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={16} />
        </Link>
        <div>
          <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Directory Navigation</span>
          <h2 className="text-xl font-bold text-slate-100 mt-1">Edit Project Parameters</h2>
        </div>
      </div>

      {error && (
        <div className="bg-red-950/20 border border-red-500/30 p-3 rounded-lg text-xs text-red-400">
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Section 1: Metadata & Planning */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-blue-400 border-b border-slate-800 pb-2">
              Metadata & Resource Planning
            </h3>
            
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Project Name *</label>
              <input 
                type="text" 
                name="name" 
                required
                value={formData.name}
                onChange={handleChange}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Company / Client Name</label>
              <input 
                type="text" 
                name="company_name" 
                value={formData.company_name}
                onChange={handleChange}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Project Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={(event) => setFormData((previous) => ({ ...previous, description: event.target.value }))}
                rows={3}
                maxLength={5000}
                placeholder="Describe the project goals and scope"
                className="w-full resize-y bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Project Type</label>
                <select
                  name="project_type"
                  value={formData.project_type}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-300 focus:outline-none focus:border-blue-500 transition-colors"
                >
                  <option value="Web">Web App</option>
                  <option value="Mobile">Mobile App</option>
                  <option value="AI/ML">AI/ML Model</option>
                  <option value="Cloud">Cloud</option>
                  <option value="DevOps">DevOps</option>
                  <option value="Security">Security</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Budget ($ USD)</label>
                <input 
                  type="number" 
                  name="budget" 
                  min="0"
                  value={formData.budget}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Duration (Days)</label>
                <input 
                  type="number" 
                  name="duration_days" 
                  min="0"
                  value={formData.duration_days}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Team Size</label>
                <input 
                  type="number" 
                  name="team_size" 
                  min="0"
                  value={formData.team_size}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Avg Experience</label>
                <input 
                  type="number" 
                  name="team_experience_years" 
                  step="0.5"
                  min="0"
                  value={formData.team_experience_years}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Technology Stack (Comma separated)</label>
              <input 
                type="text" 
                name="tech_stack" 
                value={formData.tech_stack}
                onChange={handleChange}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          {/* Section 2: Execution Metrics & Risks */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-red-400 border-b border-slate-800 pb-2">
              Execution Risk Parameters
            </h3>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Sprint Delays</label>
                <input 
                  type="number" 
                  name="sprint_delays" 
                  min="0"
                  value={formData.sprint_delays}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-red-500/50 transition-colors"
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Bug Count</label>
                <input 
                  type="number" 
                  name="bug_count" 
                  min="0"
                  value={formData.bug_count}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-red-500/50 transition-colors"
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Scope Changes</label>
                <input 
                  type="number" 
                  name="requirement_changes" 
                  min="0"
                  value={formData.requirement_changes}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-200 focus:outline-none focus:border-red-500/50 transition-colors"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                <span>Code Testing Coverage</span>
                <span className="font-mono text-blue-400 font-bold">{formData.testing_coverage}%</span>
              </div>
              <input 
                type="range" 
                name="testing_coverage" 
                min="0" 
                max="100" 
                value={formData.testing_coverage}
                onChange={handleChange}
                className="w-full h-1 bg-slate-850 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                <span>Resource Availability</span>
                <span className="font-mono text-blue-400 font-bold">{formData.resource_availability}%</span>
              </div>
              <input 
                type="range" 
                name="resource_availability" 
                min="0" 
                max="100" 
                value={formData.resource_availability}
                onChange={handleChange}
                className="w-full h-1 bg-slate-850 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <div className="flex justify-between text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  <span>Client Involvement</span>
                  <span className="text-blue-400 font-bold">{formData.client_involvement}/5</span>
                </div>
                <input 
                  type="range" 
                  name="client_involvement" 
                  min="1" 
                  max="5" 
                  value={formData.client_involvement}
                  onChange={handleChange}
                  className="w-full h-1 bg-slate-850 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  <span>Customer Satisfaction</span>
                  <span className="text-blue-400 font-bold">{formData.customer_satisfaction}/5</span>
                </div>
                <input 
                  type="range" 
                  name="customer_satisfaction" 
                  min="1" 
                  max="5" 
                  value={formData.customer_satisfaction}
                  onChange={handleChange}
                  className="w-full h-1 bg-slate-850 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                <span>Project Complexity Index</span>
                <span className="text-blue-400 font-bold">{formData.project_complexity}/5</span>
              </div>
              <input 
                type="range" 
                name="project_complexity" 
                min="1" 
                max="5" 
                value={formData.project_complexity}
                onChange={handleChange}
                className="w-full h-1 bg-slate-850 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Link 
            href="/projects"
            className="px-4 py-2 border border-slate-800 hover:bg-slate-900 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
          >
            <Save size={14} />
            {submitting ? "Saving..." : "Evaluate & Update Project"}
          </button>
        </div>
      </form>
    </div>
  );
}
