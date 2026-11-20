"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import {
  AlertCircle,
  ArrowRight,
  BrainCircuit,
  Check,
  Eye,
  EyeOff,
  Lock,
  Mail,
  ShieldCheck,
  User,
} from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { register, user } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState("member");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  useEffect(() => {
    if (user) {
      router.replace("/dashboard");
    }
  }, [router, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (fullName.trim().length < 2) {
      setError("Please enter your full name.");
      return;
    }
    if (password.length < 8) {
      setError("Your password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      await register(email.trim().toLowerCase(), password, fullName.trim(), role);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create your account.");
      setSubmitting(false);
    }
  };

  const passwordChecks = [
    { label: "At least 8 characters", valid: password.length >= 8 },
    { label: "Passwords match", valid: confirmPassword.length > 0 && password === confirmPassword },
  ];

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-4 py-8 sm:px-6">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(37,99,235,0.22),transparent_32%),radial-gradient(circle_at_90%_85%,rgba(14,165,233,0.15),transparent_30%)]" />
      <div className="relative grid w-full max-w-5xl overflow-hidden rounded-3xl border border-white/10 bg-white shadow-2xl lg:grid-cols-[0.9fr_1.1fr]">
        <aside className="hidden bg-blue-700 p-10 text-white lg:flex lg:flex-col lg:justify-between">
          <div>
            <div className="mb-12 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/15">
                <BrainCircuit className="h-5 w-5" />
              </div>
              <span className="text-sm font-semibold tracking-wide">PROJECT SIGNAL</span>
            </div>
            <p className="mb-4 text-sm font-semibold uppercase tracking-[0.18em] text-blue-100">A clearer way to lead</p>
            <h1 className="max-w-sm text-4xl font-semibold leading-tight tracking-tight">Turn project signals into confident decisions.</h1>
            <p className="mt-5 max-w-sm text-sm leading-6 text-blue-100">Create your workspace to monitor delivery health, predict risk, and keep every project moving with evidence.</p>
          </div>
          <div className="space-y-4 text-sm text-blue-50">
            <div className="flex items-center gap-3"><ShieldCheck className="h-5 w-5" /> Private workspace access</div>
            <div className="flex items-center gap-3"><Check className="h-5 w-5" /> Built for focused project teams</div>
          </div>
        </aside>

        <section className="p-6 sm:p-10">
          <div className="mb-8 lg:hidden">
            <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-blue-100 text-blue-700">
              <BrainCircuit className="h-6 w-6" />
            </div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">Project Signal</p>
          </div>
          <div className="mb-8">
            <p className="mb-2 text-xs font-bold uppercase tracking-[0.16em] text-blue-700">Get started</p>
            <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Create your account</h2>
            <p className="mt-2 text-sm text-slate-500">Set up your workspace and start making better project calls.</p>
          </div>

          {error && (
            <div role="alert" className="mb-5 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="full-name" className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-slate-600">Full name</label>
              <div className="relative">
                <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input id="full-name" type="text" required autoComplete="name" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Jane Doe" className="form-field pl-10" />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-slate-600">Work email</label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="jane@company.com" className="form-field pl-10" />
              </div>
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <label htmlFor="password" className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-slate-600">Password</label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input id="password" type={showPassword ? "text" : "password"} required autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="8+ characters" className="form-field pl-10 pr-10" />
                  <button type="button" onClick={() => setShowPassword((visible) => !visible)} aria-label={showPassword ? "Hide password" : "Show password"} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700">
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label htmlFor="confirm-password" className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-slate-600">Confirm password</label>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input id="confirm-password" type={showConfirmPassword ? "text" : "password"} required autoComplete="new-password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Repeat password" className="form-field pl-10 pr-10" />
                  <button type="button" onClick={() => setShowConfirmPassword((visible) => !visible)} aria-label={showConfirmPassword ? "Hide password confirmation" : "Show password confirmation"} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700">
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500">
              {passwordChecks.map((check) => <span key={check.label} className={`flex items-center gap-1.5 ${check.valid ? "text-emerald-700" : ""}`}><Check className="h-3.5 w-3.5" />{check.label}</span>)}
            </div>

            <div>
              <label htmlFor="role" className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.12em] text-slate-600">Your role</label>
              <select id="role" value={role} onChange={(e) => setRole(e.target.value)} className="form-field">
                <option value="member">Team member</option>
                <option value="manager">Project manager</option>
              </select>
              <p className="mt-1.5 text-xs text-slate-500">You can update team access later from the admin area.</p>
            </div>

            <button type="submit" disabled={submitting} className="primary-button mt-2 flex w-full items-center justify-center gap-2 py-3 disabled:cursor-not-allowed disabled:opacity-60">
              {submitting ? "Creating account..." : "Create account"}
              {!submitting && <ArrowRight size={16} />}
            </button>
          </form>

          <div className="mt-7 border-t border-slate-200 pt-5 text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-blue-700 hover:underline">Sign in</Link>
          </div>
        </section>
      </div>
    </main>
  );
}
