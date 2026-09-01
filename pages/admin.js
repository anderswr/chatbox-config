import { useState, useEffect } from "react";

const VOICE_OPTIONS = [
  { value: "marin", label: "Marin (anbefalt)" },
  { value: "cedar", label: "Cedar (anbefalt)" },
  { value: "alloy", label: "Alloy" },
  { value: "ash", label: "Ash" },
  { value: "ballad", label: "Ballad" },
  { value: "coral", label: "Coral" },
  { value: "echo", label: "Echo" },
  { value: "sage", label: "Sage" },
  { value: "shimmer", label: "Shimmer" },
  { value: "verse", label: "Verse" },
];

const VAD_OPTIONS = [
  { value: "low", label: "Rolig – venter lenger" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "Rask – svarer tidligere" },
  { value: "auto", label: "Automatisk" },
];

export default function Admin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const [systemPrompt, setSystemPrompt] = useState("");
  const [speakText, setSpeakText] = useState("");
  const [voice, setVoice] = useState("alloy");
  const [model, setModel] = useState("gpt-realtime");
  const [vadEagerness, setVadEagerness] = useState("auto");
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [memoryLimit, setMemoryLimit] = useState(8);

  useEffect(() => {
    if (isLoggedIn) {
      fetch("/config.json")
        .then((res) => {
          if (!res.ok) {
            throw new Error("Kunne ikke hente config.json");
          }
          return res.json();
        })
        .then((data) => {
          // Støtt både system_prompt og system_instruction, men skriv tilbake som system_prompt
          setSystemPrompt(data.system_prompt || data.system_instruction || "");
          setSpeakText(data.speak_text || "");
          setVoice(data.voice || "alloy");
          setModel(data.model || "gpt-realtime");
          setVadEagerness(data.vad_eagerness || "auto");
          setMemoryEnabled(data.memory_enabled !== false);
          setMemoryLimit(data.memory_limit ?? 8);
        })
        .catch((err) => {
          console.error("Feil ved henting av config:", err);
          alert("Kunne ikke hente config fra serveren (se konsollen for detaljer).");
        });
    }
  }, [isLoggedIn]);

  async function handleLogin(e) {
    e.preventDefault();
    const res = await fetch("/api/check-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const result = await res.json();
      if (result.ok) {
        setIsLoggedIn(true);
      } else {
        alert("Feil brukernavn eller passord");
      }
  }

  async function handleSave(e) {
    e.preventDefault();
    const res = await fetch("/api/update-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_prompt: systemPrompt,
        speak_text: speakText,
        voice: voice,
        model,
        vad_eagerness: vadEagerness,
        memory_enabled: memoryEnabled,
        memory_limit: Number(memoryLimit),
      }),
    });
    if (res.ok) {
      alert("Lagret!");
    } else {
      const err = await res.json().catch(() => ({}));
      console.error("Feil ved lagring:", err);
      alert("Kunne ikke lagre");
    }
  }

  const layoutStyle = {
    fontFamily: "sans-serif",
    lineHeight: "1.6",
    display: "flex",
    flexDirection: "column",
    minHeight: "100vh",
    backgroundColor: "#f9fafb",
  };

  const containerStyle = {
    flex: 1,
    maxWidth: "600px",
    margin: "2rem auto",
    padding: "1.5rem",
    backgroundColor: "white",
    borderRadius: "1rem",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.05)",
  };

  const footerStyle = {
    padding: "1rem",
    textAlign: "center",
    backgroundColor: "#f3f4f6",
    fontSize: "0.875rem",
    color: "#4b5563",
  };

  if (!isLoggedIn) {
    return (
      <div style={layoutStyle}>
        <div style={containerStyle}>
          <h1
            style={{
              fontSize: "1.5rem",
              fontWeight: "bold",
              marginBottom: "1rem",
            }}
          >
            Innlogging for å tilpasse boks1 din
          </h1>
          <form
            onSubmit={handleLogin}
            style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
          >
            <input
              style={{
                padding: "0.75rem",
                border: "1px solid #ccc",
                borderRadius: "0.5rem",
              }}
              placeholder="Brukernavn"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <input
              type="password"
              style={{
                padding: "0.75rem",
                border: "1px solid #ccc",
                borderRadius: "0.5rem",
              }}
              placeholder="Passord"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button
              type="submit"
              style={{
                backgroundColor: "#2563eb",
                color: "white",
                padding: "0.75rem",
                border: "none",
                borderRadius: "0.5rem",
                cursor: "pointer",
              }}
            >
              Logg inn
            </button>
          </form>
        </div>
        <footer style={footerStyle}>
          © {new Date().getFullYear()}{" "}
          <a
            href="https://www.dmz.no"
            style={{ color: "#2563eb", textDecoration: "none" }}
          >
            DMZ DATA AS
          </a>
          . Alle rettigheter reservert.
        </footer>
      </div>
    );
  }

  return (
    <div style={layoutStyle}>
      <div style={containerStyle}>
        <h1
          style={{
            fontSize: "1.5rem",
            fontWeight: "bold",
            marginBottom: "1rem",
          }}
        >
          Tilpass samtalepartneren
        </h1>

        <form
          onSubmit={handleSave}
          style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}
        >
          <div>
            <label style={{ display: "block", fontWeight: "600", marginBottom: "0.5rem" }}>
              Realtime-modell
            </label>
            <p style={{ fontSize: "0.85rem", color: "#6b7280", marginTop: 0 }}>
              Modell-ID kan oppdateres når en ny støttet Realtime-modell blir tilgjengelig.
            </p>
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              style={{ width: "100%", padding: "0.75rem", borderRadius: "0.5rem", border: "1px solid #ccc" }}
              required
            />
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontWeight: "600",
                marginBottom: "0.5rem",
              }}
            >
              Hvem er boksen, hvordan skal den svare? (system prompt)
            </label>
            <p style={{ fontSize: "0.85rem", color: "#6b7280", marginTop: 0 }}>
              Dette er “personligheten” til boks1. Den vises aldri til brukeren,
              men styrer hvordan den snakker, hva den prioriterer osv.
            </p>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              style={{
                width: "100%",
                padding: "0.75rem",
                borderRadius: "0.5rem",
                border: "1px solid #ccc",
              }}
              rows={4}
            />
          </div>

          <div>
            <label style={{ display: "block", fontWeight: "600", marginBottom: "0.5rem" }}>
              Talegjenkjenning (semantic VAD)
            </label>
            <select
              value={vadEagerness}
              onChange={(e) => setVadEagerness(e.target.value)}
              style={{ width: "100%", padding: "0.75rem", borderRadius: "0.5rem", border: "1px solid #ccc", backgroundColor: "white" }}
            >
              {VAD_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: "600" }}>
              <input
                type="checkbox"
                checked={memoryEnabled}
                onChange={(e) => setMemoryEnabled(e.target.checked)}
              />
              Bruk lokalt minne på Raspberry Pi-en
            </label>
            <label style={{ display: "block", marginTop: "0.75rem", fontSize: "0.9rem" }}>
              Maks minner per session
            </label>
            <input
              type="number"
              min="0"
              max="50"
              value={memoryLimit}
              onChange={(e) => setMemoryLimit(e.target.value)}
              disabled={!memoryEnabled}
              style={{ width: "100%", padding: "0.75rem", borderRadius: "0.5rem", border: "1px solid #ccc" }}
            />
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontWeight: "600",
                marginBottom: "0.5rem",
              }}
            >
              Oppstarts-setning (speak_text)
            </label>
            <p style={{ fontSize: "0.85rem", color: "#6b7280", marginTop: 0 }}>
              Dette er det første den sier høyt når den starter eller restarter
              – en hyggelig liten intro til samtalen.
            </p>
            <textarea
              value={speakText}
              onChange={(e) => setSpeakText(e.target.value)}
              style={{
                width: "100%",
                padding: "0.75rem",
                borderRadius: "0.5rem",
                border: "1px solid #ccc",
              }}
              rows={3}
            />
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontWeight: "600",
                marginBottom: "0.5rem",
              }}
            >
              Stemmetype
            </label>
            <p style={{ fontSize: "0.85rem", color: "#6b7280", marginTop: 0 }}>
              Velg hvilken stemme boks1 skal bruke når den snakker. Endring
              trer i kraft neste gang boksen starter.
            </p>
            <select
              value={voice}
              onChange={(e) => setVoice(e.target.value)}
              style={{
                width: "100%",
                padding: "0.75rem",
                borderRadius: "0.5rem",
                border: "1px solid #ccc",
                backgroundColor: "white",
              }}
            >
              {VOICE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label} ({opt.value})
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            style={{
              backgroundColor: "#059669",
              color: "white",
              padding: "0.75rem",
              border: "none",
              borderRadius: "0.5rem",
              cursor: "pointer",
            }}
          >
            Lagre
          </button>
        </form>
      </div>
      <footer style={footerStyle}>
        © {new Date().getFullYear()}{" "}
        <a
          href="https://www.dmz.no"
          style={{ color: "#2563eb", textDecoration: "none" }}
        >
          DMZ DATA AS
        </a>
        . Alle rettigheter reservert.
      </footer>
    </div>
  );
}
