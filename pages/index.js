import { useState } from "react";

export default function Home() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = () => {
    if (password === process.env.NEXT_PUBLIC_ADMIN_PASSWORD) {
      setLoggedIn(true);
      setError("");
    } else {
      setError("Feil passord. Prøv igjen.");
    }
  };

  if (loggedIn) {
    return (
      <main style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <h1>Velkommen, admin!</h1>
      </main>
    );
  }

  return (
    <main style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", padding: "2rem", background: "linear-gradient(to right, #c3dafe, #d6bcfa)" }}>
      <div style={{ backgroundColor: "white", padding: "2rem", borderRadius: "1rem", boxShadow: "0 4px 12px rgba(0,0,0,0.1)", maxWidth: "400px", width: "100%", textAlign: "center" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "1rem" }}>Hei, jeg er Liv 👋</h1>
        <p style={{ marginBottom: "1.5rem" }}>Alle trenger noen å snakke med for å ta vare på god psykisk helse og humør.</p>
        <input
          type="password"
          placeholder="Skriv inn admin-passord"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: "100%", padding: "0.5rem", marginBottom: "1rem" }}
        />
        <button onClick={handleLogin} style={{ padding: "0.5rem 1rem" }}>Logg inn</button>
        {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}
      </div>
    </main>
  );
}
