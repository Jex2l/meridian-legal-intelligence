const PRINCIPLES = [
  {
    title: "Never a fabricated citation",
    body: "Every citation is validated against the documents actually retrieved for your query before an answer is ever shown. An answer that can't be grounded says so, instead of inventing authority.",
  },
  {
    title: "Isolation enforced at the query, not the UI",
    body: "Your workspace's documents are filtered inside the search query itself. A client's files cannot appear in another client's results — there is no shared index to leak across.",
  },
  {
    title: "Low-confidence means we say so",
    body: "When retrieval can't find strong support for a question, the system returns \"I couldn't find support for this\" rather than a confident-sounding guess.",
  },
  {
    title: "Full audit trail",
    body: "Every query, the passages retrieved, and the final answer are logged — so your team can reconstruct and defend how a result was produced.",
  },
];

export default function Trust() {
  return (
    <section id="trust" className="bg-navy py-24 text-white">
      <div className="mx-auto max-w-7xl px-6">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-widest text-gold-light">Trust &amp; Security</p>
          <h2 className="font-serif-brand mt-3 text-3xl font-semibold md:text-4xl">
            Built for firms that get audited.
          </h2>
          <p className="mt-4 text-white/70">
            Not legal advice, and never presented as such. Every output is a reviewed starting
            point for a licensed attorney — the platform's job is to make that review fast and
            defensible.
          </p>
        </div>

        <div className="mt-14 grid gap-8 md:grid-cols-2">
          {PRINCIPLES.map((p) => (
            <div key={p.title} className="border-l-2 border-gold/60 pl-6">
              <h3 className="font-serif-brand text-lg font-semibold text-white">{p.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/65">{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
