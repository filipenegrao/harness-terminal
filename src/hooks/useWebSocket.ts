import { useEffect, useRef } from 'react';
import { useHarnessStore } from '../store/agentStore';
import type { Signal } from '../types';

const WS_URL = 'ws://127.0.0.1:7373';
const RECONNECT_DELAY_MS = 3000;

export function useWebSocket(): void {
  const wsRef = useRef<WebSocket | null>(null);
  const { setProject, applyDiff } = useHarnessStore();

  useEffect(() => {
    let active = true;

    function connect() {
      if (!active) return;
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (event: MessageEvent) => {
        try {
          const signal: Signal = JSON.parse(event.data as string);
          if (signal.type === 'full_state') {
            setProject(signal.payload as Parameters<typeof setProject>[0]);
          } else if (signal.type === 'state_diff') {
            applyDiff(signal.payload);
          }
        } catch {
          // malformed message — ignore
        }
      };

      ws.onclose = () => {
        if (active) setTimeout(connect, RECONNECT_DELAY_MS);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      active = false;
      wsRef.current?.close();
    };
  }, [setProject, applyDiff]);
}
