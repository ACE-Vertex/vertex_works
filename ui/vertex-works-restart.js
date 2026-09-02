(() => {
  "use strict";

  const VERSION = "000082";
  const ARM_MS = 2400;
  let armedUntil = 0;
  let timer = null;
  let restarting = false;

  const $ = (s, root = document) => root.querySelector(s);

  function resolveInvoke() {
    return (
      window.__TAURI__?.core?.invoke ||
      window.__TAURI__?.tauri?.invoke ||
      window.__TAURI__?.invoke ||
      null
    );
  }

  function setState(state, text) {
    const button = $("#vwRestartButton");
    if (!button) return;
    button.dataset.state = state;
    const label = button.querySelector("b");
    if (label) label.textContent = text;
  }

  function disarm() {
    armedUntil = 0;
    clearTimeout(timer);
    timer = null;
    if (!restarting) setState("idle", "RESTART");
  }

  function arm() {
    armedUntil = Date.now() + ARM_MS;
    setState("armed", "CONFIRM");
    clearTimeout(timer);
    timer = setTimeout(disarm, ARM_MS);
  }

  async function restart() {
    const invoke = resolveInvoke();
    if (!invoke) {
      setState("error", "NO BRIDGE");
      setTimeout(disarm, 1400);
      return;
    }

    restarting = true;
    clearTimeout(timer);
    setState("restarting", "RESTARTING");

    try {
      window.VertexWorksFactoryKernel?.recordEvidence?.(
        "APP_RESTART_REQUEST",
        {
          version: VERSION,
          timestamp: new Date().toISOString(),
          facility: window.VertexWorksFactoryKernel?.currentFacility?.() || "UNKNOWN",
          method: "ROOT_LAUNCHER_NATIVE_RESTART",
        }
      );
    } catch (_) {}

    try {
      await invoke("restart_vertex_works");
    } catch (error) {
      restarting = false;
      console.error("VERTEX WORKS restart failed", error);
      setState("error", "FAILED");
      setTimeout(disarm, 1600);
    }
  }

  async function handleClick() {
    if (restarting) return;
    if (Date.now() <= armedUntil) {
      await restart();
      return;
    }
    arm();
  }

  function mount() {
    if ($("#vwRestartControl")) return;
    const control = document.createElement("section");
    control.id = "vwRestartControl";
    control.className = "vw-restart-control";
    control.innerHTML = `
      <button id="vwRestartButton"
              type="button"
              data-state="idle"
              aria-label="Restart Vertex Works"
              title="Restart Vertex Works through the root launcher">
        <span aria-hidden="true">↻</span>
        <b>RESTART</b>
      </button>
    `;
    document.body.appendChild(control);
    $("#vwRestartButton")?.addEventListener("click", handleClick);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount, { once: true });
  } else {
    mount();
  }

  window.VertexWorksRestart = Object.freeze({
    version: VERSION,
    arm,
    disarm,
    restart,
  });
})();