'use client';

import { useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Loader, TrendingUp, Zap } from 'lucide-react';
import Navbar from '@/components/navbar';
import Sidebar from '@/components/sidebar';

interface SHAPContribution {
  feature_name: string;
  value: number;
  shap_value: number;
  direction: string;
  impact: string;
}

interface PredictionResult {
  prediction: string;
  success_probability: number;
  failure_probability: number;
  risk_score: number;
  risk_level: string;
  health_score: number;
  confidence_score: number;
  model_algorithm: string;
}

interface FullPredictionResult {
  baseline_prediction: PredictionResult;
  ml_prediction?: PredictionResult;
  shap_explanation?: {
    status: string;
    prediction_probability_success: number;
    top_positive_factors: SHAPContribution[];
    top_negative_factors: SHAPContribution[];
    summary: string;
  };
  prediction_method: string;
  recommended_prediction: PredictionResult;
}

export default function EnhancedPredictionsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<FullPredictionResult | null>(null);
  const [showShap, setShowShap] = useState(false);

  const [form, setForm] = useState({
    budget: 100000,
    duration_days: 120,
    team_size: 8,
    team_experience_years: 5,
    project_complexity: 3,
    requirement_changes: 2,
    sprint_delays: 1,
    bug_count: 15,
    testing_coverage: 80,
    client_involvement: 4,
    resource_availability: 85,
    customer_satisfaction: 4,
    project_type: 'Web',
  });

  const updateField = (field: string, value: string) => {
    setForm((prev) => ({
      ...prev,
      [field]: field === 'project_type' ? value : Number(value),
    }));
  };

  const handlePredict = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    setShowShap(false);

    try {
      const response = await fetch('/api/predictions/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Prediction failed');
      }

      const data: FullPredictionResult = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const PredictionCard = ({ title, pred, isRecommended = false }: any) => {
    if (!pred) return null;

    const isSuccess = pred.prediction === 'Success';

    return (
      <div className={`border-2 rounded-lg p-6 ${
        isRecommended
          ? 'border-blue-600 bg-blue-50'
          : 'border-gray-300 bg-white'
      }`}>
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          {isRecommended && (
            <span className="px-3 py-1 bg-blue-600 text-white text-xs font-semibold rounded-full">
              Recommended
            </span>
          )}
        </div>

        {/* Main Prediction */}
        <div className="mb-6 pb-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            {isSuccess ? (
              <CheckCircle className="w-8 h-8 text-green-600" />
            ) : (
              <XCircle className="w-8 h-8 text-red-600" />
            )}
            <div>
              <p className="text-2xl font-bold text-gray-900">{pred.prediction}</p>
              <p className="text-sm text-gray-600">
                {isSuccess ? 'Project likely to succeed' : 'Project at risk of failure'}
              </p>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-gray-600 text-sm">Success Probability</p>
            <p className="text-2xl font-bold text-green-600">
              {pred.success_probability.toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-gray-600 text-sm">Failure Probability</p>
            <p className="text-2xl font-bold text-red-600">
              {pred.failure_probability.toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-gray-600 text-sm">Health Score</p>
            <p className="text-2xl font-bold text-blue-600">
              {pred.health_score.toFixed(1)}
            </p>
          </div>
          <div>
            <p className="text-gray-600 text-sm">Risk Level</p>
            <p className={`text-xl font-bold ${
              pred.risk_level === 'Low' ? 'text-green-600' :
              pred.risk_level === 'Medium' ? 'text-yellow-600' :
              'text-red-600'
            }`}>
              {pred.risk_level}
            </p>
          </div>
        </div>

        <p className="text-xs text-gray-500 mt-4">
          Algorithm: {pred.model_algorithm}
        </p>
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar />
        
        <main className="flex-1 overflow-auto">
          <div className="max-w-6xl mx-auto p-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Project Predictions</h1>
            <p className="text-gray-600 mb-8">
              Get baseline and ML-powered success predictions with explainability
            </p>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Input Form */}
              <div className="lg:col-span-1">
                <div className="bg-white rounded-lg shadow-md p-6 sticky top-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">Project Metrics</h2>
                  
                  <div className="space-y-3">
                    {[
                      { key: 'budget', label: 'Budget ($)', min: 10000, max: 1000000 },
                      { key: 'duration_days', label: 'Duration (days)', min: 1, max: 365 },
                      { key: 'team_size', label: 'Team Size', min: 1, max: 50 },
                      { key: 'team_experience_years', label: 'Experience (years)', min: 0, max: 20 },
                      { key: 'project_complexity', label: 'Complexity (1-5)', min: 1, max: 5 },
                      { key: 'requirement_changes', label: 'Requirement Changes', min: 0, max: 20 },
                      { key: 'sprint_delays', label: 'Sprint Delays', min: 0, max: 20 },
                      { key: 'bug_count', label: 'Bug Count', min: 0, max: 200 },
                      { key: 'testing_coverage', label: 'Testing Coverage (%)', min: 0, max: 100 },
                      { key: 'client_involvement', label: 'Client Involvement (0-5)', min: 0, max: 5 },
                      { key: 'resource_availability', label: 'Resource Availability (%)', min: 0, max: 100 },
                      { key: 'customer_satisfaction', label: 'Satisfaction (0-5)', min: 0, max: 5 },
                    ].map((field) => (
                      <div key={field.key}>
                        <label className="block text-sm font-medium text-gray-700">
                          {field.label}
                        </label>
                        <input
                          type="number"
                          value={(form as any)[field.key]}
                          onChange={(e) => updateField(field.key, e.target.value)}
                          min={field.min}
                          max={field.max}
                          disabled={loading}
                          className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                        />
                      </div>
                    ))}

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Project Type</label>
                      <select
                        value={form.project_type}
                        onChange={(e) => updateField('project_type', e.target.value)}
                        disabled={loading}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                      >
                        <option>Web</option>
                        <option>Mobile</option>
                        <option>Desktop</option>
                        <option>Data Science</option>
                        <option>DevOps</option>
                      </select>
                    </div>
                  </div>

                  <button
                    onClick={handlePredict}
                    disabled={loading}
                    className="w-full mt-6 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader className="w-4 h-4 animate-spin" />
                        Predicting...
                      </>
                    ) : (
                      <>
                        <TrendingUp className="w-4 h-4" />
                        Get Predictions
                      </>
                    )}
                  </button>

                  {error && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
                      {error}
                    </div>
                  )}
                </div>
              </div>

              {/* Results */}
              <div className="lg:col-span-2 space-y-6">
                {result && (
                  <>
                    {/* Baseline */}
                    <PredictionCard
                      title="Baseline Prediction (IF-ELSE Algorithm)"
                      pred={result.baseline_prediction}
                    />

                    {/* ML */}
                    {result.ml_prediction && (
                      <PredictionCard
                        title="ML Prediction (XGBoost)"
                        pred={result.ml_prediction}
                      />
                    )}

                    {/* Recommended */}
                    <PredictionCard
                      title="Recommended Prediction"
                      pred={result.recommended_prediction}
                      isRecommended={true}
                    />

                    {/* SHAP Explanation */}
                    {result.shap_explanation && (
                      <div className="bg-white border-2 border-purple-300 rounded-lg p-6">
                        <button
                          onClick={() => setShowShap(!showShap)}
                          className="w-full flex items-center justify-between mb-4"
                        >
                          <div className="flex items-center gap-2">
                            <Zap className="w-5 h-5 text-purple-600" />
                            <h3 className="text-lg font-bold text-gray-900">SHAP Explanation</h3>
                          </div>
                          <span className="text-purple-600">{showShap ? '▼' : '▶'}</span>
                        </button>

                        {showShap && (
                          <>
                            <p className="text-gray-700 mb-4 italic">
                              "{result.shap_explanation.summary}"
                            </p>

                            {result.shap_explanation.top_positive_factors.length > 0 && (
                              <div className="mb-4">
                                <h4 className="font-semibold text-green-700 mb-2">✓ Positive Factors</h4>
                                <ul className="space-y-1">
                                  {result.shap_explanation.top_positive_factors.map((f) => (
                                    <li key={f.feature_name} className="text-sm text-green-700">
                                      • {f.feature_name}: {f.value.toFixed(2)}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {result.shap_explanation.top_negative_factors.length > 0 && (
                              <div>
                                <h4 className="font-semibold text-red-700 mb-2">✗ Negative Factors</h4>
                                <ul className="space-y-1">
                                  {result.shap_explanation.top_negative_factors.map((f) => (
                                    <li key={f.feature_name} className="text-sm text-red-700">
                                      • {f.feature_name}: {f.value.toFixed(2)}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}

                    {/* Info */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-sm text-blue-800">
                        <strong>Method Used:</strong> {result.prediction_method}
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
