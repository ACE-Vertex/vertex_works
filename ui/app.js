const invoke = window.__TAURI__.core.invoke;
const listen = window.__TAURI__.event.listen;

let selectedPath = null;
let selectedInspect = null;
let currentStageId = null;
let receiverInfo = null;
let currentPhase = "BOOT";
let lastOutcome = null;
let lastError = null;
let artifactStatusByPath = new Map();
let incomingItems = [];
let incomingSortMode =
  localStorage.getItem("vertex.works.incomingSort")
  || localStorage.getItem("vertex.receiver.incomingSort")
  || "name";

let shellActivityStartedAt = null;
let shellActivityTimer = null;
let shellBusyButton = null;

const $ = (id) => document.getElementById(id);

function formatElapsed(ms) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function beginShellActivity(label, button = null) {
  shellActivityStartedAt = Date.now();
  $("shellActivityText").textContent = label;
  $("shellElapsed").textContent = "00:00";
  $("shellActivity").classList.remove("hidden");

  if (shellActivityTimer) clearInterval(shellActivityTimer);
  shellActivityTimer = setInterval(() => {
    if (shellActivityStartedAt) {
      $("shellElapsed").textContent = formatElapsed(Date.now() - shellActivityStartedAt);
    }
  }, 250);

  if (shellBusyButton) shellBusyButton.classList.remove("busy");
  shellBusyButton = button;
  if (shellBusyButton) shellBusyButton.classList.add("busy");
}

function endShellActivity() {
  if (shellActivityTimer) {
    clearInterval(shellActivityTimer);
    shellActivityTimer = null;
  }
  shellActivityStartedAt = null;
  $("shellActivity").classList.add("hidden");

  if (shellBusyButton) {
    shellBusyButton.classList.remove("busy");
    shellBusyButton = null;
  }
}

const log = (msg) => {
  const stamp = new Date().toLocaleTimeString();
  $("log").textContent += `[${stamp}] ${msg}\n`;
  $("log").scrollTop = $("log").scrollHeight;
};


function appendTerminalLine(stream, text) {
  const terminal = $("terminalLog");
  if (!terminal) return;

  const line = document.createElement("div");
  line.className = `terminal-line ${stream || "stdout"}`;
  line.textContent = text;
  terminal.appendChild(line);

  while (terminal.childElementCount > 1800) {
    terminal.removeChild(terminal.firstElementChild);
  }
  terminal.scrollTop = terminal.scrollHeight;
}

function renderShellEvent(payload) {
  if (!payload) return;

  const stream = payload.stream || "stdout";
  appendTerminalLine(stream, payload.text || "");

  if (stream === "command") {
    const total = payload.command_total || 0;
    const current = payload.command_index || 0;
    $("shellCommandState").textContent =
      total > 0 ? `COMMAND ${current}/${total}` : "COMMAND";
  } else if (stream === "exit") {
    $("shellCommandState").textContent =
      payload.success ? "PASS" : "FAIL";
  } else if (stream === "system") {
    $("shellCommandState").textContent = "ACTIVE";
  }
}

async function bindVertexShellStream() {
  await listen("vertex-shell-output", (event) => {
    renderShellEvent(event.payload);
  });
}

function setPhase(phase) {
  currentPhase = phase;
}

function resetReturnLane() {
  lastOutcome = null;
  lastError = null;
  $("returnLane").classList.add("hidden");
  $("errorReportBtn").classList.add("hidden");
  $("evidenceCopyBtn").classList.add("hidden");
  $("returnLaneState").textContent = "READY";
}

function showErrorReturn(error, phase = currentPhase) {
  lastError = String(error);
  currentPhase = phase;
  $("returnLane").classList.remove("hidden");
  $("errorReportBtn").classList.remove("hidden");
  $("evidenceCopyBtn").classList.add("hidden");
  $("returnLaneState").textContent = `${phase} FAILED`;
}

function showEvidenceReturn(result) {
  lastOutcome = result;
  lastError = null;
  $("returnLane").classList.remove("hidden");
  $("errorReportBtn").classList.add("hidden");
  $("evidenceCopyBtn").classList.remove("hidden");
  $("returnLaneState").textContent = "VERIFIED / COPY READY";
}

async function boot() {
  try {
    await bindVertexShellStream();
    receiverInfo = await invoke("receiver_info");
    $("inbox").textContent = receiverInfo.inbox;
    $("allowedRoot").textContent = receiverInfo.allowed_root;
    $("liveBadge").textContent = "WORKS ONLINE";
    $("liveBadge").classList.add("live");
    log(`VERTEX WORKS online. Receiving Bay: ${receiverInfo.inbox}`);
    setPhase("IDLE");
    await refresh();
    setInterval(refresh, 2500);
  } catch (e) {
    $("liveBadge").textContent = "FAULT";
    log(`BOOT ERROR: ${e}`);
    showErrorReturn(e, "BOOT");
  }
}


function artifactFileName(path) {
  return String(path || "").split(/[\\/]/).pop() || "";
}

