from pathlib import Path
import shutil
import time

ROOT = Path(r"G:\Vertex_Project\Development\vertex_works")
APP = ROOT / "ui" / "app.js"
BACKUP_ROOT = ROOT / "MIGRATION_BACKUPS" / "CLIP_RELAY_ERROR_PRIORITY_000095"

def fail(message):
    print(f"CLIP_RELAY_ERROR_PRIORITY_000095_FAIL={message}")
    raise SystemExit(1)

if not APP.exists():
    fail(f"APP_JS_MISSING:{APP}")

app = APP.read_text(encoding="utf-8")

# 000093 already arms Evidence before copying. 000095 adds the same priority
# arm to Error Report so BOTH Return Lane report types enter Vertex Clip Relay.
error_anchor = '''$("errorReportBtn").onclick = async () => {
  const text = buildReport("ERROR");
  await copyReport(text, $("errorReportBtn"), '''
if error_anchor not in app:
    fail("ERROR_REPORT_HANDLER_ANCHOR_MISSING")

if "CLIP RELAY: PRIORITY ERROR ARMED" not in app:
    replacement = '''$("errorReportBtn").onclick = async () => {
  const text = buildReport("ERROR");
  try {
    const relay = await invoke("clip_relay_set_priority", { text, kind: "ERROR" });
    log(`CLIP RELAY: PRIORITY ERROR ARMED (${relay.bytes} bytes)`);
  } catch (e) {
    log(`CLIP RELAY ERROR ARM ERROR: ${e}`);
  }
  await copyReport(text, $("errorReportBtn"), '''
    app = app.replace(error_anchor, replacement, 1)

# Verify Evidence priority wiring still exists and remains untouched.
if 'invoke("clip_relay_set_priority", { text, kind: "EVIDENCE" })' not in app:
    fail("EVIDENCE_PRIORITY_WIRING_MISSING")

stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_ROOT / stamp / "ui" / "app.js"
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(APP, backup)

with APP.open("w", encoding="utf-8", newline="\n") as f:
    f.write(app)

print(f"BACKUP={backup}")
print("ERROR_REPORT_PRIORITY=WIRED")
print("EVIDENCE_REPORT_PRIORITY=PRESERVED")
print("RETURN_LANE_PRIORITY=BOTH_ERROR_AND_EVIDENCE")
print("RUST_RELAY_ALGORITHM=UNCHANGED")
print("VERTEX_WORKS_CLIP_RELAY_ERROR_PRIORITY_000095_SOURCE_PATCH=PASS")
