import Link from "next/link";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";

export default function LegalPage({
  title,
  effectiveDate,
  children,
}: {
  title: string;
  effectiveDate: string;
  children: React.ReactNode;
}) {
  return (
    <>
      <Nav />
      <main className="bg-background">
        <div className="mx-auto max-w-3xl px-6 py-16">
          <Link href="/" className="text-xs font-medium text-navy/50 hover:text-navy">
            ← Back to home
          </Link>

          <h1 className="font-serif-brand mt-4 text-3xl font-semibold text-navy md:text-4xl">{title}</h1>
          <p className="mt-2 text-sm text-navy/50">Effective date: {effectiveDate}</p>

          <div className="mt-6 rounded-sm border border-gold/40 bg-gold/10 px-5 py-4 text-sm leading-relaxed text-navy/80">
            <strong className="text-navy">Draft template, not legal advice.</strong> This document was
            drafted as a standard-form starting point and has not been reviewed by a licensed
            attorney. Before you rely on it, have qualified counsel review and customize it —
            particularly the governing-law/jurisdiction, your actual registered entity name, and
            any dispute-resolution terms — for your organization and the jurisdictions where you
            operate.
          </div>

          <div className="legal-content mt-10 space-y-8 text-[15px] leading-relaxed text-navy/80">
            {children}
          </div>

          <p className="mt-14 border-t border-navy/10 pt-6 text-xs text-navy/40">
            Questions about this document? Contact{" "}
            <a href="mailto:legal@meridianlegal.ai" className="underline">
              legal@meridianlegal.ai
            </a>
            .
          </p>
        </div>
      </main>
      <Footer />
    </>
  );
}
