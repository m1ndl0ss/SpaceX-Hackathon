import { initials } from "../data/community.js";
import { $, $$ } from "./dom.js";
import { renderIcons } from "./icons.js";
import { state } from "./state.js";
import { openDrawer } from "./drawers.js";
import { workspace } from "./store.js";
import { canJoin, isReportOpen } from "./workflow.js";
import { callRow, empty, feedHtml, reportRow } from "./workflow-views.js";
import { escapeHtml as e } from "./format.js";

const activeCall = (call) => ["open", "closed"].includes(call.status) && new Date(call.when).getTime() > Date.now();
const stat = (label, value, note) => `<div class="lm-stat"><div class="lm-stat-title">${e(label)}</div><div class="lm-stat-num">${value}</div><div class="lm-stat-note">${e(note)}</div></div>`;

export function applyRoleChrome() {
  $$("[data-role]").forEach((element) => { element.hidden = !element.dataset.role.split(/\s+/).includes(state.role); });
  const avatar = $(".lm-avatar");
  if (avatar) {
    avatar.textContent = initials(state.profile.name);
    avatar.setAttribute("aria-label", state.profile.name);
  }
  $("#lm-workspace-label").textContent = state.role === "people" ? state.profile.name : "Government";
}

export function renderCommunity() {
  const { calls, reports, activity } = workspace.data;
  const mine = reports.filter((report) => report.authorId === state.profile.id);
  const joined = calls.filter((call) => call.participants.includes(state.profile.id));
  const active = calls.filter(activeCall);
  const open = reports.filter(isReportOpen);
  const available = calls.filter((call) => canJoin(call) && !call.participants.includes(state.profile.id));

  $("#lm-overview-stats").innerHTML = [
    stat("Open violations", open.length, `${reports.filter((report) => report.status === "new").length} awaiting review`),
    stat("Upcoming actions", active.length, `${calls.filter((call) => canJoin(call)).length} accepting volunteers`),
    stat("Volunteers signed up", new Set(active.flatMap((call) => call.participants)).size, `${active.reduce((sum, call) => sum + call.participants.length, 0)} signups across upcoming actions`),
    stat("Violations resolved", reports.filter((report) => report.status === "resolved").length, `${reports.length} reports received`),
  ].join("");
  $("#lm-people-stats").innerHTML = [
    stat("Your upcoming actions", joined.filter(activeCall).length, `${joined.filter((call) => call.status === "completed").length} completed`),
    stat("Your reports", mine.length, `${mine.filter((report) => report.status === "new").length} awaiting review`),
    stat("Your reports resolved", mine.filter((report) => report.status === "resolved").length, `${mine.filter(isReportOpen).length} still open`),
    stat("Calls for help", available.length, "Accepting volunteers now"),
  ].join("");

  const priority = [...open].sort((a, b) => ({ urgent: 0, high: 1, normal: 2 }[a.urgency] - { urgent: 0, high: 1, normal: 2 }[b.urgency]) || new Date(b.createdAt) - new Date(a.createdAt));
  $("#lm-priority-reports").innerHTML = priority.slice(0, 3).map((report) => reportRow(report, true)).join("") || empty("All violations have been reviewed and closed.");
  $("#lm-priority-count").textContent = `${open.length} open reports · urgent reports first`;

  const reportFilter = $("#lm-report-filter").value;
  const reportSearch = $("#lm-report-search").value.trim().toLowerCase();
  const filteredReports = reports.filter((report) => (reportFilter === "all" || (reportFilter === "open" ? isReportOpen(report) : report.status === reportFilter)) && `${report.title} ${report.place} ${report.who} ${report.note}`.toLowerCase().includes(reportSearch));
  $("#lm-dashboard-reports").innerHTML = filteredReports.map((report) => reportRow(report)).join("") || empty("No violations match this search or status.");
  $("#lm-report-count").textContent = `${filteredReports.length} of ${reports.length} reports`;

  const callFilter = $("#lm-call-filter").value;
  const callSearch = $("#lm-call-search").value.trim().toLowerCase();
  const filteredCalls = calls.filter((call) => (callFilter === "all" || (callFilter === "available" ? canJoin(call) : call.status === callFilter)) && `${call.title} ${call.place} ${call.description}`.toLowerCase().includes(callSearch));
  $("#lm-dashboard-calls").innerHTML = filteredCalls.map((call) => callRow(call)).join("") || empty("No actions match this search or status.");
  $("#lm-call-count").textContent = `${filteredCalls.length} of ${calls.length} actions`;

  $("#lm-people-actions").innerHTML = [...joined].sort((a, b) => Number(activeCall(b)) - Number(activeCall(a)) || new Date(a.when) - new Date(b.when)).map((call) => callRow(call, state.profile.id)).join("") || empty("You haven’t joined an action yet. Explore the calls for help to get involved.");
  const helpFilter = $("#lm-help-filter").value;
  const opportunitySearch = $("#lm-opportunity-search").value.trim().toLowerCase();
  const offers = calls.filter((call) => call.status === "open" && new Date(call.when).getTime() > Date.now() && !call.participants.includes(state.profile.id) && (helpFilter === "all" || call.help === helpFilter) && `${call.title} ${call.place} ${call.description}`.toLowerCase().includes(opportunitySearch));
  $("#lm-people-opportunities").innerHTML = offers.map((call) => callRow(call, state.profile.id)).join("") || empty("No calls match your search. Try another location or type of help.");
  $("#lm-people-reports").innerHTML = mine.map((report) => reportRow(report)).join("") || empty("You haven’t submitted a violation report yet. Your reports and government responses will appear here.");
  $("#lm-overview-feed").innerHTML = feedHtml(activity.slice(0, 6));
  $("#lm-people-feed").innerHTML = feedHtml(activity.slice(0, 6));
  $$("[data-profile-name]").forEach((element) => { element.textContent = state.profile.name; });
  $$("[data-profile-place]").forEach((element) => { element.textContent = state.profile.place; });
  $("#lm-storage-error").textContent = workspace.error;
  $("#lm-storage-error").hidden = !workspace.error;
  renderIcons();
}

export function bindCommunity() {
  workspace.subscribe(renderCommunity);
  ["lm-report-filter", "lm-call-filter", "lm-help-filter"].forEach((id) => $(`#${id}`).addEventListener("change", renderCommunity));
  ["lm-report-search", "lm-call-search", "lm-opportunity-search"].forEach((id) => $(`#${id}`).addEventListener("input", renderCommunity));
  document.addEventListener("click", (event) => {
    const report = event.target.closest("[data-open-report]");
    const call = event.target.closest("[data-open-call]");
    if (report) openDrawer("report", { id: report.dataset.openReport });
    if (call) openDrawer("call", { id: call.dataset.openCall });
  });
  renderCommunity();
}

export function roleHome() {
  return state.role === "people" ? "people" : "overview";
}
