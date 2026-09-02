import { useEffect, useState } from "react";
import LivLogo from "../components/LivLogo";
import { REALTIME_MODELS, REALTIME_VOICES, TRANSCRIPTION_MODELS } from "../utils/realtime-options";

const VAD_OPTIONS = [
  ["auto", "Automatisk"], ["low", "Rolig – venter lenger"],
  ["medium", "Medium"], ["high", "Rask – svarer tidligere"],
];

const INITIAL = {
  system_prompt: "", speak_text: "", voice: "marin", model: "gpt-realtime",
  vad_eagerness: "auto", memory_enabled: true, memory_limit: 8, speed: 0.9,
  noise_reduction: "far_field", transcription_model: "gpt-realtime-whisper",
  max_output_tokens: 2048, reasoning_effort: "low",
};

const REASONING_OPTIONS = [
  ["minimal", "Svært kort (minst tenking)"], ["low", "Kort (rask)"],
  ["medium", "Balansert (middels)"], ["high", "Grundig (mer tenking)"],
  ["xhigh", "Svært grundig (mest tenking)"],
];

function modelName(value) {
  return REALTIME_MODELS.find((option) => option.value === value)?.label || value;
}

function Field({ label, hint, children }) {
  return <label className="field"><span>{label}</span>{hint && <small>{hint}</small>}{children}</label>;
}

function Login({ onLogin }) {
  const [username, setUsername] = useState("boks1");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    const response = await fetch("/api/check-password", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    setBusy(false);
    if (response.ok) onLogin(); else setError("Feil brukernavn eller passord.");
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <LivLogo />
        <div><h1>Logg inn</h1><p>For familie og pårørende.</p></div>
        <form onSubmit={submit} className="login-form">
          <Field label="Brukernavn"><input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></Field>
          <Field label="Passord"><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required autoFocus /></Field>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary button-full" disabled={busy}>{busy ? "Logger inn …" : "Logg inn"}</button>
        </form>
      </section>
    </main>
  );
}

