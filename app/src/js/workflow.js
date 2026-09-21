import { helpOptions, opportunities, people, regions, seedReports } from "../data/community.js";
import { isReportPhoto } from "./photo.js";

export const reportStatuses = {
  new: "Awaiting review",
  reviewing: "Under review",
  action_required: "Action needed",
  resolved: "Resolved",
  dismissed: "Dismissed",
};
export const categories = ["Water pollution", "Wildlife disturbance", "Habitat damage", "Illegal dumping", "Other"];
export const urgencies = { normal: "Normal", high: "High", urgent: "Urgent" };
export const callStatuses = { open: "Open", closed: "Signups closed", completed: "Completed", cancelled: "Cancelled" };
export const isReportOpen = (report) => !["resolved", "dismissed"].includes(report.status);
export const spacesLeft = (call) => Math.max(0, call.capacity - call.participants.length);
export const canJoin = (call, now = Date.now()) => call.status === "open" && new Date(call.when).getTime() > now && spacesLeft(call) > 0;
export const canWithdraw = (call, now = Date.now()) => ["open", "closed"].includes(call.status) && new Date(call.when).getTime() > now;
export const government = { id: "government", name: "South Holland Nature Desk", org: "South Holland Nature Desk", role: "organisation", place: "Dordrecht", type: "municipality" };

const uid = () => globalThis.crypto.randomUUID();
const iso = (now) => new Date(now).toISOString();
const fail = (message) => { throw new Error(message); };
function required(value, label, max = 200) {
  const text = String(value ?? "").trim();
  if (!text) fail(`${label} is required.`);
  if (text.length > max) fail(`${label} must be ${max} characters or fewer.`);
  return text;
}
function oneOf(value, values, label) {
  if (!values.includes(value)) fail(`Choose a valid ${label}.`);
  return value;
}

const extraResolved = [
  ["Illegal campfire on the Haringvliet spit", "Haringvliet spit", "Ash pit and scorched reeds beside the marked path.", "Hanne Visser"],
  ["Netting left in the eel channel", "Biesbosch north lock", "Abandoned fyke net snagged on a willow root.", "Bram De Smet"],
  ["Paint dump at the quay ladder", "Dordrecht quay ladder", "Empty tins and solvent smell after the weekend.", "Ines Lambert"],
  ["Quad bikes on the mudflat", "Zwin mudflat south", "Tyre ruts cutting through the high-tide roost.", "Yara Jansen"],
  ["Collapsed otter holt", "Oude Maas km 8", "Bank slip has opened the holt to the channel.", "Milan Kovač"],
  ["Seal disturbed at low tide", "Haringvliet west beach", "Dogs off lead around a hauled-out grey seal.", "Sanne Groen"],
  ["Diesel film in the creek", "Stad Gent creek", "Rainbow sheen along 40 m of slack water.", "Olivier Wouters"],
  ["Cut willows dumped in the oxbow", "Biesbosch oxbow", "Fresh brash blocking a nursery channel.", "Chiara Pauwels"],
  ["Toad fence flattened overnight", "Kempen heath edge", "Fence posts pulled and mesh folded into the ditch.", "Thijs Noyens"],
  ["Night lighting on the roost", "Zwin hide east", "Work lamps left on after a film crew packed up.", "Amina Farouk"],
  ["Herbicide spray along the towpath", "Oude Maas km 14", "Yellowed bank herbs in a 2 m strip.", "Roos Kuiper"],
  ["Kayaks landing in the reedbed", "Haringvliet quiet shore", "Repeated landings flattening a 12 m nest zone.", "Daan Vermeulen"],
  ["Mine-pool liner torn", "Minett terrace 3", "Plastic liner ripped; pool draining into slag.", "Léa Hubert"],
  ["Beaver dam partly dismantled", "Ourthe bend", "Fresh cuts and logs dragged up the bank.", "Jonas Smeets"],
  ["Avocet scrape driven over", "Zwin scrape 2", "Vehicle tracks through the new scrape.", "Eva Meijer"],
  ["Anglers camping in the buffer", "Dordrecht harbour buffer", "Tent, fire ring, and line discarded in scrub.", "Pieter Bos"],
  ["Ash dump in the forest ride", "Sonian edge path", "A barrow of ash on the ride after dry weather.", "Nora Lindemans"],
  ["Heath pan used as a soakaway", "Kempen pan 4", "Grey water hose feeding the new toad pan.", "Gert Timmermans"],
  ["Temperature logger stolen", "Oude Maas km 12", "Stake pulled; logger missing after the weekend.", "Fien Schouten"],
  ["Jet-ski wake in the no-wake reach", "Haringvliet inner", "Repeated high-speed passes past the haul-out.", "Wout Claeys"],
  ["Plastic bales in the floodplain", "Biesbosch polder gate", "Wrapped bales snagged on the flood gate.", "Lotte Claessens"],
  ["Dog walkers inside the fenced roost", "Zwin roost fence", "Gate left open; several dogs among roosting geese.", "Anouk Berger"],
  ["Oil pads washed into the reed", "Dordrecht harbour edge", "Used pads from a small spill left in the margin.", "Faisal Rahman"],
];

