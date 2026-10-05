const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

export default function Hero() {
  return (
    <section id="top" className="relative overflow-hidden bg-navy text-white">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(90deg, transparent, transparent 79px, #B68A35 80px), repeating-linear-gradient(0deg, transparent, transparent 79px, #B68A35 80px)",
        }}
      />
      <div className="relative mx-auto max-w-7xl px-6 py-28 md:py-36">
        <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-gold/40 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-gold-light">
          AI-Powered Legal Research &amp; Drafting
        </p>
        <h1 className="font-serif-brand max-w-3xl text-4xl font-semibold leading-tight tracking-tight md:text-6xl">
          Counsel you can verify, in minutes, not hours.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-white/75 md:text-xl">
          Meridian Legal Intelligence is an AI research and drafting consultancy built on one
          principle: every answer cites its source, and every source is checked before it ever
          reaches a client. No guessing. No fabricated authority. Just grounded, auditable legal
          work product — faster.
        </p>
        <div className="mt-10 flex flex-col gap-4 sm:flex-row">
          <a
            href="#contact"
            className="rounded-sm bg-gold px-7 py-3.5 text-center text-sm font-semibold text-navy transition hover:bg-gold-light"
          >
            Request a Demo
          </a>
          <a
            href={APP_URL}
            className="rounded-sm border border-white/30 px-7 py-3.5 text-center text-sm font-semibold text-white transition hover:border-white/60"
          >
            Client Login →
          </a>
        </div>

        <dl className="mt-20 grid grid-cols-2 gap-8 border-t border-white/10 pt-10 sm:grid-cols-4">
          {[
            ["100%", "Citations verified before delivery"],
            ["0", "Fabricated authorities, by design"],
            ["Per-matter", "Workspace isolation, enforced at query time"],
            ["Minutes", "From question to cited first draft"],
          ].map(([stat, label]) => (
            <div key={label}>
              <dt className="font-serif-brand text-2xl font-semibold text-gold-light md:text-3xl">{stat}</dt>
              <dd className="mt-1 text-sm text-white/60">{label}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
