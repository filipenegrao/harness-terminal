// Tauri entry point — window setup, PTY state, command registration.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod config;
mod pty;
mod sidecar;

use config::HarnessProject;
use pty::{PtyRegistry, SharedPtyRegistry, SidecarForward};
use serde_json::Value;
use std::sync::{Arc, Mutex};

/// Ensures `bootstrap_harness` only spawns PTYs once (e.g. React Strict Mode double-mount).
#[derive(Clone)]
pub struct BootstrapDone(pub Arc<Mutex<bool>>);

impl Default for BootstrapDone {
    fn default() -> Self {
        Self(Arc::new(Mutex::new(false)))
    }
}

/// Load `harness.toml`, return initial project JSON for Zustand, and spawn a PTY per agent (once).
#[tauri::command]
fn bootstrap_harness(
    app: tauri::AppHandle,
    registry: tauri::State<'_, SharedPtyRegistry>,
    forward: tauri::State<'_, SidecarForward>,
    project: tauri::State<'_, HarnessProject>,
    done: tauri::State<'_, BootstrapDone>,
) -> Result<Value, String> {
    let mut flag = done.0.lock().unwrap();
    if *flag {
        return Ok(project.project_json.clone());
    }
    for (id, cmd) in &project.spawn_pairs {
        pty::spawn_pty(
            app.clone(),
            registry.inner().clone(),
            forward.inner().clone(),
            id.clone(),
            cmd.clone(),
        )?;
    }
    *flag = true;
    Ok(project.project_json.clone())
}

/// Spawn a PTY for an agent and start the reader → event loop.
#[tauri::command]
fn pty_spawn(
    app: tauri::AppHandle,
    registry: tauri::State<'_, SharedPtyRegistry>,
    forward: tauri::State<'_, SidecarForward>,
    agent_id: String,
    command: String,
) -> Result<(), String> {
    pty::spawn_pty(
        app,
        registry.inner().clone(),
        forward.inner().clone(),
        agent_id,
        command,
    )
}

/// Write raw bytes to an agent's PTY stdin.
/// Called from xterm.js onData via invoke().
#[tauri::command]
fn pty_write(
    registry: tauri::State<'_, SharedPtyRegistry>,
    agent_id: String,
    data: Vec<u8>,
) -> Result<(), String> {
    registry.inner().lock().unwrap().write_to(&agent_id, &data)
}

fn main() {
    let pty_registry: SharedPtyRegistry = Arc::new(Mutex::new(PtyRegistry::new()));
    let harness_project =
        match config::resolve_harness_toml().and_then(|p| config::load_harness_project(&p)) {
            Ok(h) => h,
            Err(e) => HarnessProject::empty(e),
        };

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(pty_registry)
        .manage(SidecarForward::new())
        .manage(harness_project)
        .manage(BootstrapDone::default())
        .invoke_handler(tauri::generate_handler![
            bootstrap_harness,
            pty_spawn,
            pty_write
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
