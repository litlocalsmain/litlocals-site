/* Lit Locals preview factory. IntersectionObserver only. No motion library. */
(function () {
  var nodes = document.querySelectorAll(".reveal");
  if (!nodes.length) return;

  function showAll() {
    for (var i = 0; i < nodes.length; i++) nodes[i].classList.add("is-in");
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    showAll();
    return;
  }

  if (!("IntersectionObserver" in window)) {
    showAll();
    return;
  }

  var io = new IntersectionObserver(
    function (entries) {
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].isIntersecting) {
          entries[i].target.classList.add("is-in");
          io.unobserve(entries[i].target);
        }
      }
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );

  for (var j = 0; j < nodes.length; j++) io.observe(nodes[j]);
})();

(function () {
  var pop = document.getElementById("buy-pop");
  if (!pop) return;
  var closed = false;
  var x = pop.querySelector(".buy-pop-x");
  if (x) x.addEventListener("click", function () {
    closed = true;
    pop.classList.remove("is-on");
    pop.setAttribute("hidden", "");
  });

  function show() {
    if (closed) return;
    pop.removeAttribute("hidden");
    requestAnimationFrame(function () { pop.classList.add("is-on"); });
  }

  var foot = document.querySelector(".site-footer");
  if (!foot || !("IntersectionObserver" in window)) {
    window.addEventListener("scroll", function () {
      if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 80) show();
    }, { passive: true });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].isIntersecting) show();
    }
  }, { threshold: 0.2 });
  io.observe(foot);
})();

(function () {
  var chrome = document.querySelector(".preview-chrome");
  if (!chrome) return;
  function sync() {
    chrome.classList.toggle("is-scrolled", window.scrollY > 16);
  }
  window.addEventListener("scroll", sync, { passive: true });
  sync();
})();

(function () {
  var btn = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  var back = document.getElementById("nav-backdrop");
  if (!btn || !nav) return;
  function setOpen(open) {
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    nav.classList.toggle("is-open", open);
    if (back) {
      back.classList.toggle("is-on", open);
      if (open) back.removeAttribute("hidden");
      else back.setAttribute("hidden", "");
    }
  }
  btn.addEventListener("click", function () {
    setOpen(btn.getAttribute("aria-expanded") !== "true");
  });
  if (back) back.addEventListener("click", function () { setOpen(false); });
  var links = nav.querySelectorAll("a");
  for (var i = 0; i < links.length; i++) {
    links[i].addEventListener("click", function () { setOpen(false); });
  }
})();
