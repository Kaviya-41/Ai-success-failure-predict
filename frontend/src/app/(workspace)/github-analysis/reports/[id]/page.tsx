"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader } from "lucide-react";

import { apiFetch } from "@/lib/api";

interface SavedReport {
  report_id: number;
  created_at: string;
  repository_url: string;
  repository: {
    repository_name: string;
    owner: string;
    primary_language: string;
    last_updated_at: string;
    stars: number;
    forks: number;
  };
  metrics: Record<string, unknown>;
  prediction: string;
  health_score: number;
  risk_score: number;
  risk_level: string;
  success_probability: number;
  failure_probability: number;
  positive_factors: string[];
  risk_factors: string[];
  recommendations: string[];
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function PreviousGitHubReportPage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const [report, setReport] = useState<SavedReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch(`/github/reports/${id}`)
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : "The saved report could not be loaded."));
  }, [id]);

  if (error) {
    return (
      <div className="space-y-4">
        <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</p>
        <Link href="/dashboard" className="text-sm font-medium text-blue-700 hover:underline">Return to dashboard</Link>
      </div>
    );
  }

  if (!report) {
    return <div className="flex items-center gap-2 text-sm text-slate-600"><Loader className="h-4 w-4 animate-spin" /> Loading saved report...</div>;
  }

  const displayMetrics: Array<[string, unknown]> = [
    ["Repository Health", report.health_score],
    ["Risk Score", report.risk_score],
    ["Code Quality", report.metrics.code_quality],
    ["Documentation", report.metrics.documentation],
    ["Testing and CI", report.metrics.testing_ci],
    ["Dependency Risk", report.metrics.dependency_risk],
    ["Commits", report.metrics.commits],
    ["Contributors", report.metrics.contributors],
    ["Source Files", report.metrics.source_files],
    ["Test Files", report.metrics.test_files],
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex items-center gap-3">
        <button type="button" onClick={() => router.back()} aria-label="Go back" className="rounded-lg border border-slate-200 p-2 text-slate-700 hover:bg-slate-50">
          <ArrowLeft size={18} />
        </button>
        <div>
          <p className="section-label">Saved repository report</p>
          <h1 className="text-2xl font-bold text-slate-900">{report.repository.repository_name}</h1>
        </div>
      </div>

      <section className="surface-panel p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-slate-500">{new Date(report.created_at).toLocaleString()}</p>
            <a href={report.repository_url} target="_blank" rel="noreferrer" className="mt-1 inline-block break-all text-sm text-blue-700 hover:underline">{report.repository_url}</a>
          </div>
          <div className="text-left sm:text-right">
            <p className="text-sm font-semibold text-slate-500">Prediction</p>
            <p className={`text-2xl font-bold ${report.prediction.toUpperCase() === "SUCCESS" ? "text-emerald-700" : "text-red-700"}`}>{report.prediction}</p>
            <p className="text-sm text-slate-600">{report.risk_level} risk</p>
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <p className="rounded-lg bg-slate-50 p-3 text-sm">Health: <strong>{report.health_score.toFixed(1)}/100</strong></p>
          <p className="rounded-lg bg-slate-50 p-3 text-sm">Risk: <strong>{report.risk_score.toFixed(1)}/100</strong></p>
          <p className="rounded-lg bg-slate-50 p-3 text-sm">Success probability: <strong>{report.success_probability.toFixed(1)}%</strong></p>
          <p className="rounded-lg bg-slate-50 p-3 text-sm">Failure probability: <strong>{report.failure_probability.toFixed(1)}%</strong></p>
        </div>
      </section>

      <section className="surface-panel p-6">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Saved repository indicators</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {displayMetrics.map(([label, value]) => (
            <div key={String(label)} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs text-slate-500">{label}</p>
              <p className="mt-1 font-semibold text-slate-900">{typeof value === "number" ? value.toFixed(1) : String(value ?? "N/A")}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-3">
        {[
          { title: "Strengths", items: report.positive_factors },
          { title: "Weaknesses", items: report.risk_factors },
          { title: "Recommendations", items: report.recommendations },
        ].map((section) => (
          <section key={section.title} className="surface-panel p-6">
            <h2 className="mb-4 text-lg font-semibold text-slate-900">{section.title}</h2>
            <ul className="space-y-2 text-sm text-slate-700">
              {section.items.map((item) => <li key={item} className="rounded-lg bg-slate-50 p-3">{item}</li>)}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
