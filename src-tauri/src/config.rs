//! Resolve project-root `harness.toml` and build bootstrap project JSON for the webview.

use std::path::{Path, PathBuf};
use std::process::Command;

use serde::Deserialize;
use serde_json::{json, Value};

#[derive(Debug, Deserialize)]
pub struct HarnessFile {
    pub project: Option<ProjectSection>,
    pub agents: Vec<AgentSection>,
}

#[derive(Debug, Deserialize)]
pub struct ProjectSection {
    pub name: Option<String>,
    pub working_dir: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct AgentSection {
    pub id: String,
    pub name: String,
    pub icon: Option<String>,
    pub model: Option<String>,
    pub color: Option<String>,
    pub command: String,
    pub tokens_max: Option<u64>,
}

fn git_branch(working_dir: &Path) -> String {
    let out = Command::new("git")
        .args(["rev-parse", "--abbrev-ref", "HEAD"])
        .current_dir(working_dir)
        .output();
    match out {
        Ok(o) if o.status.success() => {
            String::from_utf8_lossy(&o.stdout).trim().to_string()
        }
        _ => "main".to_string(),
    }
}

/// Locate `harness.toml`: prefer cwd (typical `npm run tauri dev` from repo root), then walk parents.
pub fn resolve_harness_toml() -> Result<PathBuf, String> {
    let candidates = [
        PathBuf::from("harness.toml"),
        PathBuf::from("../harness.toml"),
    ];
    if let Ok(cwd) = std::env::current_dir() {
        let mut dir = cwd.clone();
        loop {
            let p = dir.join("harness.toml");
            if p.is_file() {
                return Ok(p);
            }
            if !dir.pop() {
                break;
            }
        }
        for c in &candidates {
            let p = cwd.join(c);
            if p.is_file() {
                return Ok(p);
            }
        }
    }
    for c in &candidates {
        if c.is_file() {
            return Ok(c.clone());
        }
    }
    Err("harness.toml not found (cwd or parents)".to_string())
}

/// Parsed harness.toml plus resolved paths — stored in Tauri state after load.
#[derive(Clone)]
pub struct HarnessProject {
    #[allow(dead_code)]
    pub config_path: PathBuf,
    pub project_json: Value,
    pub spawn_pairs: Vec<(String, String)>,
}

impl HarnessProject {
    pub fn empty(reason: impl Into<String>) -> Self {
        eprintln!("harness: {}", reason.into());
        Self {
            config_path: PathBuf::new(),
            project_json: json!({
                "project_name": "",
                "working_dir": "",
                "git_branch": "main",
                "modified_files": [],
                "last_done": Value::Null,
                "next_step": Value::Null,
                "agents": {},
            }),
            spawn_pairs: vec![],
        }
    }
}

pub fn load_harness_project(config_path: &Path) -> Result<HarnessProject, String> {
    let raw = std::fs::read_to_string(config_path).map_err(|e| e.to_string())?;
    let file: HarnessFile = toml::from_str(&raw).map_err(|e| e.to_string())?;

    let project = file.project.as_ref();
    let working_rel = project
        .and_then(|p| p.working_dir.as_deref())
        .unwrap_or(".");
    let base = config_path.parent().unwrap_or(Path::new("."));
    let working_dir = base.join(working_rel);
    let working_dir = working_dir
        .canonicalize()
        .unwrap_or_else(|_| base.join(working_rel));

    let project_name = project
        .and_then(|p| p.name.clone())
        .unwrap_or_else(|| working_dir.file_name().map(|s| s.to_string_lossy().into_owned()).unwrap_or_else(|| "project".to_string()));

    let branch = git_branch(&working_dir);
    let mut agents_obj = serde_json::Map::new();
    let mut spawn_pairs = Vec::new();

    for a in file.agents {
        spawn_pairs.push((a.id.clone(), a.command.clone()));
        let icon = a.icon.unwrap_or_default();
        let model = a.model.unwrap_or_else(|| "unknown".to_string());
        let color = a.color.unwrap_or_else(|| "blue".to_string());
        let tokens_max = a.tokens_max.unwrap_or(100_000);
        agents_obj.insert(
            a.id.clone(),
            json!({
                "id": a.id,
                "name": a.name,
                "icon": icon,
                "model": model,
                "color": color,
                "status": "idle",
                "next_agent": Value::Null,
                "tokens_used": 0,
                "tokens_max": tokens_max,
                "last_task": Value::Null,
                "last_warn": Value::Null,
                "updated_at": js_now_secs(),
            }),
        );
    }

    let project_json = json!({
        "project_name": project_name,
        "working_dir": working_dir.to_string_lossy(),
        "git_branch": branch,
        "modified_files": [],
        "last_done": Value::Null,
        "next_step": Value::Null,
        "agents": Value::Object(agents_obj),
    });

    Ok(HarnessProject {
        config_path: config_path.to_path_buf(),
        project_json,
        spawn_pairs,
    })
}

fn js_now_secs() -> f64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}
