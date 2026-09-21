import { createWorkflowStore, STORAGE_KEY } from "./workflow-store.js";
import { state } from "./state.js";

// Access storage inside methods: privacy settings may throw even on the getter.
export const workspace = createWorkflowStore({
  getItem: (key) => window.localStorage.getItem(key),
  setItem: (key, value) => window.localStorage.setItem(key, value),
});
export async function dispatch(type, payload) {
  const actor = { ...state.profile, role: state.role };
  const commit = () => workspace.dispatch(actor, { type, payload });
  // Serialize competing tab writes, including the last available volunteer spot.
  if (navigator.locks) return navigator.locks.request(STORAGE_KEY, commit);
  return commit();
}

window.addEventListener("storage", (event) => {
  if (event.key === STORAGE_KEY || event.key === null) workspace.refresh();
});

const SESSION_KEY = "yosemite.session.v1";
export function readSession() {
  try { return JSON.parse(window.sessionStorage.getItem(SESSION_KEY) || "null"); }
  catch { return null; }
}
export function saveSession(session) {
  try {
    if (session) window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
    else window.sessionStorage.removeItem(SESSION_KEY);
  } catch { /* Shared records still persist when per-tab sessions are disabled. */ }
}
