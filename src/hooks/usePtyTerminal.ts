import { useEffect, useRef } from 'react';
import { listen } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';

interface PtyOutputEvent {
  agent_id: string;
  data: number[]; // raw bytes from Rust Vec<u8> → JSON array
}

/**
 * Initialises an xterm.js terminal in `containerRef`, wires it to the
 * Tauri PTY bridge for the given agent, and handles keyboard input.
 *
 * xterm is opened once on mount and never torn down — callers must not
 * unmount/remount the container (see CLAUDE.md critical constraint).
 */
export function usePtyTerminal(
  agentId: string,
  containerRef: React.RefObject<HTMLDivElement | null>,
  cursorColor: string = '#fafafa',
): void {
  const xtermRef = useRef<unknown>(null);

  useEffect(() => {
    if (!containerRef.current || xtermRef.current) return;

    let unlisten: (() => void) | null = null;

    async function init() {
      const { Terminal } = await import('@xterm/xterm');
      const { FitAddon } = await import('@xterm/addon-fit');
      if (!containerRef.current || xtermRef.current) return;

      const term = new Terminal({
        theme: {
          background: '#18181b',
          foreground: '#fafafa',
          cursor: cursorColor,
        },
        fontFamily: "'JetBrains Mono', 'Fira Code', ui-monospace, monospace",
        fontSize: 12,
        cursorBlink: true,
      });

      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(containerRef.current!);
      fitAddon.fit();
      xtermRef.current = term;

      // PTY stdout → xterm.js
      // Rust emits Vec<u8> serialised as a JSON number array; reconstruct as Uint8Array.
      unlisten = await listen<PtyOutputEvent>(`pty-data-${agentId}`, (event) => {
        term.write(new Uint8Array(event.payload.data));
      });

      // xterm.js keyboard input → PTY stdin
      term.onData((input: string) => {
        const bytes = Array.from(new TextEncoder().encode(input));
        void invoke<void>('pty_write', { agentId, data: bytes });
      });
    }

    void init();

    return () => {
      unlisten?.();
      // xterm Terminal instance intentionally not disposed — see CLAUDE.md
    };
  }, []); // empty deps — mount once, never re-run
}
