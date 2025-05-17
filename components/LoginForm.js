import { useState } from "react";

export default function LoginForm({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin(username, password).catch(() => {
      setError("Feil brukernavn eller passord");
    });
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
      <input
        type="text"
        placeholder="Brukernavn"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
        style={{ padding: "0.3rem" }}
      />
      <input
        type="password"
        placeholder="Passord"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        style={{ padding: "0.3rem" }}
      />
      <button type="submit" style={{ padding: "0.3rem 0.6rem" }}>
        Logg inn
      </button>
      {error && <span style={{ color: "red", marginLeft: "1rem" }}>{error}</span>}
    </form>
  );
}
