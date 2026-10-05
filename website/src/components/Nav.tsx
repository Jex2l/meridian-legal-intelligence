"use client";

import { useState } from "react";
import Logo from "./Logo";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

const LINKS = [
  { href: "#services", label: "Services" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "#trust", label: "Trust & Security" },
  { href: "#about", label: "About" },
  { href: "#contact", label: "Contact" },
];

export default function Nav() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-navy/10 bg-background/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <a href="#top" aria-label="Meridian Legal Intelligence home">
          <Logo />
        </a>

        <nav className="hidden items-center gap-8 md:flex">
          {LINKS.map((link) => (
            <a key={link.href} href={link.href} className="text-sm font-medium text-navy/80 hover:text-navy">
              {link.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <a href={APP_URL} className="text-sm font-medium text-navy/80 hover:text-navy">
            Client Login
          </a>
          <a
            href="#contact"
            className="rounded-sm bg-navy px-4 py-2 text-sm font-semibold text-white transition hover:bg-navy-light"
          >
            Request a Demo
          </a>
        </div>

        <button
          onClick={() => setOpen(!open)}
          className="flex h-9 w-9 items-center justify-center text-navy md:hidden"
          aria-label="Toggle menu"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M3 6h18M3 12h18M3 18h18" />}
          </svg>
        </button>
      </div>

      {open && (
        <div className="border-t border-navy/10 bg-background px-6 py-4 md:hidden">
          <nav className="flex flex-col gap-4">
            {LINKS.map((link) => (
              <a key={link.href} href={link.href} className="text-sm font-medium text-navy/80" onClick={() => setOpen(false)}>
                {link.label}
              </a>
            ))}
            <a href={APP_URL} className="text-sm font-medium text-navy/80">
              Client Login
            </a>
            <a href="#contact" className="rounded-sm bg-navy px-4 py-2 text-center text-sm font-semibold text-white">
              Request a Demo
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}
