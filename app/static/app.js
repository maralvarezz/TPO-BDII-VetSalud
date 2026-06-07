function wireResultTabs(root = document) {
  const buttons = root.querySelectorAll(".result-tab");
  const panels = root.querySelectorAll(".result-tab-panel");

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const selected = button.dataset.tab;

      buttons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");

      panels.forEach((panel) => {
        if (panel.dataset.panel === selected) {
          panel.classList.remove("hidden");
        } else {
          panel.classList.add("hidden");
        }
      });
    });
  });
}

function setActiveQuery(queryId) {
  const buttons = document.querySelectorAll(".query-menu-item");
  buttons.forEach((button) => {
    if (button.dataset.queryId === queryId) {
      button.classList.add("is-active");
    } else {
      button.classList.remove("is-active");
    }
  });
}

function syncActiveQueryFrom(root = document) {
  const selectedContainer = root.querySelector("[data-selected-query]");
  if (!selectedContainer) {
    return;
  }
  const queryId = selectedContainer.dataset.selectedQuery;
  if (queryId) {
    setActiveQuery(queryId);
  }
}

function wireRecordNavigators(root = document) {
  const navigators = root.querySelectorAll(".record-navigator");

  navigators.forEach((navigator) => {
    if (navigator.dataset.bound === "true") {
      return;
    }

    const container = navigator.parentElement;
    const cards = container.querySelectorAll(".record-card");
    const chips = navigator.querySelectorAll(".record-chip");
    const current = navigator.querySelector("[data-record-current]");
    const prevButton = navigator.querySelector("[data-record-prev]");
    const nextButton = navigator.querySelector("[data-record-next]");

    let activeIndex = 0;

    function render() {
      cards.forEach((card) => {
        card.classList.toggle("hidden", Number(card.dataset.recordCard) !== activeIndex);
      });

      chips.forEach((chip) => {
        chip.classList.toggle("is-active", Number(chip.dataset.recordChip) === activeIndex);
      });

      if (current) {
        current.textContent = String(activeIndex + 1);
      }

      if (prevButton) {
        prevButton.disabled = activeIndex === 0;
        prevButton.classList.toggle("opacity-40", activeIndex === 0);
      }

      if (nextButton) {
        nextButton.disabled = activeIndex === cards.length - 1;
        nextButton.classList.toggle("opacity-40", activeIndex === cards.length - 1);
      }
    }

    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        activeIndex = Number(chip.dataset.recordChip);
        render();
      });
    });

    if (prevButton) {
      prevButton.addEventListener("click", () => {
        activeIndex = Math.max(0, activeIndex - 1);
        render();
      });
    }

    if (nextButton) {
      nextButton.addEventListener("click", () => {
        activeIndex = Math.min(cards.length - 1, activeIndex + 1);
        render();
      });
    }

    navigator.dataset.bound = "true";
    render();
  });
}

function wireGraphs(root = document) {
  if (typeof cytoscape === "undefined") {
    return;
  }

  const containers = root.querySelectorAll(".graph-canvas");
  containers.forEach((container) => {
    if (container.dataset.graphBound === "true") {
      return;
    }

    const payload = container.dataset.graph;
    if (!payload) {
      return;
    }

    const graph = JSON.parse(payload);
    cytoscape({
      container,
      elements: [...graph.nodes, ...graph.edges],
      minZoom: 0.55,
      maxZoom: 2.2,
      layout: {
        name: "cose",
        animate: true,
        fit: true,
        padding: 36,
      },
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-wrap": "wrap",
            "text-max-width": 120,
            color: "#e2e8f0",
            "font-size": 12,
            "font-weight": 700,
            "text-valign": "center",
            "text-halign": "center",
            "background-color": "#334155",
            "border-width": 2,
            "border-color": "#94a3b8",
            width: 60,
            height: 60,
          },
        },
        {
          selector: 'node[type = "propietario"]',
          style: {
            "background-color": "#10b981",
            "border-color": "#6ee7b7",
            shape: "round-rectangle",
            width: 150,
            height: 64,
          },
        },
        {
          selector: 'node[type = "paciente"]',
          style: {
            "background-color": "#0ea5e9",
            "border-color": "#7dd3fc",
            shape: "ellipse",
            width: 110,
            height: 110,
          },
        },
        {
          selector: 'node[type = "veterinario"]',
          style: {
            "background-color": "#a855f7",
            "border-color": "#d8b4fe",
            shape: "round-rectangle",
            width: 140,
            height: 60,
          },
        },
        {
          selector: 'node[type = "consulta"]',
          style: {
            "background-color": "#f97316",
            "border-color": "#fdba74",
            shape: "diamond",
            width: 110,
            height: 110,
          },
        },
        {
          selector: 'node[type = "vacuna"]',
          style: {
            "background-color": "#f43f5e",
            "border-color": "#fda4af",
            shape: "hexagon",
            width: 110,
            height: 110,
          },
        },
        {
          selector: 'node[type = "sucursal"]',
          style: {
            "background-color": "#14b8a6",
            "border-color": "#99f6e4",
            shape: "round-rectangle",
            width: 140,
            height: 60,
          },
        },
        {
          selector: 'node[type = "estado"]',
          style: {
            "background-color": "#eab308",
            "border-color": "#fde047",
            color: "#111827",
            shape: "round-rectangle",
            width: 170,
            height: 64,
          },
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "line-color": "#64748b",
            "target-arrow-color": "#64748b",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            color: "#94a3b8",
            "font-size": 10,
            "text-background-color": "#020617",
            "text-background-opacity": 0.8,
            "text-background-padding": 3,
          },
        },
      ],
    });

    container.dataset.graphBound = "true";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  wireResultTabs(document);
  wireRecordNavigators(document);
  wireGraphs(document);
  syncActiveQueryFrom(document);
});

document.body.addEventListener("htmx:afterSwap", (event) => {
  if (event.target && event.target.id === "query-result") {
    wireResultTabs(event.target);
    wireRecordNavigators(event.target);
    wireGraphs(event.target);
    syncActiveQueryFrom(event.target);
  }
});
