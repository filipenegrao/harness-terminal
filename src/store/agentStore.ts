import { create } from 'zustand';
import type { AgentState, ProjectState } from '../types';

// Mock data — replaced by WebSocket full_state on sidecar connect
const MOCK_PROJECT: ProjectState = {
  project_name: 'my-project',
  working_dir: '.',
  git_branch: 'main',
  modified_files: [],
  last_done: { agent: 'security', task: 'Auth middleware audit' },
  next_step: { agent: 'builder', task: 'PTY bridge spike' },
  agents: {
    orchestrator: {
      id: 'orchestrator', name: 'Orchestrator', icon: 'ti-adjustments',
      model: 'claude-sonnet-4', color: 'amber', status: 'idle',
      next_agent: null, tokens_used: 0, tokens_max: 100000,
      last_task: null, last_warn: null, updated_at: Date.now() / 1000,
    },
    builder: {
      id: 'builder', name: 'Builder', icon: 'ti-hammer',
      model: 'claude-sonnet-4', color: 'blue', status: 'working',
      next_agent: null, tokens_used: 42000, tokens_max: 100000,
      last_task: 'Implementing PTY bridge', last_warn: null,
      updated_at: Date.now() / 1000,
    },
    qa: {
      id: 'qa', name: 'QA', icon: 'ti-checklist',
      model: 'claude-sonnet-4', color: 'purple', status: 'idle',
      next_agent: null, tokens_used: 0, tokens_max: 100000,
      last_task: null, last_warn: null, updated_at: Date.now() / 1000,
    },
    security: {
      id: 'security', name: 'Security', icon: 'ti-shield-check',
      model: 'claude-sonnet-4', color: 'green', status: 'done',
      next_agent: null, tokens_used: 28000, tokens_max: 100000,
      last_task: 'Auth middleware audit', last_warn: null,
      updated_at: Date.now() / 1000,
    },
  },
};

interface HarnessStore {
  project: ProjectState;
  setProject: (state: ProjectState) => void;
  updateAgent: (agentId: string, patch: Partial<AgentState>) => void;
  applyDiff: (diff: Partial<ProjectState>) => void;
}

export const useHarnessStore = create<HarnessStore>((set) => ({
  project: MOCK_PROJECT,

  setProject: (state) => set({ project: state }),

  updateAgent: (agentId, patch) =>
    set((s) => ({
      project: {
        ...s.project,
        agents: {
          ...s.project.agents,
          [agentId]: { ...s.project.agents[agentId], ...patch },
        },
      },
    })),

  applyDiff: (diff) =>
    set((s) => ({
      project: {
        ...s.project,
        ...diff,
        agents: {
          ...s.project.agents,
          ...(diff.agents ?? {}),
        },
      },
    })),
}));
