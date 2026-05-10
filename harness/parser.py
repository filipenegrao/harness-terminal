"""Signal regex parser for the Harness Signal Protocol v1.

See AGENTS.md for the full protocol spec.
"""

import re
from typing import Optional

# Required signal — must appear on the line for it to be treated as a signal
REQUIRED = re.compile(
    r'\[STATUS:(?P<status>working|idle|done|error)\]'
    r'(?:\s+\[NEXT:(?P<next>[\w]+|none)\])?'
    r'(?:\s+\[TOKENS:(?P<tokens>\d+)\])?'
)

# Optional signal patterns — scanned independently from REQUIRED
OPTIONAL: dict[str, re.Pattern[str]] = {
    'task':    re.compile(r'\[TASK:(?P<value>[^\]]{1,120})\]'),
    'warn':    re.compile(r'\[WARN:(?P<value>[^\]]{1,240})\]'),
    'handoff': re.compile(r'\[HANDOFF:(?P<target>\w+)\s+(?P<reason>[^\]]{1,120})\]'),
}


def parse_line(agent_id: str, line: str) -> Optional[dict]:
    """Extract Harness signals from a single line of agent output.

    Args:
        agent_id: ID of the agent that produced this line.
        line: Raw stdout line (trailing newline OK).

    Returns:
        Parsed signal dict, or None if no required signal is present.
        Dict always contains: agent_id, status.
        Conditionally contains: next (str|None), tokens (int|None),
        task (dict), warn (dict), handoff (dict).
    """
    m = REQUIRED.search(line)
    if not m:
        return None

    result: dict = {'agent_id': agent_id, **m.groupdict()}

    if result.get('tokens') is not None:
        result['tokens'] = int(result['tokens'])

    # Normalise NEXT:none → Python None
    if result.get('next') == 'none':
        result['next'] = None

    for key, pat in OPTIONAL.items():
        om = pat.search(line)
        if om:
            result[key] = om.groupdict()

    return result
