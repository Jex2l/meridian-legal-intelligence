"use client";

import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Citation } from "@/lib/api";
import CitedText from "./CitedText";

type Message = {
  role: "user" | "assistant";
  mode: "ask" | "draft";
  text: string;
  citations: Citation[];
  lowConfidence?: boolean;
  rejected?: boolean;
  error?: string;
};

const SUGGESTIONS: Record<"ask" | "draft", string[]> = {
  ask: ["What does the indemnification clause say?", "Who bears the risk of loss during shipping?"],
  draft: ["Rewrite the indemnity clause to favor the buyer", "Draft a limitation-of-liability clause"],
};

export default function Chat({
  token,
  onCitationClick,
}: {
  token: string;
  onCitationClick: (citation: Citation) => void;
}) {
  const [mode, setMode] = useState<"ask" | "draft">("ask");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const scrollEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollEnd.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  async function send(overrideText?: string) {
    const text = (overrideText ?? input).trim();
    if (!text || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", mode, text, citations: [] }]);
    setLoading(true);
    try {
      if (mode === "ask") {
        const res = await api.ask(token, text);
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            mode,
            text: res.answer_text,
            citations: res.citations,
            lowConfidence: res.low_confidence,
            rejected: res.ungrounded_response_rejected,
          },
        ]);
      } else {
        const res = await api.draft(token, text);
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            mode,
            text: res.draft_text,
            citations: res.citations,
            lowConfidence: res.low_confidence,
            rejected: res.ungrounded_response_rejected,
          },
        ]);
      }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong";
      setMessages((m) => [...m, { role: "assistant", mode, text: "", citations: [], error: message }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex items-center gap-2 border-b border-gold/30 bg-gold/10 px-4 py-2 text-xs text-navy/80">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="flex-shrink-0 text-gold">
          <path
            d="M12 2 L21 6 V11 C21 16.5 17 20.5 12 22 C7 20.5 3 16.5 3 11 V6 Z"
            stroke="currentColor"
            strokeWidth="1.6"
          />
          <path d="M12 8v5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          <circle cx="12" cy="16" r="0.9" fill="currentColor" />
        </svg>
        <span>
          Not legal advice. All output must be reviewed by a licensed attorney before use.{" "}
          <a href="/disclaimer" target="_blank" rel="noopener noreferrer" className="font-medium underline">
            Learn more
          </a>
        </span>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-5">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center px-6 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-navy-pale">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-navy/50">
                <path
                  d="M4 5h16v11H9l-4 4V5Z"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinejoin="round"
                />
                <path d="M8 9h8M8 12h5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
              </svg>
            </div>
            <p className="text-sm font-medium text-navy/70">
              {mode === "ask" ? "Ask a question about your documents" : "Request a cited first draft"}
            </p>
            <p className="mt-1 max-w-xs text-xs text-navy/40">
              {mode === "ask"
                ? "Answers are grounded in your uploaded documents and the public case-law corpus, with inline citations."
                : "Describe the clause or provision you need, and get a reviewable draft with tracked reasoning."}
            </p>
            <div className="mt-5 flex flex-col gap-2">
              {SUGGESTIONS[mode].map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full border border-navy/15 bg-white px-3.5 py-1.5 text-xs text-navy/70 transition hover:border-gold hover:text-navy"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={`max-w-[85%] rounded-lg px-3.5 py-2.5 text-sm shadow-sm ${
                m.role === "user" ? "bg-navy text-white" : "border border-navy/10 bg-navy-pale text-navy"
              }`}
            >
              {m.error ? (
                <span className="flex items-start gap-1.5 text-red-600">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="mt-0.5 flex-shrink-0">
                    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" />
                    <path d="M12 8v5M12 16h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                  </svg>
                  {m.error}
                </span>
              ) : m.role === "assistant" && m.mode === "draft" && !m.lowConfidence && !m.rejected ? (
                <div>
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gold">Draft</p>
                  <CitedText text={m.text} citations={m.citations} onCitationClick={onCitationClick} />
                </div>
              ) : (
                <CitedText text={m.text} citations={m.citations} onCitationClick={onCitationClick} />
              )}
              {m.lowConfidence && !m.rejected && (
                <p className="mt-2 flex items-center gap-1.5 border-t border-navy/10 pt-1.5 text-xs text-navy/50">
                  <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-500" />
                  Low confidence — retrieval found limited support for this answer.
                </p>
              )}
              {m.rejected && (
                <p className="mt-2 flex items-center gap-1.5 border-t border-red-200 pt-1.5 text-xs text-red-500">
                  <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-red-500" />
                  Blocked: the model cited a passage outside the retrieved set.
                </p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-1 rounded-lg border border-navy/10 bg-navy-pale px-3.5 py-3">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-navy/40 [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-navy/40 [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-navy/40" />
            </div>
          </div>
        )}
        <div ref={scrollEnd} />
      </div>

      <div className="border-t border-navy/10 bg-white p-4">
        <div className="mb-2.5 flex gap-1.5 text-xs">
          <button
            onClick={() => setMode("ask")}
            className={`rounded-full px-3 py-1 font-medium transition ${
              mode === "ask" ? "bg-navy text-white" : "bg-navy-pale text-navy/60 hover:text-navy"
            }`}
          >
            Ask
          </button>
          <button
            onClick={() => setMode("draft")}
            className={`rounded-full px-3 py-1 font-medium transition ${
              mode === "draft" ? "bg-navy text-white" : "bg-navy-pale text-navy/60 hover:text-navy"
            }`}
          >
            Draft
          </button>
        </div>
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder={
              mode === "ask" ? "What does the indemnification clause say?" : "Rewrite the indemnity clause to favor the buyer"
            }
            rows={2}
            className="flex-1 resize-none rounded-md border border-navy/20 px-3 py-2 text-sm transition focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold/30"
          />
          <button
            onClick={() => send()}
            disabled={loading || !input.trim()}
            className="rounded-md bg-navy px-4 py-2 text-sm font-medium text-white transition hover:bg-navy-light disabled:cursor-not-allowed disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
