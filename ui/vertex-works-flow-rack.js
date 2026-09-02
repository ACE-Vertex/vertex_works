/* VERTEX WORKS FLOW RACK UI — 000013
 * Visual weld only.
 * Authoritative queue state remains outside the UI.
 * Human gestures emit typed command intents; this file does not mutate the domain queue.
 */
(() => {
  "use strict";

  const ROOT_ID = "vertex-flow-rack";
  const COMMAND_EVENT = "vertex-flow-rack-command";
  const CONTEXT_EVENT = "vertex-flow-rack-context";
  const READY_EVENT = "vertex-flow-rack-ready";

  const ui = {
    mounted: false,
    root: null,
    snapshot: {
      source: "UNBOUND",
      running: [],
      queue: [],
      held: [],
      updated_at: null,
    },
    dragJobId: null,
  };

  function asArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function normalizeJob(job) {
    if (!job || typeof job !== "object") {
      return null;
    }

    return {
      id: String(job.id ?? ""),
      title: String(job.title ?? job.id ?? "UNTITLED"),
      state: String(job.state ?? "Queued"),
      actor_id: job.actor_id ? String(job.actor_id) : null,
      wait_reason: job.wait_reason ? String(job.wait_reason) : null,
      correlation_id: job.correlation_id ? String(job.correlation_id) : null,
      lock_mode: job.lock_mode ? String(job.lock_mode) : null,
      lock_scope: job.lock_scope ? String(job.lock_scope) : null,
    };
  }

  function normalizeSnapshot(snapshot) {
    const input = snapshot && typeof snapshot === "object" ? snapshot : {};
    return {
      source: String(input.source ?? "UNBOUND"),
      running: asArray(input.running).map(normalizeJob).filter(Boolean),
      queue: asArray(input.queue).map(normalizeJob).filter(Boolean),
      held: asArray(input.held).map(normalizeJob).filter(Boolean),
      updated_at: input.updated_at ? String(input.updated_at) : null,
    };
  }

  function dispatchCommand(command, payload = {}) {
    window.dispatchEvent(
      new CustomEvent(COMMAND_EVENT, {
        detail: {
          capability: "flow.queue",
          command,
          payload,
          source: "HUMAN_UI",
        },
      }),
    );
  }

  function dispatchContext(job, x, y) {
    window.dispatchEvent(
      new CustomEvent(CONTEXT_EVENT, {
        detail: {
          capability: "flow.queue",
          job,
          x,
          y,
          actions:
            job.state === "Held"
              ? ["queue.resume", "queue.cancel", "queue.drop", "job.inspect"]
              : ["queue.hold", "queue.cancel", "queue.drop", "job.inspect"],
        },
      }),
    );
  }

  function textElement(tag, className, text) {
    const element = document.createElement(tag);
    element.className = className;
    element.textContent = text;
    return element;
  }

  function makeMeta(label, value) {
    const span = document.createElement("span");
    span.className = "vfr-meta";
    span.append(textElement("b", "vfr-meta-key", label));
    span.append(document.createTextNode(value));
    return span;
  }

  function makeCard(job, lane) {
    const card = document.createElement("article");
    card.className = `vfr-strip vfr-strip-${lane}`;
    card.dataset.jobId = job.id;
    card.dataset.jobState = job.state;

    const reorderable = job.state === "Queued" || job.state === "Held";
    card.draggable = reorderable;
    card.setAttribute("aria-label", `${job.title} ${job.state}`);

    const rail = document.createElement("div");
    rail.className = "vfr-strip-rail";
    rail.textContent = lane === "running" ? "NOW" : lane === "held" ? "HOLD" : "NEXT";

    const body = document.createElement("div");
    body.className = "vfr-strip-body";

    const heading = document.createElement("div");
    heading.className = "vfr-strip-heading";
    heading.append(textElement("strong", "vfr-strip-title", job.title));
    heading.append(textElement("span", "vfr-state", job.state.toUpperCase()));

    const meta = document.createElement("div");
    meta.className = "vfr-strip-meta";
    if (job.actor_id) meta.append(makeMeta("ACTOR", job.actor_id));
    if (job.wait_reason) meta.append(makeMeta("WAIT", job.wait_reason));
    if (job.lock_mode) meta.append(makeMeta("LOCK", job.lock_mode));
    if (job.lock_scope) meta.append(makeMeta("SCOPE", job.lock_scope));

    body.append(heading, meta);

    if (job.correlation_id) {
      body.append(textElement("div", "vfr-correlation", job.correlation_id));
    }

    card.append(rail, body);

    card.addEventListener("contextmenu", (event) => {
      event.preventDefault();
      event.stopPropagation();
      dispatchContext(job, event.clientX, event.clientY);
    });

    if (reorderable) {
      card.addEventListener("dragstart", (event) => {
        ui.dragJobId = job.id;
        card.classList.add("vfr-dragging");
        if (event.dataTransfer) {
          event.dataTransfer.effectAllowed = "move";
          event.dataTransfer.setData("text/plain", job.id);
        }
      });

      card.addEventListener("dragend", () => {
        ui.dragJobId = null;
        card.classList.remove("vfr-dragging");
        document
          .querySelectorAll(".vfr-drop-target")
          .forEach((element) => element.classList.remove("vfr-drop-target"));
      });
    }

    return card;
  }

  function emptyStrip(text) {
    const strip = document.createElement("div");
    strip.className = "vfr-empty-strip";
    strip.textContent = text;
    return strip;
  }

  function renderLane(container, jobs, lane, emptyText) {
    container.replaceChildren();

    if (!jobs.length) {
      container.append(emptyStrip(emptyText));
      return;
    }

    jobs.forEach((job) => {
      container.append(makeCard(job, lane));
    });
  }

  function renderQueue(container, jobs) {
    container.replaceChildren();

    if (!jobs.length) {
      container.append(emptyStrip("AWAITING LIVE FLOW BRIDGE"));
      return;
    }

    jobs.forEach((job, index) => {
      const slot = document.createElement("div");
      slot.className = "vfr-queue-slot";
      slot.dataset.queueIndex = String(index);

      slot.addEventListener("dragover", (event) => {
        if (!ui.dragJobId) return;
        event.preventDefault();
        slot.classList.add("vfr-drop-target");
        if (event.dataTransfer) {
          event.dataTransfer.dropEffect = "move";
        }
      });

      slot.addEventListener("dragleave", () => {
        slot.classList.remove("vfr-drop-target");
      });

      slot.addEventListener("drop", (event) => {
        if (!ui.dragJobId) return;
        event.preventDefault();
        slot.classList.remove("vfr-drop-target");
        dispatchCommand("queue.move", {
          job_id: ui.dragJobId,
          to_index: index,
        });
      });

      slot.append(makeCard(job, "queue"));
      container.append(slot);
    });
  }

  function updateHeader() {
    if (!ui.root) return;
    const source = ui.root.querySelector("[data-vfr-source]");
    const count = ui.root.querySelector("[data-vfr-count]");
    const time = ui.root.querySelector("[data-vfr-time]");

    source.textContent = ui.snapshot.source;
    count.textContent = `${ui.snapshot.running.length} RUN / ${ui.snapshot.queue.length} NEXT / ${ui.snapshot.held.length} HOLD`;
    time.textContent = ui.snapshot.updated_at ?? "NO LIVE CLOCK";
  }

  function render(snapshot) {
    ui.snapshot = normalizeSnapshot(snapshot);
    if (!ui.mounted) mount();
    if (!ui.root) return;

    updateHeader();
    renderLane(
      ui.root.querySelector("[data-vfr-running]"),
      ui.snapshot.running,
      "running",
      "NO ACTIVE JOB",
    );
    renderQueue(ui.root.querySelector("[data-vfr-queue]"), ui.snapshot.queue);
    renderLane(
      ui.root.querySelector("[data-vfr-held]"),
      ui.snapshot.held,
      "held",
      "HOLD BAY CLEAR",
    );
  }

  function findIncomingCargoAnchor() {
    const selectors = [
      '[data-vertex-zone="incoming-cargo"]',
      '[data-section="incoming-cargo"]',
      "#incomingCargo",
      "#incoming-cargo",
      ".incoming-cargo",
      ".incoming-cargo-panel",
    ];

    for (const selector of selectors) {
      const hit = document.querySelector(selector);
      if (hit) return hit;
    }

    const candidates = Array.from(
      document.querySelectorAll(
        "h1,h2,h3,h4,.panel-title,.section-title,.factory-title,.card-title",
      ),
    );

    const label = candidates.find((element) =>
      element.textContent?.trim().toUpperCase().includes("INCOMING CARGO"),
    );

    if (!label) return null;

    return (
      label.closest("section,.panel,.factory-panel,.factory-card,.bay,.workspace-card") ??
      label.parentElement
    );
  }

  function createRoot() {
    const root = document.createElement("section");
    root.id = ROOT_ID;
    root.className = "vertex-flow-rack";
    root.setAttribute("aria-label", "Vertex Flow Rack");

    root.innerHTML = `
      <header class="vfr-header">
        <div class="vfr-identity">
          <span class="vfr-kicker">VERTEX FLOW RACK</span>
          <strong>WORK EXECUTION STRIPS</strong>
        </div>
        <div class="vfr-status">
          <span data-vfr-source>UNBOUND</span>
          <span data-vfr-count>0 RUN / 0 NEXT / 0 HOLD</span>
          <span data-vfr-time>NO LIVE CLOCK</span>
        </div>
      </header>

      <div class="vfr-lane vfr-lane-running">
        <div class="vfr-lane-head">
          <span>NOW / RUNNING</span>
          <small>PROCESS ENTRY — REORDER LOCKED</small>
        </div>
        <div class="vfr-lane-body" data-vfr-running></div>
      </div>

      <div class="vfr-lane vfr-lane-next">
        <div class="vfr-lane-head">
          <span>NEXT / PRIORITY RACK</span>
          <small>POSITION = EXECUTION PRIORITY · DRAG = FLOW CONTROL</small>
        </div>
        <div class="vfr-lane-body vfr-queue" data-vfr-queue></div>
      </div>

      <div class="vfr-lane vfr-lane-hold">
        <div class="vfr-lane-head">
          <span>HOLD BAY</span>
          <small>DEFERRED — RECORD PRESERVED</small>
        </div>
        <div class="vfr-lane-body" data-vfr-held></div>
      </div>

      <footer class="vfr-footer">
        <span>LEFT = ACT</span>
        <span>RIGHT = CONTEXT</span>
        <span>MIDDLE = RELAY</span>
        <span>DRAG = FLOW CONTROL</span>
        <b>LIVE BRIDGE: PENDING</b>
      </footer>
    `;

    return root;
  }

  function mount() {
    if (ui.mounted) return ui.root;

    const existing = document.getElementById(ROOT_ID);
    if (existing) {
      ui.root = existing;
      ui.mounted = true;
      return existing;
    }

    const root = createRoot();
    const anchor = findIncomingCargoAnchor();

    if (anchor?.parentNode) {
      anchor.insertAdjacentElement("afterend", root);
      root.dataset.mount = "incoming-cargo-adjacent";
    } else {
      const fallback =
        document.querySelector("main,.main,.workspace,.factory-shell,.app-shell") ??
        document.body;
      fallback.append(root);
      root.dataset.mount = "fallback-shell";
    }

    ui.root = root;
    ui.mounted = true;
    render(ui.snapshot);

    window.dispatchEvent(
      new CustomEvent(READY_EVENT, {
        detail: {
          root_id: ROOT_ID,
          authoritative_state: false,
          command_event: COMMAND_EVENT,
        },
      }),
    );

    return root;
  }

  window.VertexFlowRackUI = Object.freeze({
    mount,
    render,
    commandEvent: COMMAND_EVENT,
    contextEvent: CONTEXT_EVENT,
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount, { once: true });
  } else {
    mount();
  }
})();
