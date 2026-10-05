function IconSearch() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="11" cy="11" r="6.5" />
      <path d="M20 20l-4.5-4.5" strokeLinecap="round" />
    </svg>
  );
}
function IconPencil() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M4 20l1-4.5L16 4.5a1.8 1.8 0 0 1 2.5 0l1 1a1.8 1.8 0 0 1 0 2.5L8.5 19 4 20Z" strokeLinejoin="round" />
      <path d="M14 7l3 3" />
    </svg>
  );
}
function IconDocument() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M6 3h8l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" strokeLinejoin="round" />
      <path d="M14 3v5h5M9 13h6M9 17h6" strokeLinecap="round" />
    </svg>
  );
}
function IconLayers() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M12 3l9 5-9 5-9-5 9-5Z" strokeLinejoin="round" />
      <path d="M3 13l9 5 9-5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function IconShield() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3Z" strokeLinejoin="round" />
    </svg>
  );
}
function IconClipboard() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <rect x="5" y="4" width="14" height="17" rx="1.5" />
      <path d="M9 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1M9 11h6M9 15h6" strokeLinecap="round" />
    </svg>
  );
}

const SERVICES = [
  {
    icon: IconSearch,
    title: "Grounded Legal Research",
    body:
      "Ask a question in plain English and get an answer drawn from your firm's own documents and a public case-law corpus — with inline citations linking back to the exact passage.",
  },
  {
    icon: IconPencil,
    title: "First-Draft Clause Drafting",
    body:
      "Request a rewrite — \"make this indemnity favor the buyer\" — and receive a cited first draft with tracked reasoning, ready for attorney review.",
  },
  {
    icon: IconDocument,
    title: "Document Intelligence",
    body:
      "Upload contracts, memos, and filings. We extract, clause-chunk, and index them automatically, including OCR for scanned PDFs.",
  },
  {
    icon: IconLayers,
    title: "Cross-Matter Case Research",
    body:
      "Search public case law alongside your own files in a single query, scoped correctly so research never crosses matter boundaries.",
  },
  {
    icon: IconShield,
    title: "Workspace Isolation",
    body:
      "Every matter is a walled workspace. No client's documents can ever surface in another client's results — enforced in the retrieval query itself, not as an afterthought.",
  },
  {
    icon: IconClipboard,
    title: "Audit-Ready Logging",
    body:
      "Every query, every retrieved passage, and every answer is logged, so your team can show its work on request.",
  },
];

export default function Services() {
  return (
    <section id="services" className="bg-background py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-widest text-gold">What We Do</p>
          <h2 className="font-serif-brand mt-3 text-3xl font-semibold text-navy md:text-4xl">
            Research and drafting built for scrutiny, not just speed.
          </h2>
        </div>

        <div className="mt-14 grid gap-px overflow-hidden rounded-sm border border-navy/10 bg-navy/10 sm:grid-cols-2 lg:grid-cols-3">
          {SERVICES.map((s) => (
            <div key={s.title} className="group bg-background p-8 transition-colors hover:bg-navy-pale">
              <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-full bg-gold/12 text-gold transition-colors group-hover:bg-gold/20">
                <s.icon />
              </div>
              <h3 className="font-serif-brand text-lg font-semibold text-navy">{s.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-navy/70">{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
