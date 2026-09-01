export default function LivLogo({ compact = false }) {
  return (
    <div className="brand" aria-label="Liv">
      <svg width={compact ? 26 : 30} height={compact ? 26 : 30} viewBox="0 0 30 30" fill="none" aria-hidden="true">
        <circle cx="15" cy="15" r="14" fill="#c8613f" />
        <path d="M9 15c0-3.3 2.7-6 6-6s6 2.7 6 6-2.7 6-6 6" stroke="#faf6ef" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <span>{compact ? "Livs boks hos Astrid" : "Liv"}</span>
    </div>
  );
}
