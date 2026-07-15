/*
  CareerMomentum Super Admin — auth.js
  --------------------------------------------------
  Demo-only client-side auth. Exactly 4 super admin
  accounts exist below — there is no registration flow.
  This is NOT secure for production (credentials are
  visible in the JS source and the session lives in
  sessionStorage). Swap this for a real backend/API
  before going live.
*/

const CM_ADMINS = [
  { email: "akshaykunjumon8606@gmail.com", password: "akshayk", name: "Akshay Kunjumon",  role: "Super Admin", initials: "Ak" },
  { email: "admin2@careermomentum.com", password: "Super@2024", name: "Priya Sharma", role: "Super Admin", initials: "PS" },
  { email: "admin3@careermomentum.com", password: "Super@2024", name: "Michael Chen", role: "Super Admin", initials: "MC" },
  { email: "admin4@careermomentum.com", password: "Super@2024", name: "Sara Thomas",  role: "Super Admin", initials: "ST" },
];

const CM_SESSION_KEY = "cm_admin_session";

function cmGetSession() {
  try {
    const raw = sessionStorage.getItem(CM_SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function cmLogin(email, password) {
  const match = CM_ADMINS.find(
    (a) => a.email.toLowerCase() === String(email).trim().toLowerCase() && a.password === password
  );
  if (!match) return false;
  const { password: _pw, ...safeAdmin } = match;
  sessionStorage.setItem(CM_SESSION_KEY, JSON.stringify(safeAdmin));
  return true;
}

function cmLogout() {
  sessionStorage.removeItem(CM_SESSION_KEY);
  window.location.href = "/super_admin_login";
}

// Fills in the topbar user-chip + sidebar profile block on every protected page.
function cmRenderIdentity() {
  const session = cmGetSession();
  if (!session) return;

  document.querySelectorAll("[data-identity-name]").forEach((el) => (el.textContent = session.name));
  document.querySelectorAll("[data-identity-role]").forEach((el) => (el.textContent = session.role));
  document.querySelectorAll("[data-identity-email]").forEach((el) => (el.textContent = session.email));
  document.querySelectorAll("[data-identity-initials]").forEach((el) => (el.textContent = session.initials));
}

document.addEventListener("DOMContentLoaded", cmRenderIdentity);