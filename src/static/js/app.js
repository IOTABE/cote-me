/* cote-me — front-end interactions */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    initDropdowns();
    initNavToggle();
    initAlerts();
    initForms();
    initFormsets();
    focusFirstField();
  });

  /* ---- User dropdown ---- */
  function initDropdowns() {
    var triggers = document.querySelectorAll("[data-dropdown-trigger]");
    triggers.forEach(function (trigger) {
      var menu = trigger.parentElement.querySelector("[data-dropdown-menu]");
      if (!menu) return;

      trigger.addEventListener("click", function (e) {
        e.stopPropagation();
        var open = !menu.hasAttribute("hidden");
        closeAllDropdowns();
        if (!open) {
          menu.removeAttribute("hidden");
          trigger.setAttribute("aria-expanded", "true");
        }
      });

      menu.addEventListener("click", function (e) { e.stopPropagation(); });
    });

    document.addEventListener("click", closeAllDropdowns);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeAllDropdowns();
    });
  }

  function closeAllDropdowns() {
    document.querySelectorAll("[data-dropdown-menu]").forEach(function (m) {
      m.setAttribute("hidden", "");
    });
    document.querySelectorAll("[data-dropdown-trigger]").forEach(function (t) {
      t.setAttribute("aria-expanded", "false");
    });
  }

  /* ---- Mobile nav (hamburger) toggle ---- */
  function initNavToggle() {
    var btn = document.querySelector("[data-nav-toggle]");
    if (!btn) return;
    var header = btn.closest(".app-header");
    var icon = btn.querySelector(".material-symbols-rounded");

    function setOpen(open) {
      header.classList.toggle("is-open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.setAttribute("aria-label", open ? "Fechar menu" : "Abrir menu");
      if (icon) icon.textContent = open ? "close" : "menu";
    }

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      setOpen(!header.classList.contains("is-open"));
    });

    // Fecha ao clicar fora ou em um link do menu
    document.addEventListener("click", function (e) {
      if (header.classList.contains("is-open") && !header.contains(e.target)) {
        setOpen(false);
      }
    });
    document.getElementById("nav-actions").addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && header.classList.contains("is-open")) setOpen(false);
    });
  }

  /* ---- Dismissible alerts ---- */
  function initAlerts() {
    document.querySelectorAll("[data-alert-close]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var alert = btn.closest(".alert");
        if (alert) alert.remove();
      });
    });
  }

  /* ---- Loading state on submit ---- */
  function initForms() {
    document.querySelectorAll("form").forEach(function (form) {
      form.addEventListener("submit", function () {
        var btns = form.querySelectorAll("button[type=submit][data-loading]");
        btns.forEach(function (b) {
          b.classList.add("is-loading");
          b.disabled = true;
          if (!b.querySelector(".spinner")) {
            var s = document.createElement("span");
            s.className = "spinner";
            b.prepend(s);
          }
        });
      });
    });
  }

  /* ---- Dynamic inline formsets ---- */
  function initFormsets() {
    var wrappers = document.querySelectorAll("[data-formset]");
    wrappers.forEach(function (wrapper) {
      var prefix = wrapper.getAttribute("data-formset");
      var totalInput = document.querySelector('input[name="' + prefix + '-TOTAL_FORMS"]');
      var minRows = parseInt(wrapper.getAttribute("data-min") || "1", 10);

      if (!totalInput) return;

      // Live rows only — never count the hidden [data-formset-template] row.
      function rowsOf() {
        return Array.prototype.slice
          .call(wrapper.querySelectorAll(".formset-row"))
          .filter(function (r) { return !r.closest("[data-formset-template]"); });
      }
      function nextIndex() { return rowsOf().length; }
      function updateTotal() { totalInput.value = rowsOf().length; }

      wrapper.querySelectorAll(".formset-remove").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var row = btn.closest(".formset-row");
          if (rowsOf().length <= minRows) return;
          row.remove();
          updateTotal();
        });
      });

      var addBtn = wrapper.parentElement.querySelector(".formset-add");
      if (addBtn) {
        addBtn.addEventListener("click", function () {
          var template = wrapper.querySelector("[data-formset-template]");
          if (!template) return;
          var html = template.innerHTML.replace(/__prefix__/g, nextIndex());
          var tmp = document.createElement("div");
          tmp.innerHTML = html.trim();
          var newRow = tmp.firstElementChild;
          wrapper.appendChild(newRow);
          newRow.querySelector(".formset-remove").addEventListener("click", function () {
            if (rowsOf().length <= minRows) return;
            newRow.remove();
            updateTotal();
          });
          newRow.querySelector("input, select, textarea").focus();
          updateTotal();
        });
      }
    });
  }

  /* ---- Focus first input in main content ---- */
  function focusFirstField() {
    var main = document.getElementById("main");
    if (!main) return;
    var field = main.querySelector("input, select, textarea");
    if (field && !field.value && document.activeElement === document.body) {
      // only autofocus on pure form pages (e.g. auth)
      if (main.querySelector(".auth-card")) field.focus();
    }
  }
})();
