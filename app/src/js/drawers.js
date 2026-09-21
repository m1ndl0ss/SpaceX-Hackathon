import { helpOptions, partners } from "../data/community.js";
import { sites } from "../data/sites.js";
import { $ } from "./dom.js";
import { renderIcons } from "./icons.js";
import { toast } from "./toast.js";
import { state } from "./state.js";
import { dispatch, workspace } from "./store.js";
import { categories, urgencies, reportStatuses, callStatuses, canJoin, canWithdraw, isReportOpen, spacesLeft } from "./workflow.js";
import { escapeHtml as e, formatDate, localDateTime, formError } from "./format.js";
import { callLabel, callRow, empty, feedHtml, reportRow } from "./workflow-views.js";

let lastTrigger;
let route;
let dirty = false;
const isGovernment = () => state.role === "organisation";
const errorSlot = '<p class="lm-form-error" data-form-error role="alert" tabindex="-1" hidden></p>';
const options = (values, selected) => Object.entries(values).map(([value, label]) => `<option value="${e(value)}" ${value === selected ? "selected" : ""}>${e(label)}</option>`).join("");
const helpChoices = () => helpOptions.map((item) => `<option value="${item.id}">${e(item.label)}</option>`).join("");
const field = (label, input) => `<label class="lm-field"><span class="lm-field-head">${label}</span>${input}</label>`;
const paragraph = (text) => `<p class="lm-preserve-lines">${e(text)}</p>`;
function timeline(items) {
  return items.length ? items.map((item) => `<article class="lm-timeline-item"><div class="lm-list-name">${e(item.authorName)}</div><div class="lm-list-meta">${e(formatDate(item.createdAt))} · ${e(reportStatuses[item.status] || callStatuses[item.status])}</div>${paragraph(item.body)}</article>`).join("") : empty("No updates yet. Updates will appear here when the government responds.");
}

function reportForm() {
  return { title: "Report a violation", body: `<p>Describe what you observed. Government can review your report, reply, and organise help.</p>
    <form class="lm-workflow-form" data-workflow-form="submitReport">
      ${field("Short title", '<input name="title" maxlength="140" placeholder="e.g. Discharge near the harbour" required>')}
      ${field("Location", '<input name="place" maxlength="200" placeholder="Address, landmark, or coordinates" required>')}
      <div class="lm-form-grid">${field("Type of violation", `<select name="category">${categories.map((category) => `<option>${e(category)}</option>`).join("")}</select>`)}${field("Urgency", `<select name="urgency">${options(urgencies, "normal")}</select>`)}</div>
      ${field("When you observed it", `<input type="datetime-local" name="observedAt" value="${localDateTime()}" max="${localDateTime()}" required>`)}
      ${field("What you observed", '<textarea name="note" rows="5" maxlength="4000" placeholder="What happened, what is affected, and any useful details for the team." required></textarea>')}
      ${field("Evidence link (optional)", '<input type="url" name="evidence" maxlength="2000" placeholder="https://…"><span class="lm-list-meta">Link to a photo, video, or supporting document.</span>')}
      ${errorSlot}<button type="submit" class="lm-button primary">Submit violation</button>
    </form>` };
}

function callForm(context) {
  const report = workspace.data.reports.find((item) => item.id === context.reportId);
  const site = context.site === undefined ? null : sites[context.site];
  return { title: "Post a call for help", body: `<p>Tell activists where to meet, what needs doing, and how many people you need. Publishing makes this visible in their calls for help.</p>
    <form class="lm-workflow-form" data-workflow-form="publishCall">
      ${field("Action title", `<input name="title" maxlength="140" value="${e(report ? `Help investigate: ${report.title}`.slice(0, 140) : site?.action || "")}" placeholder="e.g. Harbour water-quality survey" required>`)}
      ${field("Meeting location", `<input name="place" maxlength="200" value="${e(report?.place || site?.name || "")}" placeholder="Specific meeting point" required>`)}
      ${field("Date and time", `<input type="datetime-local" name="when" min="${localDateTime(new Date(Date.now() + 60000))}" required>`)}
      <div class="lm-form-grid">${field("Volunteers needed", '<input type="number" name="capacity" min="1" max="1000" step="1" value="8" required>')}${field("Type of help", `<select name="help">${helpChoices()}</select>`)}</div>
      ${field("What volunteers will do", `<textarea name="description" rows="5" maxlength="4000" placeholder="Tasks, meeting instructions, equipment, and what to bring." required>${e(site?.text || "")}</textarea>`)}
      ${field("Linked violation (optional)", `<select name="reportId"><option value="">No linked violation</option>${workspace.data.reports.filter(isReportOpen).map((item) => `<option value="${e(item.id)}" ${item.id === report?.id ? "selected" : ""}>${e(item.title)}</option>`).join("")}</select>`)}
      ${errorSlot}<button type="submit" class="lm-button primary">Publish call for help</button>
    </form>` };
}

