export function validateLogin(username, password) {
  const ADMIN_USER = "PIADMIN";
  const ADMIN_PASS = process.env.NEXT_PUBLIC_PIADMIN_PWD || ""; // hent fra Vercel miljøvariabel
  
  return username === ADMIN_USER && password === ADMIN_PASS;
}
