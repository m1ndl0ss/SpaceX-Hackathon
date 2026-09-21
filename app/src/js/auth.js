import { helpOptions, regions } from "../data/community.js";
import { $, root } from "./dom.js";
import { renderIcons } from "./icons.js";
import { drawAll } from "./maps.js";
import { applyRoleChrome, renderCommunity, roleHome } from "./community.js";
import { state } from "./state.js";
import { showScreen } from "./workspace.js";
import { dispatch, workspace, readSession, saveSession } from "./store.js";
import { government } from "./workflow.js";
import { formError } from "./format.js";
import { closeDrawer } from "./drawers.js";

let activistProfile;

function showChoices() {
  $("#lm-gate-choices").hidden = false;
  $("#lm-signup").hidden = true;
  $("#lm-gate-note").hidden = true;
}

function showSignup() {
  state.role = "people";
  $("#lm-gate-choices").hidden = true;
  $("#lm-signup").hidden = false;
  $("#lm-gate-note").hidden = true;
  $("#lm-signup-title").textContent = "Join as an activist";
  $("#lm-signup-copy").textContent = "Use the same name to return to your demo profile, reports, and signups. Everything stays in this browser.";
  $("#lm-signup-name").value = activistProfile?.name || "Alex Morgan";
  $("#lm-signup-place").value = activistProfile?.place || "Dordrecht";
  $("#lm-signup-help").value = activistProfile?.help || "survey";
  $("#lm-signup-form [data-form-error]").hidden = true;
  renderIcons();
}

export function showGate() {
  closeDrawer();
  saveSession(null);
  root.classList.remove("lm-in-app");
  $("#lm-gate").hidden = false;
  $(".lm-shell").hidden = true;
  $("#lm-drawer-overlay").hidden = true;
  showChoices();
}

export function enterWorkspace(role) {
  state.role = role;
  saveSession({ role, profileId: state.profile.id });
  root.classList.add("lm-in-app");
  $("#lm-gate").hidden = true;
  $("#lm-signup").hidden = true;
  $(".lm-shell").hidden = false;
  applyRoleChrome();
  renderCommunity();
  showScreen(roleHome());
  renderIcons();
  requestAnimationFrame(drawAll);
}

function readSignup() {
  const name = $("#lm-signup-name").value.trim();
  const place = $("#lm-signup-place").value;
  if (!name) return null;
  return {
    name,
    place,
    help: $("#lm-signup-help").value,
    org: "Independent",
    type: "person",
  };
}

export function bindAuth() {
  const place = $("#lm-signup-place");
  if (place && !place.dataset.ready) {
    place.innerHTML = regions.map((item) => `<option value="${item}">${item}</option>`).join("");
    place.dataset.ready = "true";
  }
  const help = $("#lm-signup-help");
  if (help && !help.dataset.ready) {
    help.innerHTML = helpOptions.map((item) => `<option value="${item.id}">${item.label}</option>`).join("");
    help.dataset.ready = "true";
  }

  $("#lm-login-people")?.addEventListener("click", showSignup);
  $("#lm-login-organisation")?.addEventListener("click", () => {
    state.profile = { ...government };
    enterWorkspace("organisation");
  });
  $("#lm-signup-back")?.addEventListener("click", showChoices);
  $("#lm-signup-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.target.querySelector('[type="submit"]');
    if (button.disabled) return;
    button.disabled = true;
    const profile = readSignup();
    try {
      if (!profile) throw new Error("Enter your name to continue.");
      state.profile = await dispatch("saveProfile", profile);
      activistProfile = state.profile;
      enterWorkspace("people");
    } catch (error) { formError(event.target, error); }
    finally { button.disabled = false; }
  });
  $("#lm-sign-out")?.addEventListener("click", showGate);
  const session = readSession();
  const profile = workspace.data.profiles.find((person) => person.id === session?.profileId);
  if (session?.role === "organisation") {
    state.profile = { ...government };
    enterWorkspace("organisation");
  } else if (session?.role === "people" && profile) {
    state.profile = profile;
    activistProfile = profile;
    enterWorkspace("people");
  } else showGate();
}
