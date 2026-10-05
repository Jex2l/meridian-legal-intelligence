const STEPS = [
  {
    n: "01",
    title: "Upload or connect your matter files",
    body: "PDFs and Word documents are extracted, split by clause and section — not arbitrary chunks — and indexed within your firm's private workspace.",
  },
  {
    n: "02",
    title: "Ask, in plain language",
    body: "Hybrid search (lexical + semantic) finds candidate passages, then a reranking pass narrows to the ones that actually answer your question.",
  },
  {
    n: "03",
    title: "Get a cited answer or draft",
    body: "Every claim in the response carries a citation to a retrieved passage. If the evidence isn't there, the answer says so instead of guessing.",
  },
  {
    n: "04",
    title: "Verify, then use it",
    body: "Click any citation to see the exact source passage highlighted. Review stays with your attorneys — we hand them a verified starting point, not a final word.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-navy-pale py-24">
      <div className="mx-auto max-w-7xl px-6">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-widest text-gold">How It Works</p>
          <h2 className="font-serif-brand mt-3 text-3xl font-semibold text-navy md:text-4xl">
            From question to verified answer, in four steps.
          </h2>
        </div>

        <ol className="mt-14 grid gap-10 md:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step) => (
            <li key={step.n}>
              <span className="font-serif-brand text-4xl font-semibold text-gold/50">{step.n}</span>
              <h3 className="font-serif-brand mt-3 text-lg font-semibold text-navy">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-navy/70">{step.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
