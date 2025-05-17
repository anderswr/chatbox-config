import { useState, useEffect } from "react";

export default function Admin() {
  // Defaultverdier, kan hentes fra backend senere
  const [systemPrompt, setSystemPrompt] = useState(
    "her kommer teksten du kan editere på nettsiden"
  );
  const [speakText, setSpeakText] = useState(
    "en tekst du kan redigere på nettsiden"
  );

  // Her kan du legge til lagring til backend / API senere
  const handleSave = () => {
    alert("Tekstene er lagret (funksjonalitet kan bygges videre)");
  };

  return (
    <div
      style={{
        maxWidth: "600px",
        margin: "3rem auto",
        fontFamily:
          "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      }}
    >
      <h1>Admin: Rediger samtalepartneren Liv</h1>

      <label htmlFor="systemPrompt" style={{ fontWeight: "bold" }}>
        System prompt:
      </label>
      <textarea
        id="systemPrompt"
        value={systemPrompt}
        onChange={(e) => setSystemPrompt(e.target.value)}
        rows={5}
        style={{ width: "100%", padding: "0.5rem", marginBottom: "1rem" }}
      />

      <label htmlFor="speakText" style={{ fontWeight: "bold" }}>
        Speak tekst:
      </label>
      <textarea
        id="speakText"
        value={speakText}
        onChange={(e) => setSpeakText(e.target.value)}
        rows={3}
        style={{ width: "100%", padding: "0.5rem", marginBottom: "1rem" }}
      />

      <button
        onClick={handleSave}
        style={{
          padding: "0.5rem 1rem",
          backgroundColor: "#0070f3",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
        }}
      >
        Lagre
      </button>
    </div>
  );
}
