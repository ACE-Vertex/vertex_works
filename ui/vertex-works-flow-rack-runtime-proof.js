/* VERTEX WORKS FLOW RACK RUNTIME PROOF — 000017
 * Runs only when the backend request marker exists.
 * It proves WebView -> Tauri -> VLAC -> FlowRack -> UI render -> Tauri acknowledgement.
 */
(() => {
  "use strict";

  function invoke() {
    return window.__TAURI__?.core?.invoke ?? null;
  }

  function frame() {
    return new Promise((resolve) => requestAnimationFrame(() => resolve()));
  }

  async function runRuntimeProof() {
    const nativeInvoke = invoke();
    if (!nativeInvoke || !window.VertexFlowRackUI) return;

    const probe = await nativeInvoke("flow_rack_runtime_probe");
    if (!probe) return;

    window.VertexFlowRackUI.render(probe.display_snapshot);
    await frame();
    await frame();

    const root = document.getElementById("vertex-flow-rack");
    const source = root?.querySelector("[data-vfr-source]")?.textContent?.trim() ?? "";
    const humanCard = root?.querySelector(`[data-job-id="${probe.human_job}"]`);
    const veraCard = root?.querySelector(`[data-job-id="${probe.vera_job}"]`);
    const renderedCards = root?.querySelectorAll(".vfr-strip").length ?? 0;

    const ack = {
      run_id: probe.run_id,
      root_present: Boolean(root),
      source_live_native: source === "LIVE_NATIVE",
      human_card_present: Boolean(humanCard),
      vera_card_present: Boolean(veraCard),
      rendered_card_count: renderedCards,
    };

    const evidence = await nativeInvoke("flow_rack_runtime_probe_finalize", { ack });

    if (evidence?.cleanup_snapshot) {
      window.VertexFlowRackUI.render(evidence.cleanup_snapshot);
    }

    window.dispatchEvent(
      new CustomEvent("vertex-flow-rack-runtime-proof", {
        detail: evidence,
      }),
    );

    console.info("[VERTEX FLOW RACK RUNTIME PROOF]", evidence);
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      () => {
        runRuntimeProof().catch((error) => {
          console.error("[VERTEX FLOW RACK RUNTIME PROOF]", error);
        });
      },
      { once: true },
    );
  } else {
    runRuntimeProof().catch((error) => {
      console.error("[VERTEX FLOW RACK RUNTIME PROOF]", error);
    });
  }
})();
