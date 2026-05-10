import './base.css';
import { invoke } from '@tauri-apps/api/core';
import { useEffect } from 'react';
import BentoGrid from './components/BentoGrid';
import StatusStrip from './components/StatusStrip';
import { useWebSocket } from './hooks/useWebSocket';
import { useHarnessStore } from './store/agentStore';
import type { ProjectState } from './types';

export default function App() {
  useWebSocket();
  const setProject = useHarnessStore((s) => s.setProject);

  useEffect(() => {
    void invoke<ProjectState>('bootstrap_harness')
      .then(setProject)
      .catch((err: unknown) => {
        console.error('bootstrap_harness failed', err);
      });
  }, [setProject]);

  return (
    <div className="app">
      <BentoGrid />
      <StatusStrip />
    </div>
  );
}