function reportDetail(id) {
  const report = workspace.data.reports.find((item) => item.id === id);
  if (!report) return { title: "Report unavailable", body: empty("This report could not be found.") };
  const linked = workspace.data.calls.filter((call) => call.reportId === id);
  const statusOptions = isReportOpen(report) ? Object.fromEntries(Object.entries(reportStatuses).filter(([key]) => key !== "new")) : { reviewing: "Reopen for review" };
  return { title: report.title, body: `<div class="lm-detail-tags"><span class="lm-pill ${isReportOpen(report) ? "amber" : ""}">${e(reportStatuses[report.status])}</span><span class="lm-pill">${e(urgencies[report.urgency])} priority</span></div>
    <dl class="lm-detail-meta"><dt>Location</dt><dd>${e(report.place)}</dd><dt>Category</dt><dd>${e(report.category)}</dd><dt>Reported by</dt><dd>${e(report.who)}</dd><dt>Observed</dt><dd>${e(formatDate(report.observedAt))}</dd><dt>Submitted</dt><dd>${e(formatDate(report.createdAt))}</dd></dl>
    ${paragraph(report.note)}
    ${report.evidence ? `<a class="lm-link" href="${e(report.evidence)}" target="_blank" rel="noopener noreferrer">View supporting evidence <i data-lucide="arrow-up-right" aria-hidden="true"></i></a>` : ""}
    <h3 class="lm-detail-heading">Response history</h3>${timeline(report.responses)}
    ${linked.length ? `<h3 class="lm-detail-heading">Linked calls for help</h3>${linked.map((call) => callRow(call, state.profile.id)).join("")}` : ""}
    ${isGovernment() ? `<h3 class="lm-detail-heading">${isReportOpen(report) ? "Respond to this violation" : "Reopen this violation"}</h3>
      <form class="lm-workflow-form" data-workflow-form="respondToReport" data-record-id="${e(id)}">
        ${field("Report status", `<select name="status">${options(statusOptions, report.status === "new" ? "reviewing" : report.status)}</select>`)}
        ${field("Response to the reporter", '<textarea name="body" rows="4" maxlength="4000" placeholder="Explain the next step, findings, or resolution. This is visible to the reporter." required></textarea>')}
        ${errorSlot}<button type="submit" class="lm-button primary">Post response</button>
      </form>${isReportOpen(report) ? `<button type="button" class="lm-button" data-create-call-for="${e(id)}"><i data-lucide="users" aria-hidden="true"></i>Request volunteers</button>` : ""}` : ""}` };
}

