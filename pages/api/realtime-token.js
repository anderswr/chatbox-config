import crypto from "crypto";

const VOICES = new Set(["marin", "cedar", "alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse"]);

function safeEqual(first, second) {
  const left = Buffer.from(first || "");
  const right = Buffer.from(second || "");
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Kun POST er støttet" });
  }

  const expectedDeviceToken = process.env.RASPBERRY_DEVICE_TOKEN || "";
  const providedDeviceToken = (req.headers.authorization || "").replace(/^Bearer\s+/i, "");
  if (!expectedDeviceToken || !safeEqual(providedDeviceToken, expectedDeviceToken)) {
    return res.status(401).json({ error: "Ugyldig enhet" });
  }

  const apiKey = process.env.OPENAI_API_KEY || "";
  if (!apiKey) {
    return res.status(500).json({ error: "OPENAI_API_KEY mangler i Vercel" });
  }

  const { model = "gpt-realtime", voice = "marin" } = req.body || {};
  if (typeof model !== "string" || !/^[a-zA-Z0-9._-]{1,100}$/.test(model)) {
    return res.status(400).json({ error: "Ugyldig modell" });
  }
  if (!VOICES.has(voice)) {
    return res.status(400).json({ error: "Ugyldig stemme" });
  }

  try {
    const response = await fetch("https://api.openai.com/v1/realtime/client_secrets", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session: {
          type: "realtime",
          model,
          audio: { output: { voice } },
        },
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.value) {
      return res.status(response.status || 502).json({
        error: "Kunne ikke opprette kortlivet Realtime-nøkkel",
        details: data.error?.message,
      });
    }
    res.setHeader("Cache-Control", "no-store");
    return res.status(200).json({ value: data.value, expires_at: data.expires_at });
  } catch (error) {
    return res.status(502).json({ error: "Kontakt med OpenAI feilet", details: error.message });
  }
}
