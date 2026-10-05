export default function Logo({ dark = false, className = "" }: { dark?: boolean; className?: string }) {
  const ink = dark ? "#F8F6F1" : "#0B1F3A";
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg width="30" height="30" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 3 L35 10 V19 C35 28 29 34.5 20 37 C11 34.5 5 28 5 19 V10 Z" stroke="#B68A35" strokeWidth="1.6" fill="none" />
        <path d="M13 21 L20 13 L27 21" stroke={ink} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <path d="M14 26 H26" stroke="#B68A35" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
      <span className="font-serif-brand text-lg font-semibold tracking-tight" style={{ color: ink }}>
        Meridian <span className="text-gold">Legal</span>
      </span>
    </span>
  );
}
