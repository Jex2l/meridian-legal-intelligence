import type { Metadata } from "next";
import LegalPage from "@/components/legal/LegalPage";

export const metadata: Metadata = {
  title: "Subprocessors — Meridian Legal Intelligence",
};

function H2({ children }: { children: React.ReactNode }) {
  return <h2 className="font-serif-brand text-xl font-semibold text-navy">{children}</h2>;
}

const SUBPROCESSORS = [
  {
    name: "Anthropic",
    purpose: "Large language model inference for answer/draft generation",
    data: "Retrieved document excerpts and your question/task text, when your workspace is configured to use Anthropic as its generation provider",
    location: "See Anthropic's own privacy and data-processing terms",
  },
  {
    name: "Self-hosted model (Ollama), when configured",
    purpose: "Large language model inference, run entirely within your own infrastructure",
    data: "Nothing leaves your infrastructure -- not a third party in this configuration, listed here for completeness",
    location: "Your own infrastructure",
  },
  {
    name: "Database/infrastructure hosting",
    purpose: "Hosting the Postgres database, application servers, and file storage that run the Service",
    data: "All account data, uploaded documents, and query/audit logs",
    location: "[Placeholder -- name your actual hosting provider(s) and region(s) here]",
  },
];

export default function SubprocessorsPage() {
  return (
    <LegalPage title="Subprocessors" effectiveDate="October 5, 2026">
      <section>
        <H2>What This Page Is</H2>
        <p className="mt-3">
          A subprocessor is a third party we use to help provide the Service, who may process
          personal information or Your Content as part of that. This page lists our current
          subprocessors, consistent with Section 4 of our{" "}
          <a href="/privacy" className="font-medium text-navy underline">
            Privacy Policy
          </a>
          . We&apos;ll update this list as our infrastructure changes.
        </p>
      </section>

      <section>
        <div className="overflow-x-auto rounded-sm border border-navy/10">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="bg-navy-pale">
              <tr>
                <th className="px-4 py-3 font-semibold text-navy">Subprocessor</th>
                <th className="px-4 py-3 font-semibold text-navy">Purpose</th>
                <th className="px-4 py-3 font-semibold text-navy">Data involved</th>
                <th className="px-4 py-3 font-semibold text-navy">Location</th>
              </tr>
            </thead>
            <tbody>
              {SUBPROCESSORS.map((s) => (
                <tr key={s.name} className="border-t border-navy/10 align-top">
                  <td className="px-4 py-3 font-medium text-navy">{s.name}</td>
                  <td className="px-4 py-3 text-navy/70">{s.purpose}</td>
                  <td className="px-4 py-3 text-navy/70">{s.data}</td>
                  <td className="px-4 py-3 text-navy/70">{s.location}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <H2>Choosing Your Generation Provider</H2>
        <p className="mt-3">
          Workspace administrators can configure whether generation runs through Anthropic or a
          self-hosted model under your own infrastructure. If keeping document content off a
          third-party provider entirely is a requirement for your organization, use the
          self-hosted configuration — see our documentation or contact us for setup help.
        </p>
      </section>

      <section>
        <H2>Notice of Changes</H2>
        <p className="mt-3">
          <em>
            [Placeholder — to be completed with counsel/ops: describe how customers are notified
            of a new subprocessor (e.g., email to workspace admins, N days&apos; advance notice,
            right to object or terminate).]
          </em>
        </p>
      </section>
    </LegalPage>
  );
}