function compareText(a, b) {
  return String(a || "").localeCompare(String(b || ""), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

function updateSortButtons() {
  $("sortNameBtn")?.classList.toggle("active", incomingSortMode === "name");
  $("sortGenreBtn")?.classList.toggle("active", incomingSortMode === "genre");
}

function sortedIncoming(items) {
  const copy = [...items];

  if (incomingSortMode === "genre") {
    return copy.sort((a, b) =>
      compareText(a.genre, b.genre)
      || compareText(artifactFileName(a.path), artifactFileName(b.path))
      || compareText(a.title, b.title)
    );
  }

  return copy.sort((a, b) =>
    compareText(artifactFileName(a.path), artifactFileName(b.path))
    || compareText(a.title, b.title)
  );
}

function setIncomingSort(mode) {
  incomingSortMode = mode === "genre" ? "genre" : "name";
  localStorage.setItem("vertex.works.incomingSort", incomingSortMode);
  updateSortButtons();
  renderIncoming();
}

function renderIncoming() {
  const list = $("artifactList");
  const previous = selectedPath;
  list.innerHTML = "";

  if (!incomingItems.length) {
    list.innerHTML = `<div class="empty incoming-empty">No .vra artifacts detected.</div>`;
    return;
  }

  const items = sortedIncoming(incomingItems);
  let lastGenre = null;

  for (const item of items) {
    if (incomingSortMode === "genre" && item.genre !== lastGenre) {
      const group = document.createElement("div");
      group.className = "genre-group";
      group.innerHTML = `<span>${escapeHtml(item.genre || "VERTEX")}</span><i></i>`;
      list.appendChild(group);
      lastGenre = item.genre;
    }

    const div = document.createElement("div");
    const historyClass = item.rolled_back ? "rolled-back" : item.applied ? "applied" : "";
    div.className = `artifact ${item.valid_manifest ? "" : "invalid"} ${historyClass} ${previous === item.path ? "selected" : ""}`;

    let badge = "";
    if (item.rolled_back) {
      badge = `<span class="artifact-badge rollback">↶ ROLLED BACK</span>`;
    } else if (item.applied && item.verified) {
      badge = `<span class="artifact-badge verified">✓ APPLIED · VERIFIED</span>`;
    } else if (item.applied) {
      badge = `<span class="artifact-badge applied-only">✓ APPLIED · VERIFY FAILED</span>`;
    }

    div.innerHTML = `
      <div class="artifact-head">
        <div class="title">${escapeHtml(item.title)}</div>
        ${badge}
      </div>
      <div class="artifact-subline">
        <span class="genre-pill">${escapeHtml(item.genre || "VERTEX")}</span>
        <span class="artifact-file">${escapeHtml(artifactFileName(item.path))}</span>
      </div>
      <div class="meta">${escapeHtml(item.artifact_id)}</div>
      <div class="meta">${escapeHtml(item.target || item.error || "")}</div>
    `;
    div.onclick = () => selectArtifact(item.path, div);
    list.appendChild(div);
  }
}


function animateCount(id, value) {
  const node = $(id);
  if (!node) return;
  const from = Number(node.textContent || 0) || 0;
  const to = Number(value || 0);
  if (from === to) {
    node.textContent = String(to);
    return;
  }
  const started = performance.now();
  const duration = 360;
  const tick = (now) => {
    const t = Math.min(1, (now - started) / duration);
    const eased = 1 - Math.pow(1 - t, 3);
    node.textContent = String(Math.round(from + (to - from) * eased));
    if (t < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function updateWorksMetrics(items) {
  const incoming = items.length;
  const verified = items.filter(x => x.applied && x.verified && !x.rolled_back).length;
  const attention = items.filter(x => !x.valid_manifest || (x.applied && !x.verified)).length;
  const ready = items.filter(x => x.valid_manifest && !x.applied && !x.rolled_back).length;

  animateCount("incomingCount", incoming);
  animateCount("readyCount", ready);
  animateCount("verifiedCount", verified);
  animateCount("attentionCount", attention);
}

async function refresh() {
  try {
    incomingItems = await invoke("scan_inbox");
    artifactStatusByPath = new Map(incomingItems.map(item => [item.path, item]));
    updateWorksMetrics(incomingItems);
    renderIncoming();
  } catch (e) {
    log(`SCAN ERROR: ${e}`);
    showErrorReturn(e, "SCAN");
  }
}

async function selectArtifact(path, node) {
  selectedPath = path;
  currentStageId = null;
  resetReturnLane();
  document.querySelectorAll(".artifact").forEach(x => x.classList.remove("selected"));
  node.classList.add("selected");

  try {
    setPhase("INSPECT");
    const result = await invoke("inspect_artifact", { path });
    selectedInspect = result;
    $("emptyState").classList.add("hidden");
    $("details").classList.remove("hidden");

    $("artifactId").textContent = result.manifest.artifact_id;
    $("artifactTitle").textContent = result.manifest.title;
    $("artifactSource").textContent =
      `${result.manifest.source.actor}${result.manifest.source.model ? " / " + result.manifest.source.model : ""}`;
    $("artifactTarget").textContent = result.manifest.target.project_root;
    $("artifactAuthority").textContent = result.manifest.authority;
    $("artifactPayload").textContent = `${result.payload_count} file(s)`;

    if (result.errors.length === 0 && result.hashes_valid) {
      const history = artifactStatusByPath.get(path);
      if (history?.rolled_back) {
        $("artifactState").textContent = "VALID · ROLLED BACK";
        $("validationBox").className = "validation ok";
        $("validationBox").textContent = "Manifest valid. Previous apply was rolled back. Ready to stage again.";
      } else if (history?.applied && history?.verified) {
        $("artifactState").textContent = "VALID · ✓ APPLIED";
        $("validationBox").className = "validation ok";
        $("validationBox").textContent = "Manifest valid. ✓ Already applied and verified. Re-stage is still allowed.";
      } else if (history?.applied) {
        $("artifactState").textContent = "VALID · ✓ APPLIED";
        $("validationBox").className = "validation ok";
        $("validationBox").textContent = "Manifest valid. ✓ Already applied, but latest verification failed. Re-stage is allowed.";
      } else {
        $("artifactState").textContent = "VALID";
        $("validationBox").className = "validation ok";
        $("validationBox").textContent = "Manifest valid. Payload SHA-256 verified. Ready to stage.";
      }
      $("stageBtn").disabled = false;
      setPhase("VALID");
    } else {
      const detail = result.errors.join("\n") || "Artifact validation failed.";
      $("artifactState").textContent = "REJECTED";
      $("validationBox").className = "validation bad";
      $("validationBox").textContent = detail;
      $("stageBtn").disabled = true;
      showErrorReturn(detail, "VALIDATE");
    }

    $("applyBtn").disabled = true;
    $("rollbackBtn").disabled = true;
    log(`Inspect ${result.manifest.artifact_id}: ${result.errors.length ? "REJECTED" : "VALID"}`);
  } catch (e) {
    $("artifactState").textContent = "INSPECT FAILED";
    log(`INSPECT ERROR: ${e}`);
    showErrorReturn(e, "INSPECT");
  }
}

$("stageBtn").onclick = async () => {
  if (!selectedPath) return;
  resetReturnLane();
  beginShellActivity("STAGE / HASH / EXTRACT", $("stageBtn"));
  try {
    setPhase("STAGE");
    $("artifactState").textContent = "STAGING";
    const result = await invoke("stage_artifact", { path: selectedPath });
    currentStageId = result.stage_id;
    $("artifactState").textContent = "STAGED";
    $("applyBtn").disabled = false;
    $("rollbackBtn").disabled = true;
    $("validationBox").className = "validation ok";
    $("validationBox").textContent =
      `STAGED: ${result.operation_count} file(s)\n${result.stage_dir}`;
    log(`STAGED ${result.stage_id} → ${result.target_root}`);
    setPhase("STAGED");
  } catch (e) {
    $("artifactState").textContent = "STAGE FAILED";
    log(`STAGE ERROR: ${e}`);
    showErrorReturn(e, "STAGE");
  } finally {
    endShellActivity();
  }
};

$("applyBtn").onclick = async () => {
  if (!currentStageId) return;
  // VERTEX_WORKS_DIRECT_APPLY_088: APPLY click is the explicit HUMAN_APPLY gate; redundant second confirmation removed.
resetReturnLane();
  $("shellCommandState").textContent = "ACTIVE";
  appendTerminalLine("system", "──────────────── APPLY / VERIFY / BUILD ────────────────");
  beginShellActivity("APPLY / VERIFY / BUILD", $("applyBtn"));
  try {
    setPhase("APPLY");
    $("artifactState").textContent = "APPLYING";
    $("applyBtn").disabled = true;
    const result = await invoke("apply_stage", { stageId: currentStageId });
    lastOutcome = result;
    $("artifactState").textContent = result.verified ? "VERIFIED" : "VERIFY FAILED";
    $("rollbackBtn").disabled = false;

    log(`APPLIED ${result.applied_files.length} file(s).`);
    log(`BACKUP ${result.backup_dir}`);
    for (const v of result.verification) {
      log(`VERIFY ${v.program} ${v.args.join(" ")} → ${v.success ? "PASS" : "FAIL"}`);
      if (v.stdout.trim()) log(v.stdout.trim());
      if (v.stderr.trim()) log(v.stderr.trim());
    }
    if (!result.verification.length) {
      log("VERIFY: no commands declared.");
    }

    await refresh();

    if (result.verified) {
      setPhase("VERIFIED");
      log("FINAL: VERIFIED");
      showEvidenceReturn(result);
    } else {
      setPhase("VERIFY");
      log("FINAL: VERIFY FAILED — rollback available");
      showErrorReturn("One or more verification commands failed.", "VERIFY");
      lastOutcome = result;
    }
  } catch (e) {
    $("artifactState").textContent = "APPLY FAILED";
    $("applyBtn").disabled = false;
    log(`APPLY ERROR: ${e}`);
    showErrorReturn(e, "APPLY");
  } finally {
    endShellActivity();
    if ($("shellCommandState").textContent === "ACTIVE") {
      $("shellCommandState").textContent = "STANDBY";
    }
  }
};

$("rollbackBtn").onclick = async () => {
  if (!currentStageId) return;
  if (!confirm("Rollback files that had pre-apply backups?")) return;
  beginShellActivity("ROLLBACK / RESTORE", $("rollbackBtn"));
  try {
    setPhase("ROLLBACK");
    const restored = await invoke("rollback_stage", { stageId: currentStageId });
    $("artifactState").textContent = "ROLLED BACK";
    log(`ROLLBACK restored ${restored.length} file(s).`);
    restored.forEach(p => log(`RESTORED ${p}`));
    currentPhase = "ROLLED_BACK";
    await refresh();
  } catch (e) {
    log(`ROLLBACK ERROR: ${e}`);
    showErrorReturn(e, "ROLLBACK");
  } finally {
    endShellActivity();
  }
};

$("errorReportBtn").onclick = async () => {
  const text = buildReport("ERROR");
  try {
    const relay = await invoke("clip_relay_set_priority", { text, kind: "ERROR" });
    log(`CLIP RELAY: PRIORITY ERROR ARMED (${relay.bytes} bytes)`);
  } catch (e) {
    log(`CLIP RELAY ERROR ARM ERROR: ${e}`);
  }
  await copyReport(text, $("errorReportBtn"), "エラー報告をコピー");
};

$("evidenceCopyBtn").onclick = async () => {
  const text = buildReport("EVIDENCE");
  try {
    const relay = await invoke("clip_relay_set_priority", { text, kind: "EVIDENCE" });
    log(`CLIP RELAY: PRIORITY EVIDENCE ARMED (${relay.bytes} bytes)`);
  } catch (e) {
    log(`CLIP RELAY ARM ERROR: ${e}`);
  }
  await copyReport(text, $("evidenceCopyBtn"), "Evidenceをコピー");
};

$("sortNameBtn").onclick = () => setIncomingSort("name");
$("sortGenreBtn").onclick = () => setIncomingSort("genre");
$("refreshBtn").onclick = refresh;
updateSortButtons();
$("clearBtn").onclick = () => $("log").textContent = "";

function reportManifest() {
  return selectedInspect?.manifest || {};
}

function clipText(value, limit = 16000) {
  const text = String(value || "");
  if (text.length <= limit) return text;
  return `${text.slice(0, limit)}\n...[truncated by VERTEX WORKS: ${text.length - limit} chars]`;
}

function buildReport(kind) {
  const m = reportManifest();
  const source = m.source
    ? `${m.source.actor || ""}${m.source.model ? " / " + m.source.model : ""}`
    : "(unknown)";
  const lines = [];

  lines.push(`=== VERTEX WORKS ${kind === "ERROR" ? "ERROR REPORT" : "EVIDENCE REPORT"} ===`);
  lines.push(`Timestamp: ${new Date().toISOString()}`);
  lines.push(`Works Version: ${receiverInfo?.version || "0.3.2"}`);
  lines.push(`Phase: ${currentPhase}`);
  lines.push("");
  lines.push(`Artifact ID: ${m.artifact_id || "(unknown)"}`);
  lines.push(`Title: ${m.title || "(unknown)"}`);
  lines.push(`Source: ${source}`);
  lines.push(`Target: ${m.target?.project_root || "(unknown)"}`);
  lines.push(`Authority: ${m.authority || "(unknown)"}`);
  lines.push(`Stage ID: ${currentStageId || "(none)"}`);
  lines.push("");

  if (lastError) {
    lines.push("--- ERROR ---");
    lines.push(clipText(lastError));
    lines.push("");
  }

  if (lastOutcome) {
    lines.push("--- APPLY STATE ---");
    lines.push(`Verified: ${Boolean(lastOutcome.verified)}`);
    lines.push(`Backup: ${lastOutcome.backup_dir || "(none)"}`);
    lines.push("Applied Files:");
    for (const file of lastOutcome.applied_files || []) {
      lines.push(`  - ${file}`);
    }
    if (!(lastOutcome.applied_files || []).length) lines.push("  (none)");
    lines.push("");

    lines.push("--- VERIFICATION ---");
    const verification = lastOutcome.verification || [];
    if (!verification.length) {
      lines.push("(no verification commands declared)");
    }
    verification.forEach((v, i) => {
      lines.push(`[${i + 1}] ${v.program} ${(v.args || []).join(" ")}`);
      lines.push(`Success: ${Boolean(v.success)}`);
      lines.push(`Exit Code: ${v.exit_code ?? "(none)"}`);
      if (v.stdout) {
        lines.push("STDOUT:");
        lines.push(clipText(v.stdout));
      }
      if (v.stderr) {
        lines.push("STDERR:");
        lines.push(clipText(v.stderr));
      }
      lines.push("");
    });
  }

  lines.push("--- WORKS LEDGER ---");
  lines.push(clipText($("log").textContent, 12000));
  lines.push("=== END REPORT ===");

  return lines.join("\n");
}

async function copyReport(text, button, normalLabel) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      fallbackCopy(text);
    }
    button.classList.add("copied");
    button.textContent = "コピー済み ✓";
    log(`RETURN LANE: ${normalLabel} → clipboard`);
    setTimeout(() => {
      button.classList.remove("copied");
      button.textContent = normalLabel;
    }, 1800);
  } catch (e) {
    try {
      fallbackCopy(text);
      button.textContent = "コピー済み ✓";
      log(`RETURN LANE: fallback clipboard copy OK`);
      setTimeout(() => button.textContent = normalLabel, 1800);
    } catch (fallbackError) {
      log(`CLIPBOARD ERROR: ${fallbackError}`);
      alert(`Clipboard copy failed:\n${fallbackError}`);
    }
  }
}

function fallbackCopy(text) {
  const area = document.createElement("textarea");
  area.value = text;
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.focus();
  area.select();
  const ok = document.execCommand("copy");
  document.body.removeChild(area);
  if (!ok) throw new Error("document.execCommand('copy') returned false");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}


document.querySelectorAll(".rail-item").forEach((button) => {
  button.addEventListener("click", () => {
    const target = document.getElementById(button.dataset.jump || "");
    if (target && !target.classList.contains("hidden")) {
      target.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    document.querySelectorAll(".rail-item").forEach(x => x.classList.remove("active"));
    button.classList.add("active");
  });
});

boot();


$("clearTerminalBtn").onclick = () => {
  $("terminalLog").innerHTML =
    `<div class="terminal-line system">VERTEX WORKS FOUNDRY CLEARED — waiting for next command</div>`;
  $("shellCommandState").textContent = "STANDBY";
};


// PROJECT X-RAY OBSERVATORY 0.4.1
let xrayReport = null;
let xraySelected = null;
const xq = id => document.getElementById(id);
function xrayFmtBytes(bytes){const mb=Number(bytes||0)/1024/1024;return mb<1024?`${mb.toFixed(mb<10?1:0)} MB`:`${(mb/1024).toFixed(1)} GB`;}
function xrayEsc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));}
function xraySwitch(mode){const x=mode==="xray";xq("xrayWorkspace")?.classList.toggle("workspace-hidden",!x);xq("forgeWorkspace")?.classList.toggle("workspace-hidden",x);document.body.classList.toggle("xray-mode",x);xq("xrayTabBtn")?.classList.toggle("active",x);xq("forgeTabBtn")?.classList.toggle("active",!x);}
function xrayReportText(r){
  const lines=["VERTEX WORKS — PROJECT X-RAY REPORT",`Root: ${r.root}`,`Top-level areas: ${r.nodes.length}`,`Folders indexed: ${(r.folders||[]).length}`,`Directories scanned: ${r.directories_scanned||0}`,`Ignored generated/cache folders: ${r.ignored_directories||0}`,`Recognized components: ${r.recognized_components||r.success_count}`,`Files: ${r.files_scanned}`,`Structural links: ${r.edges.length}`,`Success: ${r.success_count}`,`Errors: ${r.error_count}`,`Analysis findings: ${r.analysis_count}`,`Truncated: ${r.truncated?"YES":"NO"}`,"","FINDINGS"];
  r.findings.forEach(f=>lines.push(`- [${f.severity}] ${f.title}: ${f.detail}${f.path?` @ ${f.path}`:""}`));
  lines.push("","TOP-LEVEL AREAS");r.nodes.forEach(n=>lines.push(`- ${n.name} | ${n.kind} | ${n.health} | ${n.files} files | ${xrayFmtBytes(n.bytes)}`));
  const components=(r.folders||[]).filter(f=>f.manifest&&!f.ignored);
  lines.push("","RECOGNIZED COMPONENTS");components.forEach(f=>lines.push(`- ${f.relative_path} | ${f.kind} | ${f.manifest} | ${f.files} files | ${xrayFmtBytes(f.bytes)}`));
  lines.push("","RELATIONS");r.edges.forEach(e=>lines.push(`- ${e.from} -> ${e.to} [${e.kind}]`));
  return lines.join("\n");
}
async function xrayCopy(text){
  try{await navigator.clipboard.writeText(text);return true;}catch(_){const t=document.createElement("textarea");t.value=text;t.style.position="fixed";t.style.opacity="0";document.body.appendChild(t);t.select();const ok=document.execCommand("copy");t.remove();return ok;}
}
function xrayFolderChildren(r,parent){return (r.folders||[]).filter(f=>(f.parent_id??null)===(parent??null));}
function xrayFocusFolder(f){xraySelected=f.id;document.querySelectorAll(".xray-folder-row,.xray-node").forEach(e=>e.classList.toggle("active",e.dataset.node===f.id));xq("xrayStatus").textContent=`FOLDER ${f.relative_path} — ${f.kind} / ${f.files} files / ${xrayFmtBytes(f.bytes)} / ${f.state}`;}
function xrayBuildFolderRow(r,f){
  const wrap=document.createElement("div");wrap.className="xray-folder-wrap";wrap.dataset.node=f.id;
  const children=xrayFolderChildren(r,f.id);
  const row=document.createElement("div");
  // VERTEX_WORKS_RAY_PROJECT_ROOT_BINDING_064
  const vxRel = String(f.relative_path || "").replaceAll("\\", "/");
  const vxProject = vxRel.split("/").filter(Boolean)[0] || "";
  if (vxProject && vxProject !== ".") {
    row.dataset.xrayProjectRoot = `G:\\Vertex_Project\\Development\\${vxProject}`;
    row.dataset.xrayProjectName = vxProject;
  }
row.className=`xray-folder-row${f.ignored?" ignored":""}`;row.dataset.node=f.id;
  const toggle=document.createElement("button");toggle.className="xray-folder-toggle";toggle.textContent=children.length?"›":"·";toggle.disabled=!children.length;
  const icon=document.createElement("div");icon.className="xray-folder-icon";icon.textContent=f.manifest?f.kind.slice(0,2):"▱";
  const copy=document.createElement("div");copy.className="xray-folder-copy";copy.innerHTML=`<strong>${xrayEsc(f.name)}</strong><small>${f.manifest?xrayEsc(f.manifest)+" · ":""}${f.files} files · ${xrayFmtBytes(f.bytes)}</small>`;
  const state=document.createElement("span");state.className=`xray-health-chip${f.ignored?" ignored":""}`;state.textContent=f.ignored?"IGNORED":(f.manifest?"COMPONENT":"DIR");
  row.append(toggle,icon,copy,state);wrap.appendChild(row);
  row.onclick=(ev)=>{if(ev.target===toggle)return;xrayFocusFolder(f);};
  if(children.length){toggle.onclick=()=>{let child=wrap.querySelector(":scope > .xray-folder-children");const opening=!child;if(opening){child=document.createElement("div");child.className="xray-folder-children";children.forEach(c=>child.appendChild(xrayBuildFolderRow(r,c)));wrap.appendChild(child);}else{child.remove();}toggle.textContent=opening?"⌄":"›";};}
  return wrap;
}
function xrayRenderModules(r){const host=xq("xrayModuleList");host.innerHTML="";const roots=xrayFolderChildren(r,null);if(!roots.length){host.innerHTML='<div class="xray-placeholder">No folders were indexed.</div>';return;}roots.forEach(f=>host.appendChild(xrayBuildFolderRow(r,f)));}
function xrayFocusNode(id){xraySelected=id;document.querySelectorAll(".xray-folder-row,.xray-node").forEach(e=>e.classList.toggle("active",e.dataset.node===id));const n=xrayReport?.nodes.find(n=>n.id===id);if(n){xq("xrayStatus").textContent=`FOCUS ${n.name} — ${n.kind} / ${n.files} files / ${xrayFmtBytes(n.bytes)}`;}}
function xrayRenderMap(r){const map=xq("xrayMap");map.innerHTML=`<div class="xray-core"><strong>VERTEX PROJECT</strong><span>${r.nodes.length} modules</span></div>`;const count=Math.max(1,r.nodes.length);const cx=50,cy=50,rx=36,ry=34;const pos={};r.nodes.forEach((n,i)=>{const a=(Math.PI*2*i/count)-Math.PI/2;const x=cx+Math.cos(a)*rx,y=cy+Math.sin(a)*ry;pos[n.id]=[x,y];const el=document.createElement("div");el.className="xray-node";el.dataset.node=n.id;el.style.left=`${x}%`;el.style.top=`${y}%`;el.innerHTML=`<strong>${xrayEsc(n.name)}</strong><span>${xrayEsc(n.health)}</span>`;el.onclick=()=>xrayFocusNode(n.id);map.appendChild(el);});requestAnimationFrame(()=>{const rect=map.getBoundingClientRect();for(const e of r.edges){const a=pos[e.from],b=pos[e.to];if(!a||!b)continue;const x1=rect.width*a[0]/100,y1=rect.height*a[1]/100,x2=rect.width*b[0]/100,y2=rect.height*b[1]/100;const len=Math.hypot(x2-x1,y2-y1),ang=Math.atan2(y2-y1,x2-x1)*180/Math.PI;const line=document.createElement("div");line.className="xray-edge";line.dataset.kind=e.kind;line.style.left=`${x1}px`;line.style.top=`${y1}px`;line.style.width=`${len}px`;line.style.transform=`rotate(${ang}deg)`;map.insertBefore(line,map.firstChild);}});}
function xrayRenderFindings(r){const host=xq("xrayFindings");host.innerHTML="";r.findings.forEach(f=>{const sev=f.severity.toLowerCase();const el=document.createElement("div");el.className=`xray-finding ${sev}`;el.innerHTML=`<small>${xrayEsc(f.severity)}</small><strong>${xrayEsc(f.title)}</strong><p>${xrayEsc(f.detail)}</p>`;host.appendChild(el);});}
function xrayRenderReport(r){
  xrayReport=r;
  xq("xrayRoot").textContent=r.root;
  xq("xrayModuleCount").textContent=(r.folders||[]).length;
  xq("xrayFileCount").textContent=r.files_scanned.toLocaleString();
  xq("xrayEdgeCount").textContent=r.edges.length;
  xq("xraySuccessCount").textContent=r.success_count;
  xq("xrayErrorCount").textContent=r.error_count;
  xq("xrayAnalysisCount").textContent=r.analysis_count;
  xq("xrayRecognized").textContent=r.recognized_components||r.success_count;
  xq("xrayObserved").textContent=r.directories_scanned||Math.max(0,(r.folders||[]).length-r.ignored_directories);
  xq("xrayBytes").textContent=xrayFmtBytes(r.bytes_scanned);
  const risk=Math.min(100,r.error_count*28+r.findings.filter(f=>f.severity==="WARN").length*12);
  const health=Math.max(0,100-risk);
  xq("xrayRisk").textContent=risk;xq("xrayRiskBar").style.width=`${risk}%`;xq("xrayHealth").textContent=`${health}%`;xq("xrayHealthTop").textContent=`HEALTH ${health}%`;xq("xrayReportState").textContent=r.error_count?"ATTENTION":(r.truncated?"PARTIAL":"VERIFIED");xq("xrayReportPreview").textContent=xrayReportText(r);xq("xrayClipBtn").disabled=false;xq("xrayCopyJsonBtn").disabled=false;xq("xrayTimestamp").textContent=new Date().toLocaleTimeString();xq("xrayStatus").textContent=r.truncated?"SCAN PARTIAL — 500k entry safety budget reached; visible tree marks the boundary.":`SCAN COMPLETE — ${(r.folders||[]).length} folders indexed recursively; project untouched.`;xrayRenderModules(r);xrayRenderMap(r);xrayRenderFindings(r);
}
async function xrayScan(){const btn=xq("xrayScanBtn"),map=xq("xrayMap");btn.disabled=true;btn.textContent="SCANNING";map.classList.add("scanning");xq("xrayReportState").textContent="SCANNING";xq("xrayStatus").textContent="X-Ray is reading project structure… no files will be changed.";try{const r=await invoke("xray_scan_project",{root:null});xrayRenderReport(r);}catch(e){xq("xrayErrorCount").textContent="1";xq("xrayReportState").textContent="ERROR";xq("xrayFindings").innerHTML=`<div class="xray-finding error"><small>ERROR</small><strong>X-Ray scan failed</strong><p>${xrayEsc(e)}</p></div>`;xq("xrayStatus").textContent=`ERROR — ${e}`;}finally{btn.disabled=false;btn.textContent="SCAN";map.classList.remove("scanning");}}
window.addEventListener("DOMContentLoaded",()=>{xq("xrayTabBtn")?.addEventListener("click",()=>xraySwitch("xray"));xq("forgeTabBtn")?.addEventListener("click",()=>xraySwitch("forge"));xq("xrayScanBtn")?.addEventListener("click",xrayScan);xq("xrayClipBtn")?.addEventListener("click",async()=>{if(!xrayReport)return;const ok=await xrayCopy(xrayReportText(xrayReport));xq("xrayStatus").textContent=ok?"CLIPPED TO VERA — paste directly into the Vera chat lane.":"Clipboard handoff failed.";});xq("xrayCopyJsonBtn")?.addEventListener("click",async()=>{if(!xrayReport)return;await xrayCopy(JSON.stringify(xrayReport,null,2));xq("xrayStatus").textContent="X-Ray JSON copied to clipboard.";});xq("xrayAllBtn")?.addEventListener("click",()=>{document.querySelectorAll(".xray-edge").forEach(e=>e.style.display="block");xq("xrayAllBtn").classList.add("active");xq("xrayDepsBtn").classList.remove("active");});xq("xrayDepsBtn")?.addEventListener("click",()=>{document.querySelectorAll(".xray-edge").forEach(e=>e.style.display=e.dataset.kind==="DEPENDENCY"?"block":"none");xq("xrayDepsBtn").classList.add("active");xq("xrayAllBtn").classList.remove("active");});xraySwitch("xray");setTimeout(xrayScan,350);});


