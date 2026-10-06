"use client";

import { useState } from "react";

const FAQS = [
  {
    q: "Is this legal advice?",
    a: "No. Meridian is a software tool, not a law firm, and doesn't practice law. Every answer and draft is a starting point for a licensed attorney to review — not a substitute for one. See our AI Output Disclaimer for details.",
  },
  {
    q: "Can my documents be seen by other clients?",
    a: "No. Each workspace's documents are isolated at the data-retrieval layer — the filter that determines what a query can see is applied inside the search itself, not bolted on afterward. See our Trust & Security section and Privacy Policy.",
  },
  {
    q: "Does the AI ever make things up?",
    a: "Every citation in an answer is checked against the passages actually retrieved before it's shown to you. If the system can't find support for a question, it says so instead of guessing, rather than generating a plausible-sounding but ungrounded answer.",
  },
  {
    q: "Where does my data go?",
    a: "Depending on your configuration, generation runs through a third-party provider under its own data terms, or entirely within your own infrastructure via a self-hosted model. Full detail is in our Privacy Policy.",
  },
  {
    q: "Who is responsible if an AI-drafted clause is wrong?",
    a: "You and your reviewing attorney. Meridian's citation validation and confidence checks are safeguards that reduce — not eliminate — the risk of error, and all output requires human legal review before use.",
  },
];

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="bg-background py-24">
      <div className="mx-auto max-w-3xl px-6">
        <div className="text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-gold">FAQ</p>
          <h2 className="font-serif-brand mt-3 text-3xl font-semibold text-navy md:text-4xl">
            Common questions, answered plainly.
          </h2>
        </div>

        <div className="mt-12 divide-y divide-navy/10 border-y border-navy/10">
          {FAQS.map((item, i) => {
            const open = openIndex === i;
            return (
              <div key={item.q}>
                <button
                  onClick={() => setOpenIndex(open ? null : i)}
                  className="flex w-full items-center justify-between gap-4 py-5 text-left"
                  aria-expanded={open}
                >
                  <span className="font-serif-brand text-base font-semibold text-navy">{item.q}</span>
                  <span className={`flex-shrink-0 text-xl text-gold transition-transform ${open ? "rotate-45" : ""}`}>
                    +
                  </span>
                </button>
                {open && <p className="pb-5 text-sm leading-relaxed text-navy/70">{item.a}</p>}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
