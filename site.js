/* Lit Locals marketing site. Reveal, sticky header, hamburger, carousel. */
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
  var header = document.getElementById("site-header");
  if (!header) return;
  function sync() {
    header.classList.toggle("is-scrolled", window.scrollY > 16);
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

(function () {
  var scroller = document.getElementById("sample-carousel");
  if (!scroller) return;
  var wrap = scroller.parentElement;
  var prev = wrap.querySelector(".carousel-btn.prev");
  var next = wrap.querySelector(".carousel-btn.next");
  function step() {
    var card = scroller.querySelector(".sample-card");
    return card ? card.getBoundingClientRect().width + 16 : 280;
  }
  if (prev) prev.addEventListener("click", function () {
    scroller.scrollBy({ left: -step(), behavior: "smooth" });
  });
  if (next) next.addEventListener("click", function () {
    scroller.scrollBy({ left: step(), behavior: "smooth" });
  });
})();
