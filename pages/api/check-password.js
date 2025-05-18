export default function handler(req, res) {
  const correctPassword = process.env.NEXT_PUBLIC_PIADMIN_PWD;
  const { password } = req.body;

  if (password === correctPassword) {
    res.status(200).json({ ok: true });
  } else {
    res.status(401).json({ ok: false });
  }
}
