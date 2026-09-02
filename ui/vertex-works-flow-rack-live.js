/* VERTEX WORKS FLOW RACK LIVE BRIDGE — 000016
 * Human UI command intents -> Tauri -> VLAC Works Unit -> authoritative Flow Rack snapshot.
 */
(() => {
  "use strict";

  const COMMAND_EVENT = "vertex-flow-rack-command";
  const LIVE_SOURCE = "HUMAN_UI";
  let sequence = 0;

  function tauriInvoke() {
    return window.__TAURI__?.core?.invoke ?? null;
  }

  function nextCorrelation(command) {
    sequence += 1;
    return `works-ui:${Date.now()}:${sequence}:${command}`;
  }

  async function refreshSnapshot() {
    const invoke = tauriInvoke();
    if (!invoke || !window.VertexFlowRackUI) return false;

    const snapshot = await invoke("flow_rack_snapshot");
    window.VertexFlowRackUI.render(snapshot);
    return true;
  }

  async function executeIntent(detail) {
    const invoke = tauriInvoke();
    if (!invoke) {
      throw new Error("Tauri invoke unavailable for Flow Rack live bridge");
    }

    const intent = {
      source: detail?.source === "HUMAN_UI" ? LIVE_SOURCE : LIVE_SOURCE,
      command: String(detail?.command ?? ""),
      payload: detail?.payload ?? {},
      correlation_id: nextCorrelation(detail?.command ?? "unknown"),
      reason: "Vertex Works Flow Rack human UI",
    };

    return invoke("flow_rack_execute", { intent });
  }

  async function onCommand(event) {
    const detail = event?.detail ?? {};
    if (detail.capability !== "flow.queue") return;

    try {
      const result = await executeIntent(detail);
      if (result?.snapshot && window.VertexFlowRackUI) {
        window.VertexFlowRackUI.render(result.snapshot);
      } else {
        await refreshSnapshot();
      }

      window.dispatchEvent(
        new CustomEvent("vertex-flow-rack-command-result", {
          detail: {
            ok: true,
            command: detail.command,
            result,
          },
        }),
      );
    } catch (error) {
      window.dispatchEvent(
        new CustomEvent("vertex-flow-rack-command-result", {
          detail: {
            ok: false,
            command: detail.command,
            error: String(error),
          },
        }),
      );
      console.error("[VERTEX FLOW RACK LIVE]", error);
    }
  }

  async function boot() {
    window.addEventListener(COMMAND_EVENT, onCommand);
    try {
      await refreshSnapshot();
    } catch (error) {
      console.warn("[VERTEX FLOW RACK LIVE] initial snapshot unavailable", error);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }

  window.VertexFlowRackLiveBridge = Object.freeze({
    refreshSnapshot,
  });
})();
