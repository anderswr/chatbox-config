export function validateLogin(username, password) {
  const ADMIN_USER = "boks1";
  const ADMIN_PASS = process.env.NEXT_PUBLIC_PIADMIN_PWD || ""; // hent fra Vercel miljøvariabel
  
  return username === ADMIN_USER && password === ADMIN_PASS;
}
