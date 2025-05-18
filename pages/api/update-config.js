export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Kun POST-støttet' });
  }

  const { system_prompt, speak_text } = req.body;

  const token = process.env.GH_TOKEN;
  const username = process.env.GH_USERNAME;
  const repo = process.env.GH_REPO;
  const path = 'config/config.json'; // hvor i repoet filen ligger
  const branch = 'main';

  // Hent SHA for eksisterende fil
  const getRes = await fetch(`https://api.github.com/repos/${username}/${repo}/contents/${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
    }
  });

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

  const result = await updateRes.json();

  if (!updateRes.ok) {
    return res.status(500).json({ error: 'Kunne ikke lagre', details: result });
  }

  return res.status(200).json({ success: true });
}
