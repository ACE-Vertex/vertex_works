(() => {
  "use strict";

  const FACILITIES = {
    VXN: { role: "FLOW" },
    JUDGE: { role: "DECIDE" },
    SENSOR: { role: "OBSERVE" },
    EVIDENCE: { role: "PROVE" },
    RELEASE: { role: "SHIP" },
    CANONICAL: { role: "REMEMBER" },
  };

  const state = {
    orbit: null,
    workspace: null,
    mutationQueued: false,
  };

  const qsa = (root, selector) => Array.from((root || document).querySelectorAll(selector));

  function normalizedText(node) {
    return String(node?.textContent || "").replace(/\s+/g, " ").trim();
  }

  function exactText(node, value) {
    return normalizedText(node).toUpperCase() === String(value).toUpperCase();
  }

  function findTextElement(value) {
    const target = String(value).toUpperCase();
    return qsa(document, "h1,h2,h3,h4,h5,h6,button,[role='tab'],a,span,div")
      .find((el) => normalizedText(el).toUpperCase() === target) || null;
  }

  function nearestPanel(node) {
    if (!node) return null;
    return node.closest(
      "[data-panel],section,article,.panel,.card,.workspace,[class*='panel'],[class*='section'],[class*='workspace']"
    ) || node.parentElement;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  /* ---------------- Language policy ---------------- */

  function retireGlobalLanguageSettings(root = document) {
    const selectors = [
      "[data-setting='language']",
      "[data-settings-key='language']",
      ".setting-language",
      ".settings-language",
      "#language-setting",
      "#settings-language",
      "#vcr-language",
    ];

    selectors.forEach((selector) => {
      qsa(root, selector).forEach((el) => {
        el.hidden = true;
        el.setAttribute("aria-hidden", "true");
      });
    });

    qsa(root, "label,button,div,li,section").forEach((el) => {
      if (el.dataset.vwLanguageChecked === "true") return;
      el.dataset.vwLanguageChecked = "true";
      const text = normalizedText(el);
      if (!text || text.length > 90) return;
      if (!/\b(language|locale)\b/i.test(text) && !/日本語化|言語設定/.test(text)) return;

      const controls = el.querySelectorAll("select,input[type='radio'],input[type='checkbox']");
      if (controls.length || el.matches("label,li")) {
        el.hidden = true;
        el.setAttribute("aria-hidden", "true");
      }
    });

    // VCR facility chrome stays English; card/status content can remain Japanese.
    const vcrTitle = document.getElementById("vcr-title");
    const vcrNew = document.getElementById("vcr-new");
    const vcrSave = document.getElementById("vcr-save");
    const vcrDelete = document.getElementById("vcr-delete");
    if (vcrTitle) vcrTitle.textContent = "CANONICAL REGISTRY";
    if (vcrNew) vcrNew.textContent = "NEW CONCEPT";
    if (vcrSave) vcrSave.textContent = "SAVE";
    if (vcrDelete) vcrDelete.textContent = "DELETE";
  }

  /* ---------------- Theme contract ---------------- */

  function bindProductAccentContract() {
    const root = document.documentElement;
    if (root.dataset.vwProductThemeBound === "true") return;
    root.dataset.vwProductThemeBound = "true";

    // Default keeps the product-owned theme token.
    // We only alias an already-existing Works/product accent; we do not recolor the product.
    const styles = getComputedStyle(root);
    const candidates = ["--works-accent", "--product-accent", "--accent", "--accent-color"];
    const resolved = candidates.map((key) => styles.getPropertyValue(key).trim()).find(Boolean);
    if (resolved) root.style.setProperty("--vw-accent", resolved);
  }

  /* ---------------- RAY visual coherence ---------------- */

  function unifyRayPanels() {
    const explorerHeading = findTextElement("Project Explorer");
    const findingsHeading = findTextElement("Analysis Findings");

    const explorer = nearestPanel(explorerHeading);
    const findings = nearestPanel(findingsHeading);

    if (explorer) {
      explorer.classList.add("vw-unified-ray-panel", "vw-project-explorer-panel");
    }
    if (findings) {
      findings.classList.add("vw-unified-ray-panel", "vw-analysis-findings-panel");
    }
  }

  /* ---------------- Project Relation Map / Orbit Deck ---------------- */

  function relationHeading() {
    return (
      findTextElement("Project Relation Map") ||
      qsa(document, "h1,h2,h3,h4,h5,h6").find((el) =>
        /project\s+relation\s+map/i.test(normalizedText(el))
      ) ||
      null
    );
  }

  function uniqueProjectSources(panel) {
    const candidates = [];
    const selectors = [
      "[data-project]",
      "[data-project-name]",
      "[data-project-root]",
      ".project-card",
      "[class*='project-card']",
      "[class*='projectCard']",
      ".project-item",
      "[class*='project-item']",
    ];

    selectors.forEach((selector) => {
      qsa(panel || document, selector).forEach((el) => {
        const name =
          el.dataset.projectName ||
          el.dataset.project ||
          el.getAttribute("data-project-root")?.split(/[\\/]/).filter(Boolean).pop() ||
          normalizedText(el).split(/\n/)[0].trim();

        if (!name || name.length > 90) return;
        if (/project relation map|project explorer|analysis findings/i.test(name)) return;
        candidates.push({ name, source: el });
      });
    });

    // Fallback: collect project roots shown anywhere in the current Works DOM.
    if (candidates.length < 3) {
      qsa(document, "[title],[data-path],[data-root]").forEach((el) => {
        const raw = [
          el.getAttribute("title"),
          el.getAttribute("data-path"),
          el.getAttribute("data-root"),
        ].filter(Boolean).join(" ");
        const match = raw.match(/G:\\Vertex_Project\\Development\\([^\\\s]+)/i);
        if (!match) return;
        candidates.push({ name: match[1], source: el });
      });
    }

    const seen = new Set();
    return candidates.filter((item) => {
      const key = item.name.toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }).slice(0, 18);
  }

  class OrbitDeck {
    constructor(host, projects) {
      this.host = host;
      this.projects = projects;
      this.phase = 0;
      this.velocity = 0;
      this.lastFrame = performance.now();
      this.animating = true;
      this.cards = [];

      this.root = document.createElement("div");
      this.root.className = "vw-orbit-deck";
      this.root.dataset.vertexOrbit = "000026";
      this.root.innerHTML = `
        <div class="vw-orbit-core">
          <div class="vw-orbit-core-inner">
            <div class="vw-orbit-core-label">VERTEX<small>RAY CORE</small></div>
          </div>
        </div>
        <div class="vw-orbit-hint">WHEEL / ORBIT · FRONT CARD / SELECT</div>
      `;

      if (!projects.length) {
        const empty = document.createElement("div");
        empty.className = "vw-orbit-empty";
        empty.textContent = "AWAITING REAL PROJECT CARDS — NO FAKE PROJECTS";
        this.root.appendChild(empty);
      }

      projects.forEach((project, index) => this.addCard(project, index));
      host.appendChild(this.root);
      this.bind();
      requestAnimationFrame((time) => this.frame(time));
    }

    addCard(project, index) {
      const button = document.createElement("button");
      button.className = "vw-orbit-card";
      button.type = "button";
      button.innerHTML = `
        <div class="vw-orbit-name">${escapeHtml(project.name)}</div>
        <div class="vw-orbit-meta">PROJECT / RAY RELATION</div>
      `;
      button.addEventListener("click", () => this.onCardClick(index, project));
      this.root.appendChild(button);
      this.cards.push(button);
    }

    bind() {
      this.root.addEventListener("wheel", (event) => {
        event.preventDefault();
        const delta = Math.sign(event.deltaY || event.deltaX);
        this.velocity += delta * 0.075;
      }, { passive: false });

      this.root.addEventListener("pointerdown", () => {
        this.animating = true;
      });
    }

    onCardClick(index, project) {
      const count = this.projects.length;
      if (!count) return;
      const front = this.frontIndex();
      if (index !== front) {
        const step = (Math.PI * 2) / count;
        this.phase = -index * step;
        this.velocity = 0;
        this.render();
        return;
      }

      const source = project.source;
      if (source && source.isConnected) {
        try {
          source.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
        } catch (_) {}
      }

      window.dispatchEvent(new CustomEvent("vertex-project-select", {
        detail: { name: project.name, source: "RAY_ORBIT_000026" }
      }));
    }

    frontIndex() {
      const count = this.projects.length;
      if (!count) return -1;
      let best = { index: 0, depth: -Infinity };
      for (let index = 0; index < count; index++) {
        const angle = this.phase + index * (Math.PI * 2 / count);
        const depth = Math.cos(angle);
        if (depth > best.depth) best = { index, depth };
      }
      return best.index;
    }

    frame(time) {
      if (!this.root.isConnected) return;
      const dt = Math.min(32, time - this.lastFrame) / 16.667;
      this.lastFrame = time;

      if (Math.abs(this.velocity) > 0.0004) {
        this.phase += this.velocity * dt;
        this.velocity *= Math.pow(0.89, dt);
        this.render();
      } else if (this.animating) {
        this.render();
      }
      requestAnimationFrame((next) => this.frame(next));
    }

    render() {
      const count = this.projects.length;
      if (!count) return;

      const rect = this.root.getBoundingClientRect();
      const radiusX = Math.max(180, Math.min(rect.width * 0.34, 430));
      const radiusY = Math.max(105, Math.min(rect.height * 0.24, 170));
      const front = this.frontIndex();

      this.cards.forEach((card, index) => {
        const angle = this.phase + index * (Math.PI * 2 / count);
        const x = Math.sin(angle) * radiusX;
        const y = Math.sin(angle) * radiusY * 0.36;
        const depth = (Math.cos(angle) + 1) / 2; // 0 back -> 1 front
        const z = -280 + depth * 360;
        const scale = .68 + depth * .38;
        const opacity = .30 + depth * .70;
        const blur = (1 - depth) * 2.4;
        const zIndex = Math.round(10 + depth * 16);

        card.style.transform =
          `translate(-50%, -50%) translate3d(${x}px, ${y}px, ${z}px) scale(${scale})`;
        card.style.opacity = opacity.toFixed(3);
        card.style.filter = `blur(${blur.toFixed(2)}px)`;
        card.style.zIndex = String(zIndex);
        card.dataset.front = String(index === front);
        card.tabIndex = index === front ? 0 : -1;
        card.setAttribute("aria-current", index === front ? "true" : "false");
      });
    }
  }

  function enhanceRelationMap() {
    if (state.orbit?.root?.isConnected) return;

    const heading = relationHeading();
    const panel = nearestPanel(heading);
    if (!panel || panel.querySelector("[data-vertex-orbit='000026']")) return;

    const projects = uniqueProjectSources(panel);
    const mount = document.createElement("div");
    mount.dataset.vwOrbitMount = "000026";

    // Preserve original Ray source UI; the Orbit Deck is an interaction layer, not a destructive replacement.
    if (heading && heading.parentNode) {
      heading.parentNode.insertBefore(mount, heading.nextSibling);
    } else {
      panel.appendChild(mount);
    }

    state.orbit = new OrbitDeck(mount, projects);
  }

  /* ---------------- Facility workspaces ---------------- */

  function workspaceMarkup(name) {
    const meta = FACILITIES[name];
    const commonState = `<div class="vw-source-state">UI SHELL READY / LIVE BRIDGE MUST PROVE ITSELF</div>`;

    if (name === "VXN") {
      return `
        <div class="vw-facility-grid">
          <section class="vw-facility-card"><h3>TRAFFIC</h3><p>VXN message/packet traffic surface.</p>${commonState}</section>
          <section class="vw-facility-card"><h3>CONTRACT</h3><p>Capability and typed contract inspection surface.</p>${commonState}</section>
          <section class="vw-facility-card"><h3>ROUTE</h3><p>Route, relay and flow topology surface.</p>${commonState}</section>
        </div>`;
    }

    if (name === "JUDGE") {
      return `
        <div class="vw-facility-grid">
          <section class="vw-facility-card">
            <h3>VERDICTS</h3>
            <div class="vw-verdicts">
              <span class="vw-verdict">PASS</span>
              <span class="vw-verdict">PASS WITH WARNING</span>
              <span class="vw-verdict">REVIEW REQUIRED</span>
              <span class="vw-verdict">FAIL</span>
              <span class="vw-verdict">BLOCK</span>
            </div>
            ${commonState}
          </section>
          <section class="vw-facility-card"><h3>PHASE 1</h3><p>Artifact / Build / Test / Release</p></section>
          <section class="vw-facility-card"><h3>PHASE 2</h3><p>Runtime / Behavior</p></section>
          <section class="vw-facility-card"><h3>PHASE 3</h3><p>Dependency / Architecture / Compatibility</p></section>
          <section class="vw-facility-card"><h3>PHASE 4</h3><p>Visual / Performance / Memory / Security</p></section>
        </div>`;
    }

    if (name === "SENSOR") {
      return `
        <div class="vw-facility-grid">
          <section class="vw-facility-card"><h3>RUNTIME</h3><p>Process, health and runtime observation channels.</p>${commonState}</section>
          <section class="vw-facility-card"><h3>EVENT</h3><p>Change intensity and event stream observation.</p>${commonState}</section>
          <section class="vw-facility-card"><h3>RESOURCE</h3><p>CPU / memory / I/O / dependency observations.</p>${commonState}</section>
        </div>`;
    }

    if (name === "EVIDENCE") {
      return `
        <div class="vw-facility-grid">
          <section class="vw-facility-card"><h3>PROOF TIMELINE</h3><p>Artifact → Apply → Build → Test → Runtime Proof.</p>${commonState}</section>
          <section class="vw-facility-card"><h3>FAILURE</h3><p>Preserve failure evidence; never rewrite history.</p>${commonState}</section>
          <section class="vw-facility-card"><h3>SEARCH</h3><p>Evidence lookup by artifact, project, phase and result.</p>${commonState}</section>
        </div>`;
    }

    if (name === "RELEASE") {
      return `
        <div class="vw-facility-grid">
          <section class="vw-facility-card"><h3>CURRENT</h3><p>Active release / known-good identity.</p>${commonState}</section>
          <section class="vw-facility-card"><h3>PENDING</h3><p>Verified candidate waiting for safe activation.</p>${commonState}</section>
          <section class="vw-facility-card"><h3>LIFECYCLE</h3>
            <ul>
              <li>STAGE</li><li>SAFE POINT</li><li>SHUTDOWN</li><li>PROMOTE</li><li>HEALTH PROOF</li><li>COMMIT / ROLLBACK</li>
            </ul>
            ${commonState}
          </section>
        </div>`;
    }

    return `<div class="vw-facility-card"><h3>${escapeHtml(name)}</h3><p>${escapeHtml(meta.role)}</p></div>`;
  }

  function ensureWorkspace() {
    if (state.workspace?.isConnected) return state.workspace;

    const root = document.createElement("section");
    root.id = "vw-facility-workspace";
    root.dataset.open = "false";
    root.innerHTML = `
      <div class="vw-facility-shell">
        <header class="vw-facility-head">
          <div class="vw-facility-name" id="vw-facility-name">VXN</div>
          <div class="vw-facility-role" id="vw-facility-role">FLOW</div>
          <button class="vw-facility-close" type="button">CLOSE</button>
        </header>
        <main class="vw-facility-body" id="vw-facility-body"></main>
      </div>
    `;

    root.querySelector(".vw-facility-close").addEventListener("click", closeFacility);
    root.addEventListener("click", (event) => {
      if (event.target === root) closeFacility();
    });
    document.body.appendChild(root);
    state.workspace = root;
    return root;
  }

  function openFacility(name) {
    if (name === "CANONICAL") {
      if (window.VertexCanonicalRegistry?.open) {
        window.VertexCanonicalRegistry.open();
      }
      return;
    }

    const meta = FACILITIES[name];
    if (!meta) return;

    const root = ensureWorkspace();
    root.querySelector("#vw-facility-name").textContent = name;
    root.querySelector("#vw-facility-role").textContent = meta.role;
    root.querySelector("#vw-facility-body").innerHTML = workspaceMarkup(name);
    root.dataset.open = "true";

    qsa(document, ".vw-facility-button").forEach((button) => {
      button.dataset.active = String(button.dataset.facility === name);
    });
  }

  function closeFacility() {
    if (!state.workspace) return;
    state.workspace.dataset.open = "false";
    qsa(document, ".vw-facility-button").forEach((button) => {
      button.dataset.active = "false";
    });
  }

  function findFacilityNavContainer() {
    const labels = ["RAY", "FORGE", "VXN", "JUDGE", "SENSOR", "EVIDENCE", "RELEASE"];
    const elements = qsa(document, "nav,header,[role='tablist'],.tabs,[class*='nav'],[class*='tabs']");
    return elements
      .map((el) => ({
        el,
        count: labels.filter((label) => normalizedText(el).toUpperCase().includes(label)).length
      }))
      .sort((a, b) => b.count - a.count)[0]?.count >= 2
      ? elements
          .map((el) => ({
            el,
            count: labels.filter((label) => normalizedText(el).toUpperCase().includes(label)).length
          }))
          .sort((a, b) => b.count - a.count)[0].el
      : null;
  }

  function bindFacilityButtons() {
    const nav = findFacilityNavContainer();

    Object.entries(FACILITIES).forEach(([name, meta]) => {
      const existing = qsa(document, "button,[role='tab'],a").find((el) => exactText(el, name));
      if (existing) {
        if (existing.dataset.vwFacilityBound !== "true") {
          existing.dataset.vwFacilityBound = "true";
          existing.addEventListener("click", () => {
            if (FACILITIES[name]) setTimeout(() => openFacility(name), 0);
          });
        }
        return;
      }

      if (!nav) return;
      let dock = nav.querySelector(".vw-facility-dock");
      if (!dock) {
        dock = document.createElement("div");
        dock.className = "vw-facility-dock";
        nav.appendChild(dock);
      }

      const button = document.createElement("button");
      button.type = "button";
      button.className = "vw-facility-button";
      button.dataset.facility = name;
      button.innerHTML = `${name}<small>${meta.role}</small>`;
      button.addEventListener("click", () => openFacility(name));
      dock.appendChild(button);
    });
  }

  function installKeyboard() {
    if (document.documentElement.dataset.vwRefinementKeyboard === "true") return;
    document.documentElement.dataset.vwRefinementKeyboard = "true";

    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && state.workspace?.dataset.open === "true") {
        closeFacility();
      }
    });
  }

  function runEnhancements() {
    bindProductAccentContract();
    retireGlobalLanguageSettings();
    unifyRayPanels();
    bindFacilityButtons();
    enhanceRelationMap();
    installKeyboard();
  }

  function queueEnhancements() {
    if (state.mutationQueued) return;
    state.mutationQueued = true;
    requestAnimationFrame(() => {
      state.mutationQueued = false;
      runEnhancements();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    runEnhancements();

    const observer = new MutationObserver(queueEnhancements);
    observer.observe(document.body, { childList: true, subtree: true });
  });

  window.VertexWorksRefinement000026 = {
    openFacility,
    closeFacility,
    refresh: runEnhancements,
    state,
  };
})();
