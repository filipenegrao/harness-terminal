# NOTION_PROJECT_PROTOCOL.md

# Purpose

This protocol defines how orchestrators and agents must interact with the Notion database "Projetos".

The goal is:
- maintain project continuity;
- preserve operational memory;
- keep humans informed asynchronously;
- reduce token waste caused by repeated context reconstruction.

---

# Database

Primary database:
https://www.notion.so/35692a17a8b180888e69d384f8c6850f

Agents MUST treat the Notion database as:
- operational memory;
- project registry;
- task continuity layer;
- human-readable status dashboard.

---

# Mandatory Update Trigger

Agents MUST update the project entry whenever ANY of the following happens:

- a task is completed;
- a deliverable is generated;
- a repo is created;
- a milestone changes;
- the next recommended step changes;
- responsibility changes;
- blockers are identified;
- the project status materially changes.

---

# Fields

## `Nome do Projeto`

Human-readable project name.

Agents MUST:
- preserve naming consistency;
- avoid renaming existing projects unless explicitly instructed.

---

## `Status`

Allowed values:

- `Ideia`
- `Planejamento`
- `Em andamento`
- `Aguardando aprovação`
- `Bloqueado`
- `Concluído`
- `Arquivado`

Rules:
- NEVER set `Concluído` automatically.
- ONLY humans may approve final completion.
- Use `Bloqueado` when external dependency prevents progress.
- Use `Aguardando aprovação` when deliverables exist but require human review.

---

## `Última Task Finalizada`

Purpose:
Short operational memory of the latest meaningful completion.

Format:

YYYY-MM-DD — [agent] completed: [summary].

Examples:

2026-05-10 — Alfred completed: Initial PRD for Kumon-style SaaS generated.

2026-05-10 — Sabine completed: Homepage wireframe exported to /00-drafts/ui/homepage-v1.fig.

Rules:
- concise;
- factual;
- no marketing language;
- max 2 sentences;
- include artifact path when relevant.

---

## `Próxima Task`

Purpose:
Prevent project continuity loss.

Format:

[action] — owner: [agent/human]

Examples:

Review PRD and approve scope — owner: Filipe

Generate onboarding wireframes — owner: Sabine

Implement auth flow in Next.js — owner: Engineer

Rules:
- MUST be actionable;
- MUST describe ONE concrete next step;
- MUST identify owner when possible.

---

## `Data de início`

Fill when:
- project receives first active work.

Do NOT overwrite existing values.

---

## `Data de término`

Fill ONLY when:
- human explicitly confirms project completion.

NEVER infer completion automatically.

---

## `Prioridade`

Suggested interpretation:

- Alta
- Média
- Baixa

Agents MAY recommend priority changes but SHOULD avoid changing priorities automatically unless explicitly instructed.

---

## `git repo url`

Fill when:
- repository exists.

Rules:
- MUST be valid;
- NEVER invent URLs;
- preserve existing URLs.

---

## `local repo url`

Purpose:
Map local workspace path.

Examples:

/home/node/.openclaw/jobs/ui-ux/client-x/project-y

~/Development/ligatipo/storefront

Rules:
- use canonical local path;
- avoid temporary directories.

---

# Human Approval Rules

Agents MUST remember:

- AI proposes.
- Human decides.

Agents MAY:
- update progress;
- summarize work;
- suggest next actions;
- identify blockers.

Agents MUST NOT:
- mark project complete;
- archive projects;
- delete project information;
- overwrite human strategic decisions.

---

# Deliverable Awareness

When a deliverable is created, agents SHOULD mention:

- artifact type;
- path;
- repository;
- relevant branch;
- export format.

Example:

Output: PRD exported to:
jobs/micro-saas/math-app/00-drafts/prd-v1.md

---

# Blockers

If blocked, update:

Status = Bloqueado

And use:

Última Task Finalizada:
2026-05-10 — Alfred blocked: awaiting API credentials from human.

Próxima Task:
Provide OpenAI API key — owner: Filipe

---

# Orchestrator Responsibilities

Orchestrators MUST:
- ensure updates happen;
- avoid stale project states;
- maintain continuity across sessions;
- keep project memory synchronized between:
  - GitHub
  - local workspace
  - Notion
  - active agents

---

# Recommended Workflow

1. Read project row
2. Execute task
3. Generate artifacts
4. Update GitHub/local files
5. Update Notion entry
6. Notify human
7. Stop

---

# Anti-Entropy Rule

Agents SHOULD prefer updating the existing project row instead of creating duplicate projects.

Before creating a new entry:
- search for similar names;
- search related repositories;
- search existing client/project combinations.

---

# Minimalism Rule

Notion updates should be:
- concise;
- operational;
- quickly scannable.

Avoid:
- long reports;
- verbose explanations;
- unnecessary formatting;
- duplicated context.

Notion is a dashboard, not a documentation archive.

Documentation belongs in:
- markdown files;
- repositories;
- specs;
- deliverables.