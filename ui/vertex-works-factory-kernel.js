(() => {
  "use strict";

  const VERSION = "000081";
  const EVIDENCE_KEY = "vertexWorks.factoryKernel.evidence.v1";
  const MAX_EVIDENCE = 80;
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];

  let activeFacility = "RAY";
  let lastJudge = null;
  let lastRecordedSensorTimestamp = null;

  // FACTORY_NAV_LOOP_CUT_000084
  // Facility switching is a state transition only.
  // RAY/FORGE navigation controls must never be programmatically self-clicked.
  const FACTORY_NAV_SELF_CLICK = false;

  function safeClone(value) {
    return value == null ? value : JSON.parse(JSON.stringify(value));
  }

  function sensorApi() {
    return window.VertexWorksSensors || null;
  }

  function sensorSnapshot() {
    const api = sensorApi();
    try {
      return api?.snapshot?.() || null;
    } catch (_) {
      return null;
    }
  }

  function sensorReport() {
    const api = sensorApi();
    try {
      return api?.lastReport?.() || null;
    } catch (_) {
      return null;
    }
  }

  function readEvidence() {
    try {
      const raw = localStorage.getItem(EVIDENCE_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return [];
    }
  }

  function writeEvidence(records) {
    try {
      localStorage.setItem(EVIDENCE_KEY, JSON.stringify(records.slice(-MAX_EVIDENCE)));
      return true;
    } catch (_) {
      return false;
    }
  }

  function recordEvidence(type, payload) {
    const records = readEvidence();
    const entry = {
      schema: "vertex-works/evidence/1",
      timestamp: new Date().toISOString(),
      type,
      facility: activeFacility,
      payload: safeClone(payload),
    };
    records.push(entry);
    writeEvidence(records);
    renderEvidence();
    return entry;
  }

  function getCheck(report, name) {
    return report?.checks?.find((item) => item.name === name) || null;
  }

  function judgeNow() {
    const report = sensorReport();
    const snapshot = sensorSnapshot();

    const gates = [];

    function gate(name, state, detail) {
      gates.push({ name, state, detail: String(detail ?? "") });
    }

    if (!report) {
      gate("SENSOR_GATE", "BLOCK", "No runtime inspection report is available.");
    } else {
      gate(
        "SENSOR_GATE",
        report.verdict === "PASS" ? "PASS" : "BLOCK",
        `Sensor verdict: ${report.verdict}`
      );

      const mapping = [
        ["LANGUAGE_GATE", "VISIBLE_JAPANESE"],
        ["LAYOUT_GATE", "HORIZONTAL_OVERFLOW"],
        ["ASSET_GATE", "BROKEN_IMAGES"],
        ["RUNTIME_GATE", "RUNTIME_ERRORS"],
        ["DOM_ID_GATE", "DUPLICATE_IDS"],
        ["VERA_GATE", "VERA_HANDOFF"],
        ["PRODUCT_GATE", "VW_PRODUCT"],
        ["TOPBAR_GATE", "SENSOR_TOPBAR_HOST"],
      ];

      for (const [gateName, checkName] of mapping) {
        const check = getCheck(report, checkName);
        if (!check) {
          gate(gateName, "UNAVAILABLE", `${checkName} not exposed by current sensor.`);
        } else {
          gate(gateName, check.pass ? "PASS" : "BLOCK", check.detail);
        }
      }
    }

    // Build/runtime-native instrumentation is not fabricated.
    // It becomes a real gate only when a native bridge exposes evidence.
    gate(
      "NATIVE_BUILD_GATE",
      "UNAVAILABLE",
      "Native Cargo/build evidence bridge is not connected to the UI kernel yet."
    );

    const blocking = gates.filter((g) => g.state === "BLOCK");
    const unavailable = gates.filter((g) => g.state === "UNAVAILABLE");

    const verdict = blocking.length
      ? "BLOCK"
      : unavailable.length
        ? "REVIEW"
        : "PASS";

    lastJudge = {
      schema: "vertex-works/judge/1",
      judgeVersion: VERSION,
      timestamp: new Date().toISOString(),
      verdict,
      facility: activeFacility,
      sensorReportTimestamp: report?.timestamp || null,
      runtime: snapshot,
      gates,
    };

    recordEvidence("JUDGE_VERDICT", lastJudge);
    renderJudge();
    renderRelease();
    renderFactoryStrip();
    return safeClone(lastJudge);
  }

  function latestJudge() {
    return safeClone(lastJudge);
  }

  function releaseGate() {
    const verdict = lastJudge?.verdict || "NO_JUDGEMENT";
    if (verdict === "PASS") {
      return {
        state: "READY",
        detail: "All currently connected gates passed.",
        promotionConnected: false,
      };
    }
    if (verdict === "REVIEW") {
      return {
        state: "REVIEW",
        detail: "No blocking gate failed, but one or more native gates are unavailable.",
        promotionConnected: false,
      };
    }
    if (verdict === "BLOCK") {
      return {
        state: "BLOCKED",
        detail: "One or more connected inspection gates failed.",
        promotionConnected: false,
      };
    }
    return {
      state: "NOT_READY",
      detail: "Run JUDGE after a Sensor inspection.",
      promotionConnected: false,
    };
  }

  function facilityNode() {
    return $("#vwFactoryWorkspace");
  }

  function existingRay() {
    return $("#xrayWorkspace");
  }

  function existingForge() {
    return $("#forgeWorkspace");
  }

  function setVisible(el, visible) {
    if (!el) return;
    el.classList.toggle("vw-factory-hidden", !visible);
  }

  function clickExisting(id) {
    const button = document.getElementById(id);
    if (button) {
      try { button.click(); } catch (_) {}
    }
  }

  function switchFacility(name) {
    activeFacility = String(name || "RAY").toUpperCase();

    const ray = existingRay();
    const forge = existingForge();
    const factory = facilityNode();

    if (activeFacility === "RAY") {
      setVisible(factory, false);
      setVisible(ray, true);
      setVisible(forge, false);
    } else if (activeFacility === "FORGE") {
      setVisible(factory, false);
      setVisible(ray, false);
      setVisible(forge, true);
    } else {
      setVisible(ray, false);
      setVisible(forge, false);
      setVisible(factory, true);
      factory.dataset.facility = activeFacility;

      for (const panel of $$(".vw-factory-facility", factory)) {
        panel.classList.toggle("active", panel.dataset.facility === activeFacility);
      }

      if (activeFacility === "SENSOR") renderSensor();
      if (activeFacility === "JUDGE") renderJudge();
      if (activeFacility === "EVIDENCE") renderEvidence();
      if (activeFacility === "RELEASE") renderRelease();
    }

    for (const button of $$("#vwFactoryNav [data-facility]")) {
      button.classList.toggle("active", button.dataset.facility === activeFacility);
    }

    renderFactoryStrip();
  }

  function renderFactoryStrip() {
    setText("vwFactoryFacility", activeFacility);
    setText("vwFactorySensorVerdict", sensorReport()?.verdict || "IDLE");
    setText("vwFactoryJudgeVerdict", lastJudge?.verdict || "IDLE");
    const release = releaseGate();
    setText("vwFactoryReleaseGate", release.state);
  }

  function renderSensor() {
    const snapshot = sensorSnapshot();
    const report = sensorReport();

    setText("vwFullSensorWorkspace", snapshot?.workspace || "UNKNOWN");
    setText("vwFullSensorFrame", formatMetric(snapshot?.frameMs, "ms"));
    setText("vwFullSensorLoop", formatMetric(snapshot?.loopDriftMs, "ms"));
    setText("vwFullSensorDom", snapshot?.domNodes ?? "N/A");
    setText("vwFullSensorHeap", formatMetric(snapshot?.heapMB, "MB"));
    setText("vwFullSensorViewport", snapshot?.viewport || "N/A");
    setText("vwFullSensorVerdict", report?.verdict || "IDLE");
    setText("vwFullSensorTimestamp", report?.timestamp || "No inspection report yet.");

    const list = $("#vwFullSensorChecks");
    if (list) {
      list.innerHTML = "";
      const checks = report?.checks || [];
      if (!checks.length) {
        list.innerHTML = '<div class="vw-empty">Run a real Sensor inspection first.</div>';
      } else {
        for (const check of checks) {
          const row = document.createElement("div");
          row.className = `vw-kernel-row ${check.pass ? "pass" : "fail"}`;
          row.innerHTML = `
            <b>${escapeHtml(check.name)}</b>
            <span>${check.pass ? "PASS" : "FAIL"}</span>
            <em>${escapeHtml(check.detail)}</em>
          `;
          list.appendChild(row);
        }
      }
    }
  }

  function renderJudge() {
    const view = $("#vwJudgeGates");
    if (!view) return;

    const judge = lastJudge;
    setText("vwJudgeVerdictLarge", judge?.verdict || "NOT RUN");
    setText("vwJudgeTimestamp", judge?.timestamp || "Run Judge after Sensor inspection.");

    view.innerHTML = "";
    if (!judge?.gates?.length) {
      view.innerHTML = '<div class="vw-empty">No Judge verdict yet.</div>';
      return;
    }

    for (const gate of judge.gates) {
      const row = document.createElement("div");
      row.className = `vw-kernel-row ${gate.state.toLowerCase()}`;
      row.innerHTML = `
        <b>${escapeHtml(gate.name)}</b>
        <span>${escapeHtml(gate.state)}</span>
        <em>${escapeHtml(gate.detail)}</em>
      `;
      view.appendChild(row);
    }
  }

  function renderEvidence() {
    const view = $("#vwEvidenceRecords");
    if (!view) return;
    const records = readEvidence().slice().reverse();

    setText("vwEvidenceCount", records.length);

    view.innerHTML = "";
    if (!records.length) {
      view.innerHTML = '<div class="vw-empty">Evidence store is empty.</div>';
      return;
    }

    for (const record of records.slice(0, 60)) {
      const row = document.createElement("article");
      row.className = "vw-evidence-record";
      row.innerHTML = `
        <header>
          <b>${escapeHtml(record.type)}</b>
          <span>${escapeHtml(record.timestamp)}</span>
        </header>
        <pre>${escapeHtml(JSON.stringify(record.payload, null, 2))}</pre>
      `;
      view.appendChild(row);
    }
  }

  function renderRelease() {
    const gate = releaseGate();
    setText("vwReleaseState", gate.state);
    setText("vwReleaseDetail", gate.detail);
    setText(
      "vwReleasePromotion",
      gate.promotionConnected ? "CONNECTED" : "NOT CONNECTED"
    );

    const reasons = $("#vwReleaseReasons");
    if (reasons) {
      reasons.innerHTML = "";
      const blocks = lastJudge?.gates?.filter((g) => g.state !== "PASS") || [];
      if (!blocks.length) {
        reasons.innerHTML = '<div class="vw-empty">No unresolved connected gates.</div>';
      } else {
        for (const gateItem of blocks) {
          const row = document.createElement("div");
          row.className = `vw-kernel-row ${gateItem.state.toLowerCase()}`;
          row.innerHTML = `
            <b>${escapeHtml(gateItem.name)}</b>
            <span>${escapeHtml(gateItem.state)}</span>
            <em>${escapeHtml(gateItem.detail)}</em>
          `;
          reasons.appendChild(row);
        }
      }
    }
  }

  async function runSensorInspection() {
    const api = sensorApi();
    if (!api?.inspect) return null;
    const report = api.inspect();
    recordEvidence("SENSOR_INSPECTION", report);
    renderSensor();
    renderFactoryStrip();
    return report;
  }

  async function copyCurrentEvidence() {
    const bundle = {
      schema: "vertex-works/vera-handoff/1",
      timestamp: new Date().toISOString(),
      facility: activeFacility,
      sensor: sensorReport(),
      judge: lastJudge,
      releaseGate: releaseGate(),
      recentEvidence: readEvidence().slice(-12),
    };

    const text = JSON.stringify(bundle, null, 2);
    await copyText(text);
    pulseButton("vwEvidenceCopyBtn", "COPIED");
    return bundle;
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      const area = document.createElement("textarea");
      area.value = text;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }
  }

  function pulseButton(id, label) {
    const button = document.getElementById(id);
    if (!button) return;
    const old = button.textContent;
    button.textContent = label;
    setTimeout(() => { button.textContent = old; }, 900);
  }

  function formatMetric(value, suffix) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
    return `${Number(value).toFixed(1)}${suffix}`;
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = String(value);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function buildFactoryWorkspace() {
    if ($("#vwFactoryWorkspace")) return;

    const workspace = document.createElement("main");
    workspace.id = "vwFactoryWorkspace";
    workspace.className = "vw-factory-workspace vw-factory-hidden";
    workspace.innerHTML = `
      <section class="vw-factory-facility" data-facility="JUDGE">
        <header class="vw-facility-head">
          <div>
            <small>VERTEX WORKS / DECISION FACILITY</small>
            <h1>JUDGE</h1>
            <p>Connected evidence becomes a gate. Missing evidence stays unavailable.</p>
          </div>
          <div class="vw-facility-verdict">
            <small>VERDICT</small>
            <strong id="vwJudgeVerdictLarge">NOT RUN</strong>
            <span id="vwJudgeTimestamp">Run Judge after Sensor inspection.</span>
          </div>
          <button id="vwJudgeRunBtn" class="vw-primary" type="button">RUN JUDGE</button>
        </header>
        <div id="vwJudgeGates" class="vw-kernel-list"></div>
      </section>

      <section class="vw-factory-facility" data-facility="SENSOR">
        <header class="vw-facility-head">
          <div>
            <small>VERTEX WORKS / OBSERVATION FACILITY</small>
            <h1>SENSOR</h1>
            <p>Runtime facts only. No synthetic telemetry.</p>
          </div>
          <div class="vw-facility-verdict">
            <small>SENSOR VERDICT</small>
            <strong id="vwFullSensorVerdict">IDLE</strong>
            <span id="vwFullSensorTimestamp">No inspection report yet.</span>
          </div>
          <button id="vwFullSensorRunBtn" class="vw-primary" type="button">RUN INSPECTION</button>
        </header>

        <div class="vw-metric-wall">
          <article><small>WORKSPACE</small><b id="vwFullSensorWorkspace">UNKNOWN</b></article>
          <article><small>FRAME</small><b id="vwFullSensorFrame">N/A</b></article>
          <article><small>LOOP DRIFT</small><b id="vwFullSensorLoop">N/A</b></article>
          <article><small>DOM</small><b id="vwFullSensorDom">N/A</b></article>
          <article><small>HEAP</small><b id="vwFullSensorHeap">N/A</b></article>
          <article><small>VIEWPORT</small><b id="vwFullSensorViewport">N/A</b></article>
        </div>

        <div id="vwFullSensorChecks" class="vw-kernel-list"></div>
      </section>

      <section class="vw-factory-facility" data-facility="EVIDENCE">
        <header class="vw-facility-head">
          <div>
            <small>VERTEX WORKS / PROOF FACILITY</small>
            <h1>EVIDENCE</h1>
            <p>Inspection and Judge records are retained as local factory evidence.</p>
          </div>
          <div class="vw-facility-verdict">
            <small>RECORDS</small>
            <strong id="vwEvidenceCount">0</strong>
            <span>Latest 80 local kernel records.</span>
          </div>
          <button id="vwEvidenceCopyBtn" class="vw-primary" type="button">CLIP TO VERA</button>
        </header>
        <div id="vwEvidenceRecords" class="vw-evidence-list"></div>
      </section>

      <section class="vw-factory-facility" data-facility="RELEASE">
        <header class="vw-facility-head">
          <div>
            <small>VERTEX WORKS / SHIP FACILITY</small>
            <h1>RELEASE</h1>
            <p>Release readiness is derived from real connected gates.</p>
          </div>
          <div class="vw-facility-verdict">
            <small>RELEASE GATE</small>
            <strong id="vwReleaseState">NOT READY</strong>
            <span id="vwReleaseDetail">Run Judge after a Sensor inspection.</span>
          </div>
        </header>

        <div class="vw-release-contract">
          <article>
            <small>PROMOTION COMMAND</small>
            <b id="vwReleasePromotion">NOT CONNECTED</b>
            <p>The UI kernel will not pretend to promote a release until the native bridge exists.</p>
          </article>
          <article>
            <small>GATE SOURCE</small>
            <b>JUDGE / SENSOR</b>
            <p>Blocking inspection evidence prevents READY status.</p>
          </article>
        </div>

        <div id="vwReleaseReasons" class="vw-kernel-list"></div>
      </section>
    `;

    const ray = existingRay();
    if (ray?.parentElement) {
      ray.parentElement.insertBefore(workspace, ray);
    } else {
      document.body.appendChild(workspace);
    }
  }

  function extendTopNavigation() {
    const nav = $(".mode-switch");
    if (!nav || $("#vwFactoryNav")) return;

    nav.id = "vwFactoryNav";

    for (const button of $$("button", nav)) {
      if (button.id === "rayNavBtn") button.dataset.facility = "RAY";
      if (button.id === "forgeNavBtn") button.dataset.facility = "FORGE";
    }

    const facilities = [
      ["JUDGE", "03", "DECIDE"],
      ["SENSOR", "04", "OBSERVE"],
      ["EVIDENCE", "05", "PROVE"],
      ["RELEASE", "06", "SHIP"],
    ];

    for (const [name, index, sub] of facilities) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.facility = name;
      button.innerHTML = `<span class="mode-index">${index}</span><b>${name}</b><em>${sub}</em>`;
      nav.appendChild(button);
    }

    nav.addEventListener("click", (event) => {
      const button = event.target.closest("[data-facility]");
      if (!button) return;
      const facility = button.dataset.facility;
      if (facility === "RAY" || facility === "FORGE") {
        setTimeout(() => switchFacility(facility), 0);
      } else {
        event.preventDefault();
        switchFacility(facility);
      }
    });
  }

  function installFactoryStrip() {
    const topbar = $("#vertexModeBar");
    const sensorDock = $("#vwSensorDock");
    if (!topbar || $("#vwFactoryStrip")) return;

    const strip = document.createElement("section");
    strip.id = "vwFactoryStrip";
    strip.className = "vw-factory-strip";
    strip.innerHTML = `
      <span><small>FACILITY</small><b id="vwFactoryFacility">RAY</b></span>
      <span><small>SENSOR</small><b id="vwFactorySensorVerdict">IDLE</b></span>
      <span><small>JUDGE</small><b id="vwFactoryJudgeVerdict">IDLE</b></span>
      <span><small>RELEASE</small><b id="vwFactoryReleaseGate">NOT_READY</b></span>
    `;

    if (sensorDock && sensorDock.parentElement === topbar) {
      topbar.insertBefore(strip, sensorDock);
    } else {
      topbar.appendChild(strip);
    }
  }

  function removeDuplicateProductIcons() {
    // Keep the top-left product identity only. Inner facility marks remain textual.
    for (const img of $$(".xray-brand img, .works-mark img, .works-mark .vertex-project-mark")) {
      img.classList.add("vw-duplicate-product-icon");
    }
  }

  function bindKernel() {
    $("#vwJudgeRunBtn")?.addEventListener("click", judgeNow);
    $("#vwFullSensorRunBtn")?.addEventListener("click", async () => {
      await runSensorInspection();
      renderSensor();
    });
    $("#vwEvidenceCopyBtn")?.addEventListener("click", copyCurrentEvidence);

    setInterval(() => {
      const report = sensorReport();
      if (report?.timestamp && report.timestamp !== lastRecordedSensorTimestamp) {
        lastRecordedSensorTimestamp = report.timestamp;
        recordEvidence("SENSOR_INSPECTION", report);
      }

      if (activeFacility === "SENSOR") renderSensor();
      renderFactoryStrip();
    }, 2000);
  }

  function boot() {
    extendTopNavigation();
    buildFactoryWorkspace();
    installFactoryStrip();
    removeDuplicateProductIcons();
    bindKernel();
    switchFacility("RAY");

    recordEvidence("FACTORY_KERNEL_BOOT", {
      version: VERSION,
      facilities: ["RAY", "FORGE", "JUDGE", "SENSOR", "EVIDENCE", "RELEASE"],
      sensorConnected: Boolean(sensorApi()),
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => setTimeout(boot, 0), { once: true });
  } else {
    setTimeout(boot, 0);
  }

  window.VertexWorksFactoryKernel = Object.freeze({
    version: VERSION,
    switchFacility,
    judge: judgeNow,
    latestJudge,
    releaseGate,
    evidence: () => safeClone(readEvidence()),
    recordEvidence,
    currentFacility: () => activeFacility,
  });
})();
