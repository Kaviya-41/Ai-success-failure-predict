'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Loader, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';
import Navbar from '@/components/navbar';
import Sidebar from '@/components/sidebar';

interface TrainingResult {
  status: string;
  model_name?: string;
  message?: string;
  metrics?: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    roc_auc: number;
  };
  top_features?: Record<string, number>;
  training_duration_seconds?: number;
}

export default function TrainModelPage() {
  const searchParams = useSearchParams();
  const datasetId = searchParams.get('dataset_id');
  
  const [modelName, setModelName] = useState('xgboost_v1');
  const [training, setTraining] = useState(false);
  const [result, setResult] = useState<TrainingResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTrain = async () => {
    if (!datasetId) {
      setError('Dataset ID is required');
      return;
    }

    setTraining(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`/api/models/train-xgboost/${datasetId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ model_name: modelName }),
      });

      const data: TrainingResult = await response.json();

      if (!response.ok) {
        setError(data.message || 'Training failed');
      } else {
        setResult(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Training failed');
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar />
        
        <main className="flex-1 overflow-auto">
          <div className="max-w-4xl mx-auto p-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">Train XGBoost Model</h1>

            {/* Training Form */}
            <div className="bg-white rounded-lg shadow-md p-8 mb-8">
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model Name
                </label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  disabled={training}
                  placeholder="e.g., xgboost_v1"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Unique identifier for this trained model
                </p>
              </div>

              <button
                onClick={handleTrain}
                disabled={training || !datasetId}
                className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {training ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Training Model... This may take a minute
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-5 h-5" />
                    Start Training
                  </>
                )}
              </button>

              {error && (
                <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                  <p className="text-red-800">{error}</p>
                </div>
              )}
            </div>

            {/* Results */}
            {result && (
              <div className="bg-white rounded-lg shadow-md p-8">
                <div className="flex gap-3 mb-6">
                  <CheckCircle className="w-6 h-6 text-green-600 shrink-0" />
                  <div>
                    <h2 className="text-xl font-bold text-green-900">Training Complete! 🎉</h2>
                    <p className="text-green-700">{result.message}</p>
                  </div>
                </div>

                {result.metrics && (
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-gray-600 text-sm">Accuracy</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {(result.metrics.accuracy * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-gray-600 text-sm">Precision</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {(result.metrics.precision * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-gray-600 text-sm">Recall</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {(result.metrics.recall * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-gray-600 text-sm">F1 Score</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {(result.metrics.f1_score * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-gray-600 text-sm">ROC AUC</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {(result.metrics.roc_auc * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-gray-600 text-sm">Training Time</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {result.training_duration_seconds?.toFixed(1)}s
                      </p>
                    </div>
                  </div>
                )}

                {result.top_features && Object.keys(result.top_features).length > 0 && (
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-4">Top Features</h3>
                    <div className="space-y-2">
                      {Object.entries(result.top_features).map(([feature, importance], idx) => (
                        <div key={feature} className="flex items-center gap-4">
                          <span className="text-sm font-medium text-gray-600 w-32">{feature}</span>
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${Math.min(importance as number * 100, 100)}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-600 w-12 text-right">
                            {((importance as number) * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