function callDetail(id) {
  const call = workspace.data.calls.find((item) => item.id === id);
  if (!call) return { title: "Action unavailable", body: empty("This call for help could not be found.") };
  const joined = call.participants.includes(state.profile.id);
  const ended = ["completed", "cancelled"].includes(call.status);
  const report = workspace.data.reports.find((item) => item.id === call.reportId);
  const roster = call.participants.map((personId) => workspace.data.profiles.find((person) => person.id === personId)).filter(Boolean);
  return { title: call.title, body: `<div class="lm-detail-tags"><span class="lm-pill">${e(callLabel(call))}</span>${joined ? '<span class="lm-pill">You joined this action</span>' : ""}</div>
    <dl class="lm-detail-meta"><dt>When</dt><dd>${e(formatDate(call.when))}</dd><dt>Meeting point</dt><dd>${e(call.place)}</dd><dt>Organised by</dt><dd>${e(call.organiser)}</dd><dt>Type of help</dt><dd>${e(helpOptions.find((item) => item.id === call.help)?.label)}</dd></dl>
    ${paragraph(call.description)}
    <div class="lm-capacity"><div class="lm-row lm-between"><strong>${call.participants.length} / ${call.capacity} volunteers</strong><span>${spacesLeft(call)} ${spacesLeft(call) === 1 ? "spot" : "spots"} left</span></div><progress value="${call.participants.length}" max="${call.capacity}" aria-label="Volunteer signups"></progress></div>
    ${report ? `<button type="button" class="lm-link" data-open-report="${e(report.id)}">Linked violation: ${e(report.title)} <i data-lucide="arrow-up-right" aria-hidden="true"></i></button>` : ""}
    ${!isGovernment() ? joined ? (canWithdraw(call) ? `<button type="button" class="lm-button" data-withdraw-call="${e(id)}">Withdraw from action</button>` : '<p>Your signup is saved in your action history.</p>') : `<button type="button" class="lm-button primary" data-join-call="${e(id)}" ${canJoin(call) ? "" : "disabled"}>${canJoin(call) ? "Join this action" : e(callLabel(call))}</button>` : ""}
    <h3 class="lm-detail-heading">Updates for volunteers</h3>${timeline(call.updates)}
    ${isGovernment() ? `<h3 class="lm-detail-heading">Volunteer roster</h3>${roster.length ? roster.map((person) => `<div class="lm-list-row compact"><div><div class="lm-list-name">${e(person.name)}</div><div class="lm-list-meta">${e(person.place)} · ${e(helpOptions.find((item) => item.id === person.help)?.label || "Volunteer")}</div></div><span class="lm-pill">Signed up</span></div>`).join("") : empty("No volunteers have joined yet.")}
      ${!ended ? `<h3 class="lm-detail-heading">Manage this action</h3><form class="lm-workflow-form" data-workflow-form="updateCall" data-record-id="${e(id)}">
        ${field("Action status", `<select name="status">${options(callStatuses, call.status)}</select>`)}
        ${field("Update for volunteers", '<textarea name="body" rows="3" maxlength="4000" placeholder="Meeting instructions, progress, or why the action is closing." required></textarea>')}
        <p class="lm-list-meta">Completing or cancelling an action is final. Any linked violation stays open until you resolve it separately.</p>
        ${errorSlot}<button type="submit" class="lm-button primary">Save action update</button></form>` : ""}` : ""}` };
}

function drawerCopy(type, context) {
  if (type === "new-report") return state.role === "people" ? reportForm() : { title: "Activist workspace required", body: empty("Switch to an activist profile to submit a violation.") };
  if (type === "create-call") return isGovernment() ? callForm(context) : { title: "Government workspace required", body: empty("Calls for help are published by the government.") };
  if (type === "report") return reportDetail(context.id);
  if (type === "call") return callDetail(context.id);
  if (type === "activity") return { title: "Community activity", body: feedHtml(workspace.data.activity) };
  if (type === "reports") {
    const reports = isGovernment() ? workspace.data.reports : workspace.data.reports.filter((report) => report.authorId === state.profile.id);
    return { title: isGovernment() ? "Violation reports" : "Your violation reports", body: reports.map((report) => reportRow(report, true)).join("") || empty("No reports yet.") };
  }
  if (type === "site" || type === "interventions") {
    const site = sites[state.site];
    return { title: site.action, body: `<span class="lm-pill">Restoration opportunity</span>${paragraph(site.text)}<dl class="lm-detail-meta"><dt>Location</dt><dd>${e(site.name)}</dd><dt>Species</dt><dd>${e(site.species)}</dd></dl><button type="button" class="lm-button primary" data-create-call-site="${state.site}">Post a call for help here</button>` };
  }
  return { title: "Partner network", body: partners.map((partner) => `<div class="lm-list-row compact"><div><div class="lm-list-name">${e(partner.name)}</div><div class="lm-list-meta">${e(partner.type)} · ${e(partner.place)}</div></div></div>`).join("") };
}

function renderDrawer() {
  if (!route) return;
  const { title, body } = drawerCopy(route.type, route.context);
  $("#lm-drawer-title").textContent = title;
  $("#lm-drawer-body").innerHTML = `<p class="lm-form-error" id="lm-drawer-error" role="alert" hidden></p><p class="lm-sync-note" id="lm-drawer-sync" role="status" hidden>New activity is available. Your draft is kept; it will be checked against the latest record when you save.</p>${body}`;
  dirty = false;
  renderIcons();
}

