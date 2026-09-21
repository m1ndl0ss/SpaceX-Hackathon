import { applyCommand, createInitialData } from "./workflow.js";

export const STORAGE_KEY = "yosemite.workspace.v1";

function renameCoordinatorIds(workspace) {
  const rename = (record) => record?.authorId === "coordinator" ? { ...record, authorId: "government" } : record;
  return {
    ...workspace,
    reports: workspace.reports.map((report) => ({ ...rename(report), responses: (report.responses || []).map(rename) })),
    calls: workspace.calls.map((call) => ({ ...rename(call), updates: (call.updates || []).map(rename) })),
  };
}

function inflateDemoCounts(workspace, seed) {
  const known = new Set(workspace.profiles.map((person) => person.id));
  const profiles = [...workspace.profiles, ...seed.profiles.filter((person) => !known.has(person.id))];
  const reportIds = new Set(workspace.reports.map((report) => report.id));
  const reports = [...workspace.reports, ...seed.reports.filter((report) => !reportIds.has(report.id))];
  const activityIds = new Set((workspace.activity || []).map((item) => item.id));
  const activity = [...(workspace.activity || []), ...seed.activity.filter((item) => !activityIds.has(item.id))];
  const calls = workspace.calls.map((call) => {
    const seeded = seed.calls.find((item) => item.id === call.id);
    if (!seeded) return call;
    const capacity = Math.max(call.capacity, seeded.capacity);
    const participants = [...new Set([...call.participants, ...seeded.participants])].slice(0, capacity);
    return { ...call, capacity, participants };
  });
  return { ...workspace, profiles, reports, calls, activity };
}

export function createWorkflowStore(storage, now = Date.now) {
  const listeners = new Set();
  let data = createInitialData(now());
  let storageError = "";
  function read() {
    try {
      const raw = storage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = renameCoordinatorIds(JSON.parse(raw));
        if (parsed.version !== 1 || !["profiles", "reports", "calls", "activity"].every((key) => Array.isArray(parsed[key]))) {
          throw new Error("Invalid workspace data");
        }
        if (parsed.reports.some((report) => report.id === "rx1")) data = parsed;
        else {
          data = inflateDemoCounts(parsed, createInitialData(now()));
          storage.setItem(STORAGE_KEY, JSON.stringify(data));
        }
      } else {
        storage.setItem(STORAGE_KEY, JSON.stringify(data));
      }
      storageError = "";
    } catch {
      storageError = "Browser storage is unavailable or the saved workspace could not be read. Enable site storage to save your work.";
    }
  }
  read();
  return {
    get data() { return data; },
    get error() { return storageError; },
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    refresh() { read(); listeners.forEach((listener) => listener()); },
    dispatch(actor, command) {
      // Re-read before every change so another tab's last write is preserved.
      read();
      if (storageError) throw new Error(storageError);
      const next = applyCommand(data, actor, command, now());
      try { storage.setItem(STORAGE_KEY, JSON.stringify(next.data)); }
      catch { throw new Error("Your change could not be saved. Browser storage may be full or disabled. Your form has been kept so you can retry."); }
      data = next.data;
      listeners.forEach((listener) => listener());
      return next.result;
    },
  };
}
