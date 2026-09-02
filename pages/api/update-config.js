import { hasAdminSession } from "../../utils/admin-auth";
import { REALTIME_MODELS, REALTIME_VOICES, TRANSCRIPTION_MODELS } from "../../utils/realtime-options";
import { contentsUrl, githubHeaders, githubSettings } from "../../utils/github-config";

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

  const github = githubSettings();

  if (!github.token) {
    return res.status(500).json({
      error: "Mangler GH_TOKEN (eller GITHUB_TOKEN) i Vercel",
    });
  }

  try {
    // Hent SHA for eksisterende fil
    const getRes = await fetch(
      contentsUrl(github),
      {
        headers: githubHeaders(github.token),
        cache: "no-store",
      }
    );

    if (!getRes.ok) {
      const err = await getRes.json().catch(() => ({}));
      return res
        .status(502)
        .json({ error: "Kunne ikke lese config fra GitHub. Kontroller repo og token.", details: err });
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
      `https://api.github.com/repos/${github.fullName}/contents/${github.path}`,
      {
        method: "PUT",
        headers: {
          ...githubHeaders(github.token),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: "Oppdatert config fra admin-nettsiden",
          content: newContent,
          sha: sha,
          branch: github.branch,
        }),
      }
    );

    const updateData = await updateRes.json().catch(() => ({}));
    if (!updateRes.ok) {
      return res
        .status(502)
        .json({ error: "GitHub avviste lagringen. Tokenet må ha Contents: Read and write.", details: updateData });
    }

    return res.status(200).json({
      success: true,
      saved_config: configObj,
      commit: updateData.commit?.sha || null,
      github_url: updateData.content?.html_url || null,
      config_url: "/api/config",
    });
  } catch (e) {
    return res
      .status(500)
      .json({ error: "Uventet feil", details: e.message || String(e) });
  }
}
