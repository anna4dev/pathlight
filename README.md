# Pathlight

Pathlight is an MCP server for IEP-grounded lesson adaptation.

This README defines the **Shape A** v1 contract:
- Claude is the primary reasoning engine.
- MCP provides structured context, validation, and deterministic rendering.
- The output is a teacher-usable draft artifact, not free-form prose.

## Problem

Teachers often receive long IEPs and need to adapt tomorrow's lesson quickly.
Most AI outputs are either generic accommodations or unstructured text that is hard to use in class.

Pathlight focuses on one practical goal: produce a grounded, editable teacher draft for one lesson and one student.

## Product Contract (Shape A)

### Responsibilities

- **Claude**: reason over lesson + IEP, draft modifications, and revise from validation feedback.
- **MCP server**: expose resources, enforce output contract, run validation checks, and render deterministic artifacts.

### Data Flow

```mermaid
flowchart LR
teacher[TeacherPrompt] --> claude[ClaudeDesktop]
claude -->|read_resource| resources[MCPResources]
claude -->|call_tool_optional| tools[MCPToolsValidationRenderer]
resources --> iep[IEPData]
resources --> lesson[LessonData]
tools --> output[DeterministicTeacherArtifact]
```

## v1 Scope Freeze

Pathlight v1 intentionally targets:
- one student
- one lesson
- one high-quality teacher deliverable

This is deliberate to maximize output quality and reproducibility.

## v1 Deliverable

The canonical output is a **renderer-controlled artifact** with:
- before-class checklist
- phase-specific teacher actions
- scaffolded questions tied to lesson question IDs
- accommodation reminders with source references

Claude can draft content, but final structure is controlled by schema + renderer.

## Validation Contract

v1 validation is multi-layered (not schema-only):
- schema validity checks
- IEP grounding checks
- accommodation coverage checks
- lesson-question reference checks
- unsupported output detection

Validation errors are structured so Claude can self-correct or request teacher input.

## Resource Contract (Phase 2)

Pathlight now exposes segmented, predictable resources for scoped Claude reads.

- Backward-compatible full resources:
  - `student://{id}/full`
  - `lesson://{id}/full`
- Student segmented resources:
  - `student://{id}/profile`
  - `student://{id}/plaafp`
  - `student://{id}/plaafp/{section_id}`
  - `student://{id}/goals`
  - `student://{id}/goals/{goal_id}`
  - `student://{id}/accommodations`
  - `student://{id}/accommodations/{acc_id}`
  - `student://{id}/scopes/instructional_core`
- Lesson segmented resources:
  - `lesson://{id}/overview`
  - `lesson://{id}/phases`
  - `lesson://{id}/phases/{phase_id}`
  - `lesson://{id}/questions/{question_id}`
  - `lesson://{id}/scopes/phase/{phase_id}`

### Claude-grounding fields in `lesson://{id}/overview`

`lesson://{id}/overview` returns a Claude-oriented summary payload including:
- `grade`
- `subject`
- `unit_topic`
- `duration_minutes`
- `instructional_objective_summary`

### Instruction-only scope in `student://{id}/scopes/instructional_core`

This scope intentionally includes classroom-relevant fields only (profile teaching context, PLAAFP, goals, accommodations) and excludes unrelated metadata.

## Human in the Loop

AI output is draft-first.
Teacher workflow requirements:
- edit any section
- reject full draft
- regenerate only selected section(s)

Accepted sections are preserved during partial regeneration.

## Current Repository State

This repo includes:
- MCP server scaffolding and tool registry
- structured lesson and student resources
- prior workflow-oriented services and outputs (kept for reference during migration)

The active migration goal is to make Shape A the default path.

## What Is Explicitly Out of Scope (v1)

- vector retrieval and vector databases
- session memory and long-lived agent state
- multi-agent orchestration
- analytics platformization
- multi-student classroom optimization

## Example Data

- Student data: `data/students/35110GST.json`
- Lesson data: `data/lessons/community.json`
- Previous workflow outputs (reference only): `data/output/8b.json`, `data/output/70b.json`

## Architecture Notes

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design details and migration context.

## Running Locally

### 1. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -e .
```

### 3. Claude Desktop config

#### macOS

`~/Library/Application Support/Claude/claude_desktop_config.json`

#### Windows

`%APPDATA%\Claude\claude_desktop_config.json`

### macOS / Linux example

```json
{
  "mcpServers": {
    "pathlight": {
      "command": "/Users/username/path_to_project/.venv/bin/python3",
      "args": ["-m", "src.pathlight.server"]
    }
  }
}
```

### Windows example

```json
{
  "mcpServers": {
    "pathlight": {
      "command": "C:\\Users\\username\\path_to_project\\.venv\\Scripts\\python.exe",
      "args": ["-m", "src.pathlight.server"]
    }
  }
}
```

Optional environment variables:

```bash
ANTHROPIC_API_KEY=...
GROQ_API_KEY=...
```

Notes:
- During Shape A migration, external model keys are optional for context-serving and non-LLM checks.
- If you enable model-backed steps, configure provider keys accordingly.

### 4. Restart Claude Desktop

### MCP Inspector

```bash
npx @modelcontextprotocol/inspector python3 -m src.pathlight.server
```

