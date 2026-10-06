import Logo from "./Logo";

export default function Footer() {
  return (
    <footer className="border-t border-navy/10 bg-navy text-white/60">
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="flex flex-col gap-10 md:flex-row md:justify-between">
          <div className="max-w-xs">
            <Logo dark />
            <p className="mt-4 text-sm leading-relaxed">
              AI-powered legal research and drafting, grounded in your documents and verified
              before delivery.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-10 sm:grid-cols-3">
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-widest text-white/40">Company</h4>
              <ul className="mt-4 space-y-2.5 text-sm">
                <li><a href="/#about" className="hover:text-white">About</a></li>
                <li><a href="/#services" className="hover:text-white">Services</a></li>
                <li><a href="/#trust" className="hover:text-white">Trust &amp; Security</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-widest text-white/40">Platform</h4>
              <ul className="mt-4 space-y-2.5 text-sm">
                <li><a href="/portal" className="hover:text-white">Client Login</a></li>
                <li><a href="/#contact" className="hover:text-white">Request a Demo</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-widest text-white/40">Legal</h4>
              <ul className="mt-4 space-y-2.5 text-sm">
                <li><a href="/disclaimer" className="hover:text-white">AI Output Disclaimer</a></li>
                <li><a href="/privacy" className="hover:text-white">Privacy Policy</a></li>
                <li><a href="/terms" className="hover:text-white">Terms of Service</a></li>
                <li><a href="/subprocessors" className="hover:text-white">Subprocessors</a></li>
                <li><a href="/dmca" className="hover:text-white">Copyright / DMCA</a></li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-12 border-t border-white/10 pt-6 text-xs text-white/40">
          © {new Date().getFullYear()} Meridian Legal Intelligence. All rights reserved. Meridian
          does not practice law or provide legal advice.
        </div>
      </div>
    </footer>
  );
}
