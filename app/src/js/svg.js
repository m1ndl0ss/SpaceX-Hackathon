const NS = "http://www.w3.org/2000/svg";

export function svgEl(tag, attrs, parent) {
  const el = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) {
    el.setAttribute(key, value);
  }
  if (parent) parent.appendChild(el);
  return el;
}
