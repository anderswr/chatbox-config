export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Kun POST-støttet' });
  }

  const { system_prompt, speak_text } = req.body;

  if (typeof system_prompt !== 'string' || typeof speak_text !== 'string') {
    return res.status(400).json({ error: 'Ugyldig input' });
  }

  const token = process.env.GH_TOKEN;
  const username = process.env.GH_USERNAME;
  const repo = process.env.GH_REPO;
  const path = 'public/config.json'; // NB: MÅ være i `public/` for at Pi skal kunne hente den
  const branch = 'main';

  try {
    // Hent SHA for eksisterende fil
    const getRes = await fetch(`https://api.github.com/repos/${username}/${repo}/contents/${path}`, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/vnd.github+json',
      }
    });

    if (!getRes.ok) {
      const err = await getRes.json();
      return res.status(500).json({ error: 'Kunne ikke hente SHA', details: err });
    }

    const fileData = await getRes.json();
    const sha = fileData.sha;

    // Nytt innhold som base64
    const newContent = Buffer.from(JSON.stringify({ system_prompt, speak_text }, null, 2)).toString('base64');

    // Oppdater fil
    const updateRes = await fetch(`https://api.github.com/repos/${username}/${repo}/contents/${path}`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/vnd.github+json',
      },
      body: JSON.stringify({
        message: 'Oppdatert config fra admin-nettsiden',
        content: newContent,
        sha: sha,
        branch: branch
      }),
    });

    if (!updateRes.ok) {
      const err = await updateRes.json();
      return res.status(500).json({ error: 'Kunne ikke lagre til GitHub', details: err });
    }

    return res.status(200).json({ success: true });

  } catch (e) {
    return res.status(500).json({ error: 'Uventet feil', details: e.message });
  }
}
