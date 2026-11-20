"use client";

import React, { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { 
  Database, 
  Upload, 
  Cpu, 
  Check, 
  X, 
  AlertCircle, 
  CheckCircle,
  FileSpreadsheet,
  Award,
  Settings
} from "lucide-react";

interface Dataset {
  id: number;
  filename: string;
  row_count: number;
  features_json: string;
  uploaded_at: string;
}

interface ModelMetadata {
  id: number;
  model_name: string;
  algorithm: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  is_active: boolean;
}

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [models, setModels] = useState<ModelMetadata[]>([]);
  
  // Loading states
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [training, setTraining] = useState(false);
  const [activating, setActivating] = useState<number | null>(null);
  
  // Feedback messages
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const datasetList = await apiFetch("/datasets/");
      setDatasets(datasetList);
      if (datasetList.length > 0) {
        setSelectedDataset(datasetList[0]);
      }
      
      const modelList = await apiFetch("/models/compare");
      setModels(modelList);
    } catch {
      setDatasets([]);
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    
    setError("");
    setSuccess("");
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const data = await apiFetch("/datasets/upload", {
        method: "POST",
        body: formData,
      });
      setDatasets(prev => [data, ...prev]);
      setSelectedDataset(data);
      setSuccess(`Dataset '${file.name}' uploaded and parsed successfully!`);
    } catch (err: any) {
      setError(err.message || "Failed to upload dataset.");
    } finally {
      setUploading(false);
    }
  };

  const handleTrainModels = async () => {
    if (!selectedDataset) return;
    
    setError("");
    setSuccess("");
    setTraining(true);

    try {
      const data = await apiFetch(`/models/train/${selectedDataset.id}`, {
        method: "POST",
      });
      
      // Reload models comparison table
      const updatedModels = await apiFetch("/models/compare");
      setModels(updatedModels);
      
      setSuccess(`Successfully retrained all ML classifiers on '${selectedDataset.filename}'. Best model selected: ${data.best_model}`);
    } catch (err: any) {
      setError(err.message || "Failed to retrain models.");
    } finally {
      setTraining(false);
    }
  };

  const handleActivateModel = async (modelId: number) => {
    setError("");
    setSuccess("");
    setActivating(modelId);

    try {
      const data = await apiFetch(`/models/select/${modelId}`, {
        method: "POST",
      });
      
      setModels(prev => prev.map(m => m.id === modelId ? { ...m, is_active: true } : { ...m, is_active: false }));
      setSuccess(data.message);
    } catch (err: any) {
      setError(err.message || "Failed to activate model.");
    } finally {
      setActivating(null);
    }
  };

  // Helper to parse features JSON
  const getStats = (dataset: Dataset) => {
    try {
      return JSON.parse(dataset.features_json);
    } catch (e) {
      return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Alert feedbacks */}
      {error && (
        <div className="bg-red-950/20 border border-red-500/30 p-4 rounded-xl flex items-start gap-2.5 text-xs text-red-400">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="bg-emerald-950/20 border border-emerald-500/30 p-4 rounded-xl flex items-start gap-2.5 text-xs text-emerald-400">
          <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{success}</span>
        </div>
      )}

      {loading ? (
        <div className="h-96 flex flex-col items-center justify-center">
          <Database className="w-8 h-8 text-blue-500 animate-spin mb-2" />
          <p className="text-slate-500 text-xs font-mono">LOADING DATASET REGISTRY...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Column 1: Upload and Registry List */}
          <div className="space-y-6 lg:col-span-1">
            
            {/* Upload Box */}
            <div className="glass-panel p-6 rounded-xl border border-slate-800 flex flex-col items-center text-center">
              <Upload className="w-8 h-8 text-blue-500 mb-3" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Upload Dataset</h3>
              <p className="text-[11px] text-slate-500 mt-2 mb-4 leading-relaxed">
                Upload historical project metrics (CSV/Excel) containing columns: budget, bugs, sprint delays, and status (1=success, 0=fail).
              </p>
              
              <label className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded-lg py-2 text-xs font-bold transition-all cursor-pointer block text-center disabled:opacity-50">
                {uploading ? "Uploading File..." : "Select File"}
                <input 
                  type="file" 
                  accept=".csv,.xlsx,.xls" 
                  className="hidden" 
                  onChange={handleFileUpload}
                  disabled={uploading}
                />
              </label>
            </div>

            {/* Uploaded Datasets List */}
            <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Dataset Registry</h3>
              
              {datasets.length === 0 ? (
                <p className="text-xs text-slate-500 py-4 text-center">No datasets uploaded yet.</p>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {datasets.map(d => (
                    <button
                      key={d.id}
                      onClick={() => { setSelectedDataset(d); setError(""); setSuccess(""); }}
                      className={`w-full text-left p-3 rounded-lg border text-xs flex items-center gap-3 transition-colors ${
                        selectedDataset?.id === d.id
                          ? "bg-blue-600/10 border-blue-500/50 text-blue-300"
                          : "bg-slate-950/40 border-slate-800 text-slate-400 hover:bg-slate-900/30"
                      }`}
                    >
                      <FileSpreadsheet className="w-4 h-4 shrink-0" />
                      <div className="overflow-hidden flex-1">
                        <p className="font-semibold truncate text-slate-200">{d.filename}</p>
                        <p className="text-[10px] text-slate-500 mt-0.5 font-mono">{d.row_count} projects loaded</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Column 2 & 3: Detailed Inspection and Retraining */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Selected Dataset Details */}
            {selectedDataset && (
              <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Inspect Selection</span>
                    <h3 className="font-bold text-slate-200 text-sm mt-0.5">{selectedDataset.filename}</h3>
                  </div>
                  
                  {/* Train Button */}
                  {getStats(selectedDataset)?.is_trainable ? (
                    <button
                      onClick={handleTrainModels}
                      disabled={training}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                    >
                      <Cpu size={14} className={training ? "animate-spin" : ""} />
                      {training ? "Training Classifiers..." : "Train and Compare ML Models"}
                    </button>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-red-950/20 border border-red-500/20 text-red-400 text-xs rounded-lg font-semibold">
                      <X size={14} />
                      Validation Error: Missing target status column
                    </span>
                  )}
                </div>

                {/* Grid stats */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-900 text-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Total Row Count</span>
                    <span className="text-md font-bold text-slate-200 mt-1 block font-mono">{selectedDataset.row_count}</span>
                  </div>
                  <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-900 text-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Missing Values</span>
                    <span className="text-md font-bold text-slate-200 mt-1 block font-mono">
                      {getStats(selectedDataset)?.missing_total || 0}
                    </span>
                  </div>
                  <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-900 text-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Duplicate Rows</span>
                    <span className="text-md font-bold text-slate-200 mt-1 block font-mono">
                      {getStats(selectedDataset)?.duplicate_count || 0}
                    </span>
                  </div>
                  <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-900 text-center">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Feature Schema</span>
                    <span className="text-xs font-semibold text-emerald-400 mt-1.5 block">
                      {getStats(selectedDataset)?.is_trainable ? "Validated" : "Incomplete"}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Model Comparison Table */}
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Award size={16} className="text-purple-400" />
                  Model Performance Leaderboard
                </h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-500 font-semibold uppercase tracking-wider bg-slate-900/30">
                      <th className="p-3">Algorithm</th>
                      <th className="p-3">Accuracy</th>
                      <th className="p-3">Precision</th>
                      <th className="p-3">Recall</th>
                      <th className="p-3">F1-Score</th>
                      <th className="p-3">ROC-AUC</th>
                      <th className="p-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {models.map(model => (
                      <tr key={model.id} className="text-slate-300 hover:bg-slate-900/20 transition-colors">
                        <td className="p-3 font-semibold text-slate-200 flex items-center gap-1.5">
                          <Settings size={14} className="text-slate-500" />
                          {model.algorithm}
                        </td>
                        <td className="p-3 font-mono font-bold">{(model.accuracy * 100).toFixed(1)}%</td>
                        <td className="p-3 font-mono">{(model.precision * 100).toFixed(1)}%</td>
                        <td className="p-3 font-mono">{(model.recall * 100).toFixed(1)}%</td>
                        <td className="p-3 font-mono">{(model.f1_score * 100).toFixed(1)}%</td>
                        <td className="p-3 font-mono text-purple-400">{(model.roc_auc * 100).toFixed(1)}%</td>
                        <td className="p-3">
                          <div className="flex justify-center">
                            {model.is_active ? (
                              <span className="px-2 py-0.5 bg-emerald-950/40 text-emerald-400 border border-emerald-500/20 rounded-sm font-bold text-[9px]">
                                Active Classifier
                              </span>
                            ) : (
                              <button
                                onClick={() => handleActivateModel(model.id)}
                                disabled={activating !== null}
                                className="px-2 py-0.5 bg-slate-800 hover:bg-blue-600 hover:text-white rounded-sm text-[9px] font-bold transition-colors cursor-pointer disabled:opacity-50"
                              >
                                {activating === model.id ? "Activating..." : "Activate"}
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {models.length === 0 && (
                      <tr>
                        <td colSpan={7} className="py-6 text-center text-slate-500">
                          No models trained yet. Select a dataset and click retrain models.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
