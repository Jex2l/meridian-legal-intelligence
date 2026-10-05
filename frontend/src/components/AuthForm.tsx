"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { AuthSession } from "@/lib/api";
import Logo from "./Logo";

const MARKETING_URL = process.env.NEXT_PUBLIC_MARKETING_URL || "http://localhost:3001";

export default function AuthForm({ onAuthenticated }: { onAuthenticated: (s: AuthSession) => void }) {
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [workspaceName, setWorkspaceName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const session =
        mode === "signup" ? await api.signup(workspaceName, email, name, acceptedTerms) : await api.login(email);
      onAuthenticated(session);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Brand panel */}
      <div className="relative hidden w-[42%] flex-col justify-between bg-navy p-12 text-white lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(90deg, transparent, transparent 79px, #B68A35 80px), repeating-linear-gradient(0deg, transparent, transparent 79px, #B68A35 80px)",
          }}
        />
        <a href={MARKETING_URL} className="relative">
          <Logo dark />
        </a>

        <div className="relative">
          <p className="font-serif-brand text-3xl font-semibold leading-snug">
            Every answer cited. Every citation verified.
          </p>
          <ul className="mt-8 space-y-4 text-sm text-white/70">
            {[
              "Your documents are isolated to your workspace, enforced at the query level.",
              "Low-confidence answers say so, instead of guessing.",
              "Every query and source passage is logged for audit.",
            ].map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-gold" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-white/40">
          © {new Date().getFullYear()} Meridian Legal Intelligence. Not legal advice.
        </p>
      </div>

      {/* Form panel */}
      <div className="flex flex-1 items-center justify-center bg-white px-6 py-16">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>

          <h1 className="font-serif-brand text-2xl font-semibold text-navy">
            {mode === "signup" ? "Set up your workspace" : "Welcome back"}
          </h1>
          <p className="mb-8 mt-1 text-sm text-navy/60">
            {mode === "signup" ? "Create a private workspace for your firm." : "Log in to your matter workspace."}
          </p>

          <form onSubmit={submit}>
            <div className="mb-6 flex gap-1 rounded-sm bg-navy-pale p-1 text-sm">
              <button
                type="button"
                onClick={() => setMode("signup")}
                className={`flex-1 rounded-sm px-3 py-1.5 font-medium transition ${
                  mode === "signup" ? "bg-navy text-white" : "text-navy/60 hover:text-navy"
                }`}
              >
                New workspace
              </button>
              <button
                type="button"
                onClick={() => setMode("login")}
                className={`flex-1 rounded-sm px-3 py-1.5 font-medium transition ${
                  mode === "login" ? "bg-navy text-white" : "text-navy/60 hover:text-navy"
                }`}
              >
                Log in
              </button>
            </div>

            {mode === "signup" && (
              <>
                <label className="mb-1 block text-xs font-medium text-navy/70">Firm / workspace name</label>
                <input
                  required
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  className="mb-4 w-full rounded-sm border border-navy/20 px-3 py-2.5 text-sm focus:border-gold focus:outline-none"
                  placeholder="Ellis & Co."
                />
                <label className="mb-1 block text-xs font-medium text-navy/70">Your name</label>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mb-4 w-full rounded-sm border border-navy/20 px-3 py-2.5 text-sm focus:border-gold focus:outline-none"
                  placeholder="Jordan Ellis"
                />
              </>
            )}

            <label className="mb-1 block text-xs font-medium text-navy/70">Work email</label>
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mb-5 w-full rounded-sm border border-navy/20 px-3 py-2.5 text-sm focus:border-gold focus:outline-none"
              placeholder="jordan@yourfirm.com"
            />

            {mode === "signup" && (
              <label className="mb-5 flex items-start gap-2.5 text-xs text-navy/70">
                <input
                  required
                  type="checkbox"
                  checked={acceptedTerms}
                  onChange={(e) => setAcceptedTerms(e.target.checked)}
                  className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 accent-navy"
                />
                <span>
                  I agree to the{" "}
                  <a href={`${MARKETING_URL}/terms`} target="_blank" rel="noopener noreferrer" className="font-medium text-navy underline">
                    Terms of Service
                  </a>
                  ,{" "}
                  <a href={`${MARKETING_URL}/privacy`} target="_blank" rel="noopener noreferrer" className="font-medium text-navy underline">
                    Privacy Policy
                  </a>
                  , and{" "}
                  <a href={`${MARKETING_URL}/disclaimer`} target="_blank" rel="noopener noreferrer" className="font-medium text-navy underline">
                    AI Output Disclaimer
                  </a>
                  .
                </span>
              </label>
            )}

            {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={loading || (mode === "signup" && !acceptedTerms)}
              className="w-full rounded-sm bg-navy px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-navy-light disabled:opacity-50"
            >
              {loading ? "Working..." : mode === "signup" ? "Create workspace" : "Log in"}
            </button>

            <p className="mt-5 text-center text-xs text-navy/40">
              Demo authentication — email only, no password. Not production-ready.
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
