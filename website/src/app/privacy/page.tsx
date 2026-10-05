import type { Metadata } from "next";
import LegalPage from "@/components/legal/LegalPage";

export const metadata: Metadata = {
  title: "Privacy Policy — Meridian Legal Intelligence",
};

function H2({ children }: { children: React.ReactNode }) {
  return <h2 className="font-serif-brand text-xl font-semibold text-navy">{children}</h2>;
}

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" effectiveDate="October 5, 2026">
      <section>
        <H2>1. Scope</H2>
        <p className="mt-3">
          This Privacy Policy describes how Meridian Legal Intelligence (&quot;Meridian,&quot;
          &quot;we,&quot; &quot;us&quot;) collects, uses, and discloses information when you use our
          website and client portal (together, the &quot;Service&quot;). It does not apply to
          third-party sites we link to.
        </p>
      </section>

      <section>
        <H2>2. Information We Collect</H2>
        <p className="mt-3">We collect the following categories of information:</p>
        <ul className="mt-3 list-disc space-y-2 pl-6">
          <li>
            <strong>Account information:</strong> name, work email address, and workspace/firm name
            provided at signup.
          </li>
          <li>
            <strong>Your Content:</strong> documents you upload (contracts, memos, filings), the
            text extracted from them, and the questions or drafting requests you submit.
          </li>
          <li>
            <strong>Usage and log data:</strong> every query you submit, the passages our system
            retrieved in response, and the resulting answer, retained for audit and quality
            purposes as described in Section 5.
          </li>
          <li>
            <strong>Technical data:</strong> standard web request metadata (IP address, browser
            type, timestamps) collected by our infrastructure for security and reliability.
          </li>
          <li>
            <strong>Local browser storage:</strong> the client portal stores your session token in
            your browser&apos;s local storage to keep you logged in. We do not currently use
            third-party advertising or analytics cookies.
          </li>
        </ul>
      </section>

      <section>
        <H2>3. How We Use Information</H2>
        <ul className="mt-3 list-disc space-y-2 pl-6">
          <li>To provide, maintain, and secure the Service, including retrieving and generating answers from Your Content;</li>
          <li>To authenticate you and maintain workspace isolation between organizations;</li>
          <li>To log and audit queries and outputs so your organization can review how a result was produced;</li>
          <li>To monitor, debug, and improve the reliability and accuracy of the Service;</li>
          <li>To communicate with you about your account or respond to inquiries; and</li>
          <li>To comply with legal obligations.</li>
        </ul>
        <p className="mt-3">
          We do not sell your personal information or Your Content, and we do not use Your Content
          to train general-purpose models outside the operation of your own workspace.
        </p>
      </section>

      <section>
        <H2>4. How Information Is Shared</H2>
        <p className="mt-3">We share information only as follows:</p>
        <ul className="mt-3 list-disc space-y-2 pl-6">
          <li>
            <strong>AI generation providers.</strong> To produce an answer or draft, relevant
            excerpts of Your Content may be sent to a third-party large language model provider
            (for example, Anthropic, under its own data-handling terms) or, where your organization
            runs a self-hosted model (for example, via Ollama), processed entirely within your own
            infrastructure without leaving it. Which provider is used depends on your
            organization&apos;s configuration.
          </li>
          <li>
            <strong>Infrastructure providers.</strong> We use hosting, database, and related
            infrastructure providers to operate the Service, bound by confidentiality and
            data-processing obligations.
          </li>
          <li>
            <strong>Legal requirements.</strong> We may disclose information if required by law,
            subpoena, or to protect the rights, property, or safety of Meridian, our users, or
            others.
          </li>
          <li>
            <strong>Business transfers.</strong> If Meridian is involved in a merger, acquisition,
            or asset sale, information may be transferred as part of that transaction, subject to
            this Policy or a successor policy.
          </li>
        </ul>
      </section>

      <section>
        <H2>5. Data Retention</H2>
        <p className="mt-3">
          We retain account information and Your Content for as long as your workspace is active,
          and query/audit logs for the period needed to support auditability and debugging, after
          which they are deleted or anonymized on a rolling basis. You may request deletion of your
          workspace and its contents at any time by contacting us (Section 8); some audit records
          may be retained longer where required for legal or security purposes.
        </p>
      </section>

      <section>
        <H2>6. Data Security</H2>
        <p className="mt-3">
          Workspace documents are isolated at the data-retrieval layer so that one organization&apos;s
          documents are not returned in another organization&apos;s queries. We use reasonable
          administrative, technical, and physical safeguards designed to protect information
          against unauthorized access, alteration, or disclosure. No method of transmission or
          storage is completely secure, and we cannot guarantee absolute security.
        </p>
      </section>

      <section>
        <H2>7. Your Rights</H2>
        <p className="mt-3">
          Depending on your location, you may have rights to access, correct, export, or delete
          your personal information, or to object to or restrict certain processing (for example,
          under the GDPR in the EU/UK or the CCPA in California). To exercise these rights, contact
          us using the details in Section 8. We will respond within the timeframe required by
          applicable law.
        </p>
      </section>

      <section>
        <H2>8. International Transfers</H2>
        <p className="mt-3">
          <em>
            [Placeholder — to be completed with counsel: if your organization and your
            infrastructure/processors are located in different countries, describe the transfer
            mechanism used (e.g., Standard Contractual Clauses) here.]
          </em>
        </p>
      </section>

      <section>
        <H2>9. Children&apos;s Privacy</H2>
        <p className="mt-3">
          The Service is intended for business use by adults and is not directed to children under
          16. We do not knowingly collect personal information from children.
        </p>
      </section>

      <section>
        <H2>10. Changes to This Policy</H2>
        <p className="mt-3">
          We may update this Privacy Policy from time to time. We will post the updated version
          with a new effective date, and material changes will be communicated to workspace
          administrators.
        </p>
      </section>

      <section>
        <H2>11. Contact</H2>
        <p className="mt-3">
          Questions or requests regarding this Policy can be sent to{" "}
          <a href="mailto:privacy@meridianlegal.ai" className="font-medium text-navy underline">
            privacy@meridianlegal.ai
          </a>
          .
        </p>
      </section>
    </LegalPage>
  );
}
