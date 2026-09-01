import crypto from "crypto";

const COOKIE_NAME = "chatbox_admin";
const SESSION_SECONDS = 60 * 60 * 8;

function password() {
  return process.env.PIADMIN_PASSWORD || "";
}

function secret() {
  return process.env.PIADMIN_SESSION_SECRET || password();
}

function signature(expires) {
  return crypto.createHmac("sha256", secret()).update(String(expires)).digest("hex");
}

function safeEqual(first, second) {
  const left = Buffer.from(first || "");
  const right = Buffer.from(second || "");
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}

export function credentialsAreValid(username, candidate) {
  const expected = password();
  return username === "boks1" && Boolean(expected) && safeEqual(candidate, expected);
}

export function setAdminSession(res) {
  const expires = Math.floor(Date.now() / 1000) + SESSION_SECONDS;
  const secure = process.env.NODE_ENV === "production" ? "; Secure" : "";
  res.setHeader(
    "Set-Cookie",
    `${COOKIE_NAME}=${expires}.${signature(expires)}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${SESSION_SECONDS}${secure}`
  );
}

export function hasAdminSession(req) {
  if (!secret()) return false;
  const cookies = Object.fromEntries(
    (req.headers.cookie || "")
      .split(";")
      .map((part) => part.trim().split("="))
      .filter(([name, value]) => name && value)
  );
  const [expires, providedSignature] = (cookies[COOKIE_NAME] || "").split(".");
  if (!expires || Number(expires) <= Date.now() / 1000) return false;
  return safeEqual(providedSignature, signature(expires));
}
