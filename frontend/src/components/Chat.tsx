"use client";

import { useState } from "react";
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

  async function send() {
    const text = input.trim();
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
      <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800">
        Not legal advice. All output must be reviewed by a licensed attorney before use.
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400">
            Ask a question about your documents, or switch to Draft mode to request a first draft.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                m.role === "user" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-800"
              }`}
            >
              {m.error ? (
                <span className="text-red-600">Error: {m.error}</span>
              ) : m.role === "assistant" && m.mode === "draft" && !m.lowConfidence && !m.rejected ? (
                <div>
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">Draft</p>
                  <CitedText text={m.text} citations={m.citations} onCitationClick={onCitationClick} />
                </div>
              ) : (
                <CitedText text={m.text} citations={m.citations} onCitationClick={onCitationClick} />
              )}
              {m.rejected && (
                <p className="mt-1 text-xs text-red-500">
                  Blocked: the model cited a passage outside the retrieved set.
                </p>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-sm text-slate-400">Thinking...</p>}
      </div>

      <div className="border-t border-slate-200 p-4">
        <div className="mb-2 flex gap-2 text-xs">
          <button
            onClick={() => setMode("ask")}
            className={`rounded-md px-2 py-1 ${mode === "ask" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}
          >
            Ask
          </button>
          <button
            onClick={() => setMode("draft")}
            className={`rounded-md px-2 py-1 ${mode === "draft" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}
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
            className="flex-1 resize-none rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            onClick={send}
            disabled={loading}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
