// Python sidecar process manager stub.
// Sidecar exposes ws://127.0.0.1:7373 once running.

use tauri_plugin_shell::ShellExt;

/// Spawn the Python harness sidecar bundled with the app.
/// In dev: run `python harness/main.py` manually before `npm run tauri dev`.
pub fn start_sidecar(app: &tauri::AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let (_rx, _child) = app.shell().sidecar("harness")?.spawn()?;
    // TODO: pipe _rx to log sidecar stderr in dev mode
    Ok(())
}
