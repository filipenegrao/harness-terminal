"""AgentState and ProjectState dataclasses for the Harness sidecar."""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentState:
    id: str
    name: str
    icon: str
    model: str
    color: str
    tokens_max: int
    command: str
    status: str = "idle"          # working | idle | done | error
    next_agent: Optional[str] = None
    tokens_used: int = 0
    last_task: Optional[str] = None
    last_warn: Optional[str] = None
    updated_at: float = field(default_factory=time.time)

    def apply_signal(self, parsed: dict) -> None:
        """Mutate fields from a parsed signal dict (from parser.parse_line)."""
        if parsed.get('status'):
            self.status = parsed['status']
        if 'next' in parsed:
            self.next_agent = parsed['next']
        if parsed.get('tokens') is not None:
            self.tokens_used = parsed['tokens']
        if 'task' in parsed:
            self.last_task = parsed['task'].get('value')
        if 'warn' in parsed:
            self.last_warn = parsed['warn'].get('value')
        self.updated_at = time.time()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'model': self.model,
            'color': self.color,
            'status': self.status,
            'next_agent': self.next_agent,
            'tokens_used': self.tokens_used,
            'tokens_max': self.tokens_max,
            'last_task': self.last_task,
            'last_warn': self.last_warn,
            'updated_at': self.updated_at,
        }


@dataclass
class LastAction:
    agent: str
    task: str

    def to_dict(self) -> dict:
        return {'agent': self.agent, 'task': self.task}


@dataclass
class ProjectState:
    project_name: str
    working_dir: str
    git_branch: str = "main"
    modified_files: list[str] = field(default_factory=list)
    last_done: Optional[LastAction] = None
    next_step: Optional[LastAction] = None
    agents: dict[str, AgentState] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'project_name': self.project_name,
            'working_dir': self.working_dir,
            'git_branch': self.git_branch,
            'modified_files': self.modified_files,
            'last_done': self.last_done.to_dict() if self.last_done else None,
            'next_step': self.next_step.to_dict() if self.next_step else None,
            'agents': {k: v.to_dict() for k, v in self.agents.items()},
        }
