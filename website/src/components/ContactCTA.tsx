"use client";

import { useState } from "react";

export default function ContactCTA() {
  const [sent, setSent] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSent(true);
  }

  return (
    <section id="contact" className="bg-navy-pale py-24">
      <div className="mx-auto grid max-w-7xl gap-14 px-6 md:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-gold">Get Started</p>
          <h2 className="font-serif-brand mt-3 text-3xl font-semibold text-navy md:text-4xl">
            Request a demo for your firm.
          </h2>
          <p className="mt-4 max-w-md text-navy/70">
            Tell us about your practice area and matter volume. We&apos;ll set up a workspace with
            a sample of your own documents so you can see cited answers against real material.
          </p>
          <p className="mt-8 text-sm text-navy/60">
            Already a client?{" "}
            <a
              href={process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}
              className="font-semibold text-navy underline underline-offset-4"
            >
              Log in to your workspace →
            </a>
          </p>
        </div>

        <div className="rounded-sm border border-navy/10 bg-white p-8 shadow-sm">
          {sent ? (
            <div className="flex h-full flex-col items-center justify-center py-12 text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-gold/15 text-gold">
                ✓
              </div>
              <h3 className="font-serif-brand text-lg font-semibold text-navy">Thank you.</h3>
              <p className="mt-2 text-sm text-navy/60">
                A member of our team will reach out within one business day.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block text-xs font-medium text-navy/70">Full name</label>
                <input required className="w-full rounded-sm border border-navy/20 px-3 py-2.5 text-sm" placeholder="Jordan Ellis" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-navy/70">Work email</label>
                <input required type="email" className="w-full rounded-sm border border-navy/20 px-3 py-2.5 text-sm" placeholder="jordan@yourfirm.com" />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-navy/70">Firm / organization</label>
                <input required className="w-full rounded-sm border border-navy/20 px-3 py-2.5 text-sm" placeholder="Ellis & Co." />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-navy/70">What are you looking to research or draft?</label>
                <textarea rows={3} className="w-full rounded-sm border border-navy/20 px-3 py-2.5 text-sm" placeholder="Brief description of your use case" />
              </div>
              <button type="submit" className="w-full rounded-sm bg-navy py-3 text-sm font-semibold text-white transition hover:bg-navy-light">
                Request a Demo
              </button>
              <p className="text-center text-xs text-navy/40">
                Meridian Legal Intelligence does not provide legal advice. All output is reviewed by licensed counsel.
              </p>
            </form>
          )}
        </div>
      </div>
    </section>
  );
}
