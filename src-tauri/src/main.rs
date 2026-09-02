#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod canonical_registry;
mod clip_relay;
mod flow_rack_bridge;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    fs,
    io::{BufRead, BufReader, Read},
    path::{Component, Path, PathBuf},
    process::{Command, Stdio},
    sync::mpsc,
    time::{SystemTime, UNIX_EPOCH},
};
use tauri::Emitter;
use zip::ZipArchive;

#[cfg(windows)]
use std::os::windows::process::CommandExt;

const DEFAULT_INBOX: &str = r"G:\Vertex_Project\Development\_incoming";
const DEFAULT_ALLOWED_ROOT: &str = r"G:\Vertex_Project\Development";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ArtifactManifest {
    schema_version: String,
    artifact_id: String,
    title: String,
    source: ArtifactSource,
    target: ArtifactTarget,
    authority: String,
    operations: Vec<CopyOperation>,
    #[serde(default)]
    verification: Vec<VerifyCommand>,
    #[serde(default)]
    notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ArtifactSource {
    actor: String,
    model: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ArtifactTarget {
    project_root: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CopyOperation {
    op: String,
    source: String,
    destination: String,
    sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct VerifyCommand {
    program: String,
    #[serde(default)]
    args: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
struct ArtifactSummary {
    path: String,
    artifact_id: String,
    title: String,
    target: String,
    authority: String,
    valid_manifest: bool,
    error: Option<String>,
    applied: bool,
    verified: bool,
    rolled_back: bool,
    latest_stage_id: Option<String>,
    genre: String,
}

#[derive(Debug, Clone, Serialize)]
struct InspectResult {
    path: String,
    manifest: ArtifactManifest,
    payload_count: usize,
    hashes_valid: bool,
    errors: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct StageRecord {
    stage_id: String,
    artifact_path: String,
    stage_dir: String,
    target_root: String,
    backup_dir: String,
    manifest: ArtifactManifest,
}

#[derive(Debug, Clone, Serialize)]
struct StageResult {
    stage_id: String,
    stage_dir: String,
    target_root: String,
    operation_count: usize,
    hashes_valid: bool,
}

#[derive(Debug, Clone, Serialize)]
struct VerifyResult {
    program: String,
    args: Vec<String>,
    success: bool,
    exit_code: Option<i32>,
    stdout: String,
    stderr: String,
}

#[derive(Debug, Clone, Serialize)]
struct ShellStreamEvent {
    stage_id: String,
    command_index: usize,
    command_total: usize,
    stream: String,
    text: String,
    success: Option<bool>,
    exit_code: Option<i32>,
}

#[derive(Debug, Clone, Serialize)]
struct ApplyResult {
    stage_id: String,
    applied_files: Vec<String>,
    backup_dir: String,
    verification: Vec<VerifyResult>,
    verified: bool,
}

fn now_id() -> String {
    let ms = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    ms.to_string()
}

fn receiver_home() -> PathBuf {
    std::env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("."))
        .join("VertexReceiver")
}

fn ensure_dirs() -> Result<(), String> {
    fs::create_dir_all(DEFAULT_INBOX).map_err(|e| format!("create inbox: {e}"))?;
    fs::create_dir_all(receiver_home().join("staging"))
        .map_err(|e| format!("create staging: {e}"))?;
    fs::create_dir_all(receiver_home().join("backups"))
        .map_err(|e| format!("create backups: {e}"))?;
    Ok(())
}

fn is_safe_relative(value: &str) -> bool {
    let path = Path::new(value);
    if path.as_os_str().is_empty() || path.is_absolute() {
        return false;
    }
    !path.components().any(|c| {
        matches!(
            c,
            Component::ParentDir | Component::RootDir | Component::Prefix(_)
        )
    })
}

fn target_allowed(target: &Path) -> bool {
    let allowed = Path::new(DEFAULT_ALLOWED_ROOT);
    target.starts_with(allowed)
}

fn read_manifest_from_archive(path: &Path) -> Result<ArtifactManifest, String> {
    let file = fs::File::open(path).map_err(|e| format!("open artifact: {e}"))?;
    let mut zip = ZipArchive::new(file).map_err(|e| format!("open VRA zip: {e}"))?;
    let mut manifest_file = zip
        .by_name("manifest.json")
        .map_err(|_| "manifest.json not found".to_string())?;
    let mut text = String::new();
    manifest_file
        .read_to_string(&mut text)
        .map_err(|e| format!("read manifest: {e}"))?;
    serde_json::from_str(&text).map_err(|e| format!("parse manifest: {e}"))
}

fn validate_manifest(manifest: &ArtifactManifest) -> Result<(), String> {
    if manifest.schema_version != "vra/1" {
        return Err(format!("unsupported schema {}", manifest.schema_version));
    }
    if manifest.artifact_id.trim().is_empty() {
        return Err("artifact_id is empty".into());
    }
    let target = Path::new(&manifest.target.project_root);
    if !target.is_absolute() {
        return Err("target.project_root must be absolute".into());
    }
    if !target_allowed(target) {
        return Err(format!(
            "target is outside allowed Vertex development root: {}",
            manifest.target.project_root
        ));
    }
    if manifest.authority != "HUMAN_APPLY" {
        return Err("GENESIS accepts authority=HUMAN_APPLY only".into());
    }
    if manifest.operations.is_empty() {
        return Err("artifact contains no operations".into());
    }
    for op in &manifest.operations {
        if op.op != "copy" {
            return Err(format!("unsupported operation: {}", op.op));
        }
        if !is_safe_relative(&op.source) || !is_safe_relative(&op.destination) {
            return Err("operation contains unsafe path".into());
        }
        if !op.source.starts_with("payload/") {
            return Err(format!("source must live under payload/: {}", op.source));
        }
        if op.sha256.len() != 64 || !op.sha256.chars().all(|c| c.is_ascii_hexdigit()) {
            return Err(format!("invalid sha256 for {}", op.source));
        }
    }
    for cmd in &manifest.verification {
        let allowed = ["cargo", "git", "npm", "pnpm", "node", "python", "py"];
        if !allowed.iter().any(|p| *p == cmd.program) {
            return Err(format!("verification program not allowed: {}", cmd.program));
        }
    }
    Ok(())
}

fn hash_bytes(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn inspect_internal(path: &Path) -> Result<InspectResult, String> {
    let manifest = read_manifest_from_archive(path)?;
    let mut errors = Vec::new();
    if let Err(e) = validate_manifest(&manifest) {
        errors.push(e);
    }

    let file = fs::File::open(path).map_err(|e| format!("open artifact: {e}"))?;
    let mut zip = ZipArchive::new(file).map_err(|e| format!("open VRA zip: {e}"))?;

    for op in &manifest.operations {
        match zip.by_name(&op.source) {
            Ok(mut entry) => {
                let mut bytes = Vec::new();
                if let Err(e) = entry.read_to_end(&mut bytes) {
                    errors.push(format!("read {}: {e}", op.source));
                    continue;
                }
                let actual = hash_bytes(&bytes);
                if !actual.eq_ignore_ascii_case(&op.sha256) {
                    errors.push(format!(
                        "hash mismatch {} expected={} actual={}",
                        op.source, op.sha256, actual
                    ));
                }
            }
            Err(_) => errors.push(format!("payload missing: {}", op.source)),
        }
    }

    Ok(InspectResult {
        path: path.display().to_string(),
        payload_count: manifest.operations.len(),
        hashes_valid: errors.is_empty(),
        manifest,
        errors,
    })
}

fn write_stage_record(record: &StageRecord) -> Result<(), String> {
    let path = receiver_home()
        .join("staging")
        .join(&record.stage_id)
        .join("stage.json");
    let text = serde_json::to_string_pretty(record).map_err(|e| e.to_string())?;
    fs::write(path, text).map_err(|e| format!("write stage record: {e}"))
}

fn load_stage_record(stage_id: &str) -> Result<StageRecord, String> {
    if !stage_id
        .chars()
        .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_')
    {
        return Err("invalid stage id".into());
    }
    let path = receiver_home()
        .join("staging")
        .join(stage_id)
        .join("stage.json");
    let text = fs::read_to_string(path).map_err(|e| format!("read stage: {e}"))?;
    serde_json::from_str(&text).map_err(|e| format!("parse stage: {e}"))
}

fn vertex_works_project_root() -> Result<PathBuf, String> {
    let exe = std::env::current_exe().map_err(|e| format!("resolve current exe: {e}"))?;
    let mut cursor = exe
        .parent()
        .map(Path::to_path_buf)
        .ok_or_else(|| "current executable has no parent directory".to_string())?;

    for _ in 0..16 {
        let current = cursor.join("current.json");
        let entry = cursor.join("VertexWorks.exe");
        if current.is_file() && entry.is_file() {
            return Ok(cursor);
        }
        if !cursor.pop() {
            break;
        }
    }

    Err("Vertex Works project root could not be resolved from the active release".into())
}

#[tauri::command]
fn restart_vertex_works(app: tauri::AppHandle) -> Result<(), String> {
    let root = vertex_works_project_root()?;
    let entry = root.join("VertexWorks.exe");

    let mut command = Command::new(&entry);
    command.current_dir(&root);
    suppress_child_console(&mut command);
    command
        .spawn()
        .map_err(|e| format!("restart root launcher {}: {e}", entry.display()))?;

    app.exit(0);
    Ok(())
}

#[tauri::command]
fn receiver_info() -> Result<serde_json::Value, String> {
    ensure_dirs()?;
    Ok(serde_json::json!({
        "product": "VERTEX WORKS",
        "facility": "Artifact Engineering, Verification & Dispatch Facility",
        "version": "0.5.0",
        "inbox": DEFAULT_INBOX,
        "allowed_root": DEFAULT_ALLOWED_ROOT,
        "home": receiver_home().display().to_string(),
        "mode": "HUMAN_APPLY"
    }))
}

#[derive(Debug, Clone, Default)]
struct ArtifactHistoryStatus {
    applied: bool,
    verified: bool,
    rolled_back: bool,
    latest_stage_id: Option<String>,
    latest_modified_ms: u128,
}

fn artifact_history_status(artifact_id: &str) -> ArtifactHistoryStatus {
    let evidence_dir = receiver_home().join("evidence");
    let Ok(entries) = fs::read_dir(&evidence_dir) else {
        return ArtifactHistoryStatus::default();
    };

    let mut latest = ArtifactHistoryStatus::default();

    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().and_then(|e| e.to_str()) != Some("json") {
            continue;
        }

        let Ok(text) = fs::read_to_string(&path) else {
            continue;
        };
        let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) else {
            continue;
        };

        if value.get("artifact_id").and_then(|v| v.as_str()) != Some(artifact_id) {
            continue;
        }

        let modified_ms = entry
            .metadata()
            .ok()
            .and_then(|m| m.modified().ok())
            .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
            .map(|d| d.as_millis())
            .unwrap_or(0);

        if latest.latest_stage_id.is_none() || modified_ms >= latest.latest_modified_ms {
            let rolled_back = value
                .get("rolled_back")
                .and_then(|v| v.as_bool())
                .unwrap_or(false);

            latest = ArtifactHistoryStatus {
                applied: !rolled_back,
                verified: !rolled_back
                    && value
                        .get("verified")
                        .and_then(|v| v.as_bool())
                        .unwrap_or(false),
                rolled_back,
                latest_stage_id: value
                    .get("stage_id")
                    .and_then(|v| v.as_str())
                    .map(str::to_owned),
                latest_modified_ms: modified_ms,
            };
        }
    }

    latest
}

fn mark_evidence_rolled_back(stage_id: &str) -> Result<(), String> {
    let path = receiver_home()
        .join("evidence")
        .join(format!("{stage_id}.json"));

    if !path.exists() {
        return Ok(());
    }

    let text = fs::read_to_string(&path).map_err(|e| format!("read rollback evidence: {e}"))?;
    let mut value: serde_json::Value =
        serde_json::from_str(&text).map_err(|e| format!("parse rollback evidence: {e}"))?;

    value["rolled_back"] = serde_json::Value::Bool(true);
    value["rolled_back_unix_ms"] = serde_json::json!(SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis());

    let updated = serde_json::to_string_pretty(&value).map_err(|e| e.to_string())?;
    fs::write(&path, updated).map_err(|e| format!("write rollback evidence: {e}"))
}

fn artifact_genre(artifact_id: &str, title: &str, target: &str) -> String {
    let id = artifact_id.to_ascii_lowercase();
    let title = title.to_ascii_lowercase();
    let target = target.to_ascii_lowercase();

    if target.contains("vertex_receiver")
        || id.starts_with("vertex-receiver")
        || id.starts_with("vertex-works")
        || id.contains("receiver-")
        || id.starts_with("return-lane")
    {
        return "WORKS".into();
    }

    if id.starts_with("vcell") || target.contains("vertex_cell") && !id.starts_with("vscope") {
        return "vCELL".into();
    }

    if id.starts_with("vscope") || title.contains("vscope") {
        return "vSCOPE".into();
    }

    if id.contains("vxn") || target.contains("vertex_native") {
        return "VXN / NATIVE".into();
    }

    if target.contains("vertex_studio_ai")
        || id.starts_with("vsa")
        || title.contains("vertex studio")
    {
        return "VSA".into();
    }

    "VERTEX".into()
}

#[tauri::command]
fn scan_inbox() -> Result<Vec<ArtifactSummary>, String> {
    ensure_dirs()?;
    let mut out = Vec::new();
    for entry in fs::read_dir(DEFAULT_INBOX).map_err(|e| format!("read inbox: {e}"))? {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let is_vra = path
            .extension()
            .and_then(|e| e.to_str())
            .map(|e| e.eq_ignore_ascii_case("vra"))
            .unwrap_or(false);
        if !is_vra {
            continue;
        }
        match read_manifest_from_archive(&path) {
            Ok(manifest) => {
                let valid = validate_manifest(&manifest).is_ok();
                let err = validate_manifest(&manifest).err();
                let history = artifact_history_status(&manifest.artifact_id);
                let genre = artifact_genre(
                    &manifest.artifact_id,
                    &manifest.title,
                    &manifest.target.project_root,
                );

                out.push(ArtifactSummary {
                    path: path.display().to_string(),
                    artifact_id: manifest.artifact_id,
                    title: manifest.title,
                    target: manifest.target.project_root,
                    authority: manifest.authority,
                    valid_manifest: valid,
                    error: err,
                    applied: history.applied,
                    verified: history.verified,
                    rolled_back: history.rolled_back,
                    latest_stage_id: history.latest_stage_id,
                    genre,
                });
            }
            Err(e) => out.push(ArtifactSummary {
                path: path.display().to_string(),
                artifact_id: "(invalid)".into(),
                title: path
                    .file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .into(),
                target: String::new(),
                authority: String::new(),
                valid_manifest: false,
                error: Some(e),
                applied: false,
                verified: false,
                rolled_back: false,
                latest_stage_id: None,
                genre: "INVALID".into(),
            }),
        }
    }
    out.sort_by(|a, b| {
        a.title
            .to_ascii_lowercase()
            .cmp(&b.title.to_ascii_lowercase())
            .then_with(|| a.artifact_id.cmp(&b.artifact_id))
    });
    Ok(out)
}

#[tauri::command]
fn inspect_artifact(path: String) -> Result<InspectResult, String> {
    let p = PathBuf::from(path);
    inspect_internal(&p)
}

#[tauri::command]
fn stage_artifact(path: String) -> Result<StageResult, String> {
    ensure_dirs()?;
    let artifact_path = PathBuf::from(&path);
    let inspected = inspect_internal(&artifact_path)?;
    if !inspected.errors.is_empty() {
        return Err(format!(
            "artifact validation failed: {}",
            inspected.errors.join(" | ")
        ));
    }

    let stage_id = format!("{}-{}", inspected.manifest.artifact_id, now_id());
    let stage_dir = receiver_home().join("staging").join(&stage_id);
    let payload_dir = stage_dir.join("payload");
    fs::create_dir_all(&payload_dir).map_err(|e| format!("create stage: {e}"))?;

    let file = fs::File::open(&artifact_path).map_err(|e| format!("open artifact: {e}"))?;
    let mut zip = ZipArchive::new(file).map_err(|e| format!("open VRA zip: {e}"))?;

    for op in &inspected.manifest.operations {
        let mut entry = zip
            .by_name(&op.source)
            .map_err(|e| format!("payload missing: {e}"))?;
        let rel = op.source.strip_prefix("payload/").unwrap_or(&op.source);
        if !is_safe_relative(rel) {
            return Err(format!("unsafe payload path: {rel}"));
        }
        let out_path = payload_dir.join(rel);
        if let Some(parent) = out_path.parent() {
            fs::create_dir_all(parent).map_err(|e| format!("create payload dir: {e}"))?;
        }
        let mut out =
            fs::File::create(&out_path).map_err(|e| format!("create staged file: {e}"))?;
        std::io::copy(&mut entry, &mut out).map_err(|e| format!("extract payload: {e}"))?;
    }

    let backup_dir = receiver_home().join("backups").join(&stage_id);
    let record = StageRecord {
        stage_id: stage_id.clone(),
        artifact_path: artifact_path.display().to_string(),
        stage_dir: stage_dir.display().to_string(),
        target_root: inspected.manifest.target.project_root.clone(),
        backup_dir: backup_dir.display().to_string(),
        manifest: inspected.manifest.clone(),
    };
    write_stage_record(&record)?;

    Ok(StageResult {
        stage_id,
        stage_dir: stage_dir.display().to_string(),
        target_root: record.target_root,
        operation_count: record.manifest.operations.len(),
        hashes_valid: true,
    })
}

#[cfg(windows)]
fn suppress_child_console(command: &mut Command) {
    // CREATE_NO_WINDOW
    // Keeps stdout/stderr pipes available to Receiver while preventing
    // cargo/python/git/etc. console windows from flashing on the desktop.
    const CREATE_NO_WINDOW: u32 = 0x08000000;
    command.creation_flags(CREATE_NO_WINDOW);
}

#[cfg(not(windows))]
fn suppress_child_console(_command: &mut Command) {}

fn quote_shell_arg(arg: &str) -> String {
    if arg
        .chars()
        .any(|c| c.is_whitespace() || matches!(c, '"' | '\''))
    {
        format!("\"{}\"", arg.replace('"', "\\\""))
    } else {
        arg.to_string()
    }
}

fn emit_shell(
    app: &tauri::AppHandle,
    stage_id: &str,
    command_index: usize,
    command_total: usize,
    stream: &str,
    text: impl Into<String>,
    success: Option<bool>,
    exit_code: Option<i32>,
) {
    let _ = app.emit(
        "vertex-shell-output",
        ShellStreamEvent {
            stage_id: stage_id.to_string(),
            command_index,
            command_total,
            stream: stream.to_string(),
            text: text.into(),
            success,
            exit_code,
        },
    );
}

fn run_verification(
    app: &tauri::AppHandle,
    stage_id: &str,
    target_root: &Path,
    commands: &[VerifyCommand],
) -> Vec<VerifyResult> {
    let total = commands.len();
    let mut results = Vec::with_capacity(total);

    for (zero_index, cmd) in commands.iter().enumerate() {
        let command_index = zero_index + 1;
        let rendered = std::iter::once(cmd.program.clone())
            .chain(cmd.args.iter().map(|arg| quote_shell_arg(arg)))
            .collect::<Vec<_>>()
            .join(" ");

        emit_shell(
            app,
            stage_id,
            command_index,
            total,
            "command",
            format!("$ {rendered}"),
            None,
            None,
        );

        let mut command = Command::new(&cmd.program);
        command
            .args(&cmd.args)
            .current_dir(target_root)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        suppress_child_console(&mut command);

        let mut child = match command.spawn() {
            Ok(child) => child,
            Err(e) => {
                let error_text = format!("spawn failed: {e}");
                emit_shell(
                    app,
                    stage_id,
                    command_index,
                    total,
                    "stderr",
                    error_text.clone(),
                    Some(false),
                    None,
                );
                results.push(VerifyResult {
                    program: cmd.program.clone(),
                    args: cmd.args.clone(),
                    success: false,
                    exit_code: None,
                    stdout: String::new(),
                    stderr: error_text,
                });
                continue;
            }
        };

        let stdout = child.stdout.take();
        let stderr = child.stderr.take();
        let (tx, rx) = mpsc::channel::<(&'static str, String)>();

        if let Some(stdout) = stdout {
            let tx_stdout = tx.clone();
            std::thread::spawn(move || {
                let mut reader = BufReader::new(stdout);
                let mut bytes = Vec::new();
                loop {
                    bytes.clear();
                    match reader.read_until(b'\n', &mut bytes) {
                        Ok(0) => break,
                        Ok(_) => {
                            while matches!(bytes.last(), Some(b'\n' | b'\r')) {
                                bytes.pop();
                            }
                            let text = String::from_utf8_lossy(&bytes).to_string();
                            if tx_stdout.send(("stdout", text)).is_err() {
                                break;
                            }
                        }
                        Err(e) => {
                            let _ = tx_stdout.send(("stderr", format!("stdout read error: {e}")));
                            break;
                        }
                    }
                }
            });
        }

        if let Some(stderr) = stderr {
            let tx_stderr = tx.clone();
            std::thread::spawn(move || {
                let mut reader = BufReader::new(stderr);
                let mut bytes = Vec::new();
                loop {
                    bytes.clear();
                    match reader.read_until(b'\n', &mut bytes) {
                        Ok(0) => break,
                        Ok(_) => {
                            while matches!(bytes.last(), Some(b'\n' | b'\r')) {
                                bytes.pop();
                            }
                            let text = String::from_utf8_lossy(&bytes).to_string();
                            if tx_stderr.send(("stderr", text)).is_err() {
                                break;
                            }
                        }
                        Err(e) => {
                            let _ = tx_stderr.send(("stderr", format!("stderr read error: {e}")));
                            break;
                        }
                    }
                }
            });
        }

        drop(tx);

        let mut stdout_text = String::new();
        let mut stderr_text = String::new();

        for (stream, line) in rx {
            if stream == "stdout" {
                stdout_text.push_str(&line);
                stdout_text.push('\n');
            } else {
                stderr_text.push_str(&line);
                stderr_text.push('\n');
            }

            emit_shell(
                app,
                stage_id,
                command_index,
                total,
                stream,
                line,
                None,
                None,
            );
        }

        let status = child.wait();
        let (success, exit_code, wait_error) = match status {
            Ok(status) => (status.success(), status.code(), None),
            Err(e) => (false, None, Some(e.to_string())),
        };

        if let Some(error) = wait_error {
            if !stderr_text.is_empty() && !stderr_text.ends_with('\n') {
                stderr_text.push('\n');
            }
            stderr_text.push_str(&format!("wait failed: {error}\n"));
        }

        emit_shell(
            app,
            stage_id,
            command_index,
            total,
            "exit",
            if success {
                format!("PASS / EXIT {}", exit_code.unwrap_or(0))
            } else {
                match exit_code {
                    Some(code) => format!("FAIL / EXIT {code}"),
                    None => "FAIL / EXIT UNKNOWN".to_string(),
                }
            },
            Some(success),
            exit_code,
        );

        results.push(VerifyResult {
            program: cmd.program.clone(),
            args: cmd.args.clone(),
            success,
            exit_code,
            stdout: stdout_text,
            stderr: stderr_text,
        });
    }

    results
}

#[tauri::command]
fn apply_stage(app: tauri::AppHandle, stage_id: String) -> Result<ApplyResult, String> {
    let record = load_stage_record(&stage_id)?;
    validate_manifest(&record.manifest)?;

    let target_root = PathBuf::from(&record.target_root);
    if !target_allowed(&target_root) {
        return Err("target escaped allowed root".into());
    }

    let backup_dir = PathBuf::from(&record.backup_dir);
    fs::create_dir_all(&backup_dir).map_err(|e| format!("create backup: {e}"))?;

    let stage_payload = PathBuf::from(&record.stage_dir).join("payload");
    let mut applied_files = Vec::new();

    for op in &record.manifest.operations {
        let rel_source = op.source.strip_prefix("payload/").unwrap_or(&op.source);
        if !is_safe_relative(rel_source) || !is_safe_relative(&op.destination) {
            return Err("unsafe operation path during apply".into());
        }

        let source = stage_payload.join(rel_source);
        let destination = target_root.join(&op.destination);

        let bytes =
            fs::read(&source).map_err(|e| format!("read staged {}: {e}", source.display()))?;
        let actual = hash_bytes(&bytes);
        if !actual.eq_ignore_ascii_case(&op.sha256) {
            return Err(format!("staged hash changed for {}", op.source));
        }

        if destination.exists() {
            let backup_path = backup_dir.join(&op.destination);
            if let Some(parent) = backup_path.parent() {
                fs::create_dir_all(parent).map_err(|e| format!("create backup parent: {e}"))?;
            }
            fs::copy(&destination, &backup_path)
                .map_err(|e| format!("backup {}: {e}", destination.display()))?;
        }

        if let Some(parent) = destination.parent() {
            fs::create_dir_all(parent).map_err(|e| format!("create destination parent: {e}"))?;
        }

        fs::write(&destination, bytes)
            .map_err(|e| format!("apply {}: {e}", destination.display()))?;
        applied_files.push(destination.display().to_string());
    }

    emit_shell(
        &app,
        &stage_id,
        0,
        record.manifest.verification.len(),
        "system",
        format!(
            "RECEIVER> APPLY {} file(s) → {}",
            applied_files.len(),
            target_root.display()
        ),
        None,
        None,
    );

    let verification =
        run_verification(&app, &stage_id, &target_root, &record.manifest.verification);
    let verified = verification.iter().all(|v| v.success);

    let evidence_dir = receiver_home().join("evidence");
    fs::create_dir_all(&evidence_dir).map_err(|e| format!("create evidence: {e}"))?;
    let result_json = serde_json::to_string_pretty(&serde_json::json!({
        "stage_id": &stage_id,
        "artifact_id": &record.manifest.artifact_id,
        "target": &record.target_root,
        "applied_files": &applied_files,
        "backup_dir": &record.backup_dir,
        "verified": verified,
        "rolled_back": false,
        "verification": &verification,
    }))
    .map_err(|e| e.to_string())?;
    fs::write(
        evidence_dir.join(format!("{}.json", record.stage_id)),
        result_json,
    )
    .map_err(|e| format!("write evidence: {e}"))?;

    Ok(ApplyResult {
        stage_id: record.stage_id,
        applied_files,
        backup_dir: record.backup_dir,
        verification,
        verified,
    })
}

#[tauri::command]
fn rollback_stage(stage_id: String) -> Result<Vec<String>, String> {
    let record = load_stage_record(&stage_id)?;
    let target_root = PathBuf::from(&record.target_root);
    let backup_dir = PathBuf::from(&record.backup_dir);

    let mut restored = Vec::new();
    for op in &record.manifest.operations {
        if !is_safe_relative(&op.destination) {
            return Err("unsafe rollback destination".into());
        }
        let backup = backup_dir.join(&op.destination);
        let destination = target_root.join(&op.destination);

        if backup.exists() {
            if let Some(parent) = destination.parent() {
                fs::create_dir_all(parent).map_err(|e| e.to_string())?;
            }
            fs::copy(&backup, &destination)
                .map_err(|e| format!("restore {}: {e}", destination.display()))?;
            restored.push(destination.display().to_string());
        }
    }
    mark_evidence_rolled_back(&stage_id)?;
    Ok(restored)
}

#[derive(Debug, Clone, Serialize)]
struct XrayNode {
    id: String,
    name: String,
    path: String,
    kind: String,
    files: usize,
    bytes: u64,
    manifest: Option<String>,
    health: String,
}

#[derive(Debug, Clone, Serialize)]
struct XrayFolder {
    id: String,
    name: String,
    path: String,
    relative_path: String,
    parent_id: Option<String>,
    depth: usize,
    files: usize,
    bytes: u64,
    manifest: Option<String>,
    kind: String,
    state: String,
    ignored: bool,
}

#[derive(Debug, Clone, Serialize)]
struct XrayEdge {
    from: String,
    to: String,
    kind: String,
}

#[derive(Debug, Clone, Serialize)]
struct XrayFinding {
    severity: String,
    title: String,
    detail: String,
    path: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
struct XrayReport {
    schema: String,
    root: String,
    generated_ms: u128,
    nodes: Vec<XrayNode>,
    folders: Vec<XrayFolder>,
    edges: Vec<XrayEdge>,
    findings: Vec<XrayFinding>,
    directories_scanned: usize,
    ignored_directories: usize,
    recognized_components: usize,
    files_scanned: usize,
    bytes_scanned: u64,
    success_count: usize,
    error_count: usize,
    analysis_count: usize,
    truncated: bool,
}

fn xray_should_skip(name: &str) -> bool {
    matches!(
        name,
        ".git"
            | "target"
            | "node_modules"
            | ".idea"
            | ".vscode"
            | "__pycache__"
            | ".pytest_cache"
            | ".mypy_cache"
            | ".ruff_cache"
            | ".next"
            | "dist"
    )
}

fn xray_manifest_kind(dir: &Path) -> Option<(&'static str, &'static str)> {
    for (file, kind) in [
        ("Cargo.toml", "RUST"),
        ("package.json", "JS"),
        ("pyproject.toml", "PYTHON"),
        ("requirements.txt", "PYTHON"),
        ("CMakeLists.txt", "CPP"),
        ("go.mod", "GO"),
        ("pom.xml", "JAVA"),
        ("build.gradle", "JAVA"),
        ("build.gradle.kts", "KOTLIN"),
    ] {
        if dir.join(file).exists() {
            return Some((file, kind));
        }
    }
    None
}

fn xray_rel_id(root: &Path, path: &Path) -> String {
    path.strip_prefix(root)
        .unwrap_or(path)
        .components()
        .map(|c| c.as_os_str().to_string_lossy().to_string())
        .collect::<Vec<_>>()
        .join("/")
}

fn xray_scan_dir(
    root: &Path,
    dir: &Path,
    parent_id: Option<String>,
    depth: usize,
    budget: &mut usize,
    folders: &mut Vec<XrayFolder>,
    findings: &mut Vec<XrayFinding>,
    total_files: &mut usize,
    total_bytes: &mut u64,
    ignored_directories: &mut usize,
    truncated: &mut bool,
) -> (usize, u64) {
    let id = xray_rel_id(root, dir);
    let name = dir
        .file_name()
        .map(|v| v.to_string_lossy().to_string())
        .unwrap_or_else(|| id.clone());
    let ignored = xray_should_skip(&name);
    let manifest = xray_manifest_kind(dir);
    let kind = manifest.map(|(_, k)| k).unwrap_or("FOLDER");

    if ignored {
        *ignored_directories += 1;
        folders.push(XrayFolder {
            id,
            name,
            path: dir.display().to_string(),
            relative_path: xray_rel_id(root, dir),
            parent_id,
            depth,
            files: 0,
            bytes: 0,
            manifest: manifest.map(|(m, _)| m.to_string()),
            kind: kind.into(),
            state: "IGNORED_GENERATED".into(),
            ignored: true,
        });
        return (0, 0);
    }

    if *budget == 0 {
        *truncated = true;
        folders.push(XrayFolder {
            id,
            name,
            path: dir.display().to_string(),
            relative_path: xray_rel_id(root, dir),
            parent_id,
            depth,
            files: 0,
            bytes: 0,
            manifest: manifest.map(|(m, _)| m.to_string()),
            kind: kind.into(),
            state: "UNSCANNED_BUDGET".into(),
            ignored: false,
        });
        return (0, 0);
    }

    *budget = budget.saturating_sub(1);
    let mut files = 0usize;
    let mut bytes = 0u64;
    let mut entries = match fs::read_dir(dir) {
        Ok(rd) => {
            let mut v = Vec::new();
            for entry in rd {
                match entry {
                    Ok(e) => v.push(e),
                    Err(e) => findings.push(XrayFinding {
                        severity: "ERROR".into(),
                        title: "Directory entry read failed".into(),
                        detail: e.to_string(),
                        path: Some(dir.display().to_string()),
                    }),
                }
            }
            v
        }
        Err(e) => {
            findings.push(XrayFinding {
                severity: "ERROR".into(),
                title: "Directory read failed".into(),
                detail: e.to_string(),
                path: Some(dir.display().to_string()),
            });
            folders.push(XrayFolder {
                id,
                name,
                path: dir.display().to_string(),
                relative_path: xray_rel_id(root, dir),
                parent_id,
                depth,
                files: 0,
                bytes: 0,
                manifest: manifest.map(|(m, _)| m.to_string()),
                kind: kind.into(),
                state: "READ_ERROR".into(),
                ignored: false,
            });
            return (0, 0);
        }
    };
    entries.sort_by_key(|e| e.file_name().to_string_lossy().to_ascii_lowercase());

    for entry in entries {
        if *budget == 0 {
            *truncated = true;
            break;
        }
        let path = entry.path();
        let file_type = match entry.file_type() {
            Ok(v) => v,
            Err(e) => {
                findings.push(XrayFinding {
                    severity: "ERROR".into(),
                    title: "File type read failed".into(),
                    detail: e.to_string(),
                    path: Some(path.display().to_string()),
                });
                continue;
            }
        };

        if file_type.is_symlink() {
            *budget = budget.saturating_sub(1);
            continue;
        }
        if file_type.is_dir() {
            let child_id = id.clone();
            let (child_files, child_bytes) = xray_scan_dir(
                root,
                &path,
                Some(child_id),
                depth + 1,
                budget,
                folders,
                findings,
                total_files,
                total_bytes,
                ignored_directories,
                truncated,
            );
            files = files.saturating_add(child_files);
            bytes = bytes.saturating_add(child_bytes);
        } else if file_type.is_file() {
            *budget = budget.saturating_sub(1);
            files = files.saturating_add(1);
            *total_files = total_files.saturating_add(1);
            if let Ok(meta) = entry.metadata() {
                bytes = bytes.saturating_add(meta.len());
                *total_bytes = total_bytes.saturating_add(meta.len());
            }
        }
    }

    folders.push(XrayFolder {
        id,
        name,
        path: dir.display().to_string(),
        relative_path: xray_rel_id(root, dir),
        parent_id,
        depth,
        files,
        bytes,
        manifest: manifest.map(|(m, _)| m.to_string()),
        kind: kind.into(),
        state: if *truncated {
            "OBSERVED_PARTIAL"
        } else {
            "OBSERVED"
        }
        .into(),
        ignored: false,
    });
    (files, bytes)
}

fn xray_text_mentions(path: &Path, candidates: &[String]) -> Vec<String> {
    let text = fs::read_to_string(path)
        .unwrap_or_default()
        .to_ascii_lowercase();
    candidates
        .iter()
        .filter(|name| {
            let n = name.to_ascii_lowercase();
            !n.is_empty() && text.contains(&n)
        })
        .cloned()
        .collect()
}

#[tauri::command]
fn xray_scan_project(root: Option<String>) -> Result<XrayReport, String> {
    let root = PathBuf::from(root.unwrap_or_else(|| DEFAULT_ALLOWED_ROOT.to_string()));
    if !root.is_absolute() || !target_allowed(&root) {
        return Err(format!(
            "X-Ray root outside authorized Vertex development root: {}",
            root.display()
        ));
    }
    if !root.exists() {
        return Err(format!("X-Ray root not found: {}", root.display()));
    }

    let mut findings = Vec::<XrayFinding>::new();
    let mut folders = Vec::<XrayFolder>::new();
    let mut total_files = 0usize;
    let mut total_bytes = 0u64;
    let mut ignored_directories = 0usize;
    let mut truncated = false;
    // Source/Evidence trees can be large. Generated dependency/build caches are surfaced
    // as IGNORED_GENERATED folders but are not descended into.
    let mut budget = 500_000usize;

    let mut roots = Vec::new();
    let rd = fs::read_dir(&root).map_err(|e| format!("read X-Ray root: {e}"))?;
    for entry in rd {
        match entry {
            Ok(e) => match e.file_type() {
                Ok(t) if t.is_dir() && !t.is_symlink() => roots.push(e.path()),
                Ok(_) => {}
                Err(err) => findings.push(XrayFinding {
                    severity: "ERROR".into(),
                    title: "Root file type read failed".into(),
                    detail: err.to_string(),
                    path: Some(e.path().display().to_string()),
                }),
            },
            Err(e) => findings.push(XrayFinding {
                severity: "ERROR".into(),
                title: "Root directory entry read failed".into(),
                detail: e.to_string(),
                path: Some(root.display().to_string()),
            }),
        }
    }
    roots.sort_by_key(|p| {
        p.file_name()
            .map(|v| v.to_string_lossy().to_ascii_lowercase())
            .unwrap_or_default()
    });

    for path in roots {
        if budget == 0 {
            truncated = true;
            break;
        }
        let _ = xray_scan_dir(
            &root,
            &path,
            None,
            0,
            &mut budget,
            &mut folders,
            &mut findings,
            &mut total_files,
            &mut total_bytes,
            &mut ignored_directories,
            &mut truncated,
        );
    }

    folders.sort_by(|a, b| a.relative_path.cmp(&b.relative_path));

    // Topology remains intentionally readable: the central map shows top-level areas,
    // while Project Explorer carries the complete recursive folder index.
    let mut nodes = Vec::<XrayNode>::new();
    for folder in folders.iter().filter(|f| f.depth == 0) {
        nodes.push(XrayNode {
            id: folder.id.clone(),
            name: folder.name.clone(),
            path: folder.path.clone(),
            kind: if folder.manifest.is_some() {
                folder.kind.clone()
            } else {
                "AREA".into()
            },
            files: folder.files,
            bytes: folder.bytes,
            manifest: folder.manifest.clone(),
            health: if folder.ignored {
                "IGNORED".into()
            } else if folder.state == "READ_ERROR" {
                "ERROR".into()
            } else if folder.manifest.is_some() {
                "VERIFIED".into()
            } else {
                "OBSERVED".into()
            },
        });
    }

    let top_names: Vec<String> = nodes.iter().map(|n| n.name.clone()).collect();
    let mut edges = Vec::<XrayEdge>::new();
    for node in &nodes {
        let p = PathBuf::from(&node.path);
        let from = node.id.clone();
        let manifest_files = [
            "Cargo.toml",
            "package.json",
            "pyproject.toml",
            "CMakeLists.txt",
            "go.mod",
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
        ];
        let mut seen = std::collections::BTreeSet::new();
        for mf in manifest_files {
            let mp = p.join(mf);
            if !mp.exists() {
                continue;
            }
            for target in xray_text_mentions(&mp, &top_names) {
                if target != node.name && seen.insert(target.clone()) {
                    if let Some(to) = nodes
                        .iter()
                        .find(|n| n.name == target)
                        .map(|n| n.id.clone())
                    {
                        edges.push(XrayEdge {
                            from: from.clone(),
                            to,
                            kind: "DEPENDENCY".into(),
                        });
                    }
                }
            }
        }
    }

    let node_set: std::collections::BTreeSet<String> =
        nodes.iter().map(|n| n.name.clone()).collect();
    for (from, to, kind) in [
        ("vertex_brain_system", "vertex_cell", "RUNTIME"),
        ("vertex_studio_ai", "FLEET_ENGINE", "CONTROL"),
        ("vertex_studio_ai", "NERVE_ENGINE", "FLOW"),
        ("vertex_receiver", "EVIDENCE", "EVIDENCE"),
    ] {
        if node_set.contains(from) && node_set.contains(to) {
            let from_id = nodes
                .iter()
                .find(|n| n.name == from)
                .map(|n| n.id.clone())
                .unwrap_or_else(|| from.into());
            let to_id = nodes
                .iter()
                .find(|n| n.name == to)
                .map(|n| n.id.clone())
                .unwrap_or_else(|| to.into());
            if !edges.iter().any(|e| e.from == from_id && e.to == to_id) {
                edges.push(XrayEdge {
                    from: from_id,
                    to: to_id,
                    kind: kind.into(),
                });
            }
        }
    }

    let recognized_components = folders
        .iter()
        .filter(|f| f.manifest.is_some() && !f.ignored)
        .count();
    let scanned_directories = folders.iter().filter(|f| !f.ignored).count();

    findings.push(XrayFinding {
        severity: "SUCCESS".into(),
        title: "Recursive Project tree indexed".into(),
        detail: format!(
            "Indexed {} visible folders recursively; {} generated/cache folders are surfaced but not descended into.",
            folders.len(), ignored_directories
        ),
        path: Some(root.display().to_string()),
    });
    findings.push(XrayFinding {
        severity: "INFO".into(),
        title: "Manifest-bearing components".into(),
        detail: format!(
            "Detected {} build/runtime component roots across the recursive Vertex Project tree.",
            recognized_components
        ),
        path: None,
    });
    if ignored_directories > 0 {
        findings.push(XrayFinding {
            severity: "INFO".into(),
            title: "Generated/cache boundaries".into(),
            detail: format!(
                "{} generated/cache directories are visible in Project Explorer with IGNORED status; X-Ray does not descend into their contents.",
                ignored_directories
            ),
            path: None,
        });
    }
    if truncated {
        findings.push(XrayFinding {
            severity: "WARN".into(),
            title: "X-Ray entry budget reached".into(),
            detail: "The 500,000-entry safety budget was reached. The folder tree marks the scan as partial; no project data was changed.".into(),
            path: Some(root.display().to_string()),
        });
    }
    if edges.is_empty() {
        findings.push(XrayFinding {
            severity: "INFO".into(),
            title: "Sparse top-level dependency surface".into(),
            detail: "No direct top-level local references were found in recognized manifests. Recursive folder/component indexing is still complete within the scan budget.".into(),
            path: None,
        });
    }
    findings.push(XrayFinding {
        severity: "SUCCESS".into(),
        title: "Project X-Ray completed".into(),
        detail: format!(
            "Observed {} top-level areas, {} folders, {} files, {} recognized components and {} top-level structural links without mutating the project.",
            nodes.len(),
            folders.len(),
            total_files,
            recognized_components,
            edges.len()
        ),
        path: Some(root.display().to_string()),
    });

    let error_count = findings.iter().filter(|f| f.severity == "ERROR").count();
    let analysis_count = findings.len();
    Ok(XrayReport {
        schema: "vertex.works.project-xray.v1.1".into(),
        root: root.display().to_string(),
        generated_ms: SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis(),
        nodes,
        folders,
        edges,
        findings,
        directories_scanned: scanned_directories,
        ignored_directories,
        recognized_components,
        files_scanned: total_files,
        bytes_scanned: total_bytes,
        success_count: recognized_components,
        error_count,
        analysis_count,
        truncated,
    })
}

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

fn main() {
    if let Err(e) = clip_relay::start() {
        eprintln!("Vertex Clip Relay init warning: {e}");
    }

    if let Err(e) = ensure_dirs() {
        eprintln!("Vertex vCELL Receiver init warning: {e}");
    }

    tauri::Builder::default()
        .manage(flow_rack_bridge::FlowRackBridgeState::default())
        .invoke_handler(tauri::generate_handler![
            flow_rack_bridge::flow_rack_snapshot,
            flow_rack_bridge::flow_rack_execute,
            flow_rack_bridge::flow_rack_runtime_probe,
            flow_rack_bridge::flow_rack_runtime_probe_finalize,
            canonical_registry::canonical_registry_list,
            canonical_registry::canonical_registry_upsert,
            canonical_registry::canonical_registry_delete,
            canonical_registry::canonical_registry_language_pack,
            clip_relay_set_priority,
            clip_relay_status,
            xray_scope,
            xray_resolve_scope,
            restart_vertex_works,
            receiver_info,
            scan_inbox,
            inspect_artifact,
            stage_artifact,
            apply_stage,
            rollback_stage,
            xray_scan_project
        ])
        .run(tauri::generate_context!())
        .expect("error while running Vertex Receiver");
}

// VERTEX_WORKS_SCOPED_XRAY_050_BEGIN
#[derive(Debug, Clone, Serialize)]
struct ScopedXrayFinding {
    severity: String,
    title: String,
    detail: String,
    path: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
struct ScopedSourceAnchor {
    path: String,
    line: usize,
    kind: String,
    text: String,
}

#[derive(Debug, Clone, Serialize)]
struct ScopedRecentFile {
    path: String,
    bytes: u64,
    modified_unix_ms: u128,
}

#[derive(Debug, Clone, Serialize)]
struct ScopedXrayResult {
    schema: &'static str,
    scope: String,
    mode: String,
    kind: String,
    manifest: Option<String>,
    version: Option<String>,
    directories_scanned: usize,
    ignored_directories: usize,
    recognized_components: usize,
    files: usize,
    source_files: usize,
    bytes: u64,
    executables: Vec<String>,
    findings: Vec<ScopedXrayFinding>,
    source_anchors: Vec<ScopedSourceAnchor>,
    recent_files: Vec<ScopedRecentFile>,
    fingerprint: String,
    report: String,
    vera_handoff: String,
    truncated: bool,
    mutation: bool,
}

fn scoped_skip_name(name: &str) -> bool {
    matches!(
        name.to_ascii_lowercase().as_str(),
        ".git"
            | ".svn"
            | ".hg"
            | "target"
            | "node_modules"
            | "__pycache__"
            | ".pytest_cache"
            | ".mypy_cache"
            | ".ruff_cache"
            | ".cache"
            | ".next"
            | ".nuxt"
            | ".vite"
            | "dist"
            | "build"
            | "out"
            | ".venv"
            | "venv"
    )
}

fn scoped_source_extension(path: &Path) -> bool {
    matches!(
        path.extension()
            .and_then(|v| v.to_str())
            .unwrap_or_default()
            .to_ascii_lowercase()
            .as_str(),
        "rs" | "js"
            | "mjs"
            | "cjs"
            | "ts"
            | "tsx"
            | "jsx"
            | "vue"
            | "html"
            | "css"
            | "scss"
            | "py"
            | "ps1"
            | "toml"
            | "json"
            | "yaml"
            | "yml"
            | "md"
            | "txt"
            | "xml"
            | "sql"
            | "cpp"
            | "cc"
            | "c"
            | "h"
            | "hpp"
            | "cs"
            | "java"
            | "kt"
            | "go"
    )
}

fn scoped_manifest_info(dir: &Path) -> (Option<String>, String, Option<String>) {
    let manifests = [
        ("Cargo.toml", "RUST"),
        ("package.json", "JS"),
        ("pyproject.toml", "PYTHON"),
        ("requirements.txt", "PYTHON"),
        ("CMakeLists.txt", "CPP"),
        ("go.mod", "GO"),
        ("pom.xml", "JAVA"),
        ("build.gradle", "JAVA"),
        ("build.gradle.kts", "KOTLIN"),
    ];

    for (file, kind) in manifests {
        let path = dir.join(file);
        if !path.exists() {
            continue;
        }

        let version = if file == "Cargo.toml" {
            fs::read_to_string(&path).ok().and_then(|text| {
                text.lines()
                    .map(str::trim)
                    .find(|line| line.starts_with("version") && line.contains('='))
                    .and_then(|line| line.split_once('='))
                    .map(|(_, value)| value.trim().trim_matches('"').to_string())
            })
        } else if file == "package.json" {
            fs::read_to_string(&path)
                .ok()
                .and_then(|text| serde_json::from_str::<serde_json::Value>(&text).ok())
                .and_then(|value| {
                    value
                        .get("version")
                        .and_then(|v| v.as_str())
                        .map(str::to_string)
                })
        } else {
            None
        };

        return (Some(file.to_string()), kind.to_string(), version);
    }

    (None, "AREA".into(), None)
}

fn scoped_anchor_kind(line: &str) -> Option<&'static str> {
    let l = line.to_ascii_lowercase();
    if l.contains("#[tauri::command]") || l.contains("generate_handler!") {
        Some("TAURI")
    } else if l.contains("struct ") || l.contains("enum ") || l.contains("interface ") {
        Some("TYPE")
    } else if l.contains("fn ")
        || l.contains("function ")
        || l.contains("async function ")
        || l.contains("=>")
    {
        Some("FUNCTION")
    } else if l.contains("invoke(") || l.contains("nativeinvoke") {
        Some("IPC")
    } else if l.contains("clip to vera") || l.contains("clipboard") {
        Some("HANDOFF")
    } else if l.contains("x-ray") || l.contains("xray") {
        Some("XRAY")
    } else if l.contains("version") || l.contains("runtime") || l.contains("manifest") {
        Some("CONTRACT")
    } else if l.contains("error")
        || l.contains("warning")
        || l.contains("todo")
        || l.contains("fixme")
    {
        Some("ATTENTION")
    } else {
        None
    }
}

fn scoped_relative(root: &Path, path: &Path) -> String {
    path.strip_prefix(root)
        .unwrap_or(path)
        .display()
        .to_string()
}

fn scoped_is_executable(path: &Path) -> bool {
    path.extension()
        .and_then(|v| v.to_str())
        .map(|v| v.eq_ignore_ascii_case("exe"))
        .unwrap_or(false)
}

fn scoped_collect_local_path_refs(manifest: &Path, findings: &mut Vec<ScopedXrayFinding>) {
    let Ok(text) = fs::read_to_string(manifest) else {
        return;
    };
    for line in text.lines().map(str::trim) {
        if line.contains("path") && line.contains('=') && line.contains('"') {
            findings.push(ScopedXrayFinding {
                severity: "INFO".into(),
                title: "Local dependency / path relation".into(),
                detail: line.chars().take(240).collect(),
                path: Some(manifest.display().to_string()),
            });
            if findings.len() >= 24 {
                break;
            }
        }
    }
}

fn scoped_scan(scope: &Path, mode: &str) -> Result<ScopedXrayResult, String> {
    let deep = mode.eq_ignore_ascii_case("DEEP");
    let dir_budget = if deep { 30_000usize } else { 12_000usize };
    let file_budget = if deep { 150_000usize } else { 50_000usize };
    let anchor_budget = if deep { 72usize } else { 32usize };

    let (manifest, kind, version) = scoped_manifest_info(scope);
    let mut findings = Vec::<ScopedXrayFinding>::new();
    let mut source_anchors = Vec::<ScopedSourceAnchor>::new();
    let mut recent_files = Vec::<ScopedRecentFile>::new();
    let mut executables = Vec::<String>::new();

    let mut directories_scanned = 0usize;
    let mut ignored_directories = 0usize;
    let mut recognized_components = 0usize;
    let mut files = 0usize;
    let mut source_files = 0usize;
    let mut bytes = 0u64;
    let mut truncated = false;

    let mut stack = vec![scope.to_path_buf()];

    while let Some(dir) = stack.pop() {
        if directories_scanned >= dir_budget || files >= file_budget {
            truncated = true;
            break;
        }
        directories_scanned += 1;

        let (dir_manifest, _, _) = scoped_manifest_info(&dir);
        if dir_manifest.is_some() {
            recognized_components += 1;
            if let Some(m) = dir_manifest {
                scoped_collect_local_path_refs(&dir.join(m), &mut findings);
            }
        }

        let mut entries = match fs::read_dir(&dir) {
            Ok(rd) => rd.filter_map(Result::ok).collect::<Vec<_>>(),
            Err(e) => {
                findings.push(ScopedXrayFinding {
                    severity: "ERROR".into(),
                    title: "Directory read failed".into(),
                    detail: e.to_string(),
                    path: Some(dir.display().to_string()),
                });
                continue;
            }
        };
        entries.sort_by_key(|e| e.file_name().to_string_lossy().to_ascii_lowercase());

        for entry in entries {
            let path = entry.path();
            let Ok(ft) = entry.file_type() else {
                continue;
            };

            if ft.is_dir() {
                let name = entry.file_name().to_string_lossy().to_string();
                if scoped_skip_name(&name) {
                    ignored_directories += 1;
                    continue;
                }
                stack.push(path);
                continue;
            }

            if !ft.is_file() {
                continue;
            }

            files += 1;
            if files > file_budget {
                truncated = true;
                break;
            }

            let meta = entry.metadata().ok();
            let file_bytes = meta.as_ref().map(|m| m.len()).unwrap_or(0);
            bytes = bytes.saturating_add(file_bytes);

            let modified_unix_ms = meta
                .and_then(|m| m.modified().ok())
                .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
                .map(|d| d.as_millis())
                .unwrap_or(0);

            recent_files.push(ScopedRecentFile {
                path: scoped_relative(scope, &path),
                bytes: file_bytes,
                modified_unix_ms,
            });

            if scoped_is_executable(&path) {
                executables.push(scoped_relative(scope, &path));
            }

            if !scoped_source_extension(&path) {
                continue;
            }
            source_files += 1;

            if source_anchors.len() >= anchor_budget || file_bytes > 1_500_000 {
                continue;
            }

            let Ok(text) = fs::read_to_string(&path) else {
                continue;
            };

            for (idx, raw) in text.lines().enumerate() {
                if source_anchors.len() >= anchor_budget {
                    break;
                }
                let line = raw.trim();
                if line.len() < 3 {
                    continue;
                }
                if let Some(anchor_kind) = scoped_anchor_kind(line) {
                    source_anchors.push(ScopedSourceAnchor {
                        path: scoped_relative(scope, &path),
                        line: idx + 1,
                        kind: anchor_kind.into(),
                        text: line.chars().take(260).collect(),
                    });
                }
            }
        }
    }

    recent_files.sort_by(|a, b| b.modified_unix_ms.cmp(&a.modified_unix_ms));
    recent_files.truncate(if deep { 32 } else { 18 });
    executables.sort();
    executables.dedup();
    executables.truncate(24);

    findings.insert(
        0,
        ScopedXrayFinding {
            severity: "SUCCESS".into(),
            title: "Scoped X-Ray completed".into(),
            detail: format!(
                "Observed {} directories and {} files inside selected scope without mutating the project.",
                directories_scanned, files
            ),
            path: Some(scope.display().to_string()),
        },
    );

    findings.push(ScopedXrayFinding {
        severity: "INFO".into(),
        title: "Generated/cache boundaries".into(),
        detail: format!(
            "{} generated/cache directories were ignored during scoped traversal.",
            ignored_directories
        ),
        path: None,
    });

    if !executables.is_empty() {
        findings.push(ScopedXrayFinding {
            severity: "SUCCESS".into(),
            title: "Executable build artifacts found".into(),
            detail: format!(
                "{} executable artifact(s) visible in selected scope.",
                executables.len()
            ),
            path: None,
        });
    }

    if truncated {
        findings.push(ScopedXrayFinding {
            severity: "WARNING".into(),
            title: "Scoped scan budget reached".into(),
            detail: "The report is valid but partial. Use DEEP X-RAY or a narrower folder for more detail.".into(),
            path: Some(scope.display().to_string()),
        });
    }

    let mut report = String::new();
    report.push_str("VERTEX WORKS — VERTEX RAY / SCOPED X-RAY REPORT\n");
    report.push_str(&format!("Scope: {}\n", scope.display()));
    report.push_str(&format!(
        "Mode: {}\n",
        if deep { "DEEP" } else { "STANDARD" }
    ));
    report.push_str("Authority: READ ONLY\n");
    report.push_str("Mutation: NONE\n");
    report.push_str(&format!("Kind: {}\n", kind));
    report.push_str(&format!(
        "Manifest: {}\n",
        manifest.clone().unwrap_or_else(|| "NONE".into())
    ));
    report.push_str(&format!(
        "Version: {}\n",
        version.clone().unwrap_or_else(|| "UNKNOWN".into())
    ));
    report.push_str(&format!("Directories scanned: {}\n", directories_scanned));
    report.push_str(&format!(
        "Ignored generated/cache: {}\n",
        ignored_directories
    ));
    report.push_str(&format!(
        "Recognized components: {}\n",
        recognized_components
    ));
    report.push_str(&format!("Files: {}\n", files));
    report.push_str(&format!("Source-like files: {}\n", source_files));
    report.push_str(&format!("Bytes: {}\n", bytes));
    report.push_str(&format!(
        "Truncated: {}\n",
        if truncated { "YES" } else { "NO" }
    ));

    report.push_str("\nFINDINGS\n");
    for finding in &findings {
        report.push_str(&format!(
            "- [{}] {}: {}{}\n",
            finding.severity,
            finding.title,
            finding.detail,
            finding
                .path
                .as_ref()
                .map(|p| format!(" @ {p}"))
                .unwrap_or_default()
        ));
    }

    report.push_str("\nEXECUTABLES\n");
    if executables.is_empty() {
        report.push_str("- NONE OBSERVED\n");
    } else {
        for exe in &executables {
            report.push_str(&format!("- {exe}\n"));
        }
    }

    report.push_str("\nRECENT FILES\n");
    for item in &recent_files {
        report.push_str(&format!(
            "- {} | {} bytes | modified_ms={}\n",
            item.path, item.bytes, item.modified_unix_ms
        ));
    }

    report.push_str("\nIMPORTANT SOURCE ANCHORS\n");
    if source_anchors.is_empty() {
        report.push_str("- NONE OBSERVED\n");
    } else {
        for anchor in &source_anchors {
            report.push_str(&format!(
                "- [{}] {}:{} | {}\n",
                anchor.kind, anchor.path, anchor.line, anchor.text
            ));
        }
    }

    let fingerprint = hash_bytes(report.as_bytes());

    report.push_str("\nVERA HANDOFF\n");
    report.push_str(&format!("Scope fingerprint: {fingerprint}\n"));
    report.push_str(
        "Use this report as the observed current state of the selected Vertex Project scope.\n",
    );
    report.push_str("Do not infer unobserved runtime state; FACT entries and source anchors are the evidence surface.\n");

    let vera_handoff = format!(
        "VERTEX WORKS — VERTEX RAY / VERA HANDOFF CAPSULE\n\
         Scope: {}\n\
         Mode: {}\n\
         Fingerprint: {}\n\
         ReadOnly: true\n\
         Mutation: false\n\n{}",
        scope.display(),
        if deep { "DEEP" } else { "STANDARD" },
        fingerprint,
        report
    );

    Ok(ScopedXrayResult {
        schema: "vertex.works.scoped-xray.v1",
        scope: scope.display().to_string(),
        mode: if deep {
            "DEEP".into()
        } else {
            "STANDARD".into()
        },
        kind,
        manifest,
        version,
        directories_scanned,
        ignored_directories,
        recognized_components,
        files,
        source_files,
        bytes,
        executables,
        findings,
        source_anchors,
        recent_files,
        fingerprint,
        report,
        vera_handoff,
        truncated,
        mutation: false,
    })
}

fn scoped_allowed_path(path: &Path) -> Result<PathBuf, String> {
    if !path.is_absolute() {
        return Err("Scoped X-Ray target must be an absolute path".into());
    }

    let allowed = fs::canonicalize(DEFAULT_ALLOWED_ROOT)
        .map_err(|e| format!("canonicalize allowed root: {e}"))?;
    let target = fs::canonicalize(path).map_err(|e| format!("canonicalize scope: {e}"))?;

    if !target.starts_with(&allowed) {
        return Err("Scoped X-Ray target is outside the allowed Vertex development root".into());
    }
    if !target.is_dir() {
        return Err("Scoped X-Ray currently accepts folders only".into());
    }
    Ok(target)
}

#[tauri::command]
fn xray_scope(path: String, mode: Option<String>) -> Result<ScopedXrayResult, String> {
    let target = scoped_allowed_path(Path::new(&path))?;
    scoped_scan(&target, mode.as_deref().unwrap_or("STANDARD"))
}

fn scoped_label_tokens(label: &str) -> Vec<String> {
    label
        .lines()
        .flat_map(|line| line.split(|c: char| c.is_whitespace() || c == '|' || c == '·'))
        .map(|v| v.trim_matches(|c: char| !c.is_alphanumeric() && c != '_' && c != '-' && c != '.'))
        .filter(|v| v.len() >= 2)
        .map(str::to_string)
        .collect()
}

fn scoped_find_candidates(label: &str) -> Vec<PathBuf> {
    let tokens = scoped_label_tokens(label);
    let mut wanted = tokens.first().cloned().unwrap_or_default();
    if wanted.is_empty() {
        wanted = label.trim().to_string();
    }

    let root = PathBuf::from(DEFAULT_ALLOWED_ROOT);
    let mut stack = vec![root];
    let mut out = Vec::<PathBuf>::new();
    let mut seen = 0usize;

    while let Some(dir) = stack.pop() {
        seen += 1;
        if seen > 20_000 || out.len() >= 64 {
            break;
        }

        let Ok(rd) = fs::read_dir(&dir) else {
            continue;
        };

        for entry in rd.filter_map(Result::ok) {
            let Ok(ft) = entry.file_type() else {
                continue;
            };
            if !ft.is_dir() {
                continue;
            }

            let path = entry.path();
            let name = entry.file_name().to_string_lossy().to_string();
            if scoped_skip_name(&name) {
                continue;
            }

            if name.eq_ignore_ascii_case(&wanted)
                || tokens.iter().any(|t| name.eq_ignore_ascii_case(t))
            {
                out.push(path.clone());
            }
            stack.push(path);
        }
    }
    out
}

#[tauri::command]
fn xray_resolve_scope(label: String, hints: Vec<String>) -> Result<String, String> {
    let raw = label.trim();
    if raw.is_empty() {
        return Err("No folder label was detected under the pointer".into());
    }

    let path_candidate = PathBuf::from(raw);
    if path_candidate.is_absolute() {
        return Ok(scoped_allowed_path(&path_candidate)?.display().to_string());
    }

    let mut candidates = scoped_find_candidates(raw);
    if candidates.is_empty() {
        return Err(format!(
            "No folder matching '{raw}' was found under the Vertex development root"
        ));
    }
    if candidates.len() == 1 {
        return Ok(candidates.remove(0).display().to_string());
    }

    let hint_tokens = hints
        .iter()
        .flat_map(|h| scoped_label_tokens(h))
        .filter(|h| h.len() >= 3)
        .map(|h| h.to_ascii_lowercase())
        .collect::<Vec<_>>();

    let mut scored = candidates
        .into_iter()
        .map(|path| {
            let p = path.display().to_string().to_ascii_lowercase();
            let score = hint_tokens
                .iter()
                .filter(|h| p.contains(h.as_str()))
                .count();
            (score, path)
        })
        .collect::<Vec<_>>();

    scored.sort_by(|a, b| {
        b.0.cmp(&a.0)
            .then_with(|| a.1.as_os_str().len().cmp(&b.1.as_os_str().len()))
    });

    if scored.len() == 1 || scored[0].0 > scored[1].0 {
        return Ok(scored.remove(0).1.display().to_string());
    }

    Err(format!(
        "Folder label '{raw}' is ambiguous. Right-click a row that exposes its path or a more specific folder."
    ))
}
// VERTEX_WORKS_SCOPED_XRAY_050_END

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_parent_directory_escape() {
        assert!(!is_safe_relative("../evil.txt"));
        assert!(!is_safe_relative(r"..\evil.txt"));
    }

    #[test]
    fn accepts_normal_relative_paths() {
        assert!(is_safe_relative("src/main.rs"));
        assert!(is_safe_relative("nested/file.txt"));
    }

    #[test]
    fn hash_is_sha256_length() {
        assert_eq!(hash_bytes(b"vertex").len(), 64);
    }

    #[test]
    fn classifies_works_before_other_keywords() {
        assert_eq!(
            artifact_genre(
                "vertex-receiver-incoming-sort-000025",
                "Vertex Receiver",
                r"G:\Vertex_Project\Development\vertex_works"
            ),
            "WORKS"
        );
    }

    #[test]
    fn classifies_vcell_family_from_artifact_id() {
        assert_eq!(
            artifact_genre(
                "vcell-zero-churn-flow-000013-vscope-000130",
                "vCELL + vSCOPE",
                r"G:\Vertex_Project\Development"
            ),
            "vCELL"
        );
    }

    #[test]
    fn classifies_vscope_when_it_is_the_artifact_family() {
        assert_eq!(
            artifact_genre(
                "vscope-adaptive-focus-000001-live-000120",
                "vSCOPE Adaptive Focus",
                r"G:\Vertex_Project\Development"
            ),
            "vSCOPE"
        );
    }
}
