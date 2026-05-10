import { useHarnessStore } from '../store/agentStore';

export default function ContextPanel() {
  const project = useHarnessStore((s) => s.project);
  const agents = Object.values(project.agents);

  return (
    <div className="context-panel">
      <div className="context-panel__section">
        <h3 className="context-panel__heading">Context</h3>
      </div>

      <div className="context-panel__section">
        <h4 className="context-panel__subheading">Tokens</h4>
        {agents.map((agent) => {
          const pct =
            agent.tokens_max > 0
              ? Math.min((agent.tokens_used / agent.tokens_max) * 100, 100)
              : 0;
          return (
            <div key={agent.id} className="context-panel__token-row">
              <span className="context-panel__agent-name">{agent.name}</span>
              <div className="context-panel__bar-track">
                <div
                  className="context-panel__bar-fill"
                  style={{
                    width: `${pct}%`,
                    background: `var(--color-${agent.color})`,
                  }}
                />
              </div>
              <span className="context-panel__pct">{Math.round(pct)}%</span>
            </div>
          );
        })}
      </div>

      <div className="context-panel__section">
        <h4 className="context-panel__subheading">Files</h4>
        <div className="context-panel__file-tree">
          {/* file tree — Phase 2 (watchdog watcher.py) */}
          <span className="context-panel__placeholder">— not yet wired —</span>
        </div>
      </div>

      {project.last_done && (
        <div className="context-panel__banner context-panel__banner--done">
          <span className="context-panel__banner-label">Last done</span>
          <span className="context-panel__banner-value">
            {project.last_done.agent}: {project.last_done.task}
          </span>
        </div>
      )}

      {project.next_step && (
        <div className="context-panel__banner context-panel__banner--next">
          <span className="context-panel__banner-label">Next</span>
          <span className="context-panel__banner-value">
            {project.next_step.agent}: {project.next_step.task}
          </span>
        </div>
      )}
    </div>
  );
}
