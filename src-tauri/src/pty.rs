// PTY spawn and I/O bridge.
//
// Data flow:
//   portable-pty master reader
//     → background thread
//       → tauri::Emitter::emit("pty-data-{agent_id}", PtyOutputEvent)
//         → JS listen() → xterm.js term.write()
//       → optional TCP forward to Python sidecar (127.0.0.1:PTY_INGEST_PORT) for signal parsing
//
// Write path (keyboard input):
//   xterm.js term.onData → invoke("pty_write") → PtyRegistry::write_to → PTY stdin
//
// PTY → Python IPC: one localhost TCP connection (multiplexed binary frames). See `harness/server.py`.

use std::collections::HashMap;
use std::io::{Read, Write};
use std::net::TcpStream;
use std::sync::{Arc, Mutex};

use portable_pty::{native_pty_system, CommandBuilder, PtySize};
use serde::Serialize;
use tauri::Emitter;

/// Must match `PTY_INGEST_HOST` / `PTY_INGEST_PORT` in `harness/server.py`.
pub const PTY_INGEST_ADDR: &str = "127.0.0.1:7374";

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

/// Lazy TCP connection to the Python PTY ingest server; frames are `u16 id_len LE`, `u32 payload_len LE`,
/// `agent_id utf-8`, `payload`.
#[derive(Clone)]
pub struct SidecarForward(pub Arc<Mutex<Option<TcpStream>>>);

impl SidecarForward {
    pub fn new() -> Self {
        Self(Arc::new(Mutex::new(None)))
    }

    /// Forward raw PTY stdout to the sidecar; failures are silent (sidecar may not be up yet).
    pub fn forward_chunk(&self, agent_id: &str, data: &[u8]) {
        let mut guard = self.0.lock().unwrap();
        if guard.is_none() {
            if let Ok(stream) = TcpStream::connect(PTY_INGEST_ADDR) {
                let _ = stream.set_nodelay(true);
                *guard = Some(stream);
            }
        }
        if let Some(ref mut stream) = *guard {
            if write_frame(stream, agent_id, data).is_err() {
                *guard = None;
            }
        }
    }
}

fn write_frame(stream: &mut TcpStream, agent_id: &str, data: &[u8]) -> std::io::Result<()> {
    let id_bytes = agent_id.as_bytes();
    let id_len = id_bytes.len();
    if id_len > u16::MAX as usize {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidInput,
            "agent_id too long",
        ));
    }
    stream.write_all(&(id_len as u16).to_le_bytes())?;
    stream.write_all(&(data.len() as u32).to_le_bytes())?;
    stream.write_all(id_bytes)?;
    stream.write_all(data)?;
    stream.flush()
}

/// Spawn a PTY for the given shell command and wire it to the Tauri event bus.
///
/// After this call returns:
/// - The PTY process is running.
/// - A background thread forwards PTY stdout → `pty-data-{agent_id}` events.
/// - The writer is stored in `registry` for `pty_write` commands.
pub fn spawn_pty(
    app: tauri::AppHandle,
    registry: SharedPtyRegistry,
    forward: SidecarForward,
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
    let fwd = forward.clone();
    let aid = agent_id.clone();
    std::thread::spawn(move || {
        let mut buf = [0u8; 4096];
        loop {
            match reader.read(&mut buf) {
                Ok(0) | Err(_) => break,
                Ok(n) => {
                    let chunk = buf[..n].to_vec();
                    let _ = app.emit(
                        &event_name,
                        PtyOutputEvent {
                            agent_id: aid.clone(),
                            data: chunk.clone(),
                        },
                    );
                    fwd.forward_chunk(&aid, &chunk);
                }
            }
        }
    });

    Ok(())
}