/* ==========================================================================\n   VERTEX WORKS 0.5.0 — RAY ⇄ FORGE CONTINUITY / FME-LINEAGE BLUEPRINT\n   ========================================================================== */
const VERTEX_BP_STORE="vertexWorksBlueprintRelationsV1";
const VERTEX_LANG_STORE="vertexWorksLanguageV1";
let blueprintAnnotations=[];
let blueprintActiveRelation=null;
let blueprintLinkMode=false;
let blueprintLinkSource=null;
let blueprintFilter="ALL";
let vertexLanguage=localStorage.getItem(VERTEX_LANG_STORE)||"ja";

const vertexI18n={
  ja:{
    "nav.raySub":"観測・比較","nav.forgeSub":"受信・施工","nav.flow":"RAY ⇄ FORGE CONTINUITY","nav.rayContext":"Project Intelligence / Blueprint","nav.forgeContext":"Artifact Engineering / Human Gate",
    "settings.title":"表示設定","settings.language":"表示言語","settings.languageHint":"既定は日本語です","settings.local":"設定はこの端末のVERTEX WORKSに保存されます。",
    "ray.title":"PROJECT INTELLIGENCE","ray.subtitle":"構造観測 · 比較 · Blueprint · Evidence Driven · Read Only","ray.explorer":"プロジェクト・エクスプローラ","ray.scan":"スキャン","ray.explorerHint":"フォルダを展開してProjectの地層へ潜ります。Blueprint接続モードではProjectを2つ選択します。","ray.awaitScan":"スキャン待機中","ray.findings":"分析結果","ray.noFindings":"成功・エラー・分析結果をここに表示します。","ray.reportPreview":"レポートプレビュー",
    "blueprint.title":"Project Blueprint","blueprint.addRelation":"＋ 関係追加","blueprint.linkMode":"関係追加モード","blueprint.pickSource":"接続元Projectを選択","blueprint.pickTarget":"接続先Projectを選択",
    "relation.title":"関係インスペクタ","relation.emptyTitle":"関係線の中点を選択","relation.emptyHint":"依存性・相関性・優位性・系譜などを細かく観測注釈できます。","relation.type":"関係タイプ","relation.strength":"関係強度","relation.confidence":"確信度","relation.dependency":"依存レベル","relation.correlation":"相関スコア","relation.superiority":"優位性 A ⇄ B","relation.note":"観測メモ","relation.notePlaceholder":"根拠・用途・比較観点","relation.source":"SOURCE","relation.localOnly":"Blueprint注釈はProject Sourceを変更しません","relation.save":"注釈を保存","relation.delete":"注釈を削除",
    "metric.folders":"フォルダ","metric.files":"ファイル","metric.links":"関係","metric.health":"構造ヘルス","metric.risk":"リスク分析","metric.analysis":"分析結果","metric.components":"コンポーネント","metric.directories":"ディレクトリ","metric.scanned":"走査容量",
    "outcome.success":"認識 / 健全","outcome.error":"読取 / 分析失敗","outcome.analysis":"所見 / 観測","common.clear":"クリア",
    "forge.receiving":"受信","forge.incomingArtifacts":"受信アーティファクト","forge.ready":"準備完了","forge.validatedWaiting":"検証済み / 待機","forge.verified":"検証完了","forge.completedArtifacts":"完了アーティファクト","forge.attention":"要確認","forge.invalidFailed":"不正 / 検証失敗","forge.receivingBay":"受信ベイ","forge.productionRoot":"許可済みProduction Root","forge.receivingBayStep":"01 / 受信ベイ","forge.incomingCargo":"受信アーティファクト","forge.inspectionStep":"02 / 検査 + HUMAN GATE","forge.inspector":"アーティファクト・インスペクタ","forge.selectCargo":"受信アーティファクトを選択","forge.stage":"ステージ","forge.apply":"適用 / FORGE","forge.rollback":"ロールバック","forge.returnLane":"RECOVERY / RETURN LANE","forge.errorReport":"エラーレポート","forge.copyEvidence":"Evidenceをコピー","forge.foundry":"03 / FOUNDRY STREAM","forge.evidenceVault":"04 / EVIDENCE VAULT","forge.ledger":"Works Ledger"
  },
  en:{
    "nav.raySub":"Observe / Compare","nav.forgeSub":"Receive / Build","nav.flow":"RAY ⇄ FORGE CONTINUITY","nav.rayContext":"Project Intelligence / Blueprint","nav.forgeContext":"Artifact Engineering / Human Gate",
    "settings.title":"Display Settings","settings.language":"Language","settings.languageHint":"Japanese is the default","settings.local":"Settings are stored locally for this VERTEX WORKS installation.",
    "ray.title":"PROJECT INTELLIGENCE","ray.subtitle":"Structural Observation · Compare · Blueprint · Evidence Driven · Read Only","ray.explorer":"Project Explorer","ray.scan":"SCAN","ray.explorerHint":"Expand folders to inspect project layers. In Blueprint link mode, choose two projects.","ray.awaitScan":"Awaiting scan","ray.findings":"Analysis Findings","ray.noFindings":"Success, errors and analysis findings appear here.","ray.reportPreview":"REPORT PREVIEW",
    "blueprint.title":"Project Blueprint","blueprint.addRelation":"＋ ADD RELATION","blueprint.linkMode":"RELATION LINK MODE","blueprint.pickSource":"Choose source project","blueprint.pickTarget":"Choose target project",
    "relation.title":"Relation Inspector","relation.emptyTitle":"Select an edge midpoint","relation.emptyHint":"Annotate dependency, correlation, superiority, lineage and other relation properties.","relation.type":"Relation Type","relation.strength":"Relation Strength","relation.confidence":"Confidence","relation.dependency":"Dependency Level","relation.correlation":"Correlation Score","relation.superiority":"Superiority A ⇄ B","relation.note":"Observation Note","relation.notePlaceholder":"Evidence, use, comparison axis","relation.source":"SOURCE","relation.localOnly":"Blueprint annotations never mutate Project Source","relation.save":"SAVE ANNOTATION","relation.delete":"DELETE ANNOTATION",
    "metric.folders":"FOLDERS","metric.files":"FILES","metric.links":"LINKS","metric.health":"STRUCTURAL HEALTH","metric.risk":"RISK ANALYSIS","metric.analysis":"ANALYSIS RESULT","metric.components":"Components","metric.directories":"Directories","metric.scanned":"Scanned",
    "outcome.success":"recognized / healthy","outcome.error":"read / analysis failures","outcome.analysis":"findings / observations","common.clear":"CLEAR",
    "forge.receiving":"RECEIVING","forge.incomingArtifacts":"incoming artifacts","forge.ready":"READY","forge.validatedWaiting":"validated / waiting","forge.verified":"VERIFIED","forge.completedArtifacts":"completed artifacts","forge.attention":"ATTENTION","forge.invalidFailed":"invalid / verify failed","forge.receivingBay":"RECEIVING BAY","forge.productionRoot":"AUTHORIZED PRODUCTION ROOT","forge.receivingBayStep":"01 / RECEIVING BAY","forge.incomingCargo":"Incoming Cargo","forge.inspectionStep":"02 / INSPECTION + HUMAN GATE","forge.inspector":"Artifact Inspector","forge.selectCargo":"SELECT INCOMING CARGO","forge.stage":"STAGE","forge.apply":"APPLY / FORGE","forge.rollback":"ROLLBACK","forge.returnLane":"RECOVERY / RETURN LANE","forge.errorReport":"ERROR REPORT","forge.copyEvidence":"COPY EVIDENCE","forge.foundry":"03 / FOUNDRY STREAM","forge.evidenceVault":"04 / EVIDENCE VAULT","forge.ledger":"Works Ledger"
  }
};
function vertexT(key){return (vertexI18n[vertexLanguage]&&vertexI18n[vertexLanguage][key])||vertexI18n.ja[key]||key;}
function applyVertexLanguage(lang){vertexLanguage=lang==="en"?"en":"ja";localStorage.setItem(VERTEX_LANG_STORE,vertexLanguage);document.documentElement.lang=vertexLanguage;document.querySelectorAll("[data-i18n]").forEach(el=>{el.textContent=vertexT(el.dataset.i18n);});document.querySelectorAll("[data-i18n-placeholder]").forEach(el=>{el.placeholder=vertexT(el.dataset.i18nPlaceholder);});xq("langJaBtn")?.classList.toggle("active",vertexLanguage==="ja");xq("langEnBtn")?.classList.toggle("active",vertexLanguage==="en");if(xq("modeContextText"))xq("modeContextText").textContent=vertexT(document.body.classList.contains("xray-mode")?"nav.rayContext":"nav.forgeContext");}

