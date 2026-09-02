use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::State;

use vertex_vlac_flow_rack::{FlowRack, JobCard, JobState, LockMode, LockRequest, LockScope};
use vertex_vlac_types::{
    AccessContext, ActorIdentity, ActorKind, CommandDecision, CommandRequest, Permission,
    ProductIdentity, SessionIdentity, SessionLifecycle, TransportKind,
};
use vertex_vlac_works_unit::{
    execute, registry_with_works_flow, BindingError, DomainOutcome, WorksFlowCommand, WorksOutput,
};

const RUNTIME_PROBE_EVIDENCE: &str = r"G:\Vertex_Project\Development\vertex_llm_access_connector\docs\evidence\RUNTIME_000017_LIVE.json";

#[derive(Debug, Default)]
pub struct FlowRackBridgeState {
    rack: Mutex<FlowRack>,
    runtime_probe: Mutex<Option<RuntimeProbeContext>>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct FlowRackIntent {
    pub source: String,
    pub command: String,
    #[serde(default)]
    pub payload: Value,
    pub correlation_id: Option<String>,
    pub reason: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct FlowRackJobView {
    pub id: String,
    pub title: String,
    pub state: String,
    pub actor_id: Option<String>,
    pub wait_reason: Option<String>,
    pub correlation_id: Option<String>,
    pub lock_mode: Option<String>,
    pub lock_scope: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct FlowRackSnapshot {
    pub source: String,
    pub running: Vec<FlowRackJobView>,
    pub queue: Vec<FlowRackJobView>,
    pub held: Vec<FlowRackJobView>,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct FlowRackBridgeResult {
    pub decision: String,
    pub message: Option<String>,
    pub domain: String,
    pub correlation_id: Option<String>,
    pub snapshot: FlowRackSnapshot,
}

#[derive(Debug, Clone)]
struct ActorProfile {
    id: &'static str,
    kind: ActorKind,
    permission: Permission,
}

#[derive(Debug, Clone)]
struct RuntimeProbeContext {
    run_id: String,
    human_job: String,
    vera_job: String,
    order_after_vera_move: Vec<String>,
    order_after_human_move: Vec<String>,
    human_audit: bool,
    vera_audit: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct RuntimeProbeStart {
    pub run_id: String,
    pub human_job: String,
    pub vera_job: String,
    pub order_after_vera_move: Vec<String>,
    pub order_after_human_move: Vec<String>,
    pub human_audit: bool,
    pub vera_audit: bool,
    pub display_snapshot: FlowRackSnapshot,
}

#[derive(Debug, Clone, Deserialize)]
pub struct RuntimeProbeUiAck {
    pub run_id: String,
    pub root_present: bool,
    pub source_live_native: bool,
    pub human_card_present: bool,
    pub vera_card_present: bool,
    pub rendered_card_count: usize,
}

#[derive(Debug, Clone, Serialize)]
pub struct RuntimeProbeEvidence {
    pub artifact: String,
    pub works_version: String,
    pub run_id: String,
    pub timestamp: String,
    pub webview_to_tauri: bool,
    pub rust_state_owner: bool,
    pub human_audit: bool,
    pub vera_audit: bool,
    pub order_after_vera_move: Vec<String>,
    pub order_after_human_move: Vec<String>,
    pub ui_root_present: bool,
    pub ui_source_live_native: bool,
    pub ui_human_card_present: bool,
    pub ui_vera_card_present: bool,
    pub ui_rendered_card_count: usize,
    pub cleanup_empty: bool,
    pub result: String,
    pub cleanup_snapshot: FlowRackSnapshot,
}

fn actor_profile(source: &str) -> Result<ActorProfile, String> {
    match source {
        "HUMAN_UI" => Ok(ActorProfile {
            id: "human-local",
            kind: ActorKind::Human,
            permission: Permission::Admin,
        }),
        "VERA_LOCAL" => Ok(ActorProfile {
            id: "vera",
            kind: ActorKind::Vera,
            permission: Permission::Control,
        }),
        "SERVICE_LOCAL" => Ok(ActorProfile {
            id: "works-service",
            kind: ActorKind::Service,
            permission: Permission::Control,
        }),
        other => Err(format!("unsupported local Flow Rack actor source: {other}")),
    }
}

fn now_stamp() -> String {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis().to_string())
        .unwrap_or_else(|_| "0".into())
}

fn runtime_dir() -> PathBuf {
    std::env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir)
        .join("VertexReceiver")
        .join("runtime")
}

fn runtime_probe_request_path() -> PathBuf {
    runtime_dir().join("flow_rack_runtime_probe_000017.request")
}

fn runtime_probe_local_evidence_path() -> PathBuf {
    runtime_dir().join("flow_rack_runtime_probe_000017.json")
}

fn request_for(intent: &FlowRackIntent, profile: &ActorProfile) -> CommandRequest {
    let correlation_id = intent
        .correlation_id
        .clone()
        .or_else(|| Some(format!("flow:{}", now_stamp())));
    let session_id = format!("works:{}:local", profile.id);

    CommandRequest {
        command_id: format!("cmd:{}:{}:{}", profile.id, intent.command, now_stamp()),
        actor: ActorIdentity {
            id: profile.id.into(),
            kind: profile.kind,
            display_name: None,
        },
        session_id: session_id.clone(),
        capability: "flow.queue".into(),
        command: intent.command.clone(),
        reason: intent.reason.clone(),
        correlation_id,
    }
}

fn access_for(request: &CommandRequest, profile: &ActorProfile) -> AccessContext {
    AccessContext {
        session: SessionIdentity {
            session_id: request.session_id.clone(),
            actor_id: request.actor.id.clone(),
            source_product: ProductIdentity {
                product_id: "vertex_works".into(),
                instance_id: "local".into(),
                version: "0.5.0".into(),
            },
            lifecycle: SessionLifecycle::Active,
        },
        granted_permission: profile.permission,
        transport: TransportKind::Native,
    }
}

fn payload_string(payload: &Value, key: &str) -> Result<String, String> {
    payload
        .get(key)
        .and_then(Value::as_str)
        .map(str::to_owned)
        .ok_or_else(|| format!("missing string payload field: {key}"))
}

fn payload_usize(payload: &Value, key: &str) -> Result<usize, String> {
    payload
        .get(key)
        .and_then(Value::as_u64)
        .and_then(|value| usize::try_from(value).ok())
        .ok_or_else(|| format!("missing integer payload field: {key}"))
}

fn parse_lock_mode(value: &str) -> Result<LockMode, String> {
    match value.to_ascii_lowercase().as_str() {
        "read" => Ok(LockMode::Read),
        "write" => Ok(LockMode::Write),
        other => Err(format!("unsupported lock mode: {other}")),
    }
}

fn parse_locks(payload: &Value) -> Result<Vec<LockRequest>, String> {
    let Some(items) = payload.get("locks").and_then(Value::as_array) else {
        return Ok(Vec::new());
    };

    items
        .iter()
        .map(|item| {
            let project = payload_string(item, "project")?;
            let mode = parse_lock_mode(&payload_string(item, "mode")?)?;
            let scope = match item.get("path").and_then(Value::as_str) {
                Some(path) if !path.is_empty() => LockScope::path(project, path.to_owned()),
                _ => LockScope::project(project),
            };
            Ok(LockRequest { scope, mode })
        })
        .collect()
}

fn typed_command(intent: &FlowRackIntent) -> Result<WorksFlowCommand, String> {
    match intent.command.as_str() {
        "queue.list" => Ok(WorksFlowCommand::List),
        "job.inspect" => Ok(WorksFlowCommand::Inspect {
            job_id: payload_string(&intent.payload, "job_id")?,
        }),
        "queue.insert" => Ok(WorksFlowCommand::Insert {
            job_id: payload_string(&intent.payload, "job_id")?,
            title: intent
                .payload
                .get("title")
                .and_then(Value::as_str)
                .unwrap_or("UNTITLED")
                .to_owned(),
            locks: parse_locks(&intent.payload)?,
            at: intent
                .payload
                .get("at")
                .and_then(Value::as_u64)
                .and_then(|value| usize::try_from(value).ok()),
        }),
        "queue.move" => Ok(WorksFlowCommand::Move {
            job_id: payload_string(&intent.payload, "job_id")?,
            to_index: payload_usize(&intent.payload, "to_index")?,
        }),
        "queue.hold" => Ok(WorksFlowCommand::Hold {
            job_id: payload_string(&intent.payload, "job_id")?,
        }),
        "queue.resume" => Ok(WorksFlowCommand::Resume {
            job_id: payload_string(&intent.payload, "job_id")?,
        }),
        "queue.cancel" => Ok(WorksFlowCommand::Cancel {
            job_id: payload_string(&intent.payload, "job_id")?,
        }),
        "queue.drop" => Ok(WorksFlowCommand::Drop {
            job_id: payload_string(&intent.payload, "job_id")?,
        }),
        "queue.start_next_available" => Ok(WorksFlowCommand::StartNextAvailable),
        "process.complete" => Ok(WorksFlowCommand::Complete {
            job_id: payload_string(&intent.payload, "job_id")?,
        }),
        "process.fail" => Ok(WorksFlowCommand::Fail {
            job_id: payload_string(&intent.payload, "job_id")?,
        }),
        other => Err(format!("unsupported Flow Rack command: {other}")),
    }
}

fn state_name(state: JobState) -> &'static str {
    match state {
        JobState::Queued => "Queued",
        JobState::Held => "Held",
        JobState::Running => "Running",
        JobState::Completed => "Completed",
        JobState::Failed => "Failed",
        JobState::Cancelled => "Cancelled",
        JobState::Dropped => "Dropped",
    }
}

fn lock_view(job: &JobCard) -> (Option<String>, Option<String>) {
    let Some(lock) = job.locks.first() else {
        return (None, None);
    };

    let mode = match lock.mode {
        LockMode::Read => "READ",
        LockMode::Write => "WRITE",
    }
    .to_owned();

    let scope = match &lock.scope.path {
        Some(path) => format!("{}/{}", lock.scope.project, path),
        None => lock.scope.project.clone(),
    };

    (Some(mode), Some(scope))
}

fn job_view(rack: &FlowRack, job: &JobCard) -> FlowRackJobView {
    let (lock_mode, lock_scope) = lock_view(job);
    let wait_reason = rack
        .wait_reason(&job.id)
        .ok()
        .flatten()
        .map(|reason| format!("{reason:?}"));

    FlowRackJobView {
        id: job.id.clone(),
        title: job.title.clone(),
        state: state_name(job.state).into(),
        actor_id: Some(job.origin.actor_id.clone()),
        wait_reason,
        correlation_id: job.origin.correlation_id.clone(),
        lock_mode,
        lock_scope,
    }
}

fn snapshot_of(rack: &FlowRack) -> FlowRackSnapshot {
    let running = rack
        .running_jobs()
        .into_iter()
        .map(|job| job_view(rack, job))
        .collect();

    let mut queue = Vec::new();
    let mut held = Vec::new();

    for job_id in rack.order() {
        let Some(job) = rack.job(job_id) else {
            continue;
        };
        match job.state {
            JobState::Held => held.push(job_view(rack, job)),
            JobState::Queued => queue.push(job_view(rack, job)),
            _ => {}
        }
    }

    FlowRackSnapshot {
        source: "LIVE_NATIVE".into(),
        running,
        queue,
        held,
        updated_at: now_stamp(),
    }
}

fn decision_name(decision: CommandDecision) -> &'static str {
    match decision {
        CommandDecision::Accepted => "ACCEPTED",
        CommandDecision::Rejected => "REJECTED",
        CommandDecision::RequiresHuman => "REQUIRES_HUMAN",
    }
}

fn domain_name(outcome: &DomainOutcome) -> String {
    match outcome {
        DomainOutcome::NotExecuted => "NOT_EXECUTED".into(),
        DomainOutcome::Applied(WorksOutput::None) => "APPLIED".into(),
        DomainOutcome::Applied(WorksOutput::Queue(_)) => "APPLIED_QUEUE".into(),
        DomainOutcome::Applied(WorksOutput::Job(_)) => "APPLIED_JOB".into(),
        DomainOutcome::Applied(WorksOutput::Started(Some(job_id))) => {
            format!("STARTED:{job_id}")
        }
        DomainOutcome::Applied(WorksOutput::Started(None)) => "STARTED:NONE".into(),
        DomainOutcome::Rejected(BindingError::CapabilityMismatch) => {
            "REJECTED:CAPABILITY_MISMATCH".into()
        }
        DomainOutcome::Rejected(BindingError::CommandPayloadMismatch) => {
            "REJECTED:COMMAND_PAYLOAD_MISMATCH".into()
        }
        DomainOutcome::Rejected(BindingError::UnknownJob(job_id)) => {
            format!("REJECTED:UNKNOWN_JOB:{job_id}")
        }
        DomainOutcome::Rejected(BindingError::Domain(error)) => {
            format!("REJECTED:DOMAIN:{error:?}")
        }
    }
}

fn execute_intent(
    rack: &mut FlowRack,
    intent: &FlowRackIntent,
) -> Result<FlowRackBridgeResult, String> {
    let profile = actor_profile(&intent.source)?;
    let command = typed_command(intent)?;
    let request = request_for(intent, &profile);
    let access = access_for(&request, &profile);
    let envelope = vertex_vlac_works_unit::WorksCommandEnvelope { request, command };
    let registry = registry_with_works_flow();
    let execution = execute(&registry, rack, &envelope, &access);

    Ok(FlowRackBridgeResult {
        decision: decision_name(execution.evaluation.result.decision).into(),
        message: execution.evaluation.result.message.clone(),
        domain: domain_name(&execution.outcome),
        correlation_id: execution.evaluation.result.correlation_id.clone(),
        snapshot: snapshot_of(rack),
    })
}

fn probe_intent(source: &str, command: &str, payload: Value, run_id: &str) -> FlowRackIntent {
    FlowRackIntent {
        source: source.into(),
        command: command.into(),
        payload,
        correlation_id: Some(format!("runtime:{run_id}:{source}:{command}")),
        reason: Some("Vertex Works Flow Rack runtime proof 000017".into()),
    }
}

fn start_runtime_probe_internal(
    rack: &mut FlowRack,
    slot: &mut Option<RuntimeProbeContext>,
) -> Result<RuntimeProbeStart, String> {
    if let Some(context) = slot.as_ref() {
        return Ok(RuntimeProbeStart {
            run_id: context.run_id.clone(),
            human_job: context.human_job.clone(),
            vera_job: context.vera_job.clone(),
            order_after_vera_move: context.order_after_vera_move.clone(),
            order_after_human_move: context.order_after_human_move.clone(),
            human_audit: context.human_audit,
            vera_audit: context.vera_audit,
            display_snapshot: snapshot_of(rack),
        });
    }

    if !rack.order().is_empty() || !rack.running_jobs().is_empty() {
        return Err("runtime proof requires an empty Flow Rack".into());
    }

    let run_id = now_stamp();
    let human_job = format!("runtime-human-{run_id}");
    let vera_job = format!("runtime-vera-{run_id}");

    execute_intent(
        rack,
        &probe_intent(
            "HUMAN_UI",
            "queue.insert",
            serde_json::json!({"job_id":human_job,"title":"RUNTIME PROOF — HUMAN"}),
            &run_id,
        ),
    )?;

    execute_intent(
        rack,
        &probe_intent(
            "VERA_LOCAL",
            "queue.insert",
            serde_json::json!({"job_id":vera_job,"title":"RUNTIME PROOF — VERA"}),
            &run_id,
        ),
    )?;

    execute_intent(
        rack,
        &probe_intent(
            "VERA_LOCAL",
            "queue.move",
            serde_json::json!({"job_id":vera_job,"to_index":0}),
            &run_id,
        ),
    )?;
    let order_after_vera_move = rack.order().to_vec();

    execute_intent(
        rack,
        &probe_intent(
            "HUMAN_UI",
            "queue.move",
            serde_json::json!({"job_id":human_job,"to_index":0}),
            &run_id,
        ),
    )?;
    let order_after_human_move = rack.order().to_vec();

    let human_audit = rack
        .audit()
        .iter()
        .any(|record| record.operation == "queue.move" && record.actor_id == "human-local");
    let vera_audit = rack
        .audit()
        .iter()
        .any(|record| record.operation == "queue.move" && record.actor_id == "vera");

    let context = RuntimeProbeContext {
        run_id: run_id.clone(),
        human_job: human_job.clone(),
        vera_job: vera_job.clone(),
        order_after_vera_move: order_after_vera_move.clone(),
        order_after_human_move: order_after_human_move.clone(),
        human_audit,
        vera_audit,
    };

    *slot = Some(context);

    Ok(RuntimeProbeStart {
        run_id,
        human_job,
        vera_job,
        order_after_vera_move,
        order_after_human_move,
        human_audit,
        vera_audit,
        display_snapshot: snapshot_of(rack),
    })
}

fn cleanup_runtime_probe(
    rack: &mut FlowRack,
    context: &RuntimeProbeContext,
) -> Result<FlowRackSnapshot, String> {
    for job_id in [&context.human_job, &context.vera_job] {
        if let Some(job) = rack.job(job_id) {
            if matches!(job.state, JobState::Queued | JobState::Held) {
                execute_intent(
                    rack,
                    &probe_intent(
                        "SERVICE_LOCAL",
                        "queue.drop",
                        serde_json::json!({"job_id":job_id}),
                        &context.run_id,
                    ),
                )?;
            }
        }
    }

    Ok(snapshot_of(rack))
}

fn persist_runtime_evidence(evidence: &RuntimeProbeEvidence) -> Result<(), String> {
    let text = serde_json::to_string_pretty(evidence).map_err(|error| error.to_string())?;

    let project_path = PathBuf::from(RUNTIME_PROBE_EVIDENCE);
    if let Some(parent) = project_path.parent() {
        fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    }
    fs::write(&project_path, format!("{text}\n")).map_err(|error| error.to_string())?;

    let local = runtime_probe_local_evidence_path();
    if let Some(parent) = local.parent() {
        fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    }
    fs::write(local, format!("{text}\n")).map_err(|error| error.to_string())?;

    Ok(())
}

#[tauri::command]
pub fn flow_rack_snapshot(
    state: State<'_, FlowRackBridgeState>,
) -> Result<FlowRackSnapshot, String> {
    let rack = state
        .rack
        .lock()
        .map_err(|_| "Flow Rack state lock poisoned".to_string())?;
    Ok(snapshot_of(&rack))
}

#[tauri::command]
pub fn flow_rack_execute(
    state: State<'_, FlowRackBridgeState>,
    intent: FlowRackIntent,
) -> Result<FlowRackBridgeResult, String> {
    let mut rack = state
        .rack
        .lock()
        .map_err(|_| "Flow Rack state lock poisoned".to_string())?;
    execute_intent(&mut rack, &intent)
}

#[tauri::command]
pub fn flow_rack_runtime_probe(
    state: State<'_, FlowRackBridgeState>,
) -> Result<Option<RuntimeProbeStart>, String> {
    if !runtime_probe_request_path().exists() {
        return Ok(None);
    }

    let mut rack = state
        .rack
        .lock()
        .map_err(|_| "Flow Rack state lock poisoned".to_string())?;
    let mut slot = state
        .runtime_probe
        .lock()
        .map_err(|_| "Flow Rack runtime probe lock poisoned".to_string())?;

    start_runtime_probe_internal(&mut rack, &mut slot).map(Some)
}

#[tauri::command]
pub fn flow_rack_runtime_probe_finalize(
    state: State<'_, FlowRackBridgeState>,
    ack: RuntimeProbeUiAck,
) -> Result<RuntimeProbeEvidence, String> {
    let mut rack = state
        .rack
        .lock()
        .map_err(|_| "Flow Rack state lock poisoned".to_string())?;
    let mut slot = state
        .runtime_probe
        .lock()
        .map_err(|_| "Flow Rack runtime probe lock poisoned".to_string())?;
    let context = slot
        .as_ref()
        .cloned()
        .ok_or_else(|| "runtime proof context not active".to_string())?;

    if ack.run_id != context.run_id {
        return Err("runtime proof run id mismatch".into());
    }

    let cleanup_snapshot = cleanup_runtime_probe(&mut rack, &context)?;
    let cleanup_empty = cleanup_snapshot.running.is_empty()
        && cleanup_snapshot.queue.is_empty()
        && cleanup_snapshot.held.is_empty();

    let pass = context.human_audit
        && context.vera_audit
        && ack.root_present
        && ack.source_live_native
        && ack.human_card_present
        && ack.vera_card_present
        && ack.rendered_card_count >= 2
        && cleanup_empty;

    let evidence = RuntimeProbeEvidence {
        artifact: "vertex-works-flow-rack-live-runtime-proof-000017".into(),
        works_version: "0.5.0".into(),
        run_id: context.run_id.clone(),
        timestamp: now_stamp(),
        webview_to_tauri: true,
        rust_state_owner: true,
        human_audit: context.human_audit,
        vera_audit: context.vera_audit,
        order_after_vera_move: context.order_after_vera_move.clone(),
        order_after_human_move: context.order_after_human_move.clone(),
        ui_root_present: ack.root_present,
        ui_source_live_native: ack.source_live_native,
        ui_human_card_present: ack.human_card_present,
        ui_vera_card_present: ack.vera_card_present,
        ui_rendered_card_count: ack.rendered_card_count,
        cleanup_empty,
        result: if pass { "PASS" } else { "FAIL" }.into(),
        cleanup_snapshot,
    };

    persist_runtime_evidence(&evidence)?;

    if pass {
        let _ = fs::remove_file(runtime_probe_request_path());
    }

    *slot = None;
    Ok(evidence)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn intent(source: &str, command: &str, payload: Value) -> FlowRackIntent {
        FlowRackIntent {
            source: source.into(),
            command: command.into(),
            payload,
            correlation_id: Some(format!("corr:{source}:{command}")),
            reason: Some("bridge test".into()),
        }
    }

    #[test]
    fn human_and_vera_share_the_same_live_execute_path() {
        let mut rack = FlowRack::default();

        let insert_a = execute_intent(
            &mut rack,
            &intent(
                "HUMAN_UI",
                "queue.insert",
                json!({"job_id":"a","title":"A"}),
            ),
        )
        .unwrap();
        assert_eq!(insert_a.decision, "ACCEPTED");

        let insert_b = execute_intent(
            &mut rack,
            &intent(
                "VERA_LOCAL",
                "queue.insert",
                json!({"job_id":"b","title":"B"}),
            ),
        )
        .unwrap();
        assert_eq!(insert_b.decision, "ACCEPTED");

        execute_intent(
            &mut rack,
            &intent(
                "VERA_LOCAL",
                "queue.move",
                json!({"job_id":"b","to_index":0}),
            ),
        )
        .unwrap();
        assert_eq!(rack.order(), &["b", "a"]);

        execute_intent(
            &mut rack,
            &intent("HUMAN_UI", "queue.move", json!({"job_id":"a","to_index":0})),
        )
        .unwrap();
        assert_eq!(rack.order(), &["a", "b"]);

        assert!(rack
            .audit()
            .iter()
            .any(|record| record.operation == "queue.move" && record.actor_id == "vera"));
        assert!(rack
            .audit()
            .iter()
            .any(|record| record.operation == "queue.move" && record.actor_id == "human-local"));
    }

    #[test]
    fn bridge_snapshot_is_authoritative_and_partitioned() {
        let mut rack = FlowRack::default();

        execute_intent(
            &mut rack,
            &intent(
                "HUMAN_UI",
                "queue.insert",
                json!({"job_id":"run","title":"Run"}),
            ),
        )
        .unwrap();
        execute_intent(
            &mut rack,
            &intent(
                "HUMAN_UI",
                "queue.insert",
                json!({"job_id":"hold","title":"Hold"}),
            ),
        )
        .unwrap();
        execute_intent(
            &mut rack,
            &intent("HUMAN_UI", "queue.hold", json!({"job_id":"hold"})),
        )
        .unwrap();
        execute_intent(
            &mut rack,
            &intent("SERVICE_LOCAL", "queue.start_next_available", json!({})),
        )
        .unwrap();

        let snapshot = snapshot_of(&rack);
        assert_eq!(snapshot.running.len(), 1);
        assert_eq!(snapshot.running[0].id, "run");
        assert_eq!(snapshot.held.len(), 1);
        assert_eq!(snapshot.held[0].id, "hold");
        assert!(snapshot.queue.is_empty());
    }

    #[test]
    fn unsupported_source_is_rejected_before_vlac_execution() {
        let mut rack = FlowRack::default();
        let result = execute_intent(
            &mut rack,
            &intent(
                "REMOTE_UNAUTHENTICATED",
                "queue.insert",
                json!({"job_id":"x","title":"X"}),
            ),
        );
        assert!(result.is_err());
        assert!(rack.order().is_empty());
    }

    #[test]
    fn bridge_preserves_lock_wait_visibility() {
        let mut rack = FlowRack::default();

        execute_intent(
            &mut rack,
            &intent(
                "HUMAN_UI",
                "queue.insert",
                json!({
                    "job_id":"writer",
                    "title":"Writer",
                    "locks":[{"project":"vertex_works","path":"src","mode":"write"}]
                }),
            ),
        )
        .unwrap();
        execute_intent(
            &mut rack,
            &intent(
                "HUMAN_UI",
                "queue.insert",
                json!({
                    "job_id":"reader",
                    "title":"Reader",
                    "locks":[{"project":"vertex_works","path":"src/main.rs","mode":"read"}]
                }),
            ),
        )
        .unwrap();

        execute_intent(
            &mut rack,
            &intent("SERVICE_LOCAL", "queue.start_next_available", json!({})),
        )
        .unwrap();

        let snapshot = snapshot_of(&rack);
        assert_eq!(snapshot.queue.len(), 1);
        assert_eq!(snapshot.queue[0].id, "reader");
        assert_eq!(
            snapshot.queue[0].wait_reason.as_deref(),
            Some("LockConflict")
        );
        assert_eq!(snapshot.queue[0].lock_mode.as_deref(), Some("READ"));
    }

    #[test]
    fn runtime_probe_uses_both_human_and_vera_and_can_cleanup() {
        let mut rack = FlowRack::default();
        let mut slot = None;
        let start = start_runtime_probe_internal(&mut rack, &mut slot).unwrap();

        assert!(start.human_audit);
        assert!(start.vera_audit);
        assert_eq!(start.display_snapshot.queue.len(), 2);
        assert_eq!(start.order_after_human_move[0], start.human_job);

        let context = slot.as_ref().unwrap().clone();
        let cleanup = cleanup_runtime_probe(&mut rack, &context).unwrap();
        assert!(cleanup.queue.is_empty());
        assert!(cleanup.running.is_empty());
        assert!(cleanup.held.is_empty());
    }

    #[test]
    fn runtime_probe_refuses_to_touch_nonempty_real_queue() {
        let mut rack = FlowRack::default();
        execute_intent(
            &mut rack,
            &intent(
                "HUMAN_UI",
                "queue.insert",
                json!({"job_id":"real","title":"Real Work"}),
            ),
        )
        .unwrap();

        let mut slot = None;
        let result = start_runtime_probe_internal(&mut rack, &mut slot);
        assert!(result.is_err());
        assert_eq!(rack.order(), &["real"]);
    }
}
