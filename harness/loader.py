"""Reads harness.toml and builds initial ProjectState."""

import os
import subprocess
import tomllib
from pathlib import Path

from state import AgentState, ProjectState


def _git_branch(working_dir: str) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.stdout.strip() or "main"
    except Exception:
        return "main"


def load_config(config_path: Path) -> ProjectState:
    """Load harness.toml and return a fully initialised ProjectState."""
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    project = raw.get("project", {})
    working_dir = os.path.expanduser(project.get("working_dir", "."))
    working_dir = str(Path(config_path).parent / working_dir)

    agents: dict[str, AgentState] = {}
    for a in raw.get("agents", []):
        agent = AgentState(
            id=a["id"],
            name=a["name"],
            icon=a.get("icon", ""),
            model=a.get("model", "unknown"),
            color=a.get("color", "blue"),
            tokens_max=a.get("tokens_max", 100000),
            command=a.get("command", ""),
        )
        agents[agent.id] = agent

    return ProjectState(
        project_name=project.get("name", Path(working_dir).name),
        working_dir=working_dir,
        git_branch=_git_branch(working_dir),
        agents=agents,
    )
