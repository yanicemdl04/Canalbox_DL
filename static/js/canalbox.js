/* =====================================================================
   CANAL BOX — Interactions & animations (GSAP)
   Principes Disney : anticipation, ease in/out, overlapping, staging.
   ===================================================================== */
(function () {
  "use strict";
  document.documentElement.classList.remove("no-js");

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const hasGSAP = typeof window.gsap !== "undefined";

  /* ---------------------------------------------------- Orbes flottants */
  function floatOrbs() {
    if (!hasGSAP || reduced) return;
    gsap.utils.toArray(".cb-orb").forEach((orb, i) => {
      gsap.to(orb, {
        x: "random(-60, 60)", y: "random(-50, 50)", scale: "random(0.9, 1.15)",
        duration: 9 + i * 2, repeat: -1, yoyo: true, ease: "sine.inOut",
      });
    });
  }

  /* ---------------------------------------------------- Révélation au scroll */
  function revealOnScroll() {
    const els = gsap.utils.toArray(".reveal");
    if (!hasGSAP) { els.forEach((e) => (e.style.opacity = 1)); return; }
    if (reduced) { gsap.set(els, { opacity: 1, y: 0, filter: "none" }); return; }

    if (gsap.registerPlugin && window.ScrollTrigger) gsap.registerPlugin(ScrollTrigger);

    els.forEach((el) => {
      const delay = parseFloat(el.dataset.delay || 0);
      gsap.fromTo(el,
        { opacity: 0, y: 34, filter: "blur(10px)" },
        {
          opacity: 1, y: 0, filter: "blur(0px)", duration: 0.9, delay, ease: "power3.out",
          scrollTrigger: window.ScrollTrigger ? { trigger: el, start: "top 88%", once: true } : undefined,
        }
      );
    });
  }

  /* ---------------------------------------------------- Entrée séquencée (stagger) */
  function staggerGroups() {
    if (!hasGSAP || reduced) return;
    gsap.utils.toArray("[data-stagger]").forEach((group) => {
      const items = group.children;
      gsap.fromTo(items,
        { opacity: 0, y: 24, filter: "blur(8px)" },
        {
          opacity: 1, y: 0, filter: "blur(0px)", duration: 0.7, ease: "power3.out",
          stagger: 0.08,
          scrollTrigger: window.ScrollTrigger ? { trigger: group, start: "top 85%", once: true } : undefined,
        }
      );
    });
  }

  /* ---------------------------------------------------- Tilt liquide sur cartes */
  function tiltCards() {
    if (reduced) return;
    document.querySelectorAll("[data-tilt]").forEach((card) => {
      let raf = null;
      card.addEventListener("mousemove", (e) => {
        const r = card.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top) / r.height - 0.5;
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          card.style.transform = `perspective(900px) rotateY(${px * 6}deg) rotateX(${-py * 6}deg) translateY(-6px)`;
          card.style.setProperty("--mx", `${(px + 0.5) * 100}%`);
          card.style.setProperty("--my", `${(py + 0.5) * 100}%`);
        });
      });
      card.addEventListener("mouseleave", () => {
        card.style.transform = "";
      });
    });
  }

  /* ---------------------------------------------------- Compteurs animés */
  function countUp() {
    document.querySelectorAll("[data-count]").forEach((el) => {
      const target = parseFloat(el.dataset.count);
      const decimals = (el.dataset.count.split(".")[1] || "").length;
      const suffix = el.dataset.suffix || "";
      if (!hasGSAP || reduced) { el.textContent = target.toLocaleString("fr-FR") + suffix; return; }
      const obj = { v: 0 };
      gsap.to(obj, {
        v: target, duration: 1.6, ease: "power2.out",
        scrollTrigger: window.ScrollTrigger ? { trigger: el, start: "top 92%", once: true } : undefined,
        onUpdate: () => {
          el.textContent = obj.v.toLocaleString("fr-FR", {
            minimumFractionDigits: decimals, maximumFractionDigits: decimals,
          }) + suffix;
        },
      });
    });
  }

  /* ---------------------------------------------------- Anneaux de confiance */
  function confRings() {
    document.querySelectorAll("[data-ring]").forEach((svg) => {
      const val = parseFloat(svg.dataset.ring); // 0..1
      const circle = svg.querySelector(".value");
      if (!circle) return;
      const r = circle.r.baseVal.value;
      const c = 2 * Math.PI * r;
      circle.style.strokeDasharray = c;
      const offset = c * (1 - val);
      if (!hasGSAP || reduced) { circle.style.strokeDashoffset = offset; return; }
      circle.style.strokeDashoffset = c;
      gsap.to(circle, {
        strokeDashoffset: offset, duration: 1.4, ease: "power3.out",
        scrollTrigger: window.ScrollTrigger ? { trigger: svg, start: "top 92%", once: true } : undefined,
      });
    });
  }

  /* ---------------------------------------------------- Barres de graphique */
  function animateBars() {
    if (!hasGSAP || reduced) {
      document.querySelectorAll("[data-bar]").forEach((b) => (b.style.height = b.dataset.bar + "%"));
      document.querySelectorAll("[data-progress]").forEach((p) => (p.style.width = p.dataset.progress + "%"));
      return;
    }
    gsap.utils.toArray("[data-bar]").forEach((bar) => {
      const h = bar.dataset.bar + "%";
      gsap.fromTo(bar, { height: "0%" }, {
        height: h, duration: 1.1, ease: "power3.out", delay: Math.random() * 0.2,
        scrollTrigger: window.ScrollTrigger ? { trigger: bar, start: "top 96%", once: true } : undefined,
      });
    });
    gsap.utils.toArray("[data-progress]").forEach((p) => {
      gsap.fromTo(p, { width: "0%" }, {
        width: p.dataset.progress + "%", duration: 1.2, ease: "power3.out",
        scrollTrigger: window.ScrollTrigger ? { trigger: p, start: "top 96%", once: true } : undefined,
      });
    });
  }

  /* ---------------------------------------------------- Boutons : ripple + loading */
  function buttonInteractions() {
    document.querySelectorAll("[data-loading]").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (btn.classList.contains("is-loading")) return;
        btn.classList.add("is-loading");
        setTimeout(() => btn.classList.remove("is-loading"), 1600);
      });
    });
  }

  /* ---------------------------------------------------- Toasts */
  window.cbToast = function (message, type = "info") {
    let wrap = document.querySelector(".toast-wrap");
    if (!wrap) { wrap = document.createElement("div"); wrap.className = "toast-wrap"; document.body.appendChild(wrap); }
    const icons = {
      success: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
      error: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>',
      info: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16v-4M12 8h.01"/><circle cx="12" cy="12" r="10"/></svg>',
    };
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.innerHTML = `<div class="toast-icon">${icons[type] || icons.info}</div><span>${message}</span>`;
    wrap.appendChild(el);
    if (hasGSAP && !reduced) {
      gsap.fromTo(el, { opacity: 0, x: 40, scale: 0.9 }, { opacity: 1, x: 0, scale: 1, duration: 0.5, ease: "back.out(1.6)" });
      gsap.to(el, { opacity: 0, x: 40, duration: 0.4, delay: 4, ease: "power2.in", onComplete: () => el.remove() });
    } else {
      setTimeout(() => el.remove(), 4200);
    }
  };

  function initServerToasts() {
    document.querySelectorAll("[data-server-toast]").forEach((n) => {
      window.cbToast(n.dataset.message, n.dataset.level || "info");
      n.remove();
    });
  }

  /* ---------------------------------------------------- Modales */
  function initModals() {
    document.querySelectorAll("[data-modal-open]").forEach((trigger) => {
      trigger.addEventListener("click", () => openModal(trigger.dataset.modalOpen));
    });
    document.querySelectorAll("[data-modal-close]").forEach((btn) => {
      btn.addEventListener("click", () => closeModal(btn.closest(".modal-backdrop")));
    });
    document.querySelectorAll(".modal-backdrop").forEach((bd) => {
      bd.addEventListener("click", (e) => { if (e.target === bd) closeModal(bd); });
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") document.querySelectorAll(".modal-backdrop.open").forEach(closeModal);
    });
  }
  function openModal(id) {
    const bd = document.getElementById(id);
    if (!bd) return;
    bd.classList.add("open");
    const modal = bd.querySelector(".modal");
    if (hasGSAP && !reduced && modal) {
      gsap.fromTo(bd, { opacity: 0 }, { opacity: 1, duration: 0.3 });
      gsap.fromTo(modal, { opacity: 0, scale: 0.92, y: 20, filter: "blur(10px)" },
        { opacity: 1, scale: 1, y: 0, filter: "blur(0px)", duration: 0.5, ease: "back.out(1.5)" });
    }
  }
  function closeModal(bd) {
    if (!bd) return;
    const modal = bd.querySelector(".modal");
    if (hasGSAP && !reduced && modal) {
      gsap.to(modal, { opacity: 0, scale: 0.94, y: 12, duration: 0.3, ease: "power2.in" });
      gsap.to(bd, { opacity: 0, duration: 0.3, delay: 0.05, onComplete: () => bd.classList.remove("open") });
    } else { bd.classList.remove("open"); }
  }
  window.cbOpenModal = openModal;

  /* ---------------------------------------------------- Menus déroulants */
  function initDropdowns() {
    document.querySelectorAll("[data-dropdown]").forEach((dd) => {
      const trigger = dd.querySelector("[data-dropdown-trigger]");
      const menu = dd.querySelector("[data-dropdown-menu]");
      if (!trigger || !menu) return;
      trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = menu.classList.contains("open");
        document.querySelectorAll("[data-dropdown-menu].open").forEach((m) => m.classList.remove("open"));
        if (!isOpen) {
          menu.classList.add("open");
          if (hasGSAP && !reduced) {
            gsap.fromTo(menu, { opacity: 0, y: -8, scale: 0.97 }, { opacity: 1, y: 0, scale: 1, duration: 0.32, ease: "power3.out" });
          }
        } else { menu.classList.remove("open"); }
      });
    });
    document.addEventListener("click", () => {
      document.querySelectorAll("[data-dropdown-menu].open").forEach((m) => m.classList.remove("open"));
    });
  }

  /* ---------------------------------------------------- Navbar au scroll */
  function initNavbar() {
    const nav = document.querySelector("[data-navbar]");
    if (!nav) return;
    const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 20);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------------------------------------------------- Menu mobile */
  function initMobileMenu() {
    const btn = document.querySelector("[data-mobile-toggle]");
    const menu = document.querySelector("[data-mobile-menu]");
    if (!btn || !menu) return;
    btn.addEventListener("click", () => {
      const open = menu.classList.toggle("open");
      document.body.style.overflow = open ? "hidden" : "";
      if (hasGSAP && !reduced && open) {
        gsap.fromTo(menu.querySelectorAll("a"), { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, stagger: 0.06, ease: "power3.out" });
      }
    });
    menu.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => { menu.classList.remove("open"); document.body.style.overflow = ""; }));
  }

  /* ---------------------------------------------------- Notation par étoiles (input) */
  function initStarInput() {
    document.querySelectorAll("[data-star-input]").forEach((wrap) => {
      const stars = Array.from(wrap.querySelectorAll("button"));
      const hidden = wrap.parentElement.querySelector("input[type=hidden]");
      const paint = (n) => stars.forEach((s, i) => s.classList.toggle("filled", i < n));
      stars.forEach((star, i) => {
        star.addEventListener("mouseenter", () => paint(i + 1));
        star.addEventListener("click", () => {
          wrap.dataset.value = i + 1;
          if (hidden) hidden.value = i + 1;
          paint(i + 1);
          if (hasGSAP && !reduced) gsap.fromTo(star, { scale: 1 }, { scale: 1.35, duration: 0.25, yoyo: true, repeat: 1, ease: "power2.out" });
        });
      });
      wrap.addEventListener("mouseleave", () => paint(parseInt(wrap.dataset.value || 0)));
    });
  }

  /* ---------------------------------------------------- Compteur de caractères */
  function initCharCounter() {
    document.querySelectorAll("[data-char-counter]").forEach((ta) => {
      const out = document.querySelector(ta.dataset.charCounter);
      const max = ta.getAttribute("maxlength") || 600;
      const update = () => { if (out) out.textContent = `${ta.value.length} / ${max}`; };
      ta.addEventListener("input", update); update();
    });
  }

  /* ---------------------------------------------------- Compteur (skeleton -> contenu, démo) */
  function initSkeletonDemo() {
    document.querySelectorAll("[data-skeleton-swap]").forEach((zone) => {
      setTimeout(() => {
        const sk = zone.querySelector("[data-skeleton]");
        const real = zone.querySelector("[data-real]");
        if (sk && real) {
          real.hidden = false;
          if (hasGSAP && !reduced) {
            gsap.to(sk, { opacity: 0, duration: 0.4, onComplete: () => (sk.style.display = "none") });
            gsap.fromTo(real, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" });
          } else { sk.style.display = "none"; }
        }
      }, 1200);
    });
  }

  /* ---------------------------------------------------- Transition d'entrée de page */
  function pageEnter() {
    if (!hasGSAP || reduced) return;
    const hero = document.querySelector("[data-page-enter]");
    if (hero) {
      gsap.fromTo(hero, { opacity: 0, y: 16, filter: "blur(6px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.8, ease: "power3.out" });
    }
  }

  /* ---------------------------------------------------- Init */
  function init() {
    floatOrbs();
    revealOnScroll();
    staggerGroups();
    tiltCards();
    countUp();
    confRings();
    animateBars();
    buttonInteractions();
    initServerToasts();
    initModals();
    initDropdowns();
    initNavbar();
    initMobileMenu();
    initStarInput();
    initCharCounter();
    initSkeletonDemo();
    pageEnter();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
