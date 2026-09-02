export default function handler(req, res) {
  if (req.method !== "GET") {
    return res.status(405).json({ error: "Kun GET er støttet" });
  }
  res.setHeader("Cache-Control", "no-store");
  return res.status(200).json({
    ok: true,
    service: "chatbox-config",
    commit: process.env.VERCEL_GIT_COMMIT_SHA || null,
    environment: process.env.VERCEL_ENV || process.env.NODE_ENV || null,
  });
}

