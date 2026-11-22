// Progressive enhancement du site du tuto — aucune dependance.
// Sans ce fichier, tout reste lisible : il ajoute seulement le confort.
(function () {
  "use strict";

  // 0. Sommaire : place apres le schema, et pliable sur petit ecran.
  var toc = document.querySelector("nav#TOC");
  if (toc) {
    var repere = document.querySelector("figure.flow") || document.querySelector("main.page > div[align='center']");
    if (repere && repere.parentNode) repere.parentNode.insertBefore(toc, repere.nextSibling);
    if (window.matchMedia && window.matchMedia("(max-width: 720px)").matches) {
      var d = document.createElement("details");
      d.className = "sommaire-pliant";
      var s = document.createElement("summary");
      s.textContent = "Sommaire";
      toc.parentNode.insertBefore(d, toc);
      d.appendChild(s);
      d.appendChild(toc);
    }
  }

  // 1. Lien de navigation correspondant a la page courante.
  var page = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".topbar nav a[data-page]").forEach(function (a) {
    if (a.getAttribute("href") === page) a.classList.add("actif");
  });

  // 2. Ancre cliquable sur chaque titre de section.
  document.querySelectorAll("h2[id], h3[id]").forEach(function (h) {
    var a = document.createElement("a");
    a.className = "ancre";
    a.href = "#" + h.id;
    a.textContent = "#";
    a.setAttribute("aria-label", "Lien vers cette section");
    h.appendChild(a);
  });

  // 3. Les tableaux larges defilent au lieu de deborder.
  document.querySelectorAll("main.page table").forEach(function (t) {
    if (t.parentNode.classList && t.parentNode.classList.contains("tableau-defilant")) return;
    var d = document.createElement("div");
    d.className = "tableau-defilant";
    t.parentNode.insertBefore(d, t);
    d.appendChild(t);
  });

  // 4. Blocs de code : langue affichee + bouton copier.
  document.querySelectorAll(".sourceCode").forEach(function (bloc) {
    var pre = bloc.querySelector("pre");
    var code = bloc.querySelector("code");
    if (!pre || !code) return;
    var m = (code.className || "").match(/sourceCode\s+([\w+-]+)/);
    if (m) {
      var l = document.createElement("span");
      l.className = "langage";
      l.textContent = m[1];
      bloc.appendChild(l);
    }
    var b = document.createElement("button");
    b.type = "button";
    b.className = "copier";
    b.textContent = "Copier";
    b.addEventListener("click", function () {
      var texte = code.innerText;
      function fini() {
        b.textContent = "Copie !";
        b.classList.add("fait");
        setTimeout(function () { b.textContent = "Copier"; b.classList.remove("fait"); }, 1600);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(texte).then(fini, function () {});
      } else {
        var z = document.createElement("textarea");
        z.value = texte;
        document.body.appendChild(z);
        z.select();
        try { document.execCommand("copy"); fini(); } catch (e) {}
        document.body.removeChild(z);
      }
    });
    bloc.appendChild(b);
  });

  // 5. Retour en haut : visible seulement apres avoir defile.
  var haut = document.querySelector("a.haut");
  if (haut) {
    haut.style.transition = "opacity .2s ease";
    var majHaut = function () {
      var visible = window.scrollY > 600;
      haut.style.opacity = visible ? "1" : "0";
      haut.style.pointerEvents = visible ? "auto" : "none";
    };
    window.addEventListener("scroll", majHaut, { passive: true });
    majHaut();
  }

  // 6. Sommaire : surligne la section en cours de lecture.
  var liens = Array.prototype.slice.call(document.querySelectorAll("nav#TOC a[href^='#']"));
  if (!liens.length || !("IntersectionObserver" in window)) return;
  var parId = {};
  liens.forEach(function (a) {
    var id = a.getAttribute("href").slice(1);
    try { id = decodeURIComponent(id); } catch (e) {}
    parId[id] = a;
  });
  var obs = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (e) {
      if (!e.isIntersecting) return;
      liens.forEach(function (a) { a.classList.remove("actif"); });
      var a = parId[e.target.id];
      if (a) a.classList.add("actif");
    });
  }, { rootMargin: "-80px 0px -70% 0px" });
  document.querySelectorAll("h2[id]").forEach(function (h) { obs.observe(h); });
})();