function xraySwitch(mode){
  const ray=mode==="xray"||mode==="ray";
  xq("xrayWorkspace")?.classList.toggle("workspace-hidden",!ray);
  xq("forgeWorkspace")?.classList.toggle("workspace-hidden",ray);
  document.body.classList.toggle("xray-mode",ray);
  document.body.classList.toggle("forge-mode",!ray);
  xq("rayNavBtn")?.classList.toggle("active",ray);xq("forgeNavBtn")?.classList.toggle("active",!ray);
  if(xq("modeWorkspaceName"))xq("modeWorkspaceName").textContent=ray?"VERTEX RAY":"VERTEX FORGE";
  if(xq("modeContextText"))xq("modeContextText").textContent=vertexT(ray?"nav.rayContext":"nav.forgeContext");
}

function loadBlueprintAnnotations(){try{const raw=JSON.parse(localStorage.getItem(VERTEX_BP_STORE)||"[]");blueprintAnnotations=Array.isArray(raw)?raw:[];}catch(_){blueprintAnnotations=[];}}
function saveBlueprintAnnotations(){localStorage.setItem(VERTEX_BP_STORE,JSON.stringify(blueprintAnnotations));}
function bpRelationId(e){return e.id||`scan:${e.from}:${e.to}:${e.kind||e.type||"RELATED"}`;}
function bpRelations(r){
  const base=(r?.edges||[]).map(e=>({id:bpRelationId(e),from:e.from,to:e.to,type:e.kind||"RELATED",strength:70,confidence:75,dependency:e.kind==="DEPENDENCY"?"HARD":"NORMAL",correlation:0,superiority:0,note:"",source:"X-RAY",manual:false}));
  const byId=new Map(base.map(e=>[e.id,e]));
  blueprintAnnotations.forEach(a=>{if(a.manual){byId.set(a.id,{...a});}else{byId.set(a.id,{...(byId.get(a.id)||{}),...a});}});
  return [...byId.values()];
}
function bpTypeClass(t){return String(t||"RELATED").toLowerCase();}
function bpTypeVisible(t){return blueprintFilter==="ALL"||String(t||"").toUpperCase()===blueprintFilter;}
function bpNodeName(id){return xrayReport?.nodes?.find(n=>n.id===id)?.name||id||"—";}
function bpAnnotationFor(rel){return blueprintAnnotations.find(a=>a.id===rel.id);}

