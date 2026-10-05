export default function About() {
  return (
    <section id="about" className="bg-background py-24">
      <div className="mx-auto grid max-w-7xl gap-14 px-6 md:grid-cols-2 md:items-center">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-gold">About Meridian</p>
          <h2 className="font-serif-brand mt-3 text-3xl font-semibold text-navy md:text-4xl">
            We built the platform we wished existed.
          </h2>
          <div className="mt-6 space-y-4 text-navy/70">
            <p>
              Meridian Legal Intelligence was founded on a simple frustration: legal research tools
              that sound confident and are wrong are worse than tools that are slow. So we built
              ours around verification first — hybrid retrieval, reranking, and citation validation
              that runs before an answer ever reaches a screen.
            </p>
            <p>
              We work with firms and in-house teams who need research and first drafts fast, but
              who cannot afford to have an associate chase down a citation that was never real.
              Every document stays inside your firm&apos;s own workspace, isolated from every
              other client we serve.
            </p>
            <p className="font-medium text-navy">
              Meridian doesn&apos;t practice law. We build the tools your lawyers use to practice it faster.
            </p>
          </div>
        </div>

        <div className="rounded-sm border border-navy/10 bg-navy-pale p-10">
          <h3 className="font-serif-brand text-xl font-semibold text-navy">Our principles</h3>
          <ul className="mt-6 space-y-5">
            {[
              "Verification before speed — never the other way around.",
              "Your documents are never training data, and never visible to another client.",
              "A system that says \"I don't know\" is more useful than one that guesses.",
              "Attorneys review everything. We shorten the path to that review.",
            ].map((item) => (
              <li key={item} className="flex gap-3 text-sm text-navy/80">
                <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-gold" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
