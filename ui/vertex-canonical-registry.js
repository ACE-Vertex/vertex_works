(() => {
  const state = {
    cards: [],
    selected: null,
    language: "vertex-ja",
    pack: null,
  };

  const now = () => new Date().toISOString();
  const byId = (id) => document.getElementById(id);

  function tauriInvoke() {
    return window.__TAURI__?.core?.invoke || null;
  }

  async function invoke(command, args = {}) {
    const fn = tauriInvoke();
    if (!fn) throw new Error("TAURI invoke unavailable");
    return fn(command, args);
  }

  function slug(text) {
    return String(text || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9\u3040-\u30ff\u3400-\u9fff]+/g, "-")
      .replace(/^-+|-+$/g, "") || `concept-${Date.now()}`;
  }

  function text(id) {
    return byId(id)?.value?.trim() || "";
  }

  function listValue(id) {
    return text(id).split(",").map((v) => v.trim()).filter(Boolean);
  }

  function statusLabel(value) {
    return state.pack?.status?.[value] || value;
  }

  function importanceLabel(value) {
    return state.pack?.importance?.[value] || value;
  }

  function uiLabel(key, fallback) {
    return state.pack?.ui?.[key] || fallback;
  }

  function renderShell() {
    if (byId("vcr-shell")) return;

    const launch = document.createElement("button");
    launch.id = "vcr-launcher";
    launch.textContent = "VCR";
    launch.title = "Vertex Canonical Registry";
    document.body.appendChild(launch);

    const shell = document.createElement("section");
    shell.id = "vcr-shell";
    shell.dataset.open = "false";
    shell.innerHTML = `
      <div class="vcr-panel">
        <header class="vcr-head">
          <div class="vcr-title" id="vcr-title">CANONICAL REGISTRY</div>
          <input class="vcr-search" id="vcr-search" placeholder="Search..." />
          <select class="vcr-select" id="vcr-language">
            <option value="vertex-ja">Vertex 日本語</option>
            <option value="ja-JP">日本語</option>
            <option value="en-US">English</option>
          </select>
          <button class="vcr-btn" id="vcr-new">NEW CONCEPT</button>
          <button class="vcr-btn" id="vcr-close">CLOSE</button>
        </header>
        <div class="vcr-body">
          <div class="vcr-list" id="vcr-list"></div>
          <div class="vcr-editor">
            <div class="vcr-grid">
              <label class="vcr-field">
                <span class="vcr-label">FORMAL NAME</span>
                <input class="vcr-input" id="vcr-formal-name" />
              </label>
              <label class="vcr-field">
                <span class="vcr-label">ABBREVIATION</span>
                <input class="vcr-input" id="vcr-abbreviation" />
              </label>
            </div>
            <div class="vcr-grid">
              <label class="vcr-field">
                <span class="vcr-label">STATUS</span>
                <select class="vcr-select" id="vcr-status">
                  <option>IDEA</option>
                  <option>CANDIDATE</option>
                  <option>ADOPTED</option>
                  <option>DEPRECATED</option>
                </select>
              </label>
              <label class="vcr-field">
                <span class="vcr-label">IMPORTANCE</span>
                <select class="vcr-select" id="vcr-importance">
                  <option>NORMAL</option>
                  <option>IMPORTANT</option>
                  <option>CRITICAL</option>
                </select>
              </label>
            </div>
            <div class="vcr-grid">
              <label class="vcr-field">
                <span class="vcr-label">SCOPE</span>
                <input class="vcr-input" id="vcr-scope" />
              </label>
              <label class="vcr-field">
                <span class="vcr-label">CATEGORY</span>
                <input class="vcr-input" id="vcr-category" />
              </label>
            </div>
            <label class="vcr-field">
              <span class="vcr-label">SUMMARY</span>
              <textarea class="vcr-textarea" id="vcr-summary"></textarea>
            </label>
            <label class="vcr-field">
              <span class="vcr-label">FUNCTION</span>
              <textarea class="vcr-textarea" id="vcr-function"></textarea>
            </label>
            <label class="vcr-field">
              <span class="vcr-label">DESCRIPTION</span>
              <textarea class="vcr-textarea" id="vcr-description"></textarea>
            </label>
            <label class="vcr-field">
              <span class="vcr-label">ORIGIN</span>
              <textarea class="vcr-textarea" id="vcr-origin"></textarea>
            </label>
            <div class="vcr-grid">
              <label class="vcr-field">
                <span class="vcr-label">ALIASES (comma separated)</span>
                <input class="vcr-input" id="vcr-aliases" />
              </label>
              <label class="vcr-field">
                <span class="vcr-label">RELATED (comma separated)</span>
                <input class="vcr-input" id="vcr-related" />
              </label>
            </div>
            <div class="vcr-grid">
              <label class="vcr-field">
                <span class="vcr-label">FLAVOR BADGE</span>
                <input class="vcr-input" id="vcr-flavor" placeholder="超絶採用‼️" />
              </label>
              <label class="vcr-field">
                <span class="vcr-label">ADOPTED BY</span>
                <input class="vcr-input" id="vcr-adopted-by" value="Human + Vera" />
              </label>
            </div>
            <label class="vcr-field">
              <span class="vcr-label">NOTES</span>
              <textarea class="vcr-textarea" id="vcr-notes"></textarea>
            </label>
            <div class="vcr-editor-actions">
              <button class="vcr-btn vcr-btn-danger" id="vcr-delete">DELETE</button>
              <button class="vcr-btn" id="vcr-save">SAVE</button>
            </div>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(shell);

    launch.addEventListener("click", open);
    byId("vcr-close").addEventListener("click", close);
    byId("vcr-new").addEventListener("click", newCard);
    byId("vcr-save").addEventListener("click", save);
    byId("vcr-delete").addEventListener("click", remove);
    byId("vcr-search").addEventListener("input", renderCards);
    byId("vcr-language").addEventListener("change", async (event) => {
      state.language = event.target.value;
      await loadLanguage();
      renderCards();
      updateLabels();
    });

    shell.addEventListener("click", (event) => {
      if (event.target === shell) close();
    });

    window.addEventListener("keydown", (event) => {
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "k") {
        event.preventDefault();
        open();
      }
      if (event.key === "Escape" && shell.dataset.open === "true") close();
    });
  }

  async function loadLanguage() {
    try {
      state.pack = await invoke("canonical_registry_language_pack", { language: state.language });
    } catch (error) {
      console.warn("[VCR] language pack unavailable", error);
      state.pack = null;
    }
  }

  function updateLabels() {
    byId("vcr-title").textContent = uiLabel("registry", "CANONICAL REGISTRY");
    byId("vcr-new").textContent = uiLabel("new_card", "NEW CARD");
    byId("vcr-save").textContent = uiLabel("save", "SAVE");
    byId("vcr-delete").textContent = uiLabel("delete", "DELETE");
    byId("vcr-search").placeholder = uiLabel("search", "Search...");
  }

  async function refresh() {
    const snapshot = await invoke("canonical_registry_list");
    state.cards = snapshot.cards || [];
    renderCards();
  }

  function normalizedSearch(card) {
    return [
      card.formal_name,
      card.abbreviation,
      ...(card.aliases || []),
      card.summary,
      card.function,
      card.description,
      card.origin,
      ...(card.related || []),
      card.flavor_badge,
      card.notes,
    ].join(" ").toLowerCase();
  }

  function renderCards() {
    const list = byId("vcr-list");
    if (!list) return;

    const query = text("vcr-search").toLowerCase();
    const cards = state.cards.filter((card) => !query || normalizedSearch(card).includes(query));

    if (!cards.length) {
      list.innerHTML = `<div class="vcr-empty">${uiLabel("empty", "No cards.")}</div>`;
      return;
    }

    list.innerHTML = "";
    cards.forEach((card) => {
      const el = document.createElement("button");
      el.className = "vcr-card";
      el.dataset.selected = String(state.selected?.card_id === card.card_id);
      el.innerHTML = `
        <div class="vcr-card-top">
          <div class="vcr-card-name">${escapeHtml(card.formal_name)}</div>
          <div class="vcr-card-abbr">${escapeHtml(card.abbreviation || "")}</div>
        </div>
        <div class="vcr-card-summary">${escapeHtml(card.summary || card.function || "")}</div>
        <div class="vcr-badges">
          <span class="vcr-badge">${escapeHtml(statusLabel(card.status))}</span>
          <span class="vcr-badge">${escapeHtml(importanceLabel(card.importance || "NORMAL"))}</span>
          ${card.flavor_badge ? `<span class="vcr-badge vcr-badge-flavor">${escapeHtml(card.flavor_badge)}</span>` : ""}
        </div>
      `;
      el.addEventListener("click", () => selectCard(card));
      list.appendChild(el);
    });
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function setValue(id, value) {
    const el = byId(id);
    if (el) el.value = value ?? "";
  }

  function selectCard(card) {
    state.selected = card;
    setValue("vcr-formal-name", card.formal_name);
    setValue("vcr-abbreviation", card.abbreviation);
    setValue("vcr-status", card.status);
    setValue("vcr-importance", card.importance || "NORMAL");
    setValue("vcr-scope", card.scope);
    setValue("vcr-category", card.category);
    setValue("vcr-summary", card.summary);
    setValue("vcr-function", card.function);
    setValue("vcr-description", card.description);
    setValue("vcr-origin", card.origin);
    setValue("vcr-aliases", (card.aliases || []).join(", "));
    setValue("vcr-related", (card.related || []).join(", "));
    setValue("vcr-flavor", card.flavor_badge);
    setValue("vcr-adopted-by", card.adopted_by);
    setValue("vcr-notes", card.notes);
    renderCards();
  }

  function newCard(seed = {}) {
    state.selected = null;
    setValue("vcr-formal-name", seed.formal_name || "");
    setValue("vcr-abbreviation", seed.abbreviation || "");
    setValue("vcr-status", seed.status || "CANDIDATE");
    setValue("vcr-importance", seed.importance || "NORMAL");
    setValue("vcr-scope", seed.scope || "VERTEX");
    setValue("vcr-category", seed.category || "CONCEPT");
    setValue("vcr-summary", seed.summary || "");
    setValue("vcr-function", seed.function || "");
    setValue("vcr-description", seed.description || "");
    setValue("vcr-origin", seed.origin || "");
    setValue("vcr-aliases", seed.aliases || "");
    setValue("vcr-related", seed.related || "");
    setValue("vcr-flavor", seed.flavor_badge || "超採用！");
    setValue("vcr-adopted-by", seed.adopted_by || "Human + Vera");
    setValue("vcr-notes", seed.notes || "");
    renderCards();
  }

  async function save() {
    const formalName = text("vcr-formal-name");
    if (!formalName) return;

    const existing = state.selected;
    const card = {
      card_id: existing?.card_id || slug(formalName),
      formal_name: formalName,
      abbreviation: text("vcr-abbreviation"),
      aliases: listValue("vcr-aliases"),
      summary: text("vcr-summary"),
      function: text("vcr-function"),
      description: text("vcr-description"),
      status: byId("vcr-status").value,
      importance: byId("vcr-importance").value,
      scope: text("vcr-scope"),
      category: text("vcr-category"),
      origin: text("vcr-origin"),
      related: listValue("vcr-related"),
      supersedes: existing?.supersedes || [],
      replaced_by: existing?.replaced_by || [],
      flavor_badge: text("vcr-flavor"),
      notes: text("vcr-notes"),
      adopted_by: text("vcr-adopted-by"),
      created_at: existing?.created_at || now(),
      updated_at: now(),
    };

    const snapshot = await invoke("canonical_registry_upsert", { card });
    state.cards = snapshot.cards || [];
    state.selected = state.cards.find((item) => item.card_id === card.card_id) || card;
    renderCards();
    selectCard(state.selected);

    window.dispatchEvent(new CustomEvent("vertex-canonical-card-saved", { detail: state.selected }));
  }

  async function remove() {
    if (!state.selected) return;
    const snapshot = await invoke("canonical_registry_delete", { cardId: state.selected.card_id });
    state.cards = snapshot.cards || [];
    state.selected = null;
    newCard();
    renderCards();
  }

  async function open(seed = null) {
    renderShell();
    byId("vcr-shell").dataset.open = "true";
    await loadLanguage();
    updateLabels();
    await refresh();
    if (seed) newCard(seed);
    else if (state.selected) selectCard(state.selected);
  }

  function close() {
    const shell = byId("vcr-shell");
    if (shell) shell.dataset.open = "false";
  }

  window.VertexCanonicalRegistry = {
    open,
    close,
    refresh,
    capture(textValue, extra = {}) {
      return open({
        formal_name: extra.formal_name || "",
        abbreviation: extra.abbreviation || "",
        summary: extra.summary || "",
        function: extra.function || "",
        description: extra.description || String(textValue || ""),
        origin: extra.origin || "Captured from Vertex Works",
        status: extra.status || "CANDIDATE",
        importance: extra.importance || "NORMAL",
        scope: extra.scope || "VERTEX",
        category: extra.category || "CONCEPT",
        flavor_badge: extra.flavor_badge || "採用候補！",
        notes: extra.notes || "",
      });
    },
  };

  document.addEventListener("DOMContentLoaded", () => {
    renderShell();
    loadLanguage().then(updateLabels);
  });
})();
