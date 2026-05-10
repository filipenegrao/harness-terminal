export type AgentStatus = 'working' | 'idle' | 'done' | 'error';

export interface AgentState {
  id: string;
  name: string;
  icon: string;
  model: string;
  color: string;
  status: AgentStatus;
  next_agent: string | null;
  tokens_used: number;
  tokens_max: number;
  last_task: string | null;
  last_warn: string | null;
  updated_at: number;
}

export interface LastAction {
  agent: string;
  task: string;
}

export interface ProjectState {
  project_name: string;
  working_dir: string;
  git_branch: string;
  modified_files: string[];
  last_done: LastAction | null;
  next_step: LastAction | null;
  agents: Record<string, AgentState>;
}

export interface Signal {
  type: 'full_state' | 'state_diff';
  payload: Partial<ProjectState>;
}
