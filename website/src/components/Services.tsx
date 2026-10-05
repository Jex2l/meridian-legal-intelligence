const SERVICES = [
  {
    title: "Grounded Legal Research",
    body:
      "Ask a question in plain English and get an answer drawn from your firm's own documents and a public case-law corpus — with inline citations linking back to the exact passage.",
  },
  {
    title: "First-Draft Clause Drafting",
    body:
      "Request a rewrite — \"make this indemnity favor the buyer\" — and receive a cited first draft with tracked reasoning, ready for attorney review.",
  },
  {
    title: "Document Intelligence",
    body:
      "Upload contracts, memos, and filings. We extract, clause-chunk, and index them automatically, including OCR for scanned PDFs.",
  },
  {
    title: "Cross-Matter Case Research",
    body:
      "Search public case law alongside your own files in a single query, scoped correctly so research never crosses matter boundaries.",
  },
  {
    title: "Workspace Isolation",
    body:
      "Every matter is a walled workspace. No client's documents can ever surface in another client's results — enforced in the retrieval query itself, not as an afterthought.",
  },
  {
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
            <div key={s.title} className="bg-background p-8">
              <div className="mb-4 h-px w-10 bg-gold" />
              <h3 className="font-serif-brand text-lg font-semibold text-navy">{s.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-navy/70">{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