function xrayFocusNode(id){
  xraySelected=id;document.querySelectorAll(".xray-folder-row,.xray-node").forEach(e=>e.classList.toggle("active",e.dataset.node===id));
  const n=xrayReport?.nodes.find(n=>n.id===id);
  if(n)xq("xrayStatus").textContent=`FOCUS ${n.name} — ${n.kind} / ${n.files} files / ${xrayFmtBytes(n.bytes)}`;
  if(blueprintLinkMode){
    if(!blueprintLinkSource){blueprintLinkSource=id;xq("blueprintLinkStatus").textContent=vertexT("blueprint.pickTarget");document.querySelectorAll(".xray-node").forEach(e=>e.classList.toggle("link-source",e.dataset.node===id));}
    else if(blueprintLinkSource!==id){const rel={id:`manual:${Date.now()}`,from:blueprintLinkSource,to:id,type:"RELATED",strength:70,confidence:70,dependency:"NONE",correlation:0,superiority:0,note:"",source:"HUMAN BLUEPRINT",manual:true};blueprintActiveRelation=rel;blueprintLinkMode=false;blueprintLinkSource=null;xq("blueprintLinkNotice")?.classList.add("hidden");openRelationEditor(rel,true);}
  }
}

function xrayRenderMap(r){
  const map=xq("xrayMap");if(!map)return;map.innerHTML=`<div class="xray-core"><strong>VERTEX PROJECT</strong><span>${r.nodes.length} projects</span></div>`;
  const count=Math.max(1,r.nodes.length),cx=50,cy=50,rx=37,ry=35,pos={};
  r.nodes.forEach((n,i)=>{const a=(Math.PI*2*i/count)-Math.PI/2,x=cx+Math.cos(a)*rx,y=cy+Math.sin(a)*ry;pos[n.id]=[x,y];const el=document.createElement("div");el.className="xray-node blueprint-node";el.dataset.node=n.id;el.style.left=`${x}%`;el.style.top=`${y}%`;el.innerHTML=`<i class="bp-port port-top"></i><i class="bp-port port-right"></i><i class="bp-port port-bottom"></i><i class="bp-port port-left"></i><div class="bp-node-kicker">${xrayEsc(n.kind)}</div><strong>${xrayEsc(n.name)}</strong><span>${xrayEsc(n.health)} · ${n.files} files</span>`;el.onclick=()=>xrayFocusNode(n.id);map.appendChild(el);});
  requestAnimationFrame(()=>{const rect=map.getBoundingClientRect();for(const e of bpRelations(r)){const a=pos[e.from],b=pos[e.to];if(!a||!b)continue;const x1=rect.width*a[0]/100,y1=rect.height*a[1]/100,x2=rect.width*b[0]/100,y2=rect.height*b[1]/100,len=Math.hypot(x2-x1,y2-y1),ang=Math.atan2(y2-y1,x2-x1)*180/Math.PI;const edge=document.createElement("div");edge.className=`xray-edge bp-edge ${bpTypeClass(e.type)}`;edge.dataset.kind=e.type;edge.dataset.relid=e.id;edge.style.left=`${x1}px`;edge.style.top=`${y1}px`;edge.style.width=`${len}px`;edge.style.transform=`rotate(${ang}deg)`;edge.style.display=bpTypeVisible(e.type)?"block":"none";map.insertBefore(edge,map.firstChild);const mid=document.createElement("button");mid.className=`bp-edge-mid ${bpTypeClass(e.type)}`;mid.dataset.relid=e.id;mid.dataset.kind=e.type;mid.style.left=`${(x1+x2)/2}px`;mid.style.top=`${(y1+y2)/2}px`;mid.style.display=bpTypeVisible(e.type)?"block":"none";mid.textContent=e.type;mid.title=`${bpNodeName(e.from)} → ${bpNodeName(e.to)} / ${e.type}`;mid.onclick=ev=>{ev.stopPropagation();openRelationEditor(e,false);};map.appendChild(mid);}});
}

