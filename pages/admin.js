import { useState } from "react";

export default function Admin() {
  const [systemPrompt, setSystemPrompt] = useState("");
  const [speakText, setSpeakText] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    const res = await fetch("/api/update-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ system_prompt: systemPrompt, speak_text: speakText }),
    });
    if (res.ok) alert("Oppdatert!");
    else alert("Feil ved oppdatering");
  }

  return (
    <main className="p-4 max-w-xl mx-auto">
      <h1 className="text-xl font-bold mb-4">Rediger Samtalepartneren Liv</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block font-medium">System Prompt</label>
          <textarea value={systemPrompt} onChange={e => setSystemPrompt(e.target.value)} className="w-full p-2 border rounded" />
        </div>
        <div>
          <label className="block font-medium">Starttekst (speak)</label>
          <textarea value={speakText} onChange={e => setSpeakText(e.target.value)} className="w-full p-2 border rounded" />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Lagre</button>
      </form>
    </main>
  );
}
