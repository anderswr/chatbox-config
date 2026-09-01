import { contentsUrl, githubHeaders, githubSettings } from "../../utils/github-config";

export default async function handler(req, res) {
  if (req.method !== "GET") return res.status(405).json({ error: "Kun GET er støttet" });

  const settings = githubSettings();
  try {
    const response = await fetch(contentsUrl(settings), {
      headers: githubHeaders(settings.token),
      cache: "no-store",
    });
    if (!response.ok) {
      const details = await response.json().catch(() => ({}));
      return res.status(502).json({ error: "Kunne ikke hente konfigurasjonen fra GitHub", details });
    }
    const file = await response.json();
    const config = JSON.parse(Buffer.from(file.content, "base64").toString("utf8"));
    res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate, proxy-revalidate");
    res.setHeader("CDN-Cache-Control", "no-store");
    res.setHeader("Vercel-CDN-Cache-Control", "no-store");
    return res.status(200).json(config);
  } catch (error) {
    return res.status(502).json({ error: "Kunne ikke lese konfigurasjonen", details: error.message });
  }
}