function setRangePair(id,valueId,val){const el=xq(id),out=xq(valueId);if(el)el.value=Number(val||0);if(out)out.textContent=String(Number(val||0));}
function openRelationEditor(rel,isDraft=false){blueprintActiveRelation={...rel};xq("relationEmpty")?.classList.add("hidden");xq("relationEditor")?.classList.remove("hidden");xq("relationModeChip").textContent=isDraft?"DRAFT":(rel.manual?"ANNOTATION":"X-RAY");xq("relationFrom").textContent=bpNodeName(rel.from);xq("relationTo").textContent=bpNodeName(rel.to);xq("relationType").value=rel.type||"RELATED";setRangePair("relationStrength","relationStrengthValue",rel.strength??70);setRangePair("relationConfidence","relationConfidenceValue",rel.confidence??70);xq("relationDependency").value=rel.dependency||"NONE";setRangePair("relationCorrelation","relationCorrelationValue",rel.correlation??0);setRangePair("relationSuperiority","relationSuperiorityValue",rel.superiority??0);xq("relationNote").value=rel.note||"";xq("relationSourceTag").textContent=rel.source||"X-RAY";xq("relationDeleteBtn").disabled=isDraft&&!bpAnnotationFor(rel);document.querySelectorAll(".bp-edge-mid").forEach(e=>e.classList.toggle("active",e.dataset.relid===rel.id));}
function closeRelationEditor(){blueprintActiveRelation=null;xq("relationEditor")?.classList.add("hidden");xq("relationEmpty")?.classList.remove("hidden");xq("relationModeChip").textContent="IDLE";document.querySelectorAll(".bp-edge-mid").forEach(e=>e.classList.remove("active"));}
function relationFromEditor(){if(!blueprintActiveRelation)return null;return {...blueprintActiveRelation,type:xq("relationType").value,strength:Number(xq("relationStrength").value),confidence:Number(xq("relationConfidence").value),dependency:xq("relationDependency").value,correlation:Number(xq("relationCorrelation").value),superiority:Number(xq("relationSuperiority").value),note:xq("relationNote").value,source:blueprintActiveRelation.manual?"HUMAN BLUEPRINT":"X-RAY + HUMAN ANNOTATION"};}
function saveActiveRelation(){const rel=relationFromEditor();if(!rel)return;const i=blueprintAnnotations.findIndex(a=>a.id===rel.id);if(i>=0)blueprintAnnotations[i]=rel;else blueprintAnnotations.push(rel);saveBlueprintAnnotations();blueprintActiveRelation=rel;xq("relationModeChip").textContent="ANNOTATED";if(xrayReport){xrayRenderMap(xrayReport);xq("xrayReportPreview").textContent=xrayReportText(xrayReport);}xq("xrayStatus").textContent="BLUEPRINT ANNOTATION SAVED — Project Source remains untouched.";}
function deleteActiveRelation(){if(!blueprintActiveRelation)return;const i=blueprintAnnotations.findIndex(a=>a.id===blueprintActiveRelation.id);if(i>=0){blueprintAnnotations.splice(i,1);saveBlueprintAnnotations();}closeRelationEditor();if(xrayReport){xrayRenderMap(xrayReport);xq("xrayReportPreview").textContent=xrayReportText(xrayReport);}xq("xrayStatus").textContent="BLUEPRINT ANNOTATION REMOVED — Project Source remains untouched.";}
function setBlueprintFilter(filter){blueprintFilter=filter;document.querySelectorAll("[data-relfilter]").forEach(b=>b.classList.toggle("active",b.dataset.relfilter===filter));document.querySelectorAll(".bp-edge,.bp-edge-mid").forEach(e=>e.style.display=bpTypeVisible(e.dataset.kind)?"block":"none");}
function startBlueprintLink(){if(!xrayReport?.nodes?.length)return;blueprintLinkMode=true;blueprintLinkSource=null;xq("blueprintLinkNotice")?.classList.remove("hidden");xq("blueprintLinkStatus").textContent=vertexT("blueprint.pickSource");document.querySelectorAll(".xray-node").forEach(e=>e.classList.remove("link-source"));}
function cancelBlueprintLink(){blueprintLinkMode=false;blueprintLinkSource=null;xq("blueprintLinkNotice")?.classList.add("hidden");document.querySelectorAll(".xray-node").forEach(e=>e.classList.remove("link-source"));}

