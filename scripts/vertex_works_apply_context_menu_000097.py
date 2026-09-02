from pathlib import Path
import shutil
import time

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
APP = ROOT / "ui" / "app.js"
BACKUP_ROOT = ROOT / "MIGRATION_BACKUPS" / "VERTEX_CONTEXT_MENU_000097"

MARKER = "VERTEX_WORKS_CONTEXT_MENU_000097_BEGIN"

def fail(message):
    print(f"VERTEX_CONTEXT_MENU_000097_FAIL={message}")
    raise SystemExit(1)

if not APP.exists():
    fail(f"APP_JS_MISSING:{APP}")

app = APP.read_text(encoding="utf-8")

if MARKER in app:
    print("ALREADY_APPLIED=TRUE")
    raise SystemExit(0)

# We rely only on helpers/contracts already observed in Works source:
# $(), selectArtifact(), selectedInspect, selectedPath, navigator.clipboard.
required = [
    "function selectArtifact(",
    "selectedInspect",
    "selectedPath",
    'document.querySelectorAll(".artifact")',
]
for token in required:
    if token not in app:
        fail(f"REQUIRED_SOURCE_TOKEN_MISSING:{token}")

block = r'''

// VERTEX_WORKS_CONTEXT_MENU_000097_BEGIN
// Vertex products do not expose the host/WebView default context menu.
// Left = ACT, Right = CONTEXT, Middle = RELAY.
(() => {
  const VERTEX_PRODUCT_SITE = "https://vertex.a-portal.net/";
  const MENU_ID = "vertexContextMenu000097";
  const TOAST_ID = "vertexContextToast000097";

  function ensureVertexContextStyle() {
    if (document.getElementById("vertexContextStyle000097")) return;
    const style = document.createElement("style");
    style.id = "vertexContextStyle000097";
    style.textContent = `
      #${MENU_ID}{
        position:fixed; z-index:2147483600; min-width:250px;
        background:rgba(7,11,15,.985);
        border:1px solid rgba(255,132,24,.55);
        box-shadow:0 18px 42px rgba(0,0,0,.55),0 0 18px rgba(255,112,0,.10);
        border-radius:9px; padding:7px;
        font-family:inherit; color:#dfe7ee; user-select:none;
        backdrop-filter:blur(14px);
      }
      #${MENU_ID}.hidden{display:none}
      #${MENU_ID} .vcm-head{
        padding:7px 9px 8px; color:#f07b1c; font-size:11px;
        letter-spacing:.14em; text-transform:uppercase;
        border-bottom:1px solid rgba(255,132,24,.18); margin-bottom:5px;
      }
      #${MENU_ID} .vcm-sub{
        display:block; margin-top:4px; color:#87929d; letter-spacing:.03em;
        font-size:10px; text-transform:none; max-width:310px;
        overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
      }
      #${MENU_ID} button{
        width:100%; display:flex; align-items:center; justify-content:space-between;
        gap:18px; border:0; background:transparent; color:#dce4eb;
        padding:8px 10px; border-radius:6px; text-align:left; cursor:pointer;
        font:inherit; font-size:12px;
      }
      #${MENU_ID} button:hover{
        background:rgba(255,126,24,.12); color:#ff9a43;
        box-shadow:inset 2px 0 0 #f07b1c;
      }
      #${MENU_ID} .vcm-danger{color:#d88f79}
      #${MENU_ID} .vcm-sep{
        height:1px; background:rgba(255,255,255,.07); margin:5px 4px;
      }
      #${TOAST_ID}{
        position:fixed; right:22px; bottom:22px; z-index:2147483601;
        max-width:430px; padding:11px 14px; border-radius:8px;
        background:rgba(7,11,15,.97); border:1px solid rgba(255,132,24,.45);
        color:#dce4eb; box-shadow:0 12px 34px rgba(0,0,0,.48);
        font-family:inherit; font-size:12px; white-space:pre-wrap;
      }
      #${TOAST_ID}.hidden{display:none}
    `;
    document.head.appendChild(style);
  }

  function ensureVertexContextNodes() {
    ensureVertexContextStyle();
    let menu = document.getElementById(MENU_ID);
    if (!menu) {
      menu = document.createElement("div");
      menu.id = MENU_ID;
      menu.className = "hidden";
      document.body.appendChild(menu);
    }
    let toast = document.getElementById(TOAST_ID);
    if (!toast) {
      toast = document.createElement("div");
      toast.id = TOAST_ID;
      toast.className = "hidden";
      document.body.appendChild(toast);
    }
    return { menu, toast };
  }

  function vertexToast(text) {
    const { toast } = ensureVertexContextNodes();
    toast.textContent = text;
    toast.classList.remove("hidden");
    clearTimeout(vertexToast._timer);
    vertexToast._timer = setTimeout(() => toast.classList.add("hidden"), 2600);
  }

  async function vertexCopy(text) {
    const value = String(text || "");
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      vertexToast("VERTEX CONTEXT\nCopied to clipboard");
    } catch (_) {
      const area = document.createElement("textarea");
      area.value = value;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
      vertexToast("VERTEX CONTEXT\nCopied to clipboard");
    }
  }

  async function vertexClipIn(text, kind="CONTEXT") {
    const value = String(text || "");
    if (!value) return;
    try {
      const relay = await invoke("clip_relay_set_priority", { text:value, kind });
      vertexToast(`VERTEX CLIP RELAY\n${kind} armed / ${relay.bytes} bytes`);
    } catch (e) {
      await vertexCopy(value);
      vertexToast(`VERTEX CLIP RELAY unavailable\nFallback clipboard copy`);
    }
  }

  function closeVertexContextMenu() {
    document.getElementById(MENU_ID)?.classList.add("hidden");
  }

  function menuItem(label, action, tail="", danger=false) {
    const button = document.createElement("button");
    if (danger) button.classList.add("vcm-danger");
    const left = document.createElement("span");
    left.textContent = label;
    const right = document.createElement("span");
    right.textContent = tail;
    right.style.opacity = ".45";
    right.style.fontSize = "10px";
    button.append(left, right);
    button.onclick = async () => {
      closeVertexContextMenu();
      await action();
    };
    return button;
  }

  function separator() {
    const div = document.createElement("div");
    div.className = "vcm-sep";
    return div;
  }

  function artifactNodeFromTarget(target) {
    return target?.closest?.(".artifact") || null;
  }

  function artifactContextText(node) {
    const title = node?.querySelector?.(".title")?.textContent?.trim()
      || node?.textContent?.trim()?.split("\n")?.[0]
      || "Incoming Cargo";
    const path = node?.dataset?.vertexPath || node?.dataset?.path || "";
    return { title, path };
  }

  function showProductProperties() {
    const version = receiverInfo?.version || "0.5.0";
    const inbox = receiverInfo?.inbox || "";
    const root = receiverInfo?.allowed_root || "";
    vertexToast(
      `VERTEX WORKS ${version}\n` +
      `Receiving Bay: ${inbox}\n` +
      `Production Root: ${root}`
    );
  }

  function openProductSite() {
    try {
      window.open(VERTEX_PRODUCT_SITE, "_blank", "noopener,noreferrer");
    } catch (_) {
      vertexCopy(VERTEX_PRODUCT_SITE);
      vertexToast("PRODUCT SITE URL copied");
    }
  }

  function showHelp() {
    vertexToast(
      "VERTEX WORKS — INPUT MAP\n" +
      "Left Click : ACT\n" +
      "Right Click: CONTEXT\n" +
      "Middle Click: CLIP RELAY"
    );
  }

  function openVertexContextMenu(event) {
    event.preventDefault();
    event.stopPropagation();

    const { menu } = ensureVertexContextNodes();
    menu.replaceChildren();

    const selection = String(window.getSelection?.()?.toString?.() || "").trim();
    const artifact = artifactNodeFromTarget(event.target);

    const head = document.createElement("div");
    head.className = "vcm-head";

    if (artifact) {
      const info = artifactContextText(artifact);
      head.textContent = "INCOMING CARGO";
      const sub = document.createElement("span");
      sub.className = "vcm-sub";
      sub.textContent = info.title;
      head.appendChild(sub);
      menu.appendChild(head);

      menu.appendChild(menuItem("INSPECT", async () => artifact.click(), "ACT"));
      if (info.path) {
        menu.appendChild(menuItem("CLIP IN PATH", async () => vertexClipIn(info.path, "ARTIFACT_PATH"), "RELAY"));
        menu.appendChild(menuItem("COPY PATH", async () => vertexCopy(info.path), "COPY"));
      }
      menu.appendChild(separator());
      menu.appendChild(menuItem("PROPERTIES", async () => {
        const text = `${info.title}${info.path ? "\n" + info.path : ""}`;
        vertexToast(text);
      }));
    } else if (selection) {
      head.textContent = "TEXT SELECTION";
      const sub = document.createElement("span");
      sub.className = "vcm-sub";
      sub.textContent = selection;
      head.appendChild(sub);
      menu.appendChild(head);
      menu.appendChild(menuItem("CLIP IN", async () => vertexClipIn(selection, "TEXT"), "RELAY"));
      menu.appendChild(menuItem("COPY", async () => vertexCopy(selection), "COPY"));
    } else {
      head.textContent = "VERTEX WORKS";
      const sub = document.createElement("span");
      sub.className = "vcm-sub";
      sub.textContent = "Product Context";
      head.appendChild(sub);
      menu.appendChild(head);
      menu.appendChild(menuItem("PRODUCT PROPERTIES", async () => showProductProperties()));
      menu.appendChild(menuItem("HELP / INPUT GUIDE", async () => showHelp()));
      menu.appendChild(separator());
      menu.appendChild(menuItem("VERTEX PRODUCT SITE", async () => openProductSite(), "WEB"));
    }

    document.body.appendChild(menu);
    menu.classList.remove("hidden");

    const pad = 10;
    const rect = menu.getBoundingClientRect();
    const x = Math.min(event.clientX, window.innerWidth - rect.width - pad);
    const y = Math.min(event.clientY, window.innerHeight - rect.height - pad);
    menu.style.left = `${Math.max(pad, x)}px`;
    menu.style.top = `${Math.max(pad, y)}px`;
  }

  // Suppress Chromium/WebView/Windows-style default context menus everywhere
  // inside Vertex Works and route all right-clicks into Vertex Context.
  document.addEventListener("contextmenu", openVertexContextMenu, true);
  document.addEventListener("pointerdown", (event) => {
    if (event.button !== 2 && !event.target.closest?.(`#${MENU_ID}`)) {
      closeVertexContextMenu();
    }
  }, true);
  window.addEventListener("blur", closeVertexContextMenu);
  window.addEventListener("resize", closeVertexContextMenu);
  document.addEventListener("scroll", closeVertexContextMenu, true);

  // Attach a stable path to current/future Incoming Cargo cards.
  const originalRenderIncoming = typeof renderIncoming === "function" ? renderIncoming : null;
  if (originalRenderIncoming) {
    renderIncoming = function(...args) {
      const result = originalRenderIncoming.apply(this, args);
      document.querySelectorAll(".artifact").forEach((node) => {
        if (node.dataset.vertexPath) return;
        const text = node.textContent || "";
        const match = incomingItems?.find?.((item) =>
          text.includes(item.artifact_id || "") || text.includes(artifactFileName(item.path))
        );
        if (match?.path) node.dataset.vertexPath = match.path;
      });
      return result;
    };
  }

  ensureVertexContextNodes();
})();
// VERTEX_WORKS_CONTEXT_MENU_000097_END
'''

stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_ROOT / stamp / "ui" / "app.js"
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(APP, backup)

with APP.open("w", encoding="utf-8", newline="\n") as f:
    f.write(app.rstrip() + "\n" + block + "\n")

print(f"BACKUP={backup}")
print("NATIVE_CONTEXT_MENU=BLOCKED")
print("VERTEX_CONTEXT_MENU=ENABLED")
print("BLANK_CONTEXT=PRODUCT_PROPERTIES_HELP_PRODUCT_SITE")
print("ARTIFACT_CONTEXT=INSPECT_CLIP_PATH_COPY_PATH_PROPERTIES")
print("TEXT_CONTEXT=CLIP_IN_COPY")
print("MOUSE_POLICY=LEFT_ACT_RIGHT_CONTEXT_MIDDLE_RELAY")
print("VERTEX_WORKS_CONTEXT_MENU_000097_SOURCE_PATCH=PASS")
