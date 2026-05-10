import { useHarnessStore } from '../store/agentStore';
import type { AgentStatus } from '../types';

export default function StatusStrip() {
  const project = useHarnessStore((s) => s.project);
  const agents = Object.values(project.agents);

  const counts = agents.reduce<Partial<Record<AgentStatus, number>>>((acc, a) => {
    acc[a.status] = (acc[a.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="status-strip">
      <span className="status-strip__project">{project.project_name}</span>
      <span className="status-strip__divider" />

      <span className="status-strip__counts">
        {counts.working != null && (
          <span className="status-strip__count status-strip__count--working">
            {counts.working} working
          </span>
        )}
        {counts.idle != null && (
          <span className="status-strip__count status-strip__count--idle">
            {counts.idle} idle
          </span>
        )}
        {counts.done != null && (
          <span className="status-strip__count status-strip__count--done">
            {counts.done} done
          </span>
        )}
        {counts.error != null && (
          <span className="status-strip__count status-strip__count--error">
            {counts.error} error
          </span>
        )}
      </span>

      <span className="status-strip__spacer" />

      {project.last_done && (
        <span className="status-strip__last">
          Last: {project.last_done.agent} — {project.last_done.task}
        </span>
      )}
      {project.next_step && (
        <span className="status-strip__next">
          Next: {project.next_step.agent} — {project.next_step.task}
        </span>
      )}
    </div>
  );
}
