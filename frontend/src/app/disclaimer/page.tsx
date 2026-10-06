import type { Metadata } from "next";
import LegalPage from "@/components/legal/LegalPage";

export const metadata: Metadata = {
  title: "AI Output Disclaimer — Meridian Legal Intelligence",
};

function H2({ children }: { children: React.ReactNode }) {
  return <h2 className="font-serif-brand text-xl font-semibold text-navy">{children}</h2>;
}

export default function DisclaimerPage() {
  return (
    <LegalPage title="AI Output Disclaimer" effectiveDate="October 5, 2026">
      <section>
        <H2>Not Legal Advice</H2>
        <p className="mt-3">
          Meridian Legal Intelligence is a software tool. It is not a law firm, does not practice
          law, and nothing it produces — answers, citations, summaries, or drafted clause
          language — is legal advice. Using the Service does not create an attorney-client
          relationship between you and Meridian, or between you and any individual involved in
          building or operating it.
        </p>
      </section>

      <section>
        <H2>How Output Is Generated</H2>
        <p className="mt-3">
          The Service retrieves passages from documents you&apos;ve uploaded and, where enabled, a
          public case-law corpus, and uses a large language model to generate an answer or draft
          grounded in those passages. Every citation in an answer is checked against the passages
          actually retrieved before the answer is shown to you, and the system is designed to
          respond &quot;I couldn&apos;t find support for this&quot; rather than guess when it
          cannot find adequate support. These are engineering safeguards intended to reduce, not
          eliminate, the risk of error.
        </p>
      </section>

      <section>
        <H2>Output Can Still Be Wrong</H2>
        <p className="mt-3">Despite these safeguards, AI-generated output can:</p>
        <ul className="mt-3 list-disc space-y-2 pl-6">
          <li>Misstate, oversimplify, or misinterpret what a cited passage actually says;</li>
          <li>Omit relevant context, exceptions, or more recent authority not present in the indexed documents;</li>
          <li>Reflect the limitations of the underlying documents or corpus, which may be incomplete, outdated, or specific to a jurisdiction that doesn&apos;t match your matter; or</li>
          <li>Produce drafted language that is a reasonable starting point but not appropriate for your specific facts or client without revision.</li>
        </ul>
      </section>

      <section>
        <H2>Your Responsibility</H2>
        <p className="mt-3">
          A qualified, licensed attorney must review, verify, and take responsibility for any
          output before it is relied upon, filed, sent to a client or counterparty, or otherwise
          acted on. You are responsible for independently verifying citations against primary
          sources, confirming the applicable law for your jurisdiction and matter, and exercising
          your own professional judgment. Meridian&apos;s citation-validation and
          low-confidence-fallback mechanisms are aids to that review, not a substitute for it.
        </p>
      </section>

      <section>
        <H2>No Guarantee of Outcome</H2>
        <p className="mt-3">
          Meridian makes no representation or warranty about the accuracy, completeness, or
          suitability of any output for a particular matter, and no representation about the
          outcome of any matter in which the Service&apos;s output is used.
        </p>
      </section>

      <section>
        <H2>Related Documents</H2>
        <p className="mt-3">
          This Disclaimer supplements, and should be read together with, our{" "}
          <a href="/terms" className="font-medium text-navy underline">
            Terms of Service
          </a>{" "}
          and{" "}
          <a href="/privacy" className="font-medium text-navy underline">
            Privacy Policy
          </a>
          .
        </p>
      </section>
    </LegalPage>
  );
}
