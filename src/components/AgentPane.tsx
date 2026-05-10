import { useRef } from 'react';
import type { AgentState } from '../types';
import { usePtyTerminal } from '../hooks/usePtyTerminal';

interface Props {
  agent: AgentState;
}

const STATUS_COLOR: Record<string, string> = {
  working: 'var(--color-amber)',
  idle:    'var(--color-muted)',
  done:    'var(--color-green)',
  error:   'var(--color-red)',
};

// Map color name → CSS variable for xterm cursor
const CURSOR_COLOR: Record<string, string> = {
  amber:  '#f59e0b',
  blue:   '#60a5fa',
  purple: '#a78bfa',
  green:  '#4ade80',
};

export default function AgentPane({ agent }: Props) {
  const termRef = useRef<HTMLDivElement>(null);

  // xterm init + PTY bridge — mounted once, never remounted
  usePtyTerminal(agent.id, termRef, CURSOR_COLOR[agent.color] ?? '#fafafa');

  const tokenPct =
    agent.tokens_max > 0
      ? Math.min((agent.tokens_used / agent.tokens_max) * 100, 100)
      : 0;

  return (
    <div className={`agent-pane agent-pane--${agent.color}`}>
      <div className="agent-pane__header">
        <span className={`agent-pane__icon ${agent.icon}`} aria-hidden />
        <span className="agent-pane__name">{agent.name}</span>
        <span
          className="agent-pane__status-dot"
          title={agent.status}
          style={{ background: STATUS_COLOR[agent.status] ?? 'var(--color-muted)' }}
        />
      </div>

      <div className="agent-pane__terminal" ref={termRef} />

      <div className="agent-pane__footer">
        <span className="agent-pane__model">{agent.model}</span>
        {agent.last_task && (
          <span
            className="agent-pane__task"
            title={agent.last_task}
            style={{
              flex: 1,
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-muted)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              margin: '0 var(--space-2)',
            }}
          >
            {agent.last_task}
          </span>
        )}
        <span className="agent-pane__tokens">
          {(agent.tokens_used / 1000).toFixed(1)}k /{' '}
          {(agent.tokens_max / 1000).toFixed(0)}k
        </span>
        <div className="agent-pane__token-bar">
          <div
            className="agent-pane__token-fill"
            style={{
              width: `${tokenPct}%`,
              background: `var(--color-${agent.color})`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
