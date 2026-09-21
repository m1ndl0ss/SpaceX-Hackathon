(function (root) {
  var DRAW_MS = 1550;
  var FILL_MS = 280;
  var FADE_MS = 550;

  function mount(target, opts) {
    opts = opts || {};
    var el = typeof target === 'string' ? document.querySelector(target) : target;
    if (!el) throw new Error('BearStartup: mount target not found');
    var hold = opts.holdMs == null ? 800 : opts.holdMs;
    var reduce = root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches;

    el.classList.add('bear-startup');
    el.setAttribute('aria-hidden', 'true');

    function finish() {
      el.classList.add('is-done');
      window.setTimeout(function () {
        if (opts.remove !== false) el.remove();
        if (typeof opts.onDone === 'function') opts.onDone();
      }, FADE_MS + 150);
    }

    function play() {
      var wait = reduce ? 80 : DRAW_MS + FILL_MS + hold;
      window.setTimeout(finish, wait);
    }

    if (el.querySelector('svg')) {
      play();
      return el;
    }

    var svgUrl = opts.svgUrl || 'bear.svg';
    fetch(svgUrl)
      .then(function (r) { return r.text(); })
      .then(function (markup) {
        el.innerHTML = markup;
        play();
      })
      .catch(function () {
        console.warn('BearStartup: could not load', svgUrl);
      });
    return el;
  }

  root.BearStartup = { mount: mount };
})(typeof window !== 'undefined' ? window : globalThis);
