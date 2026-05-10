// Tauri entry point — window setup, PTY state, command registration.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod pty;
mod sidecar;

use pty::{PtyRegistry, SharedPtyRegistry};
use std::sync::{Arc, Mutex};

/// Spawn a PTY for an agent and start the reader → event loop.
/// Call once per agent on session start.
#[tauri::command]
fn pty_spawn(
    app: tauri::AppHandle,
    registry: tauri::State<'_, SharedPtyRegistry>,
    agent_id: String,
    command: String,
) -> Result<(), String> {
    pty::spawn_pty(app, registry.inner().clone(), agent_id, command)
}

/// Write raw bytes to an agent's PTY stdin.
/// Called from xterm.js onData via invoke().
#[tauri::command]
fn pty_write(
    registry: tauri::State<'_, SharedPtyRegistry>,
    agent_id: String,
    data: Vec<u8>,
) -> Result<(), String> {
    registry.lock().unwrap().write_to(&agent_id, &data)
}

fn main() {
    let pty_registry: SharedPtyRegistry = Arc::new(Mutex::new(PtyRegistry::new()));

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(pty_registry)
        .invoke_handler(tauri::generate_handler![pty_spawn, pty_write])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