function extraVolunteers() {
  return Array.from({ length: 80 }, (_, index) => ({
    id: `dv${index + 1}`,
    name: `Local volunteer ${index + 1}`,
    place: regions[index % regions.length],
    role: "people",
    help: "survey",
    hours: 6 + (index % 30),
    status: "Active",
  }));
}

function extraResolvedNotes(profiles, now) {
  return Array.from({ length: 80 }, (_, index) => {
    const author = profiles[(index + 4) % profiles.length];
    const createdAt = iso(now - (30 + index) * 86400000);
    return {
      id: `rx${index + 1}`,
      title: `Closed ${categories[index % categories.length].toLowerCase()} case ${index + 1}`,
      place: author.place,
      note: "Logged, checked, and closed during the autumn sweep.",
      category: categories[index % categories.length],
      urgency: "normal",
      evidence: "",
      photo: "",
      authorId: author.id,
      who: author.name,
      status: "resolved",
      observedAt: createdAt,
      createdAt,
      responses: [{
        id: `response-rx${index + 1}`,
        authorId: government.id,
        authorName: government.name,
        body: "Record closed after a field check. No further action required.",
        status: "resolved",
        createdAt: iso(now - (29 + index) * 86400000),
      }],
    };
  });
}

function crewFor(index, ids) {
  const usable = index === 0 ? ids.filter((id) => id !== "jb") : ids;
  const start = (index * 17) % usable.length;
  return Array.from({ length: 22 }, (_, offset) => usable[(start + offset) % usable.length]);
}