function xrayReportText(r){
  const lines=["VERTEX WORKS — VERTEX RAY / PROJECT X-RAY REPORT",`Root: ${r.root}`,`Top-level areas: ${r.nodes.length}`,`Folders indexed: ${(r.folders||[]).length}`,`Directories scanned: ${r.directories_scanned??0}`,`Ignored generated/cache folders: ${r.ignored_directories??0}`,`Recognized components: ${r.recognized_components??r.success_count}`,`Files: ${r.files_scanned}`,`Structural links: ${r.edges.length}`,`Blueprint annotations: ${blueprintAnnotations.length}`,`Success: ${r.success_count}`,`Errors: ${r.error_count}`,`Analysis findings: ${r.analysis_count}`,`Truncated: ${r.truncated?"YES":"NO"}`,"","FINDINGS"];
  r.findings.forEach(f=>lines.push(`- [${f.severity}] ${f.title}: ${f.detail}${f.path?` @ ${f.path}`:""}`));
  lines.push("","TOP-LEVEL AREAS");r.nodes.forEach(n=>lines.push(`- ${n.name} | ${n.kind} | ${n.health} | ${n.files} files | ${xrayFmtBytes(n.bytes)}`));
  const components=r.components||[];lines.push("","RECOGNIZED COMPONENTS");components.forEach(f=>lines.push(`- ${f.relative_path} | ${f.kind} | ${f.manifest} | ${f.files} files | ${xrayFmtBytes(f.bytes)}`));
  lines.push("","RELATIONS");bpRelations(r).forEach(e=>lines.push(`- ${bpNodeName(e.from)} -> ${bpNodeName(e.to)} [${e.type}] strength=${e.strength} confidence=${e.confidence} dependency=${e.dependency} correlation=${e.correlation} superiority=${e.superiority}${e.note?` note=${e.note}`:""}`));
  return lines.join("\n");
}

