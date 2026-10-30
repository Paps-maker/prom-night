(function () {
  "use strict";

  const WHATSAPP_NUMBER = "254790427109";

  // NAVBAR: background on scroll + mobile menu
  const navbar = document.getElementById("navbar");
  const navToggle = document.getElementById("navToggle");
  const navLinks = document.getElementById("navLinks");
  const mobileBuy = document.getElementById("mobileBuy");

  function onScroll() {
    const y = window.scrollY;
    navbar.classList.toggle("scrolled", y > 40);
    mobileBuy.classList.toggle("show", y > window.innerHeight * 0.8);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  function setMenu(open) {
    navLinks.classList.toggle("open", open);
    navbar.classList.toggle("menu-open", open);
    navToggle.setAttribute("aria-expanded", open);
    navToggle.innerHTML = open ? '<i class="bi-x-lg"></i>' : '<i class="bi-list"></i>';
  }
  navToggle.addEventListener("click", () => setMenu(!navLinks.classList.contains("open")));
  navLinks.querySelectorAll("a").forEach(a => a.addEventListener("click", () => setMenu(false)));

  // ACTIVE NAV LINK
  const linkFor = {};
  navLinks.querySelectorAll("a").forEach(a => { linkFor[a.getAttribute("href").slice(1)] = a; });
  const sectionObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting || !linkFor[entry.target.id]) return;
      navLinks.querySelectorAll("a").forEach(a => a.classList.remove("active"));
      linkFor[entry.target.id].classList.add("active");
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  document.querySelectorAll("main section[id]").forEach(s => sectionObserver.observe(s));

  // REVEAL ON SCROLL
  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll(".reveal").forEach(el => revealObserver.observe(el));

  // MENU: only one open at a time
  const menus = document.querySelectorAll(".menu-item");
  menus.forEach(d => d.addEventListener("toggle", () => {
    if (d.open) menus.forEach(o => { if (o !== d) o.open = false; });
  }));

  // GALLERY LIGHTBOX
  const lightbox = document.getElementById("lightbox");
  const lightboxImg = document.getElementById("lightboxImg");
  document.querySelectorAll("#gallery button").forEach(btn => {
    btn.addEventListener("click", () => {
      lightboxImg.src = btn.dataset.src;
      lightbox.showModal();
    });
  });
  document.getElementById("lightboxClose").addEventListener("click", () => lightbox.close());
  lightbox.addEventListener("click", e => { if (e.target === lightbox) lightbox.close(); });

  // WHATSAPP FORMS
  const val = id => document.getElementById(id).value.trim();
  const openWhatsApp = message =>
    window.open(`https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`, "_blank");

  document.getElementById("formIndividual").addEventListener("submit", e => {
    e.preventDefault();
    openWhatsApp(
      "Hello! I want to register for Mr & Miss Prom as an individual.\n\n" +
      `Name: ${val("indName")}\nEmail: ${val("indEmail")}\nPhone: ${val("indPhone")}`
    );
  });

  document.getElementById("formCouple").addEventListener("submit", e => {
    e.preventDefault();
    openWhatsApp(
      "Hello! We want to register for Mr & Miss Prom as a couple.\n\n" +
      `Partner 1:\nName: ${val("c1Name")}\nEmail: ${val("c1Email")}\nPhone: ${val("c1Phone")}\n\n` +
      `Partner 2:\nName: ${val("c2Name")}\nEmail: ${val("c2Email")}\nPhone: ${val("c2Phone")}`
    );
  });

  document.getElementById("formContact").addEventListener("submit", e => {
    e.preventDefault();
    const phone = val("ctPhone");
    openWhatsApp(`Hi, I'm ${val("ctName")}${phone ? ` (${phone})` : ""}.\n\n${val("ctMsg")}`);
  });
})();
