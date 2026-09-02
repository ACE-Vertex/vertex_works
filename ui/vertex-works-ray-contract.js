(() => {
  "use strict";

  const VERSION = "000087";
  const $ = (s, root = document) => root.querySelector(s);
  const state = {
    linkMode: "UNKNOWN",
    endpoints: "UNVERIFIED",
    saveDispatch: "UNVERIFIED",
    deleteDispatch: "UNVERIFIED",
    relationEditorVisible: false,
    from: "",
    to: "",
  };

  function visible(el) {
    if (!el) return false;
    const style = getComputedStyle(el);
    return !el.classList.contains("hidden") &&
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      style.opacity !== "0";
  }

  function cleanText(el) {
    return (el?.textContent || "").trim().replace(/\s+/g, " ");
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = String(value);
  }

  function refreshCapability() {
    const notice = $("#blueprintLinkNotice");
    const editor = $("#relationEditor");
    const from = cleanText($("#relationFrom"));
    const to = cleanText($("#relationTo"));

    state.relationEditorVisible = visible(editor);
    state.from = from;
    state.to = to;

    if (visible(notice)) state.linkMode = "LIVE";
    if (
      state.relationEditorVisible &&
      from && to &&
      from !== "—" && to !== "—" &&
      from !== "-" && to !== "-"
    ) {
      state.endpoints = "LIVE";
    }

    setText("vwRayRelationLink", state.linkMode);
    setText("vwRayRelationEndpoints", state.endpoints);
    setText("vwRayRelationSave", state.saveDispatch);
    setText("vwRayRelationDelete", state.deleteDispatch);

    const master = $("#vwRayRelationMaster");
    if (master) {
      let value = "STATIC";
      if (state.linkMode === "LIVE") value = "LINK LIVE";
      if (state.endpoints === "LIVE") value = "ENDPOINTS LIVE";
      if (state.saveDispatch === "OBSERVED") value = "SAVE DISPATCH";
      master.textContent = value;
      master.dataset.state = value.replace(/\s+/g, "-").toLowerCase();
    }
  }

  function buildContractPanel() {
    if ($("#vwRayContract")) return;
    const head = $(".blueprint-head");
    if (!head) return;

    const panel = document.createElement("section");
    panel.id = "vwRayContract";
    panel.className = "vw-ray-contract";
    panel.innerHTML = `
      <div class="vw-ray-contract-title">
        <small>RAY CAPABILITY CONTRACT</small>
        <b>RELATION MAP</b>
      </div>
      <div class="vw-ray-contract-cell">
        <small>EDITOR</small>
        <b>OFF</b>
        <em>NO GRID / SNAP / DRAG</em>
      </div>
      <div class="vw-ray-contract-cell">
        <small>RELATION</small>
        <b id="vwRayRelationMaster" data-state="static">STATIC</b>
        <em>OBSERVED, NOT FABRICATED</em>
      </div>
      <button id="vwRayRelationTestBtn" type="button">TEST LINK MODE</button>
    `;
    head.appendChild(panel);
  }

  function buildDiagnostics() {
    if ($("#vwRayRelationDiag")) return;
    const inspector = $(".relation-inspector");
    if (!inspector) return;

    const diag = document.createElement("section");
    diag.id = "vwRayRelationDiag";
    diag.className = "vw-ray-relation-diag";
    diag.innerHTML = `
      <header>
        <small>RELATION RUNTIME DIAGNOSTIC</small>
        <b>LIVE PATH</b>
      </header>
      <div><span>LINK MODE</span><b id="vwRayRelationLink">UNKNOWN</b></div>
      <div><span>ENDPOINT PAIR</span><b id="vwRayRelationEndpoints">UNVERIFIED</b></div>
      <div><span>SAVE DISPATCH</span><b id="vwRayRelationSave">UNVERIFIED</b></div>
      <div><span>DELETE DISPATCH</span><b id="vwRayRelationDelete">UNVERIFIED</b></div>
      <p>Diagnostic observes the existing Relation path. It does not create fake relations.</p>
    `;
    inspector.prepend(diag);
  }

  function relabelBlueprint() {
    const title = $(".blueprint-head h2");
    if (title) {
      title.removeAttribute("data-i18n");
      title.textContent = "Project Relation Map";
    }
    const lineage = $(".blueprint-head small");
    if (lineage) lineage.textContent = "PROJECT TOPOLOGY / RELATION MAP";

    const rayBrandTitle = $(".xray-brand strong");
    if (rayBrandTitle) {
      rayBrandTitle.removeAttribute("data-i18n");
      rayBrandTitle.textContent = "PROJECT INTELLIGENCE";
    }
    const rayBrandSub = $(".xray-brand span");
    if (rayBrandSub) {
      rayBrandSub.removeAttribute("data-i18n");
      rayBrandSub.textContent = "STRUCTURE / RELATION / EVIDENCE / READ ONLY";
    }
  }

  function declassifyEditorNodes() {
    const map = $("#xrayMap");
    if (!map) return;
    map.dataset.mode = "relation-map";
    map.setAttribute("aria-label", "Project Relation Map");

    // Existing visual nodes stay as relation endpoints / topology evidence.
    // They are explicitly not presented as draggable editor cards.
    const mark = () => {
      const candidates = map.querySelectorAll(
        '[class*="node"], [class*="project-card"], [class*="blueprint-card"]'
      );
      for (const el of candidates) {
        if (el === map || el.classList.contains("xray-core-placeholder")) continue;
        el.classList.add("vw-relation-node");
        el.removeAttribute("draggable");
        el.style.cursor = "pointer";
      }
    };
    mark();
    new MutationObserver(mark).observe(map, { childList: true, subtree: true });
  }

  async function testLinkMode() {
    const add = $("#blueprintAddRelationBtn");
    const cancel = $("#blueprintCancelLinkBtn");
    const btn = $("#vwRayRelationTestBtn");

    if (!add || !cancel) {
      state.linkMode = "MISSING";
      refreshCapability();
      if (btn) btn.textContent = "PATH MISSING";
      return;
    }

    if (btn) {
      btn.disabled = true;
      btn.textContent = "TESTING";
    }

    const notice = $("#blueprintLinkNotice");
    const wasVisible = visible(notice);

    try {
      if (!wasVisible) add.click();
      await new Promise(r => setTimeout(r, 120));
      state.linkMode = visible(notice) ? "LIVE" : "FAIL";
      refreshCapability();

      // Return to the original idle state. No endpoints are selected, no relation is saved.
      if (!wasVisible && visible(notice)) {
        cancel.click();
        await new Promise(r => setTimeout(r, 80));
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = state.linkMode === "LIVE" ? "LINK MODE PASS" : "TEST LINK MODE";
      }
      refreshCapability();
    }
  }

  function observeExistingRelationPath() {
    const notice = $("#blueprintLinkNotice");
    const editor = $("#relationEditor");
    const chip = $("#relationModeChip");

    const observer = new MutationObserver(refreshCapability);
    for (const el of [notice, editor, chip, $("#relationFrom"), $("#relationTo")]) {
      if (el) observer.observe(el, {
        attributes: true,
        childList: true,
        subtree: true,
        characterData: true,
      });
    }

    $("#blueprintAddRelationBtn")?.addEventListener("click", () => {
      setTimeout(refreshCapability, 0);
    });

    $("#blueprintCancelLinkBtn")?.addEventListener("click", () => {
      setTimeout(refreshCapability, 0);
    });

    $("#relationSaveBtn")?.addEventListener("click", () => {
      state.saveDispatch = "OBSERVED";
      setTimeout(refreshCapability, 0);
    }, true);

    $("#relationDeleteBtn")?.addEventListener("click", () => {
      state.deleteDispatch = "OBSERVED";
      setTimeout(refreshCapability, 0);
    }, true);
  }

  function boot() {
    relabelBlueprint();
    buildContractPanel();
    buildDiagnostics();
    declassifyEditorNodes();
    observeExistingRelationPath();
    $("#vwRayRelationTestBtn")?.addEventListener("click", testLinkMode);
    refreshCapability();

    try {
      window.VertexWorksFactoryKernel?.recordEvidence?.("RAY_CAPABILITY_CONTRACT", {
        version: VERSION,
        blueprintEditor: "DISABLED_BY_CAPABILITY_GATE",
        grid: false,
        snap: false,
        drag: false,
        relationUiContract: true,
        relationRuntime: "OBSERVE_EXISTING_PATH",
        theme: "VW_ORANGE_CHROME",
      });
    } catch (_) {}
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => setTimeout(boot, 0), { once: true });
  } else {
    setTimeout(boot, 0);
  }

  window.VertexWorksRayContract = Object.freeze({
    version: VERSION,
    testLinkMode,
    state: () => ({ ...state }),
  });
})();