export function openDrawer(type, context = {}) {
  if ($("#lm-drawer-overlay").hidden) lastTrigger = document.activeElement;
  route = { type, context };
  renderDrawer();
  $("#lm-drawer-overlay").hidden = false;
  $(".lm-workspace").inert = true;
  document.body.classList.add("lm-modal-open");
  $(".lm-drawer").scrollTop = 0;
  $("#lm-close-drawer").focus();
}

export function closeDrawer() {
  if ($("#lm-drawer-overlay").hidden) return;
  $("#lm-drawer-overlay").hidden = true;
  $(".lm-workspace").inert = false;
  document.body.classList.remove("lm-modal-open");
  route = null;
  if (lastTrigger?.isConnected) lastTrigger.focus();
  else $("#lm-sign-out").focus();
}

export function bindDrawers() {
  document.addEventListener("click", async (event) => {
    const drawer = event.target.closest("[data-drawer]");
    if (drawer) openDrawer(drawer.dataset.drawer);
    const linked = event.target.closest("[data-create-call-for]");
    if (linked) openDrawer("create-call", { reportId: linked.dataset.createCallFor });
    const site = event.target.closest("[data-create-call-site]");
    if (site) openDrawer("create-call", { site: Number(site.dataset.createCallSite) });
    const join = event.target.closest("[data-join-call]");
    const withdraw = event.target.closest("[data-withdraw-call]");
    if (join || withdraw) {
      const button = join || withdraw;
      if (button.disabled) return;
      button.disabled = true;
      try {
        const id = join?.dataset.joinCall || withdraw.dataset.withdrawCall;
        await dispatch(join ? "joinCall" : "withdrawCall", { id });
        openDrawer("call", { id });
        toast(join ? "You’re signed up. Find this action in Your actions." : "Signup withdrawn. Your spot is available again.");
      } catch (error) {
        $("#lm-drawer-error").textContent = error.message;
        $("#lm-drawer-error").hidden = false;
      } finally { button.disabled = false; }
    }
  });
  $("#lm-drawer-body").addEventListener("input", () => { dirty = true; });
  $("#lm-drawer-body").addEventListener("change", () => { dirty = true; });
  $("#lm-drawer-body").addEventListener("submit", async (event) => {
    const form = event.target.closest("[data-workflow-form]");
    if (!form) return;
    event.preventDefault();
    const button = form.querySelector('[type="submit"]');
    if (button.disabled) return;
    button.disabled = true;
    const payload = Object.fromEntries(new FormData(form));
    if (form.dataset.recordId) payload.id = form.dataset.recordId;
    try {
      const type = form.dataset.workflowForm;
      const result = await dispatch(type, payload);
      openDrawer(["publishCall", "updateCall"].includes(type) ? "call" : "report", { id: result.id });
      toast({ submitReport: "Violation submitted. Government can now review it.", respondToReport: "Response posted and report status updated.", publishCall: "Call for help published. Activists can now join.", updateCall: "Action updated. Volunteers can see your message." }[type]);
    } catch (error) { formError(form, error); }
    finally { button.disabled = false; }
  });
  workspace.subscribe(() => {
    if (!route || ["create-call", "new-report"].includes(route.type)) return;
    if (dirty) { $("#lm-drawer-sync").hidden = false; return; }
    const focused = document.activeElement;
    const focusName = focused?.getAttribute("name");
    const focusWasInDrawer = $("#lm-drawer-body").contains(focused);
    renderDrawer();
    if (focusWasInDrawer) ($("#lm-drawer-body").querySelector(`[name="${focusName || ""}"]`) || $("#lm-close-drawer")).focus();
  });
  $("#lm-site-action")?.addEventListener("click", () => openDrawer("site"));
  $("[data-incident]")?.addEventListener("click", (event) => openDrawer("report", { id: event.currentTarget.dataset.incident }));
  $("#lm-close-drawer").addEventListener("click", closeDrawer);
  $("#lm-drawer-overlay").addEventListener("click", (event) => { if (event.target === $("#lm-drawer-overlay")) closeDrawer(); });
  document.getElementById("last-mile").addEventListener("keydown", (event) => {
    if ($("#lm-drawer-overlay").hidden) return;
    if (event.key === "Escape") { event.preventDefault(); closeDrawer(); }
    if (event.key !== "Tab") return;
    const controls = [...$("#lm-drawer-overlay").querySelectorAll('button,a[href],input,select,textarea,[tabindex="0"]')].filter((element) => !element.disabled && element.getClientRects().length);
    const first = controls[0];
    const last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
}
