import { $ } from "./dom.js";

const LINE = "Evaluating species. Tracing water. Ranking where to act.";

export function bindBoot() {
  const boot = $("#lm-boot");
  const typed = $("#lm-boot-typed");
  if (!boot || !typed) return;

  const finish = () => {
    boot.classList.add("is-done");
    window.setTimeout(() => {
      boot.hidden = true;
    }, 560);
  };

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    typed.textContent = LINE;
    finish();
    return;
  }

  let index = 0;
  const type = () => {
    index += 1;
    typed.textContent = LINE.slice(0, index);
    if (index < LINE.length) window.setTimeout(type, 22);
    else window.setTimeout(finish, 1100);
  };

  window.setTimeout(type, 420);
}
