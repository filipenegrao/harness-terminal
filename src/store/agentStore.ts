import { create } from 'zustand';
import type { AgentState, ProjectState } from '../types';

/** Until `bootstrap_harness` + WebSocket run, the grid is empty or stale. */
const EMPTY_PROJECT: ProjectState = {
  project_name: '',
  working_dir: '',
  git_branch: 'main',
  modified_files: [],
  last_done: null,
  next_step: null,
  agents: {},
};

interface HarnessStore {
  project: ProjectState;
  setProject: (state: ProjectState) => void;
  updateAgent: (agentId: string, patch: Partial<AgentState>) => void;
  applyDiff: (diff: Partial<ProjectState>) => void;
}

export const useHarnessStore = create<HarnessStore>((set) => ({
  project: EMPTY_PROJECT,

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
    set((s) => {
      const { agents: agentPatches, ...rest } = diff;
      let agents = s.project.agents;
      if (agentPatches) {
        agents = { ...agents };
        for (const [id, patch] of Object.entries(agentPatches)) {
          const prev = agents[id];
          if (prev && patch) {
            agents[id] = { ...prev, ...patch };
          }
        }
      }
      return {
        project: {
          ...s.project,
          ...rest,
          agents,
        },
      };
    }),
}));
