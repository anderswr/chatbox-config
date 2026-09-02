import { credentialsAreValid, setAdminSession } from "../../utils/admin-auth";

export default function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Kun POST er støttet" });
  }
  const { username, password } = req.body || {};
  if (credentialsAreValid(username, password)) {
    setAdminSession(res);
    res.status(200).json({ ok: true });
  } else {
    res.status(401).json({ ok: false });
  }
}
