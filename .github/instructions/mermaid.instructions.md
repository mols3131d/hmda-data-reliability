---
name: "Local Mermaid Diagrams"
description: "Create, edit, validate, and preview Mermaid diagrams locally in VS Code using the Mermaid extension and GitHub Copilot. Do not use Mermaid Chart cloud, account, sync, credits, or paid services."
applyTo: "**/*.md, **/*.mmd, **/*.mermaid"
---

# Mermaid AI Skills

When the user asks to create, edit, or visualize any diagram, use the Mermaid
VS Code extension tools and commands described below.

## Workflow

1. Determine the diagram type and generate Mermaid syntax.
1. Write the diagram to a `.mmd` file in the project.
1. Validate syntax: correct first-line keyword, arrow types, balanced brackets.
1. Preview via the Mermaid extension — open the `.mmd` file (auto-preview) or run
   **MermaidChart: Preview Diagram** (`mermaidChart.preview`).

## LM Tools — call these for every diagram interaction

- `mermaid-diagram-validator` — validate Mermaid syntax before presenting any diagram
- `mermaid-diagram-preview` — render a live preview inside VS Code after generating
- `get-syntax-docs-mermaid` — fetch correct syntax docs for any diagram type

## VS Code Commands

Invoke via Command Palette or the VS Code command API (GitHub Copilot in VS Code only).
Do not invent command IDs. Prefer writing/editing `.mmd` files when a command is not needed.

### Diagram editing & preview

- **Preview** (`mermaidChart.preview`) — preview the active Mermaid editor (`.mmd` / `.mermaid` must be open).
- **Create Diagram** (`mermaidChart.createMermaidFile`) — creates a demo flowchart and opens preview side by side.
- **Improve Diagram** (`mermaidChart.improveDiagram`) — uses Copilot / LM API; suggests layout + styling variants for the active diagram.

### Generate diagrams (GitHub Copilot required)

- **Generate Diagram from Code** (`mermaidChart.generateDiagramFromCode`)
- **Generate Cloud Diagram** (`mermaidChart.generateCloudDiagram`)
- **Generate ER Diagram** (`mermaidChart.generateERDiagram`)
- **Generate Docker Diagram** (`mermaidChart.generateDockerDiagram`)
- **Open AI Chat** (`mermaidChart.openCopilotChat`)

### Install / update this pack

- **MermaidChart: Install AI Skills…** (`mermaidChart.installAiSkills`)

## @mermaid-chart slash commands

| Command | Purpose |
| -------------------------------------- | ------------------------------------ |
| `/generate_diagram_from_code` | General diagram from any source file |
| `/generate_execution_sequence` | Sequence diagram from code flow |
| `/generate_er_diagram` | ER diagram from schema / models |
| `/generate_cloud_architecture_diagram` | Cloud / CI-CD architecture |
| `/generate_docker_diagram` | Architecture from Dockerfiles |
| `/generate_c4_topdown_architecture` | C4 top-down architecture |
| `/analyze_code_ownership` | Code ownership diagram |
| `/generate_dependency_diagram` | Dependency / security visualisation |

## Rules

1. Always call `mermaid-diagram-validator` before showing any diagram.
1. Always call `mermaid-diagram-preview` after generating a diagram.
1. Use `get-syntax-docs-mermaid` before generating an unfamiliar diagram type.
1. Prefer `@mermaid-chart` slash commands for complex generation.
1. Write diagrams to `.mmd` files; never return unvalidated Mermaid syntax.

## Docs

More commands and features: <https://marketplace.visualstudio.com/items?itemName=MermaidChart.vscode-mermaid-chart>
