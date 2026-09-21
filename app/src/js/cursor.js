import { root } from "./dom.js";

const HOVER_SEL = "a, button, select, label, summary, [role='button'], .lm-action, .lm-map-pin, input[type='range'], input[type='checkbox']";

export function bindCursor() {
  if (!window.matchMedia("(pointer: fine) and (hover: hover)").matches) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const cursor = document.createElement("div");
  cursor.className = "lm-cursor";
  cursor.setAttribute("aria-hidden", "true");
  cursor.innerHTML = `<div class="lm-cursor-ring"><i></i></div><div class="lm-cursor-dot"></div>`;
  root.appendChild(cursor);
  root.classList.add("lm-has-cursor");

  const dot = cursor.querySelector(".lm-cursor-dot");
  const ring = cursor.querySelector(".lm-cursor-ring");
  let x = window.innerWidth / 2;
  let y = window.innerHeight / 2;
  let rx = x;
  let ry = y;

  const onMove = (event) => {
    x = event.clientX;
    y = event.clientY;
    cursor.classList.add("is-on");
    const over = event.target instanceof Element && event.target.closest(HOVER_SEL);
    cursor.classList.toggle("is-hover", Boolean(over));
  };

  window.addEventListener("pointermove", onMove, { passive: true });
  window.addEventListener("pointerdown", () => cursor.classList.add("is-down"));
  window.addEventListener("pointerup", () => cursor.classList.remove("is-down"));
  document.addEventListener("pointerleave", () => cursor.classList.remove("is-on"));
  window.addEventListener("blur", () => cursor.classList.remove("is-on"));

  const frame = () => {
    rx += (x - rx) * 0.16;
    ry += (y - ry) * 0.16;
    dot.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    ring.style.transform = `translate3d(${rx}px, ${ry}px, 0)`;
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}
