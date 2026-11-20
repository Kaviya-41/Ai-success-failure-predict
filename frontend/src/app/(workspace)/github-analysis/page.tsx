'use client';

import { useCallback, useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, GitBranch, Loader, ShieldAlert, TrendingUp, FileText, RefreshCw, Clock3, Eye } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface RepositorySummary {
  repository_name: string;
  owner: string;
  description: string;
  primary_language: string;
  created_at: string;
  last_updated_at: string;
  stars: number;
  forks: number;
  open_issues: number;
  watchers: number;
  private: boolean;
}

interface AnalysisResult {
  report_id?: number;
  created_at?: string;
  status: string;
  message?: string;
  repository?: RepositorySummary;
  metrics?: Record<string, unknown>;
  prediction?: string;
  success_probability?: number;
  failure_probability?: number;
  risk_score?: number;
  health_score?: number;
  risk_level?: string;
  risk_factors?: string[];
  positive_factors?: string[];
  recommendations?: string[];
  recovery_plan?: string[];
  motivation?: string;
}

interface SavedReportSummary {
  id: number;
  repository_url: string;
  repository_name: string;
  prediction: string;
  health_score: number;
  risk_score: number;
  risk_level: string;
  created_at: string;
}

const statusToneClass: Record<string, string> = {
  SUCCESS: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  FAILURE: 'bg-red-100 text-red-800 border-red-200',
  LOW: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  MEDIUM: 'bg-amber-100 text-amber-800 border-amber-200',
  HIGH: 'bg-red-100 text-red-800 border-red-200',
};

