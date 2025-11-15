export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Kun POST-støttet" });
  }

  const { system_prompt, speak_text, voice } = req.body;

  if (typeof system_prompt !== "string" || typeof speak_text !== "string") {
    return res.status(400).json({ error: "Ugyldig input" });
  }

  if (voice !== undefined && typeof voice !== "string") {
    return res.status(400).json({ error: "Ugyldig verdi for voice" });
  }

  const token = process.env.GH_TOKEN;
  const username = process.env.GH_USERNAME;
  const repo = process.env.GH_REPO;
  const path = "public/config.json"; // MÅ være i `public/` for at Pi skal kunne hente den
  const branch = "main";

  if (!token || !username || !repo) {
    return res.status(500).json({
      error: "Mangler GitHub-konfig (GH_TOKEN, GH_USERNAME, GH_REPO)",
    });
  }

  try {
    // Hent SHA for eksisterende fil
    const getRes = await fetch(
      `https://api.github.com/repos/${username}/${repo}/contents/${path}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github+json",
        },
      }
    );

    if (!getRes.ok) {
      const err = await getRes.json().catch(() => ({}));
      return res
        .status(500)
        .json({ error: "Kunne ikke hente SHA", details: err });
    }

    const fileData = await getRes.json();
    const sha = fileData.sha;

    // Bygg nytt config-objekt
    const configObj = {
      system_prompt,
      speak_text,
    };

    if (voice && voice.trim()) {
      configObj.voice = voice.trim();
    }

    // Nytt innhold som base64
    const newContent = Buffer.from(
      JSON.stringify(configObj, null, 2)
    ).toString("base64");

    // Oppdater fil
    const updateRes = await fetch(
      `https://api.github.com/repos/${username}/${repo}/contents/${path}`,
      {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github+json",
        },
        body: JSON.stringify({
          message: "Oppdatert config fra admin-nettsiden",
          content: newContent,
          sha: sha,
          branch: branch,
        }),
      }
    );

    if (!updateRes.ok) {
      const err = await updateRes.json().catch(() => ({}));
      return res
        .status(500)
        .json({ error: "Kunne ikke lagre til GitHub", details: err });
    }

    return res.status(200).json({ success: true });
  } catch (e) {
    return res
      .status(500)
      .json({ error: "Uventet feil", details: e.message || String(e) });
  }
}
