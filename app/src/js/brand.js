export const brandMark = `<img class="lm-logo" src="/bear.png?v=outline" alt="" width="40" height="40">`;

export function renderBrand() {
  document.querySelectorAll(".lm-brand-symbol").forEach((el) => {
    el.innerHTML = brandMark;
  });
}