export default function GitHubAnalysisPage() {
  const [repositoryUrl, setRepositoryUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [savedReports, setSavedReports] = useState<SavedReportSummary[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [loadingReportId, setLoadingReportId] = useState<number | null>(null);

  const refreshReports = useCallback(async () => {
    const data = await apiFetch('/github/reports');
    setSavedReports(Array.isArray(data.reports) ? data.reports : []);
  }, []);

  useEffect(() => {
    refreshReports()
      .catch((err) => {
        setHistoryError(err instanceof Error ? err.message : 'Saved reports could not be loaded.');
      })
      .finally(() => setReportsLoading(false));
  }, [refreshReports]);

  const handleAnalyze = async () => {
    const trimmedUrl = repositoryUrl.trim();

    if (!trimmedUrl) {
      setError('Please enter a valid GitHub repository URL.');
      return;
    }

    let parsedUrl: URL;
    try {
      parsedUrl = new URL(trimmedUrl);
    } catch {
      setError('Enter a full URL such as https://github.com/owner/repository.');
      return;
    }

    const repositoryPath = parsedUrl.pathname.match(/^\/[A-Za-z0-9][A-Za-z0-9-]{0,38}\/[A-Za-z0-9._-]{1,100}(?:\.git)?\/?$/);
    if (
      !['http:', 'https:'].includes(parsedUrl.protocol)
      || parsedUrl.hostname !== 'github.com'
      || parsedUrl.username
      || parsedUrl.password
      || parsedUrl.port
      || parsedUrl.search
      || parsedUrl.hash
      || !repositoryPath
    ) {
      setError('Please enter a valid GitHub repository URL.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await apiFetch('/github/analyze', {
        method: 'POST',
        body: JSON.stringify({ repository_url: trimmedUrl }),
      });

      setResult(data);
      setError(null);
      setHistoryError(null);
      refreshReports().catch((err) => {
        setHistoryError(err instanceof Error ? err.message : 'Saved reports could not be refreshed.');
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Repository analysis could not be completed. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewReport = async (reportId: number) => {
    setLoadingReportId(reportId);
    setHistoryError(null);
    try {
      const report = await apiFetch(`/github/reports/${reportId}`);
      setResult(report);
      setRepositoryUrl(report.repository?.repository_name
        ? `https://github.com/${report.repository.repository_name}`
        : '');
      setError(null);
    } catch (err) {
      setHistoryError(err instanceof Error ? err.message : 'The saved report could not be opened.');
    } finally {
      setLoadingReportId(null);
    }
  };

  const prediction = result?.prediction?.toUpperCase() || 'UNKNOWN';
  const riskLevel = result?.risk_level || 'Unknown';

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <p className="section-label">Project intelligence</p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">GitHub Project Analysis</h1>
        <p className="max-w-3xl text-sm text-slate-600">
        Analyse a GitHub repository directly. Activity, code-structure, documentation, testing, and dependency indicators are evaluated using the existing IF–ELSE prediction engine.
        </p>
      </div>

      <div className="surface-panel p-6">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
            <GitBranch className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Repository input</h2>
            <p className="text-sm text-slate-600">Enter a public GitHub repository URL. No manual project details are required.</p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-[1fr_auto]">
          <div>
            <label htmlFor="repository-url" className="mb-2 block text-sm font-medium text-slate-700">GitHub Repository URL</label>
            <input
              id="repository-url"
              type="url"
              autoComplete="url"
              value={repositoryUrl}
              onChange={(event) => setRepositoryUrl(event.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAnalyze();
              }}
              placeholder="https://github.com/owner/repository"
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none ring-0 transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {loading ? <Loader className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {loading ? 'Analysing repository...' : 'Analyse Repository'}
          </button>
        </div>

        {error && (
          <div className="mt-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      <section className="surface-panel p-6" aria-labelledby="saved-reports-heading">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Clock3 className="h-5 w-5 text-blue-600" />
            <h2 id="saved-reports-heading" className="text-lg font-semibold text-slate-900">Saved analysis reports</h2>
          </div>
          <span className="text-xs text-slate-500">Reports are saved automatically after analysis.</span>
        </div>
        {historyError && (
          <p role="alert" className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">{historyError}</p>
        )}
        {reportsLoading ? (
          <p className="text-sm text-slate-500">Loading saved reports...</p>
        ) : savedReports.length ? (
          <ul className="divide-y divide-slate-200">
            {savedReports.map((report) => (
              <li key={report.id} className="flex flex-col gap-3 py-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-medium text-slate-900">{report.repository_name}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {report.prediction} · {report.risk_level} risk · {new Date(report.created_at).toLocaleString()}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleViewReport(report.id)}
                  disabled={loadingReportId === report.id}
                  className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                >
                  {loadingReportId === report.id ? <Loader className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />}
                  View report
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">No saved reports yet. Analyse a repository to create one.</p>
        )}
      </section>

      {result && result.status === 'success' && (
        <>
          {result.report_id && (
            <p className="text-sm text-emerald-700">
              Report #{result.report_id} saved{result.created_at ? ` on ${new Date(result.created_at).toLocaleString()}` : ''}.
            </p>
          )}
          <div className="surface-panel overflow-hidden">
            <div className={`border-b px-6 py-4 ${statusToneClass[prediction]}`}>
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-3">
                  {prediction === 'SUCCESS' ? <CheckCircle className="h-6 w-6" /> : <ShieldAlert className="h-6 w-6" />}
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em]">Project prediction</p>
                    <h2 className="text-2xl font-bold">{prediction}</h2>
                  </div>
                </div>
                <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold ${statusToneClass[prediction]}`}>
                  {prediction} · Risk {riskLevel}
                </span>
              </div>
            </div>

            <div className="grid gap-4 p-6 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Success probability</p>
                <p className="mt-3 text-2xl font-bold text-slate-900">{result.success_probability ?? 0}%</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Failure probability</p>
                <p className="mt-3 text-2xl font-bold text-slate-900">{result.failure_probability ?? 0}%</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Risk score</p>
                <p className="mt-3 text-2xl font-bold text-slate-900">{result.risk_score ?? 0}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Health score</p>
                <p className="mt-3 text-2xl font-bold text-slate-900">{result.health_score ?? 0}</p>
              </div>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
            <div className="space-y-6">
              <div className="surface-panel p-6">
                <div className="mb-4 flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-blue-600" />
                  <h3 className="text-lg font-semibold text-slate-900">Risk analysis</h3>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    { label: 'Development Activity', value: Number(result.metrics?.activity_score ?? 0), higherIsBetter: true },
                    { label: 'Issue Management', value: Number(result.metrics?.issue_resolution ?? 0), higherIsBetter: true },
                    { label: 'Contributor Activity', value: Number(result.metrics?.contributor_activity ?? 0), higherIsBetter: true },
                    { label: 'Repository Maintenance', value: Number(result.metrics?.maintenance ?? 0), higherIsBetter: true },
                    { label: 'Documentation', value: Number(result.metrics?.documentation ?? 0), higherIsBetter: true },
                    { label: 'Testing and CI', value: Number(result.metrics?.testing_ci ?? 0), higherIsBetter: true },
                    { label: 'Code Structure', value: Number(result.metrics?.code_quality ?? 0), higherIsBetter: true },
                    { label: 'Dependency Risk', value: Number(result.metrics?.dependency_risk ?? 0), higherIsBetter: false },
                  ].map((metric) => {
                    const score = metric.higherIsBetter ? metric.value : 100 - metric.value;
                    const label = score >= 60 ? 'Healthy' : score >= 40 ? 'Moderate' : 'At risk';
                    const tone = score >= 60 ? 'SUCCESS' : score >= 40 ? 'MEDIUM' : 'FAILURE';
                    return (
                      <div key={metric.label} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-sm text-slate-600">{metric.label}</span>
                          <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${statusToneClass[tone]}`}>
                            {label}
                          </span>
                        </div>
                        <p className="mt-2 text-2xl font-bold text-slate-900">{metric.value.toFixed(0)}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="surface-panel p-6">
                  <div className="mb-4 flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-emerald-600" />
                    <h3 className="text-lg font-semibold text-slate-900">Strengths</h3>
                  </div>
                  <ul className="space-y-3">
                    {(result.positive_factors ?? []).map((item) => (
                      <li key={item} className="flex gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                        <span className="mt-1 h-2.5 w-2.5 rounded-full bg-emerald-500" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="surface-panel p-6">
                  <div className="mb-4 flex items-center gap-2">
                    <ShieldAlert className="h-5 w-5 text-red-600" />
                    <h3 className="text-lg font-semibold text-slate-900">Weaknesses and risks</h3>
                  </div>
                  <ul className="space-y-3">
                    {(result.risk_factors ?? []).map((item) => (
                      <li key={item} className="flex gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                        <span className="mt-1 h-2.5 w-2.5 rounded-full bg-red-500" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="surface-panel p-6">
                <div className="mb-4 flex items-center gap-2">
                  <RefreshCw className="h-5 w-5 text-blue-600" />
                  <h3 className="text-lg font-semibold text-slate-900">{prediction === 'SUCCESS' ? 'Keep it going' : 'Recommended actions'}</h3>
                </div>
                <ul className="space-y-3">
                  {(result.recommendations ?? []).map((item) => (
                    <li key={item} className="flex gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                      <span className="mt-1 h-2.5 w-2.5 rounded-full bg-blue-500" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="space-y-6">
              <div className="surface-panel p-6">
                <h3 className="mb-4 text-lg font-semibold text-slate-900">Repository summary</h3>
                <div className="space-y-3 text-sm text-slate-700">
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Repository</span><strong className="text-right text-slate-900">{result.repository?.repository_name || 'N/A'}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Owner</span><strong className="text-right text-slate-900">{result.repository?.owner || 'N/A'}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Primary language</span><strong className="text-right text-slate-900">{result.repository?.primary_language || 'Unknown'}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Contributors</span><strong className="text-right text-slate-900">{String(result.metrics?.contributors ?? 0)}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Commits (total)</span><strong className="text-right text-slate-900">{String(result.metrics?.commits ?? 0)}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Recent commits (30 days, max 100)</span><strong className="text-right text-slate-900">{String(result.metrics?.recent_commits_30d ?? 0)}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Open issues</span><strong className="text-right text-slate-900">{String(result.metrics?.open_issues ?? 0)}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Closed issues</span><strong className="text-right text-slate-900">{String(result.metrics?.closed_issues ?? 0)}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Pull requests</span><strong className="text-right text-slate-900">{Number(result.metrics?.open_pull_requests ?? 0) + Number(result.metrics?.closed_pull_requests ?? 0)}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Source / test files</span><strong className="text-right text-slate-900">{String(result.metrics?.source_files ?? 0)} / {String(result.metrics?.test_files ?? 0)}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Dependency files</span><strong className="text-right text-slate-900">{Array.isArray(result.metrics?.dependency_files) ? result.metrics.dependency_files.length : 0}</strong></div>
                  <div className="flex justify-between gap-4 border-b border-slate-200 pb-2"><span>Recent activity score</span><strong className="text-right text-slate-900">{String(result.metrics?.recent_activity ?? 0)}</strong></div>
                  <div className="flex justify-between gap-4 pb-2"><span>Last updated</span><strong className="text-right text-slate-900">{result.repository?.last_updated_at ? new Date(result.repository.last_updated_at).toLocaleDateString() : 'N/A'}</strong></div>
                  {typeof result.metrics?.languages === 'object' && result.metrics.languages !== null && !Array.isArray(result.metrics.languages) && (
                    <div className="border-t border-slate-200 pt-3">
                      <p className="mb-2 font-medium text-slate-800">Languages (bytes)</p>
                      <ul className="space-y-1">
                        {Object.entries(result.metrics.languages as Record<string, number>).map(([language, bytes]) => (
                          <li key={language} className="flex justify-between gap-4 text-xs">
                            <span>{language}</span><strong>{Number(bytes).toLocaleString()}</strong>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {Array.isArray(result.metrics?.analysis_limits) && (
                <div className="surface-panel p-6">
                  <h3 className="mb-3 text-sm font-semibold text-slate-900">Analysis coverage and limitations</h3>
                  <ul className="space-y-2 text-xs text-slate-600">
                    {(result.metrics.analysis_limits as string[]).map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </div>
              )}

              {prediction === 'SUCCESS' && result.motivation && (
                <div className="surface-panel border-emerald-200 bg-emerald-50 p-6">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
                    <p className="text-sm text-emerald-800">{result.motivation}</p>
                  </div>
                </div>
              )}

              {prediction === 'FAILURE' && result.recovery_plan && result.recovery_plan.length > 0 && (
                <div className="surface-panel border-red-200 bg-red-50 p-6">
                  <div className="mb-4 flex items-center gap-2 text-red-800">
                    <AlertCircle className="h-5 w-5" />
                    <h3 className="text-lg font-semibold">Project recovery plan</h3>
                  </div>
                  <ul className="space-y-3 text-sm text-red-800">
                    {result.recovery_plan.map((step) => (
                      <li key={step} className="rounded-xl border border-red-200 bg-white p-3">{step}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
