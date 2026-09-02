(() => {
  "use strict";

  const SENSOR_VERSION = "000080";
  const SAMPLE_MS = 1500;
  const runtimeErrors = [];
  let lastTick = performance.now();
  let frameMs = null;
  let loopDriftMs = 0;
  let lastInspection = null;

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const state = {
    frameMs: null,
    loopDriftMs: 0,
    domNodes: 0,
    heapMB: null,
    viewport: "",
    workspace: "UNKNOWN",
    online: navigator.onLine,
    visibility: document.visibilityState,
    errorCount: 0,
    inspection: null,
  };

  window.addEventListener("error", (event) => {
    runtimeErrors.push({
      type: "error",
      message: String(event.message || "Unknown runtime error"),
      time: new Date().toISOString(),
    });
    if (runtimeErrors.length > 50) runtimeErrors.shift();
  });

  window.addEventListener("unhandledrejection", (event) => {
    runtimeErrors.push({
      type: "unhandledrejection",
      message: String(event.reason || "Unhandled promise rejection"),
      time: new Date().toISOString(),
    });
    if (runtimeErrors.length > 50) runtimeErrors.shift();
  });

  function isHidden(el) {
    if (!el) return true;
    const style = getComputedStyle(el);
    return (
      style.display === "none" ||
      style.visibility === "hidden" ||
      Number(style.opacity || "1") === 0 ||
      el.hidden
    );
  }

  function activeWorkspace() {
    const ray = $("#xrayWorkspace");
    const forge = $("#forgeWorkspace");
    const rayVisible = ray && !isHidden(ray) && !ray.classList.contains("workspace-hidden");
    const forgeVisible = forge && !isHidden(forge) && !forge.classList.contains("workspace-hidden");
    if (rayVisible && !forgeVisible) return "RAY";
    if (forgeVisible && !rayVisible) return "FORGE";
    if (rayVisible && forgeVisible) return "RAY+FORGE";
    return "UNKNOWN";
  }

  function heapMB() {
    const memory = performance.memory;
    if (!memory || typeof memory.usedJSHeapSize !== "number") return null;
    return memory.usedJSHeapSize / (1024 * 1024);
  }

  function sampleFrame() {
    requestAnimationFrame((t1) => {
      requestAnimationFrame((t2) => {
        frameMs = Math.max(0, t2 - t1);
        state.frameMs = frameMs;
      });
    });
  }

  function refreshRuntimeState() {
    const now = performance.now();
    const expected = lastTick + SAMPLE_MS;
    loopDriftMs = Math.max(0, now - expected);
    lastTick = now;

    state.loopDriftMs = loopDriftMs;
    state.domNodes = document.getElementsByTagName("*").length;
    state.heapMB = heapMB();
    state.viewport = `${window.innerWidth}x${window.innerHeight}`;
    state.workspace = activeWorkspace();
    state.online = navigator.onLine;
    state.visibility = document.visibilityState;
    state.errorCount = runtimeErrors.length;

    sampleFrame();
    renderSensorStrip();
  }

  function visibleJapaneseNodes() {
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          const value = node.nodeValue?.trim();
          if (!value || !/[\u3040-\u30ff\u3400-\u9fff]/.test(value)) {
            return NodeFilter.FILTER_REJECT;
          }
          const parent = node.parentElement;
          if (!parent || isHidden(parent)) return NodeFilter.FILTER_REJECT;
          if (parent.closest("#vwSensorPanel")) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        },
      }
    );

    const matches = [];
    while (walker.nextNode() && matches.length < 20) {
      matches.push(walker.currentNode.nodeValue.trim().slice(0, 120));
    }
    return matches;
  }

  function duplicateIds() {
    const counts = new Map();
    for (const el of $$("[id]")) {
      counts.set(el.id, (counts.get(el.id) || 0) + 1);
    }
    return [...counts.entries()].filter(([, count]) => count > 1);
  }

  function brokenImages() {
    return $$("img").filter((img) => img.complete && img.naturalWidth === 0);
  }

  function veraHandoffPresent() {
    const explicit = $("[id*='vera' i], [class*='vera' i]");
    if (explicit) return true;
    return $$("button").some((button) =>
      /clip\s+to\s+vera|send\s+to\s+vera/i.test(button.textContent || "")
    );
  }

  function stylesheetLoaded(fragment) {
    return $$("link[rel='stylesheet']").some((link) =>
      String(link.getAttribute("href") || "").includes(fragment)
    );
  }

  function brandIconHealthy() {
    const images = $$("img[src*='vertex-works-app-icon.png']");
    return images.length > 0 && images.every((img) => !img.complete || img.naturalWidth > 0);
  }

  function runInspection() {
    const jp = visibleJapaneseNodes();
    const dup = duplicateIds();
    const broken = brokenImages();
    const overflowPx = Math.max(
      0,
      document.documentElement.scrollWidth - document.documentElement.clientWidth
    );

    const checks = [
      check("DOC_LANG_EN", document.documentElement.lang.toLowerCase() === "en",
        document.documentElement.lang || "(empty)"),
      check("VW_PRODUCT", document.documentElement.dataset.product === "VW",
        document.documentElement.dataset.product || "(empty)"),
      check("ORANGE_THEME", stylesheetLoaded("vertex-works-orange.css"),
        "vertex-works-orange.css"),
      check("BRAND_ICON", brandIconHealthy(),
        "VW product icon"),
      check("RAY_SURFACE", !!$("#xrayWorkspace"),
        "xrayWorkspace"),
      check("FORGE_SURFACE", !!$("#forgeWorkspace"),
        "forgeWorkspace"),
      check("VERA_HANDOFF", veraHandoffPresent(),
        "clip/send control"),
      check("DUPLICATE_IDS", dup.length === 0,
        dup.length ? JSON.stringify(dup.slice(0, 8)) : "none"),
      check("VISIBLE_JAPANESE", jp.length === 0,
        jp.length ? jp.slice(0, 6).join(" | ") : "none"),
      check("HORIZONTAL_OVERFLOW", overflowPx <= 2,
        `${overflowPx}px`),
      check("BROKEN_IMAGES", broken.length === 0,
        broken.length ? broken.map((img) => img.src).slice(0, 5).join(" | ") : "none"),
      check("RUNTIME_ERRORS", runtimeErrors.length === 0,
        `${runtimeErrors.length}`),
      check("SENSOR_TOPBAR_HOST", $("#vwSensorDock")?.parentElement?.id === "vertexModeBar",
        $("#vwSensorDock")?.parentElement?.id || "no-host"),
    ];

    const failed = checks.filter((item) => !item.pass);
    const verdict = failed.length === 0 ? "PASS" : "FAIL";

    lastInspection = {
      schema: "vertex-works/inspection/1",
      sensorVersion: SENSOR_VERSION,
      timestamp: new Date().toISOString(),
      verdict,
      activeWorkspace: activeWorkspace(),
      runtime: {
        frameMs: numberOrNull(state.frameMs),
        eventLoopDriftMs: numberOrNull(state.loopDriftMs),
        domNodes: state.domNodes,
        heapMB: numberOrNull(state.heapMB),
        viewport: state.viewport,
        online: state.online,
        visibility: state.visibility,
        capturedRuntimeErrors: runtimeErrors.slice(-20),
      },
      checks,
    };
    state.inspection = lastInspection;

    renderInspection(lastInspection);
    renderSensorStrip();
    return lastInspection;
  }

  function check(name, pass, detail) {
    return { name, pass: Boolean(pass), detail: String(detail ?? "") };
  }

  function numberOrNull(value) {
    return Number.isFinite(value) ? Number(value.toFixed(2)) : null;
  }

  function sensorValue(value, suffix = "") {
    if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
    return `${value}${suffix}`;
  }

  function renderSensorStrip() {
    const verdict = lastInspection?.verdict || "IDLE";
    const badge = $("#vwSensorVerdict");
    if (badge) {
      badge.textContent = verdict;
      badge.dataset.verdict = verdict;
    }

    setText("vwSensorWorkspace", state.workspace);
    setText("vwSensorFrame", sensorValue(
      Number.isFinite(state.frameMs) ? state.frameMs.toFixed(1) : null, "ms"
    ));
    setText("vwSensorLoop", sensorValue(
      Number.isFinite(state.loopDriftMs) ? state.loopDriftMs.toFixed(1) : null, "ms"
    ));
    setText("vwSensorDom", state.domNodes);
    setText("vwSensorHeap", state.heapMB === null ? "N/A" : `${state.heapMB.toFixed(1)}MB`);
  }

  function renderInspection(report) {
    const list = $("#vwInspectionList");
    if (!list) return;
    list.innerHTML = "";
    for (const item of report.checks) {
      const row = document.createElement("div");
      row.className = `vw-inspection-row ${item.pass ? "pass" : "fail"}`;
      const name = document.createElement("b");
      name.textContent = item.name;
      const status = document.createElement("span");
      status.textContent = item.pass ? "PASS" : "FAIL";
      const detail = document.createElement("em");
      detail.textContent = item.detail;
      row.append(name, status, detail);
      list.appendChild(row);
    }
    setText("vwInspectionTimestamp", report.timestamp);
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = String(value);
  }

  async function copyReport() {
    const report = lastInspection || runInspection();
    const text = JSON.stringify(report, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      flashButton("vwSensorCopyBtn", "COPIED");
    } catch (_) {
      const area = document.createElement("textarea");
      area.value = text;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
      flashButton("vwSensorCopyBtn", "COPIED");
    }
  }

  function flashButton(id, label) {
    const button = document.getElementById(id);
    if (!button) return;
    const prior = button.textContent;
    button.textContent = label;
    setTimeout(() => { button.textContent = prior; }, 900);
  }

  function bind() {
    $("#vwSensorToggle")?.addEventListener("click", () => {
      $("#vwSensorPanel")?.classList.toggle("open");
    });
    $("#vwSensorCloseBtn")?.addEventListener("click", () => {
      $("#vwSensorPanel")?.classList.remove("open");
    });
    $("#vwSensorInspectBtn")?.addEventListener("click", runInspection);
    $("#vwSensorCopyBtn")?.addEventListener("click", copyReport);

    window.addEventListener("online", refreshRuntimeState);
    window.addEventListener("offline", refreshRuntimeState);
    document.addEventListener("visibilitychange", refreshRuntimeState);

    refreshRuntimeState();
    setInterval(refreshRuntimeState, SAMPLE_MS);
    setTimeout(runInspection, 1200);
  }

  function mount() {
    if ($("#vwSensorDock")) return;

    const host = $("#vertexModeBar");
    if (!host) {
      console.error("VERTEX WORKS SENSOR BUS: vertexModeBar host missing");
      return;
    }

    const dock = document.createElement("section");
    dock.id = "vwSensorDock";
    dock.className = "vw-sensor-dock";
    dock.innerHTML = `
      <button id="vwSensorToggle" class="vw-sensor-toggle" type="button"
              aria-label="Open Vertex Works sensors">
        <span class="vw-sensor-pulse"></span>
        <b>SENSOR</b>
        <em id="vwSensorWorkspace">BOOT</em>
        <strong id="vwSensorVerdict" data-verdict="IDLE">IDLE</strong>
      </button>

      <div id="vwSensorPanel" class="vw-sensor-panel" aria-label="Vertex Works Sensor Bus">
        <header>
          <div>
            <small>VERTEX WORKS / REAL OBSERVATION</small>
            <h3>SENSOR BUS <span>000080</span></h3>
          </div>
          <button id="vwSensorCloseBtn" type="button">×</button>
        </header>

        <div class="vw-runtime-grid">
          <article><small>FRAME</small><b id="vwSensorFrame">N/A</b></article>
          <article><small>LOOP</small><b id="vwSensorLoop">N/A</b></article>
          <article><small>DOM</small><b id="vwSensorDom">0</b></article>
          <article><small>HEAP</small><b id="vwSensorHeap">N/A</b></article>
        </div>

        <section class="vw-inspection-head">
          <div>
            <small>INSPECTION GATE</small>
            <strong id="vwInspectionTimestamp">NOT RUN</strong>
          </div>
          <div>
            <button id="vwSensorInspectBtn" type="button">RUN INSPECTION</button>
            <button id="vwSensorCopyBtn" type="button">COPY REPORT</button>
          </div>
        </section>

        <div id="vwInspectionList" class="vw-inspection-list">
          <div class="vw-inspection-empty">
            Waiting for the first real inspection cycle.
          </div>
        </div>

        <footer>
          <span>NO FAKE TELEMETRY</span>
          <span>LOW-FREQUENCY SAMPLE ${SAMPLE_MS}ms</span>
        </footer>
      </div>
    `;

    const settingsButton = $("#settingsBtn");
    if (settingsButton && settingsButton.parentElement === host) {
      host.insertBefore(dock, settingsButton);
    } else {
      host.appendChild(dock);
    }

    bind();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount, { once: true });
  } else {
    mount();
  }

  window.VertexWorksSensors = Object.freeze({
    version: SENSOR_VERSION,
    inspect: runInspection,
    snapshot: () => JSON.parse(JSON.stringify(state)),
    lastReport: () => lastInspection ? JSON.parse(JSON.stringify(lastInspection)) : null,
  });
})();