export function createInitialData(now = Date.now()) {
  const profiles = [...people, ...extraVolunteers()].map((person) => ({ ...person, role: "people", help: person.help || "survey" }));
  const ids = profiles.map((person) => person.id);
  const calls = opportunities.map((item, index) => ({
    id: item.id,
    title: item.title,
    place: item.place,
    when: iso(now + (5 + index * 2) * 86400000),
    help: item.help,
    description: `${item.need} needed to support ${item.title.toLowerCase()}. Meet at the main entrance to ${item.place}. Bring weatherproof clothing and water; the government will provide equipment and a briefing.`,
    capacity: 32,
    participants: crewFor(index, ids),
    status: "open",
    reportId: index === 1 ? "r2" : index === 2 ? "r3" : null,
    authorId: government.id,
    organiser: government.name,
    createdAt: iso(now - (index + 1) * 86400000),
    updates: [],
  }));
  const statuses = ["new", "reviewing", "action_required", "resolved", "action_required"];
  const reports = seedReports.map((item, index) => ({
    id: item.id,
    title: ["Possible discharge in the harbour", "Wildlife disturbed by jet-skis", "Riverbank collapse", "Disturbance near the Zwin roost", "Protected pools drying out"][index],
    place: item.place,
    note: index === 0 ? "Iridescent sheen on slack water near the harbour edge." : index === 3 ? "Visitors entering the marked bird roost area." : item.note,
    category: categories[index === 0 ? 0 : index === 1 || index === 3 ? 1 : 2],
    urgency: index === 0 ? "urgent" : index === 4 ? "high" : "normal",
    evidence: "",
    photo: "",
    authorId: profiles.find((person) => person.name === item.who).id,
    who: item.who,
    status: statuses[index],
    observedAt: iso(now - (index + 1) * 3600000),
    createdAt: iso(now - (index + 1) * 3600000),
    responses: index === 0 ? [] : [{
      id: `response-${index}`, authorId: government.id, authorName: government.name,
      body: ["", "A field check is being coordinated. Please keep a safe distance from the haul-out.", "Bank damage confirmed. Volunteers are needed to document the affected stretch.", "The access barrier has been restored and the roost is clear.", "A habitat team is assessing water levels and arranging a site visit."][index],
      status: statuses[index], createdAt: iso(now - index * 1800000),
    }],
  }));
  extraResolved.forEach((entry, index) => {
    const [title, place, note, who] = entry;
    const author = profiles.find((person) => person.name === who);
    const createdAt = iso(now - (6 + index) * 86400000);
    reports.push({
      id: `r${index + 6}`,
      title,
      place,
      note,
      category: categories[index % categories.length],
      urgency: "normal",
      evidence: "",
      photo: "",
      authorId: author.id,
      who,
      status: "resolved",
      observedAt: createdAt,
      createdAt,
      responses: [{
        id: `response-extra-${index}`,
        authorId: government.id,
        authorName: government.name,
        body: "Site checked and closed. No further action needed for this record.",
        status: "resolved",
        createdAt: iso(now - (5 + index) * 86400000),
      }],
    });
  });
  reports.push(...extraResolvedNotes(profiles, now));
  return {
    version: 1,
    profiles,
    reports,
    calls,
    activity: reports.map((report) => ({ id: `activity-${report.id}`, kind: "report", targetId: report.id, title: `${report.who} reported ${report.title.toLowerCase()}`, detail: report.place, createdAt: report.createdAt })),
  };
}

