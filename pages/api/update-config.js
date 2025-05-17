// pages/api/update-config.js
export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).end();

  const { system_prompt, speak_text } = req.body;
  const token = process.env.GH_WRITE_TOKEN;
  const repo = "DITT_BRUKERNAVN/chatbox-config";

  const configPath = "public/config.json";

  const apiUrl = `https://api.github.com/repos/${repo}/contents/${configPath}`;

  // Hent eksisterende fil for SHA
  const current = await fetch(apiUrl, {
    headers: { Authorization: `Bearer ${token}` },
  }).then((r) => r.json());

  const content = {
    system_prompt,
    speak_text,
  };

  const response = await fetch(apiUrl, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: "Oppdatert config.json fra admin-panelet",
      content: Buffer.from(JSON.stringify(content, null, 2)).toString("base64"),
      sha: current.sha,
    }),
  });

  if (response.ok) {
    res.status(200).json({ ok: true });
  } else {
    const error = await response.json();
    res.status(500).json({ error });
  }
}
