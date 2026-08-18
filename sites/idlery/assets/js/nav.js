/* Marks the primary-navigation link for the section currently in view.
   Purely additive: every link and every section works with this file absent. */
(function () {
  "use strict";

  var links = Array.prototype.slice.call(
    document.querySelectorAll('.site-nav a[href*="#"]')
  );
  if (!links.length || typeof IntersectionObserver !== "function") return;

  var byId = {};
  var sections = [];

  links.forEach(function (link) {
    var id = link.getAttribute("href").split("#")[1];
    if (!id) return;
    var section = document.getElementById(id);
    if (!section) return;
    byId[id] = link;
    sections.push(section);
  });
  if (!sections.length) return;

  var current = null;

  function setCurrent(id) {
    if (id === current) return;
    current = id;
    links.forEach(function (link) {
      link.removeAttribute("aria-current");
    });
    if (byId[id]) byId[id].setAttribute("aria-current", "true");
  }

  var observer = new IntersectionObserver(
    function (entries) {
      var visible = entries
        .filter(function (entry) {
          return entry.isIntersecting;
        })
        .sort(function (a, b) {
          return b.intersectionRatio - a.intersectionRatio;
        });
      if (visible.length) setCurrent(visible[0].target.id);
    },
    { rootMargin: "-45% 0px -45% 0px", threshold: [0, 0.25, 0.5, 1] }
  );

  sections.forEach(function (section) {
    observer.observe(section);
  });
})();
