import { hasAdminSession } from "../../utils/admin-auth";
import { REALTIME_MODELS, REALTIME_VOICES, TRANSCRIPTION_MODELS } from "../../utils/realtime-options";

const MODELS = new Set(REALTIME_MODELS.map(({ value }) => value));
const VOICES = new Set(REALTIME_VOICES.map(({ value }) => value));
const TRANSCRIPTIONS = new Set(TRANSCRIPTION_MODELS.map(({ value }) => value));
const VAD_EAGERNESS = new Set(["low", "medium", "high", "auto"]);
const NOISE_REDUCTION = new Set(["off", "near_field", "far_field"]);
const REASONING_EFFORT = new Set(["minimal", "low", "medium", "high", "xhigh"]);

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Kun POST-støttet" });
  }

  if (!hasAdminSession(req)) {
    return res.status(401).json({ error: "Ikke innlogget" });
  }

  const {
    system_prompt, speak_text, voice, model, vad_eagerness, memory_enabled,
    memory_limit, speed, noise_reduction, transcription_model,
    max_output_tokens, reasoning_effort,
  } = req.body;

  if (typeof system_prompt !== "string" || typeof speak_text !== "string") {
    return res.status(400).json({ error: "Ugyldig input" });
  }

  if (!VOICES.has(voice)) {
    return res.status(400).json({ error: "Ugyldig stemme" });
  }
  if (!MODELS.has(model)) {
    return res.status(400).json({ error: "Ugyldig modell" });
  }
  if (!VAD_EAGERNESS.has(vad_eagerness)) {
    return res.status(400).json({ error: "Ugyldig VAD-innstilling" });
  }
  if (typeof memory_enabled !== "boolean" || !Number.isInteger(memory_limit) || memory_limit < 0 || memory_limit > 50) {
    return res.status(400).json({ error: "Ugyldig minneinnstilling" });
  }
  if (typeof speed !== "number" || speed < 0.25 || speed > 1.5) {
    return res.status(400).json({ error: "Ugyldig talehastighet" });
  }
  if (!NOISE_REDUCTION.has(noise_reduction) || !TRANSCRIPTIONS.has(transcription_model)) {
    return res.status(400).json({ error: "Ugyldig lydinnstilling" });
  }
  if (!Number.isInteger(max_output_tokens) || max_output_tokens < 1 || max_output_tokens > 4096) {
    return res.status(400).json({ error: "Ugyldig token-grense" });
  }
  if (!REASONING_EFFORT.has(reasoning_effort)) {
    return res.status(400).json({ error: "Ugyldig reasoning effort" });
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
      system_prompt: system_prompt.trim(),
      speak_text: speak_text.trim(),
      voice,
      model: model.trim(),
      vad_eagerness,
      memory_enabled,
      memory_limit,
      speed,
      noise_reduction,
      transcription_model,
      max_output_tokens,
      reasoning_effort,
    };

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