export default function Admin() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [config, setConfig] = useState(INITIAL);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  function update(name, value) { setConfig((current) => ({ ...current, [name]: value })); }

  useEffect(() => {
    if (!loggedIn) return;
    setLoading(true);
    fetch(`/api/config?t=${Date.now()}`, { cache: "no-store" })
      .then((response) => { if (!response.ok) throw new Error(); return response.json(); })
      .then((data) => setConfig({ ...INITIAL, ...data, system_prompt: data.system_prompt || data.system_instruction || "" }))
      .catch(() => setMessage("Kunne ikke hente innstillingene. Prøv igjen."))
      .finally(() => setLoading(false));
  }, [loggedIn]);

  async function save(event) {
    event.preventDefault(); setSaving(true); setMessage("");
    const payload = {
      ...config, memory_limit: Number(config.memory_limit), speed: Number(config.speed),
      max_output_tokens: Number(config.max_output_tokens),
    };
    const response = await fetch("/api/update-config", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      setSaving(false);
      setMessage(`${result.error || "Kunne ikke lagre innstillingene."}${result.details?.message ? ` ${result.details.message}` : ""}`);
      return;
    }
    const commitQuery = /^[a-f0-9]{40}$/i.test(result.commit || "") ? `ref=${result.commit}&` : "";
    const verification = await fetch(`/api/config?${commitQuery}t=${Date.now()}`, { cache: "no-store" });
    const verifiedConfig = await verification.json().catch(() => null);
    const verified = verification.ok && verifiedConfig && Object.entries(result.saved_config).every(([key, value]) => verifiedConfig[key] === value);
    setSaving(false);
    setMessage(verified
      ? `Alle innstillingene er lagret og kontrollert i GitHub.${result.github_url ? ` ${result.github_url}` : ""}`
      : "GitHub tok imot lagringen, men kontrollen av den nye config-filen feilet. Prøv å laste siden på nytt.");
  }

  if (!loggedIn) return <Login onLogin={() => setLoggedIn(true)} />;

  return (
    <main className="admin-shell">
      <header className="admin-topbar">
        <LivLogo compact />
        <div><span>Familie og pårørende</span><button className="button button-secondary button-small" onClick={() => setLoggedIn(false)}>Logg ut</button></div>
      </header>

      <section className="status-grid" aria-label="Status">
        <article className="status-card status-positive"><span>Boksen</span><strong><i /> Konfigurasjon klar</strong></article>
        <article className="status-card"><span>Oppdatering</span><strong>Hvert 5. minutt</strong></article>
        <article className="status-card"><span>Lokalt minne</span><strong>{config.memory_enabled ? "Slått på" : "Slått av"}</strong></article>
        <article className="status-card"><span>Samtalemodell</span><strong>{modelName(config.model)}</strong></article>
      </section>

      <form onSubmit={save} className="settings-grid">
        <div className="settings-column settings-main">
          <section className="settings-card prompt-card">
            <h1>Hvem er Astrid?</h1>
            <p>Dette leser Liv før hver samtale. Skriv som om du forteller det til en ny hjemmehjelp.</p>
            <textarea maxLength={4000} value={config.system_prompt} onChange={(e) => update("system_prompt", e.target.value)} rows={13} disabled={loading} />
            <div className="card-actions"><span>{config.system_prompt.length.toLocaleString("nb-NO")} av 4 000 tegn</span></div>
          </section>

          <section className="settings-card info-card">
            <h2>Dagen hennes</h2>
            <p>Liv bruker hovedinstruksen og det lokale minnet for å holde samtalen personlig og gjenkjennelig.</p>
            <div className="soft-row"><strong>Hovedinstruks</strong><span>Sendes til hver nye samtale</span></div>
            <div className="soft-row"><strong>Oppdateringer</strong><span>Hentes automatisk fra nettsiden</span></div>
            <div className="soft-row"><strong>Personlig minne</strong><span>{config.memory_enabled ? `${config.memory_limit} relevante minner per samtale` : "Lagring er slått av"}</span></div>
          </section>
        </div>

        <div className="settings-column">
          <section className="settings-card voice-card">
            <h2>Stemmen</h2>
            <Field label="Hvem skal snakke">
              <select value={config.voice} onChange={(e) => update("voice", e.target.value)}>{REALTIME_VOICES.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select>
            </Field>
            <Field label="Talehastighet" hint={`${Number(config.speed).toFixed(2).replace(".", ",")} ×`}>
              <input type="range" min="0.25" max="1.5" step="0.05" value={config.speed} onChange={(e) => update("speed", e.target.value)} />
            </Field>
            <Field label="Første setning når boksen slås på"><textarea rows={3} value={config.speak_text} onChange={(e) => update("speak_text", e.target.value)} /></Field>
            <label className="toggle-row"><span><strong>Liv husker samtaler</strong><small>{config.memory_enabled ? `${config.memory_limit} relevante minner` : "Slått av"}</small></span><input type="checkbox" checked={config.memory_enabled} onChange={(e) => update("memory_enabled", e.target.checked)} /><i /></label>
          </section>

          <details className="technical-card" open>
            <summary><span><strong>Tekniske innstillinger</strong><small>Samtalemodell, støyfjerning, teksting og svarlengde.</small></span><b>⌄</b></summary>
            <div className="technical-fields">
              <Field label="Samtalemodell"><select value={config.model} onChange={(e) => update("model", e.target.value)}>{REALTIME_MODELS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></Field>
              <Field label="Når skal Liv svare?"><select value={config.vad_eagerness} onChange={(e) => update("vad_eagerness", e.target.value)}>{VAD_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
              <Field label="Støyreduksjon"><select value={config.noise_reduction} onChange={(e) => update("noise_reduction", e.target.value)}><option value="far_field">Far field – Jabra</option><option value="near_field">Near field – nær mikrofon</option><option value="off">Av</option></select></Field>
              <Field label="Transkripsjon"><select value={config.transcription_model} onChange={(e) => update("transcription_model", e.target.value)}>{TRANSCRIPTION_MODELS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></Field>
              <div className="field-pair">
                <Field label="Maksimal svarlengde"><select value={config.max_output_tokens} onChange={(e) => update("max_output_tokens", e.target.value)}><option value="512">Kort (ca. 20 sek.)</option><option value="1024">Normal (ca. 40 sek.)</option><option value="2048">Lang (anbefalt)</option><option value="4096">Svært lang (mer bruk)</option></select></Field>
                <Field label="Minner per samtale"><input type="number" min="0" max="50" value={config.memory_limit} onChange={(e) => update("memory_limit", e.target.value)} disabled={!config.memory_enabled} /></Field>
              </div>
              <Field label="Hvor grundig skal Liv tenke?"><select value={config.reasoning_effort} onChange={(e) => update("reasoning_effort", e.target.value)}>{REASONING_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
            </div>
          </details>
        </div>
        <footer className="save-footer">
          <div><strong>Lagre alle innstillinger</strong><span>Hovedinstruks, stemme og tekniske valg lagres samlet.</span></div>
          <button className="button button-primary" disabled={saving || loading}>{saving ? "Lagrer …" : "Lagre og send til boksen"}</button>
          {message && <p className={message.startsWith("Alle innstillingene") ? "save-message success" : "save-message error"} role="status">{message}</p>}
        </footer>
      </form>
    </main>
  );
}