// All writes pass through the same rules, whether used by the UI or a server.
// Clone before validation so failed commands cannot partially mutate the workspace.
export function applyCommand(source, actor, command, now = Date.now()) {
  const data = structuredClone(source);
  const stamp = iso(now);
  const { type, payload = {} } = command;
  const requireRole = (role) => {
    if (actor?.role !== role || (role === "people" && !data.profiles.some((person) => person.id === actor.id))) fail("This action is not available in your workspace.");
  };
  const activity = (kind, targetId, title, detail) => data.activity.unshift({ id: uid(), kind, targetId, title, detail, createdAt: stamp });
  let result;

  if (type === "saveProfile") {
    const name = required(payload.name, "Name", 80);
    const place = required(payload.place, "Place", 120);
    const help = oneOf(payload.help, helpOptions.map((option) => option.id), "way to help");
    const existing = data.profiles.find((person) => person.name.toLowerCase() === name.toLowerCase());
    result = { ...(existing || {}), id: existing?.id || uid(), name, place, help, role: "people", type: "person" };
    if (existing) Object.assign(existing, result);
    else data.profiles.push(result);
  } else if (type === "submitReport") {
    requireRole("people");
    const observed = new Date(payload.observedAt).getTime();
    if (!Number.isFinite(observed) || observed > now) fail("Choose an observation time in the past or present.");
    const evidence = String(payload.evidence || "").trim();
    if (evidence) {
      let url;
      try { url = new URL(evidence); } catch { fail("Evidence must be a valid http or https link."); }
      if (!["https:", "http:"].includes(url.protocol) || evidence.length > 2000) fail("Evidence must be a valid http or https link.");
    }
    const photo = String(payload.photo || "").trim();
    if (photo && !isReportPhoto(photo)) fail("The photo could not be saved. Choose a smaller JPEG, PNG, or WebP image.");
    result = {
      id: uid(), title: required(payload.title, "Report title", 140),
      place: required(payload.place, "Location", 200), note: required(payload.note, "What you observed", 4000),
      category: oneOf(payload.category, categories, "category"), urgency: oneOf(payload.urgency, Object.keys(urgencies), "urgency"),
      observedAt: iso(observed), evidence, photo, authorId: actor.id, who: actor.name, status: "new", createdAt: stamp, responses: [],
    };
    data.reports.unshift(result);
    activity("report", result.id, `${actor.name} reported ${result.title.toLowerCase()}`, result.place);
  } else if (type === "respondToReport") {
    requireRole("organisation");
    const report = data.reports.find((item) => item.id === payload.id);
    if (!report) fail("This report could not be found.");
    const status = oneOf(payload.status, Object.keys(reportStatuses).filter((key) => key !== "new"), "report status");
    if (!isReportOpen(report) && status !== "reviewing") fail("Reopen this report for review before updating it.");
    report.responses.push({ id: uid(), body: required(payload.body, "Response", 4000), status, authorId: actor.id, authorName: actor.name, createdAt: stamp });
    report.status = status;
    activity("report", report.id, `${actor.name} responded to ${report.title.toLowerCase()}`, reportStatuses[status]);
    result = report;
  } else if (type === "publishCall") {
    requireRole("organisation");
    const when = new Date(payload.when).getTime();
    if (!Number.isFinite(when) || when <= now) fail("Choose a future date and time for the action.");
    const capacity = Number(payload.capacity);
    if (!Number.isInteger(capacity) || capacity < 1 || capacity > 1000) fail("Choose between 1 and 1,000 volunteers.");
    const report = payload.reportId ? data.reports.find((item) => item.id === payload.reportId) : null;
    if (payload.reportId && (!report || !isReportOpen(report))) fail("Link this call to an open report.");
    result = {
      id: uid(), title: required(payload.title, "Action title", 140), place: required(payload.place, "Meeting location", 200),
      description: required(payload.description, "Action details", 4000), when: iso(when), capacity,
      help: oneOf(payload.help, helpOptions.map((option) => option.id), "type of help"),
      participants: [], status: "open", reportId: report?.id || null, authorId: actor.id, organiser: actor.name, createdAt: stamp, updates: [],
    };
    data.calls.unshift(result);
    if (report) {
      report.status = "action_required";
      report.responses.push({ id: uid(), body: `Call for help published: ${result.title}.`, status: report.status, authorId: actor.id, authorName: actor.name, createdAt: stamp });
    }
    activity("call", result.id, `${actor.name} published ${result.title.toLowerCase()}`, result.place);
  } else if (type === "joinCall" || type === "withdrawCall") {
    requireRole("people");
    const call = data.calls.find((item) => item.id === payload.id);
    if (!call) fail("This call for help could not be found.");
    const joined = call.participants.includes(actor.id);
    if (type === "joinCall") {
      if (joined) fail("You have already joined this action.");
      if (!canJoin(call, now)) fail("This action is no longer accepting volunteers.");
      call.participants.push(actor.id);
    } else {
      if (!joined) fail("You are not signed up for this action.");
      if (!canWithdraw(call, now)) fail("Signups for this action have ended.");
      call.participants = call.participants.filter((id) => id !== actor.id);
    }
    activity("call", call.id, `${actor.name} ${type === "joinCall" ? "joined" : "withdrew from"} ${call.title.toLowerCase()}`, `${call.participants.length} / ${call.capacity} volunteers`);
    result = call;
  } else if (type === "updateCall") {
    requireRole("organisation");
    const call = data.calls.find((item) => item.id === payload.id);
    if (!call) fail("This call for help could not be found.");
    if (["completed", "cancelled"].includes(call.status)) fail("This action has ended and can no longer be changed.");
    const status = oneOf(payload.status, Object.keys(callStatuses), "action status");
    if (status === "open" && new Date(call.when).getTime() <= now) fail("An action in the past cannot accept signups. Close, complete, or cancel it.");
    const body = required(payload.body, "Update for volunteers", 4000);
    call.status = status;
    call.updates.push({ id: uid(), body, status, authorName: actor.name, createdAt: stamp });
    activity("call", call.id, `${actor.name} updated ${call.title.toLowerCase()}`, callStatuses[status]);
    result = call;
  } else fail("Unknown workspace action.");

  return { data, result };
}
