// PTY spawn and I/O bridge.
//
// Data flow:
//   portable-pty master reader
//     → background thread
//       → tauri::Emitter::emit("pty-data-{agent_id}", PtyOutputEvent)
//         → JS listen() → xterm.js term.write()
//
// Write path (keyboard input):
//   xterm.js term.onData → invoke("pty_write") → PtyRegistry::write_to → PTY stdin

use std::collections::HashMap;
use std::io::{Read, Write};
use std::sync::{Arc, Mutex};

use portable_pty::{native_pty_system, CommandBuilder, PtySize};
use serde::Serialize;
use tauri::Emitter;

/// Payload emitted as a Tauri event to the webview.
/// `data` is raw PTY bytes; JS reconstructs via `new Uint8Array(event.payload.data)`.
#[derive(Clone, Serialize)]
pub struct PtyOutputEvent {
    pub agent_id: String,
    pub data: Vec<u8>,
}

/// Holds one write-half per spawned PTY, keyed by agent_id.
pub struct PtyRegistry {
    writers: HashMap<String, Box<dyn Write + Send>>,
}

impl PtyRegistry {
    pub fn new() -> Self {
        Self {
            writers: HashMap::new(),
        }
    }

    pub fn write_to(&mut self, agent_id: &str, data: &[u8]) -> Result<(), String> {
        let w = self
            .writers
            .get_mut(agent_id)
            .ok_or_else(|| format!("no PTY for agent '{}'", agent_id))?;
        w.write_all(data).map_err(|e| e.to_string())?;
        w.flush().map_err(|e| e.to_string())
    }
}

pub type SharedPtyRegistry = Arc<Mutex<PtyRegistry>>;

/// Spawn a PTY for the given shell command and wire it to the Tauri event bus.
///
/// After this call returns:
/// - The PTY process is running.
/// - A background thread forwards PTY stdout → `pty-data-{agent_id}` events.
/// - The writer is stored in `registry` for `pty_write` commands.
pub fn spawn_pty(
    app: tauri::AppHandle,
    registry: SharedPtyRegistry,
    agent_id: String,
    command: String,
) -> Result<(), String> {
    let pty_system = native_pty_system();

    let pair = pty_system
        .openpty(PtySize {
            rows: 24,
            cols: 80,
            pixel_width: 0,
            pixel_height: 0,
        })
        .map_err(|e| e.to_string())?;

    let writer = pair.master.take_writer().map_err(|e| e.to_string())?;
    let mut reader = pair.master.try_clone_reader().map_err(|e| e.to_string())?;

    registry
        .lock()
        .unwrap()
        .writers
        .insert(agent_id.clone(), writer);

    let mut cmd = CommandBuilder::new("sh");
    cmd.arg("-c");
    cmd.arg(&command);
    let _child = pair.slave.spawn_command(cmd).map_err(|e| e.to_string())?;
    // slave fd must be closed in parent after fork so child gets EOF correctly
    drop(pair.slave);

    // Reader thread — runs until PTY closes
    let event_name = format!("pty-data-{}", agent_id);
    std::thread::spawn(move || {
        let mut buf = [0u8; 4096];
        loop {
            match reader.read(&mut buf) {
                Ok(0) | Err(_) => break,
                Ok(n) => {
                    let _ = app.emit(
                        &event_name,
                        PtyOutputEvent {
                            agent_id: agent_id.clone(),
                            data: buf[..n].to_vec(),
                        },
                    );
                }
            }
        }
    });

    Ok(())
}