window.addEventListener("DOMContentLoaded",()=>{
  loadBlueprintAnnotations();applyVertexLanguage(vertexLanguage);
  xq("rayNavBtn")?.addEventListener("click",()=>xraySwitch("ray"));xq("forgeNavBtn")?.addEventListener("click",()=>xraySwitch("forge"));
  xq("settingsBtn")?.addEventListener("click",()=>xq("settingsPanel")?.classList.toggle("hidden"));xq("settingsCloseBtn")?.addEventListener("click",()=>xq("settingsPanel")?.classList.add("hidden"));
  xq("langJaBtn")?.addEventListener("click",()=>applyVertexLanguage("ja"));xq("langEnBtn")?.addEventListener("click",()=>applyVertexLanguage("en"));
  xq("blueprintAddRelationBtn")?.addEventListener("click",startBlueprintLink);xq("blueprintCancelLinkBtn")?.addEventListener("click",cancelBlueprintLink);
  document.querySelectorAll("[data-relfilter]").forEach(btn=>btn.addEventListener("click",()=>setBlueprintFilter(btn.dataset.relfilter)));
  ["relationStrength","relationConfidence","relationCorrelation","relationSuperiority"].forEach(id=>xq(id)?.addEventListener("input",()=>{const ids={relationStrength:"relationStrengthValue",relationConfidence:"relationConfidenceValue",relationCorrelation:"relationCorrelationValue",relationSuperiority:"relationSuperiorityValue"};xq(ids[id]).textContent=xq(id).value;}));
  xq("relationSaveBtn")?.addEventListener("click",saveActiveRelation);xq("relationDeleteBtn")?.addEventListener("click",deleteActiveRelation);
  xraySwitch("ray");
});


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

