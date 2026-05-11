import { useShallow } from 'zustand/react/shallow';
import { useHarnessStore } from '../store/agentStore';
import AgentPane from './AgentPane';
import ContextPanel from './ContextPanel';
import UserTerminal from './UserTerminal';

export default function BentoGrid() {
  const agents = useHarnessStore(useShallow((s) => Object.values(s.project.agents)));

  return (
    <div className="bento-grid">
      <div className="bento-context">
        <ContextPanel />
      </div>
      <div className="bento-agents">
        {agents.map((agent) => (
          <AgentPane key={agent.id} agent={agent} />
        ))}
      </div>
      <div className="bento-user">
        <UserTerminal />
      </div>
    </div>
  );
}
