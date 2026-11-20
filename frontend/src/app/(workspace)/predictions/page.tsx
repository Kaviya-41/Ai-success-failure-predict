"use client";

import React, { useState } from "react";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Activity,
  BrainCircuit,
  Loader2,
} from "lucide-react";

import { runPrediction } from "@/lib/api";


type PredictionResult = {
  is_successful_prediction: boolean;

  success_probability: number;

  failure_probability: number;

  risk_score: number;

  risk_level: string;

  health_score: number;

  confidence_score: number;

  prediction_time_ms: number;

  model_algorithm: string;

  prediction: string;

  top_risk_factors: string[];

  top_success_factors: string[];

  recommendations: string[];

  success_conditions: number;

  failure_conditions: number;

  total_conditions: number;

  project_type: string;
};


export default function PredictionsPage() {

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [result, setResult] =
    useState<PredictionResult | null>(null);


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

    project_type: "Web",
  });


  function updateField(
    field: string,
    value: string
  ) {

    setForm((previous) => ({
      ...previous,

      [field]:
        field === "project_type"
          ? value
          : Number(value),
    }));
  }


  async function handlePrediction() {

    setLoading(true);

    setError("");

    setResult(null);

    try {

      const data =
        await runPrediction(form);

      setResult(data);

    } catch (err: any) {

      setError(
        err?.message ||
        "Prediction failed."
      );

    } finally {

      setLoading(false);
    }
  }


  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">

      <div className="max-w-6xl mx-auto">

        {/* Header */}

        <div className="mb-8">

          <div className="flex items-center gap-3">

            <BrainCircuit
              className="text-blue-500"
              size={32}
            />

            <div>

              <h1 className="text-3xl font-bold">
                AI Predictions
              </h1>

              <p className="text-slate-400 mt-1">
                Success / Failure Decision Analysis
              </p>

            </div>

          </div>

        </div>


        {/* Algorithm information */}

        <div className="mb-6 rounded-xl border border-blue-500/20 bg-blue-500/5 p-5">

          <div className="flex gap-3">

            <Activity
              className="text-blue-400 mt-1"
              size={22}
            />

            <div>

              <h2 className="font-semibold text-blue-300">
                Algorithm
              </h2>

              <p className="text-sm text-slate-400 mt-1">
                The system reads the project
                conditions and uses an IF-ELSE
                decision rule to classify the
                project as Success or Failure.
              </p>

            </div>

          </div>

        </div>


        {/* Input form */}

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">

          <h2 className="text-xl font-bold mb-6">
            Project Information
          </h2>


          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">


            {/* Budget */}

            <InputField
              label="Budget"
              value={form.budget}
              onChange={(v) =>
                updateField("budget", v)
              }
            />


            {/* Duration */}

            <InputField
              label="Duration (Days)"
              value={form.duration_days}
              onChange={(v) =>
                updateField(
                  "duration_days",
                  v
                )
              }
            />


            {/* Team */}

            <InputField
              label="Team Size"
              value={form.team_size}
              onChange={(v) =>
                updateField(
                  "team_size",
                  v
                )
              }
            />


            <InputField
              label="Team Experience (Years)"
              value={
                form.team_experience_years
              }
              onChange={(v) =>
                updateField(
                  "team_experience_years",
                  v
                )
              }
            />


            <InputField
              label="Project Complexity (1-5)"
              value={
                form.project_complexity
              }
              onChange={(v) =>
                updateField(
                  "project_complexity",
                  v
                )
              }
            />


            <InputField
              label="Requirement Changes"
              value={
                form.requirement_changes
              }
              onChange={(v) =>
                updateField(
                  "requirement_changes",
                  v
                )
              }
            />


            <InputField
              label="Sprint Delays"
              value={
                form.sprint_delays
              }
              onChange={(v) =>
                updateField(
                  "sprint_delays",
                  v
                )
              }
            />


            <InputField
              label="Bug Count"
              value={form.bug_count}
              onChange={(v) =>
                updateField(
                  "bug_count",
                  v
                )
              }
            />


            <InputField
              label="Testing Coverage (%)"
              value={
                form.testing_coverage
              }
              onChange={(v) =>
                updateField(
                  "testing_coverage",
                  v
                )
              }
            />


            <InputField
              label="Client Involvement (1-5)"
              value={
                form.client_involvement
              }
              onChange={(v) =>
                updateField(
                  "client_involvement",
                  v
                )
              }
            />


            <InputField
              label="Resource Availability (%)"
              value={
                form.resource_availability
              }
              onChange={(v) =>
                updateField(
                  "resource_availability",
                  v
                )
              }
            />


            <InputField
              label="Customer Satisfaction (1-5)"
              value={
                form.customer_satisfaction
              }
              onChange={(v) =>
                updateField(
                  "customer_satisfaction",
                  v
                )
              }
            />


            {/* Project Type */}

            <div>

              <label className="block text-sm text-slate-400 mb-2">
                Project Type
              </label>

              <select
                value={form.project_type}
                onChange={(e) =>
                  updateField(
                    "project_type",
                    e.target.value
                  )
                }
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white outline-none focus:border-blue-500"
              >

                <option value="Web">
                  Web
                </option>

                <option value="Mobile">
                  Mobile
                </option>

                <option value="AI/ML">
                  AI/ML
                </option>

                <option value="Cloud">
                  Cloud
                </option>

                <option value="DevOps">
                  DevOps
                </option>

                <option value="Security">
                  Security
                </option>

              </select>

            </div>

          </div>


          {/* Button */}

          <button
            onClick={handlePrediction}
            disabled={loading}
            className="mt-8 w-full rounded-lg bg-blue-600 px-5 py-3 font-semibold hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >

            {loading ? (

              <span className="flex items-center justify-center gap-2">

                <Loader2
                  className="animate-spin"
                  size={18}
                />

                Checking Project...

              </span>

            ) : (

              "Run Success / Failure Analysis"

            )}

          </button>


          {/* Error */}

          {error && (

            <div className="mt-5 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-300">

              {error}

            </div>

          )}

        </div>


        {/* Result */}

        {result && (

          <div className="mt-8 space-y-6">


            {/* Main result */}

            <div
              className={`rounded-2xl border p-8 text-center ${
                result.is_successful_prediction
                  ? "border-emerald-500/30 bg-emerald-500/10"
                  : "border-red-500/30 bg-red-500/10"
              }`}
            >

              {result.is_successful_prediction ? (

                <CheckCircle
                  className="mx-auto text-emerald-400"
                  size={64}
                />

              ) : (

                <XCircle
                  className="mx-auto text-red-400"
                  size={64}
                />

              )}


              <h2 className="mt-4 text-4xl font-bold">

                {result.prediction}

              </h2>


              <p className="mt-2 text-slate-400">

                Based on the predefined
                Success/Failure conditions

              </p>

            </div>


            {/* Statistics */}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">


              <ResultCard
                title="Success"
                value={`${result.success_probability}%`}
              />


              <ResultCard
                title="Failure"
                value={`${result.failure_probability}%`}
              />


              <ResultCard
                title="Risk Score"
                value={`${result.risk_score}%`}
              />


              <ResultCard
                title="Health Score"
                value={`${result.health_score}%`}
              />

            </div>


            {/* Conditions */}

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">

              <h2 className="text-xl font-bold mb-5">
                Decision Conditions
              </h2>


              <div className="grid grid-cols-3 gap-4 text-center">

                <div>

                  <div className="text-3xl font-bold text-emerald-400">
                    {result.success_conditions}
                  </div>

                  <div className="text-sm text-slate-400">
                    Success Conditions
                  </div>

                </div>


                <div>

                  <div className="text-3xl font-bold text-red-400">
                    {result.failure_conditions}
                  </div>

                  <div className="text-sm text-slate-400">
                    Failure Conditions
                  </div>

                </div>


                <div>

                  <div className="text-3xl font-bold text-blue-400">
                    {result.total_conditions}
                  </div>

                  <div className="text-sm text-slate-400">
                    Total Conditions
                  </div>

                </div>

              </div>

            </div>


            {/* Risk factors */}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">


              <div className="rounded-2xl border border-red-500/20 bg-slate-900/60 p-6">

                <h2 className="font-bold text-red-300 flex items-center gap-2">

                  <AlertTriangle size={18} />

                  Risk Factors

                </h2>


                <ul className="mt-4 space-y-2">

                  {result.top_risk_factors.length > 0 ? (

                    result.top_risk_factors.map(
                      (factor, index) => (

                        <li
                          key={index}
                          className="text-sm text-slate-300"
                        >
                          • {factor}
                        </li>

                      )
                    )

                  ) : (

                    <li className="text-sm text-slate-500">
                      No major risk factors.
                    </li>

                  )}

                </ul>

              </div>


              <div className="rounded-2xl border border-emerald-500/20 bg-slate-900/60 p-6">

                <h2 className="font-bold text-emerald-300 flex items-center gap-2">

                  <CheckCircle size={18} />

                  Success Factors

                </h2>


                <ul className="mt-4 space-y-2">

                  {result.top_success_factors.length > 0 ? (

                    result.top_success_factors.map(
                      (factor, index) => (

                        <li
                          key={index}
                          className="text-sm text-slate-300"
                        >
                          • {factor}
                        </li>

                      )
                    )

                  ) : (

                    <li className="text-sm text-slate-500">
                      No major success factors.
                    </li>

                  )}

                </ul>

              </div>

            </div>


            {/* Recommendations */}

            <div className="rounded-2xl border border-blue-500/20 bg-slate-900/60 p-6">

              <h2 className="text-xl font-bold">
                Recommendations
              </h2>


              <ul className="mt-4 space-y-3">

                {result.recommendations.map(
                  (recommendation, index) => (

                    <li
                      key={index}
                      className="text-sm text-slate-300"
                    >

                      <span className="text-blue-400 mr-2">
                        {index + 1}.
                      </span>

                      {recommendation}

                    </li>

                  )
                )}

              </ul>

            </div>


            {/* Algorithm */}

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6">

              <h2 className="text-lg font-bold mb-4">
                Algorithm Used
              </h2>

              <pre className="overflow-x-auto rounded-lg bg-slate-900 p-5 text-sm text-slate-300">

{`BEGIN

    Read project conditions

    IF success conditions >=
       failure conditions THEN

        Print "SUCCESS"

    ELSE

        Print "FAILURE"

    ENDIF

END`}

              </pre>

              <p className="mt-4 text-xs text-slate-500">

                Algorithm:
                Success/Failure IF-ELSE
                Decision-Making Algorithm

              </p>

            </div>


          </div>

        )}

      </div>

    </div>
  );
}


/* ---------------------------------------------------------
   Input component
--------------------------------------------------------- */

function InputField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: string) => void;
}) {

  return (

    <div>

      <label className="block text-sm text-slate-400 mb-2">
        {label}
      </label>

      <input
        type="number"
        value={value}
        onChange={(e) =>
          onChange(e.target.value)
        }
        className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-white outline-none focus:border-blue-500"
      />

    </div>
  );
}


/* ---------------------------------------------------------
   Result card
--------------------------------------------------------- */

function ResultCard({
  title,
  value,
}: {
  title: string;
  value: string;
}) {

  return (

    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">

      <p className="text-sm text-slate-400">
        {title}
      </p>

      <p className="mt-2 text-2xl font-bold">
        {value}
      </p>

    </div>
  );
}