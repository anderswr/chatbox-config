import { useState, useEffect } from "react";

export default function Admin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const [systemPrompt, setSystemPrompt] = useState("");
  const [speakText, setSpeakText] = useState("");

  useEffect(() => {
    if (isLoggedIn) {
      fetch("/config.json")
        .then((res) => res.json())
        .then((data) => {
          setSystemPrompt(data.system_prompt || "");
          setSpeakText(data.speak_text || "");
        });
    }
  }, [isLoggedIn]);

  async function handleLogin(e) {
    e.preventDefault();
    if (username === "PIADMIN") {
      const res = await fetch("/api/check-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const result = await res.json();
      if (result.ok) {
        setIsLoggedIn(true);
      } else {
        alert("Feil passord");
      }
    } else {
      alert("Feil brukernavn");
    }
  }

  async function handleSave(e) {
    e.preventDefault();
    const res = await fetch("/api/update-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ system_prompt: systemPrompt, speak_text: speakText }),
    });
    if (res.ok) alert("Lagret!");
    else alert("Kunne ikke lagre");
  }

  if (!isLoggedIn) {
    return (
      <div className="p-4 max-w-md mx-auto">
        <h1 className="text-xl font-bold mb-4">Admin Innlogging</h1>
        <form onSubmit={handleLogin} className="space-y-4">
          <input
            className="w-full p-2 border"
            placeholder="Brukernavn"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            className="w-full p-2 border"
            placeholder="Passord"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="bg-blue-600 text-white px-4 py-2 rounded" type="submit">
            Logg inn
          </button>
        </form>
      </div>
    );
  }

  return (
    <main className="p-4 max-w-xl mx-auto">
      <h1 className="text-xl font-bold mb-4">Rediger Samtalepartneren Liv</h1>
      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="block font-medium">System Prompt</label>
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            className="w-full p-2 border rounded"
          />
        </div>
        <div>
          <label className="block font-medium">Starttekst (speak)</label>
          <textarea
            value={speakText}
            onChange={(e) => setSpeakText(e.target.value)}
            className="w-full p-2 border rounded"
          />
        </div>
        <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded">
          Lagre
        </button>
      </form>
    </main>
  );
}
