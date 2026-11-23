/* Клієнтська валідація публічних форм (novalidate): дзеркало бекенд-правил, iOS Safari. */
(function () {
  var NAME_RE = /^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ'’\- ]{2,255}$/;
  var LETTER_RE = /[A-Za-zА-Яа-яЁёІіЇїЄєҐґ]/;
  var MSG = {
    name: "Ім'я може містити лише літери, пробіл, дефіс і апостроф",
    nameShort: "Вкажіть ім'я (щонайменше 2 символи)",
    phone: "Формат телефону: 380XXXXXXXXX, +380… або 0XXXXXXXXX",
    email: "Вкажіть коректний email",
    comment: "Коментар занадто довгий",
  };

  function digits(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function normalizePhone(value) {
    var d = digits(value);
    if (d.indexOf("380") === 0 && d.length === 12) return d;
    if (d.indexOf("0") === 0 && d.length === 10) return "38" + d;
    if (d.length === 9) return "380" + d;
    return "";
  }

  function showError(field, message) {
    var wrap = field.closest(".field") || field.parentElement;
    if (!wrap) return;
    var box = wrap.querySelector("[data-js-error]");
    if (!box) {
      box = document.createElement("div");
      box.className = "field-error";
      box.setAttribute("data-js-error", "1");
      wrap.appendChild(box);
    }
    box.textContent = message;
  }

  function clearError(field) {
    var wrap = field.closest(".field") || field.parentElement;
    if (!wrap) return;
    var box = wrap.querySelector("[data-js-error]");
    if (box) box.remove();
  }

  function checkName(field) {
    var value = (field.value || "").trim().replace(/\s+/g, " ");
    if (!field.required && !value) return true;
    if (value.length < 2) {
      showError(field, MSG.nameShort);
      return false;
    }
    if (!NAME_RE.test(value) || !LETTER_RE.test(value)) {
      showError(field, MSG.name);
      return false;
    }
    return true;
  }

  function checkPhone(field) {
    var value = (field.value || "").trim();
    if (!field.required && !value) return true;
    if (!normalizePhone(value)) {
      showError(field, MSG.phone);
      return false;
    }
    return true;
  }

  function checkEmail(field) {
    var value = (field.value || "").trim();
    if (!field.required && !value) return true;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) || value.length > 254) {
      showError(field, MSG.email);
      return false;
    }
    return true;
  }

  function checkComment(field) {
    if ((field.value || "").length > 1000) {
      showError(field, MSG.comment);
      return false;
    }
    return true;
  }

  function validateForm(form) {
    var ok = true;
    form.querySelectorAll("[data-js-error]").forEach(function (el) {
      el.remove();
    });
    form.querySelectorAll("input, textarea").forEach(function (field) {
      if (field.name === "website" || field.type === "hidden" || field.type === "file") return;
      var name = field.getAttribute("name") || "";
      var type = field.getAttribute("type") || "";
      if (name === "full_name" || name === "first_name" || name === "last_name" || name === "author_name") {
        if (!checkName(field)) ok = false;
      } else if (name === "phone" || (type === "tel")) {
        if (!checkPhone(field)) ok = false;
      } else if (type === "email" || name === "email") {
        if (!checkEmail(field)) ok = false;
      } else if (name === "comment") {
        if (!checkComment(field)) ok = false;
      }
    });
    return ok;
  }

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form || form.tagName !== "FORM") return;
    if (!form.hasAttribute("novalidate") && !form.hasAttribute("data-validate-form")) return;
    if (!validateForm(form)) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, true);
})();
