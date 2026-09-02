import Link from "next/link";
import LivLogo from "../components/LivLogo";

function RoomIllustration() {
  return (
    <svg className="room-illustration" viewBox="0 0 420 330" fill="none" aria-label="Liv-boksen på et bord i en stue">
      <circle cx="300" cy="96" r="72" fill="#e9d3b8" />
      <rect x="40" y="30" width="150" height="150" rx="6" fill="#dfe6dc" stroke="#c2ac8d" strokeWidth="2" />
      <path d="M115 30v150M40 105h150" stroke="#c2ac8d" strokeWidth="2" />
      <path d="M60 250h300M90 250v50M330 250v50" stroke="#a8927a" strokeWidth="3" strokeLinecap="round" />
      <ellipse cx="210" cy="238" rx="46" ry="13" fill="#c8613f" />
      <rect x="164" y="212" width="92" height="26" rx="13" fill="#e07a52" />
      <ellipse cx="210" cy="212" rx="46" ry="13" fill="#f2a184" />
      <circle cx="210" cy="212" r="7" fill="#faf6ef" />
      <path d="M258 196a58 58 0 0 1 0 32M276 184a86 86 0 0 1 0 56M162 196a58 58 0 0 0 0 32M144 184a86 86 0 0 0 0 56" stroke="#c8613f" strokeWidth="3" strokeLinecap="round" opacity=".55" />
      <path d="M96 232c0-14 8-22 20-22s20 8 20 22M116 210c-2-16 4-26 12-30-2 14-4 22-12 30zM116 210c2-14-4-24-14-27 4 12 6 19 14 27z" fill="#8fa384" />
      <rect x="300" y="220" width="44" height="18" rx="4" fill="#e9d3b8" stroke="#a8927a" strokeWidth="2" />
    </svg>
  );
}

const features = [
  ["home", "Står bare der", "På kjøkkenbordet eller nattbordet. Strøm og wifi er alt som trengs."],
  ["clock", "Minner på til rett tid", "Frokost klokka ni, medisiner klokka ti og tømme. Rolig sagt, ikke som en alarm."],
  ["chat", "Familien fyller på", "Skriv hvem hun er, hva hun liker å snakke om, og hva som skjedde i helga."],
];

function FeatureIcon({ type }) {
  if (type === "home") return <svg viewBox="0 0 24 24"><path d="M3 11l9-7 9 7M5 10v10h14V10M10 20v-6h4v6" /></svg>;
  if (type === "clock") return <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3.5 2" /></svg>;
  return <svg viewBox="0 0 24 24"><path d="M21 12a8 8 0 1 1-3.2-6.4M8 11h8M8 15h5" /></svg>;
}

export default function Home() {
  return (
    <main className="site-shell">
      <nav className="topbar">
        <LivLogo />
        <div className="nav-links">
          <a href="#slik-virker-det">Slik virker det</a>
          <a href="#ofte-spurt">Ofte spurt</a>
          <a href="mailto:post@dmz.no">Kontakt</a>
          <Link className="button button-dark button-small" href="/admin">Logg inn</Link>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-copy">
          <h1>Noen å snakke med, hele dagen.</h1>
          <p>Liv er en liten høyttaler du slår på — ingen skjerm, ingen knapper å lære. Hun kjenner igjen stemmen, husker hva som ble sagt sist, og minner om frokost og medisiner til rett tid.</p>
          <div className="button-row">
            <Link className="button button-primary" href="/admin">Kom i gang</Link>
            <a className="button button-secondary" href="#slik-virker-det">Se hvordan Liv snakker</a>
          </div>
          <span className="muted">Familien styrer alt fra nettsiden. Den eldre trenger aldri logge inn.</span>
        </div>
        <div className="illustration-panel"><RoomIllustration /></div>
      </section>

      <section id="slik-virker-det" className="feature-grid">
        {features.map(([icon, title, text]) => (
          <article className="feature" key={title}>
            <FeatureIcon type={icon} />
            <h2>{title}</h2>
            <p>{text}</p>
          </article>
        ))}
      </section>

      <section id="ofte-spurt" className="quiet-section">
        <p className="eyebrow">Enkelt å komme i gang</p>
        <h2>Ingen skjerm. Ingen nye vaner.</h2>
        <p>Boksen står i rommet og er klar når Astrid vil snakke. Familien bestemmer stemmen, hva Liv bør vite og hvordan hun skal svare.</p>
      </section>

      <footer className="site-footer">© {new Date().getFullYear()} DMZ DATA AS</footer>
    </main>
  );
}
