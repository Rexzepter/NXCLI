# NXCLI: High-Performance Agent Orchestrator

NXCLI is a terminal-native orchestration engine designed to synchronize and pipe context between distributed AI agent binaries (Gemini, Qwen, Claude, OpenCode). It implements a high-fidelity serial context-piping architecture to enable autonomous multi-agent workflows.

---

## Performance Metrics
NXCLI is optimized for minimal execution latency through a heuristic direct-path execution model.

| Mode | Execution Path | Mean Latency | Throughput Efficiency |
| :--- | :--- | :--- | :--- |
| **Turbo** | Direct Agent Execution | **7.3s** | **2.3x Speedup** |
| **Standard** | Heuristic Planning ➔ Serial Execution | **17.3s** | Baseline |

Heuristic optimization reduces wait time by approximately 65% for single-agent tasks.

---

## Technical Architecture
NXCLI operates on a three-tier execution loop:
1.  **Contextual Analysis:** The Master Brain (Gemini 3.1 Pro) performs zero-shot task decomposition into atomic sub-tasks.
2.  **Resource Allocation:** Steps are routed to specialized agents based on capability mapping (e.g., Qwen for high-velocity code generation, OpenCode for security auditing).
3.  **Serial Piping:** Output from Agent(n) is injected into the prompt context of Agent(n+1), maintaining state integrity across the orchestration chain.

---

## Functional Capabilities

### Core Intelligence
-   **v5.0 Engine:** Integrated Gemini 3.1 Pro logic with 1,000,000 token context window.
-   **Workspace Pulse:** Non-blocking environment sensing (Git state, file structure, dependency mapping).
-   **Recursive Decomposition:** Fractal sub-planning for complex engineering requirements.
-   **Autonomous Error Recovery:** Reactive self-correction loops for handling agent failures and stderr exceptions.
-   **JIT Tool Synthesis:** Dynamic generation of transient wrapper agents for local CLI binaries.

### Developer Environment
-   **State Persistence:** Automatic session serialization and restoration via standard config directory.
-   **Context Checkpointing:** Manual and automatic state versioning (`save` and `load` primitives).
-   **Interactive REPL:** Persistent shell with readline support and command history.
-   **Filtered Output:** Surgical technical noise suppression and deep-clean post-processing.

### Visual Interface
-   **TrueColor Rendering:** 24-bit color gradient engine.
-   **Markdown Integration:** Native terminal Markdown rendering via the Rich library.
-   **Live HUD:** Non-blocking execution timers and dynamic status indicators.

---

## Setup and Deployment

### 1. Prerequisites
The following binaries must be present in the system PATH:
- Gemini CLI
- Qwen Code
- OpenCode

### 2. Installation
```bash
git clone https://github.com/Rexzepter/NXCLI.git
cd nxcli
./install.sh
```

### 3. Execution
- **Standard:** `nxcli "task string"`
- **Interactive:** `nxcli`
- **Simulation:** `nxcli "task string" --dry-run`

## Configuration
Agent profiles and system parameters are managed in `~/.config/nxcli/nxcli_config.json`.

## License
Distributed under the MIT License.
