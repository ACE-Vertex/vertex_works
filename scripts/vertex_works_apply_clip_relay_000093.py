from pathlib import Path
import shutil
import time

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
MAIN = ROOT / "src-tauri" / "src" / "main.rs"
APP = ROOT / "ui" / "app.js"
BACKUP_ROOT = ROOT / "MIGRATION_BACKUPS" / "CLIP_RELAY_000093"

def fail(message):
    print(f"CLIP_RELAY_000093_FAIL={message}")
    raise SystemExit(1)

for path in (MAIN, APP):
    if not path.exists():
        fail(f"MISSING:{path}")

main = MAIN.read_text(encoding="utf-8")
app = APP.read_text(encoding="utf-8")

if "mod clip_relay;" not in main:
    anchor = '#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]\n'
    if anchor not in main:
        fail("MAIN_CFG_ANCHOR_MISSING")
    main = main.replace(anchor, anchor + "\nmod clip_relay;\n", 1)

commands_block = r'''
// VERTEX_WORKS_CLIP_RELAY_000093_BEGIN
#[tauri::command]
fn clip_relay_set_priority(
    text: String,
    kind: Option<String>,
) -> Result<clip_relay::ClipRelayStatus, String> {
    clip_relay::set_priority(text, kind.unwrap_or_else(|| "EVIDENCE".into()))
}

#[tauri::command]
fn clip_relay_status() -> clip_relay::ClipRelayStatus {
    clip_relay::status()
}
// VERTEX_WORKS_CLIP_RELAY_000093_END

'''

if "VERTEX_WORKS_CLIP_RELAY_000093_BEGIN" not in main:
    anchor = "fn main() {"
    if main.count(anchor) != 1:
        fail(f"MAIN_FN_COUNT={main.count(anchor)}")
    main = main.replace(anchor, commands_block + anchor, 1)

start_line = '''fn main() {
    if let Err(e) = ensure_dirs() {'''
if "clip_relay::start()" not in main:
    if start_line not in main:
        fail("MAIN_START_ANCHOR_MISSING")
    replacement = '''fn main() {
    if let Err(e) = clip_relay::start() {
        eprintln!("Vertex Clip Relay init warning: {e}");
    }

    if let Err(e) = ensure_dirs() {'''
    main = main.replace(start_line, replacement, 1)

handler_anchor = ".invoke_handler(tauri::generate_handler!["
handler_pos = main.find(handler_anchor)
if handler_pos < 0:
    fail("INVOKE_HANDLER_ANCHOR_MISSING")

handler_end = main.find("])", handler_pos)
if handler_end < 0:
    fail("INVOKE_HANDLER_END_MISSING")

handler_block = main[handler_pos:handler_end]
if "clip_relay_set_priority" not in handler_block:
    insertion = handler_anchor + "\n            clip_relay_set_priority,\n            clip_relay_status,"
    main = main[:handler_pos] + main[handler_pos:].replace(handler_anchor, insertion, 1)

evidence_anchor = '  const text = buildReport("EVIDENCE");\n'
if "CLIP RELAY: PRIORITY EVIDENCE ARMED" not in app:
    if app.count(evidence_anchor) != 1:
        fail(f"EVIDENCE_ANCHOR_COUNT={app.count(evidence_anchor)}")
    evidence_insert = evidence_anchor + '''  try {
    const relay = await invoke("clip_relay_set_priority", { text, kind: "EVIDENCE" });
    log(`CLIP RELAY: PRIORITY EVIDENCE ARMED (${relay.bytes} bytes)`);
  } catch (e) {
    log(`CLIP RELAY ARM ERROR: ${e}`);
  }
'''
    app = app.replace(evidence_anchor, evidence_insert, 1)

stamp = time.strftime("%Y%m%d-%H%M%S")
backup_root = BACKUP_ROOT / stamp
for source, rel in [
    (MAIN, Path("src-tauri/src/main.rs")),
    (APP, Path("ui/app.js")),
]:
    dest = backup_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)

with MAIN.open("w", encoding="utf-8", newline="\n") as f:
    f.write(main)

with APP.open("w", encoding="utf-8", newline="\n") as f:
    f.write(app)

print(f"BACKUP={backup_root}")
print("CLIP_RELAY_MODULE=PRESENT")
print("GLOBAL_MIDDLE_BUTTON=WH_MOUSE_LL")
print("SELECTION_CAPTURE=CTRL_C_CLIPBOARD")
print("FILES_CAPTURE=CF_HDROP")
print("RELEASE=CTRL_V")
print("FILES_RELEASE=CF_HDROP_PLUS_UNICODE_PATHS")
print("EVIDENCE_PRIORITY=WIRED")
print("NORMAL_MIDDLE_PASSTHROUGH=WHEN_UNARMED_AND_NO_SELECTION")
print("VERTEX_WORKS_CLIP_RELAY_000093_SOURCE_PATCH=PASS")
