(function () {
  function applySingleOpenBehavior(container) {
    var items = container.querySelectorAll("details.faq-item");
    items.forEach(function (item) {
      item.addEventListener("toggle", function () {
        if (!item.open) return;
        items.forEach(function (other) {
          if (other !== item) other.removeAttribute("open");
        });
      });
    });
  }

  function groupByCategory(items) {
    var grouped = {};
    items.forEach(function (item) {
      var category = item.category || "Sonstiges";
      if (!grouped[category]) grouped[category] = [];
      grouped[category].push(item);
    });
    return grouped;
  }

  function renderFaq(container, data) {
    var items = Array.isArray(data.items) ? data.items.slice() : [];
    items.sort(function (a, b) {
      if (a.category === b.category) return (a.order || 0) - (b.order || 0);
      return String(a.category || "").localeCompare(String(b.category || ""));
    });

    var grouped = groupByCategory(items);
    var categoryOrder = ["Verein", "Sause"];
    var remaining = Object.keys(grouped).filter(function (c) {
      return categoryOrder.indexOf(c) === -1;
    });
    var orderedCategories = categoryOrder.concat(remaining.sort());

    container.innerHTML = "";
    var hasOpenSet = false;

    orderedCategories.forEach(function (category) {
      var groupItems = grouped[category];
      if (!groupItems || !groupItems.length) return;

      var heading = document.createElement("h4");
      heading.textContent = category;
      container.appendChild(heading);

      groupItems.forEach(function (item) {
        var details = document.createElement("details");
        details.className = "faq-item";
        if (!hasOpenSet) {
          details.open = true;
          hasOpenSet = true;
        }

        var summary = document.createElement("summary");
        summary.textContent = item.question || "";
        details.appendChild(summary);

        var answer = document.createElement("p");
        answer.textContent = item.answer || "";
        details.appendChild(answer);

        container.appendChild(details);
      });
    });

    applySingleOpenBehavior(container);
  }

  function renderError(container) {
    container.innerHTML =
      "<p>FAQ konnte nicht geladen werden. Bitte FAQ-JSON neu erzeugen.</p>";
  }

  document.addEventListener("DOMContentLoaded", function () {
    var container = document.querySelector("#faq .faq-accordion-wrapper");
    if (!container) return;

    var source = container.getAttribute("data-source") || "assets/data/faq.json";
    fetch(source)
      .then(function (res) {
        if (!res.ok) throw new Error("Failed to fetch FAQ data");
        return res.json();
      })
      .then(function (data) {
        renderFaq(container, data);
      })
      .catch(function () {
        renderError(container);
      });
  });
})();
