import { useEffect, useRef } from 'react';

export default function UserTerminal() {
  const termRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<unknown>(null);

  useEffect(() => {
    async function init() {
      if (!termRef.current || xtermRef.current) return;
      const { Terminal } = await import('@xterm/xterm');
      const { FitAddon } = await import('@xterm/addon-fit');
      if (!termRef.current || xtermRef.current) return;
      const term = new Terminal({
        theme: {
          background: '#18181b',
          foreground: '#fafafa',
          cursor: '#4ade80', // green cursor — visual distinction from agent panes
        },
        fontFamily: "'JetBrains Mono', 'Fira Code', ui-monospace, monospace",
        fontSize: 12,
        cursorBlink: true,
      });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(termRef.current);
      fitAddon.fit();
      xtermRef.current = term;
    }
    void init();
  }, []); // mount once

  return (
    <div className="user-terminal">
      <div className="user-terminal__header">
        <span className="user-terminal__badge">you</span>
        <span className="user-terminal__label">Terminal</span>
      </div>
      <div className="user-terminal__term" ref={termRef} />
    </div>
  );
}
