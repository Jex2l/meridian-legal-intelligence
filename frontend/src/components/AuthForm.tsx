"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { AuthSession } from "@/lib/api";

export default function AuthForm({ onAuthenticated }: { onAuthenticated: (s: AuthSession) => void }) {
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [workspaceName, setWorkspaceName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const session =
        mode === "signup" ? await api.signup(workspaceName, email, name) : await api.login(email);
      onAuthenticated(session);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <form onSubmit={submit} className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="mb-1 text-xl font-semibold text-slate-900">LexRAG</h1>
        <p className="mb-6 text-sm text-slate-500">Legal research &amp; drafting assistant</p>

        <div className="mb-4 flex gap-2 text-sm">
          <button
            type="button"
            onClick={() => setMode("signup")}
            className={`rounded-md px-3 py-1 ${mode === "signup" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}
          >
            New workspace
          </button>
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`rounded-md px-3 py-1 ${mode === "login" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}
          >
            Log in
          </button>
        </div>

        {mode === "signup" && (
          <>
            <label className="mb-1 block text-xs font-medium text-slate-600">Firm / workspace name</label>
            <input
              required
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              className="mb-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              placeholder="Acme Law LLP"
            />
            <label className="mb-1 block text-xs font-medium text-slate-600">Your name</label>
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mb-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              placeholder="Alice Attorney"
            />
          </>
        )}

        <label className="mb-1 block text-xs font-medium text-slate-600">Email</label>
        <input
          required
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-4 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="alice@acme.law"
        />

        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Working..." : mode === "signup" ? "Create workspace" : "Log in"}
        </button>

        <p className="mt-4 text-xs text-slate-400">
          Demo auth: email-only, no password. Not production-ready.
        </p>
      </form>
    </div>
  );
}
