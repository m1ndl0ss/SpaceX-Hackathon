export const root = document.getElementById("last-mile");

export const $ = (selector, scope = root) => scope.querySelector(selector);
export const $$ = (selector, scope = root) => [...scope.querySelectorAll(selector)];
