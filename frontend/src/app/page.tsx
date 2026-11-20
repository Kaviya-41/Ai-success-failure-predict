"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  ClipboardCheck,
  ShieldCheck,
  Activity,
} from "lucide-react";

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-3 font-semibold text-slate-900">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-blue-100 text-blue-700">
              <BrainCircuit size={18} />
            </div>
            <span className="text-lg tracking-tight">RiskPilot</span>
          </Link>

          <div className="flex items-center gap-3">
            {user ? (
              <Link href="/dashboard" className="primary-button inline-flex items-center gap-2">
                Go to dashboard
                <ArrowRight size={16} />
              </Link>
            ) : (
              <>
                <Link href="/login" className="secondary-button">
                  Sign in
                </Link>
                <Link href="/register" className="primary-button">
                  Create account
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-16 md:py-20">
        <section className="grid items-center gap-10 lg:grid-cols-[1.25fr_0.75fr]">
          <div>
            <span className="section-label mb-5 inline-flex rounded-full border border-blue-200 bg-blue-50 px-3 py-2 text-blue-700">
              <Activity size={12} />
              Project risk intelligence
            </span>
            <h1 className="max-w-xl text-4xl font-semibold tracking-tight text-slate-900 md:text-5xl">
              Predict project outcomes before delivery risk becomes a problem.
            </h1>
            <p className="mt-5 max-w-xl text-lg text-slate-600">
              Monitor project health, analyze risk signals, and evaluate the likelihood of success or failure using a practical decision engine built for software delivery teams.
            </p>

            {!user ? (
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link href="/register" className="primary-button inline-flex items-center justify-center gap-2">
                  Create account
                  <ArrowRight size={16} />
                </Link>
                <Link href="/login" className="secondary-button inline-flex items-center justify-center">
                  Sign in
                </Link>
              </div>
            ) : (
              <div className="mt-8">
                <Link href="/dashboard" className="primary-button inline-flex items-center gap-2">
                  Open dashboard
                  <ArrowRight size={16} />
                </Link>
              </div>
            )}
          </div>

          <div className="surface-panel p-6">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="section-label">Decision engine</p>
                <h2 className="mt-2 text-xl font-semibold text-slate-900">Success / Failure Decision Engine</h2>
              </div>
              <div className="rounded-lg bg-blue-50 p-2 text-blue-700">
                <ClipboardCheck size={18} />
              </div>
            </div>

            <div className="space-y-4">
              {[
                { title: "Project metrics", detail: "Read delivery signals from budget, team, testing, and schedule data." },
                { title: "Validation", detail: "Check risk conditions against the project profile." },
                { title: "Outcome", detail: "If conditions indicate healthy execution, result is SUCCESS; otherwise FAILURE." },
              ].map((step, index) => (
                <div key={step.title} className="flex gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-semibold text-slate-800">{step.title}</p>
                    <p className="mt-1 text-sm text-slate-600">{step.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-16 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {[
            { title: "Portfolio overview", text: "Track total project exposure and active risk levels.", icon: BarChart3 },
            { title: "Project health", text: "Understand the delivery trajectory of each active initiative.", icon: ShieldCheck },
            { title: "Risk analysis", text: "Review driver metrics such as delays, bugs, and coverage.", icon: Activity },
            { title: "Decision clarity", text: "Explain the driver behind success or failure outcomes.", icon: BrainCircuit },
          ].map(({ title, text, icon: Icon }) => (
            <div key={title} className="surface-panel p-5">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md bg-blue-50 text-blue-700">
                <Icon size={16} />
              </div>
              <h3 className="text-base font-semibold text-slate-900">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{text}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}

