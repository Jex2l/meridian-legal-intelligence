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
      <div className="border-b border-gold/30 bg-gold/10 px-4 py-2 text-xs text-navy/80">
        Not legal advice. All output must be reviewed by a licensed attorney before use.{" "}
        <a
          href={`${process.env.NEXT_PUBLIC_MARKETING_URL || "http://localhost:3001"}/disclaimer`}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium underline"
        >
          Learn more
        </a>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-sm text-navy/40">
            Ask a question about your documents, or switch to Draft mode to request a first draft.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] rounded-sm px-3 py-2 text-sm ${
                m.role === "user" ? "bg-navy text-white" : "bg-navy-pale text-navy"
              }`}
            >
              {m.error ? (
                <span className="text-red-600">Error: {m.error}</span>
              ) : m.role === "assistant" && m.mode === "draft" && !m.lowConfidence && !m.rejected ? (
                <div>
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gold">Draft</p>
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
        {loading && <p className="text-sm text-navy/40">Thinking...</p>}
      </div>

      <div className="border-t border-navy/10 p-4">
        <div className="mb-2 flex gap-2 text-xs">
          <button
            onClick={() => setMode("ask")}
            className={`rounded-sm px-2 py-1 transition ${mode === "ask" ? "bg-navy text-white" : "bg-navy-pale text-navy/60"}`}
          >
            Ask
          </button>
          <button
            onClick={() => setMode("draft")}
            className={`rounded-sm px-2 py-1 transition ${mode === "draft" ? "bg-navy text-white" : "bg-navy-pale text-navy/60"}`}
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
            className="flex-1 resize-none rounded-sm border border-navy/20 px-3 py-2 text-sm focus:border-gold focus:outline-none"
          />
          <button
            onClick={send}
            disabled={loading}
            className="rounded-sm bg-navy px-4 py-2 text-sm font-medium text-white transition hover:bg-navy-light disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
