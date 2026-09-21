import { $ } from "./dom.js";

let toastTimer;

export function toast(message) {
  clearTimeout(toastTimer);
  const el = $("#lm-toast");
  el.textContent = message;
  el.hidden = false;
  toastTimer = setTimeout(() => {
    el.hidden = true;
  }, 3500);
}
