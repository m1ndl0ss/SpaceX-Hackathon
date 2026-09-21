import { escapeHtml as e, formatDate, timeAgo } from "./format.js";
import { isReportPhoto } from "./photo.js";
import { callStatuses, reportStatuses, spacesLeft, urgencies } from "./workflow.js";

export const empty = (message) => `<p class="lm-empty">${e(message)}</p>`;
export function callLabel(call) {
  if (call.status !== "open") return callStatuses[call.status];
  if (new Date(call.when).getTime() <= Date.now()) return "Signups ended";
  return spacesLeft(call) === 0 ? "Fully staffed" : "Accepting volunteers";
}
export function reportRow(report, compact = false) {
  return `<div class="lm-list-row lm-record-row ${compact ? "compact" : ""}">
    <div><button type="button" class="lm-record-title" data-open-report="${e(report.id)}">${e(report.title)}</button>
      <div class="lm-list-meta">${e(report.place)} · ${e(report.category)}</div>
      <div class="lm-list-meta">${e(report.who)} · ${e(timeAgo(report.createdAt))}${report.urgency !== "normal" ? ` · <strong class="lm-urgency">${e(urgencies[report.urgency])}</strong>` : ""}${isReportPhoto(report.photo) ? " · Photo attached" : ""}</div>
    </div>
    <span class="lm-pill ${["new", "action_required"].includes(report.status) ? "amber" : ""}">${e(reportStatuses[report.status])}</span>
    ${compact ? "" : `<button type="button" class="lm-button" data-open-report="${e(report.id)}" aria-label="View report: ${e(report.title)}">View report</button>`}
  </div>`;
}
export function callRow(call, profileId) {
  const joined = call.participants.includes(profileId);
  return `<div class="lm-list-row lm-record-row lm-call-row">
    <div><button type="button" class="lm-record-title" data-open-call="${e(call.id)}">${e(call.title)}</button>
      <div class="lm-list-meta">${e(call.place)} · ${e(formatDate(call.when))}</div>
      <div class="lm-list-meta">${call.participants.length} / ${call.capacity} volunteers · ${e(callLabel(call))}${joined ? " · <strong>You joined</strong>" : ""}${call.reportId ? " · Linked to a violation" : ""}</div>
    </div>
    <button type="button" class="lm-button ${joined ? "" : "primary"}" data-open-call="${e(call.id)}" aria-label="View action: ${e(call.title)}">${joined ? "Your signup" : "View action"}</button>
  </div>`;
}
export function feedHtml(items) {
  if (!items.length) return empty("Activity will appear here as reports and actions are updated.");
  return items.map((item) => `<div class="lm-feed-item">
    <div class="lm-feed-icon ${item.kind === "report" ? "amber" : ""}"><i data-lucide="${item.kind === "report" ? "radio" : "users"}" aria-hidden="true"></i></div>
    <div class="lm-feed-copy"><button type="button" class="lm-record-title" data-open-${item.kind}="${e(item.targetId)}">${e(item.title)}</button><p>${e(item.detail)}</p></div>
    <time class="lm-feed-time" datetime="${e(item.createdAt)}" title="${e(formatDate(item.createdAt))}">${e(timeAgo(item.createdAt))}</time>
  </div>`).join("");
}
