import type { Metadata } from "next";
import LegalPage from "@/components/legal/LegalPage";

export const metadata: Metadata = {
  title: "Copyright / DMCA Policy — Meridian Legal Intelligence",
};

function H2({ children }: { children: React.ReactNode }) {
  return <h2 className="font-serif-brand text-xl font-semibold text-navy">{children}</h2>;
}

export default function DmcaPage() {
  return (
    <LegalPage title="Copyright / DMCA Policy" effectiveDate="October 5, 2026">
      <section>
        <H2>Respecting Copyright</H2>
        <p className="mt-3">
          Meridian respects the intellectual property rights of others and expects users of the
          Service to do the same. This policy explains how to notify us of a claimed copyright
          infringement involving content on our website or submitted to the Service, consistent
          with the U.S. Digital Millennium Copyright Act (DMCA) and equivalent laws elsewhere.
        </p>
      </section>

      <section>
        <H2>Filing a Notice</H2>
        <p className="mt-3">If you believe content accessible through the Service infringes your copyright, send a written notice including:</p>
        <ul className="mt-3 list-disc space-y-2 pl-6">
          <li>A physical or electronic signature of the copyright owner or an authorized agent;</li>
          <li>Identification of the copyrighted work claimed to have been infringed;</li>
          <li>Identification of the material claimed to be infringing and information reasonably sufficient to locate it;</li>
          <li>Your contact information (address, telephone number, and email);</li>
          <li>A statement that you have a good-faith belief that use of the material is not authorized by the copyright owner, its agent, or the law; and</li>
          <li>A statement, made under penalty of perjury, that the information in the notice is accurate and that you are authorized to act on behalf of the copyright owner.</li>
        </ul>
        <p className="mt-3">
          Send notices to our designated agent at{" "}
          <a href="mailto:dmca@meridianlegal.ai" className="font-medium text-navy underline">
            dmca@meridianlegal.ai
          </a>
          . <em>[Placeholder — to be completed: register a DMCA agent with the U.S. Copyright
          Office and list the registered name/address here if you operate in or serve U.S.
          users.]</em>
        </p>
      </section>

      <section>
        <H2>Counter-Notification</H2>
        <p className="mt-3">
          If you believe material you submitted was removed or disabled by mistake or
          misidentification, you may send a counter-notification containing your identification of
          the material and its location before removal, a statement under penalty of perjury that
          you have a good-faith belief it was removed in error, your contact information, and your
          consent to the jurisdiction of the applicable federal court.
        </p>
      </section>

      <section>
        <H2>Your Own Uploads</H2>
        <p className="mt-3">
          As set out in Section 4 of our{" "}
          <a href="/terms" className="font-medium text-navy underline">
            Terms of Service
          </a>
          , you represent that you have the rights necessary to upload any document to the Service.
          Do not upload material you do not have the right to use, including a third party&apos;s
          copyrighted work, without authorization.
        </p>
      </section>

      <section>
        <H2>Repeat Infringers</H2>
        <p className="mt-3">
          We may terminate the accounts of users determined to be repeat infringers in appropriate
          circumstances.
        </p>
      </section>
    </LegalPage>
  );
}
