export function validateLogin(username, password) {
  const ADMIN_USER = "boks1";
  const ADMIN_PASS = process.env.PIADMIN_PASSWORD || "";
  
  return username === ADMIN_USER && password === ADMIN_PASS;
}
