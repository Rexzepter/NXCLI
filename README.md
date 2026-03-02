# NXCLI: The High-Performance Agent Orchestrator 🚀

**NXCLI** is a terminal-native orchestrator designed to unify your local AI agents (Gemini, Qwen, Claude, OpenCode) into a single, cohesive "Super-Agent." 

It doesn't just "talk" to models; it **conducts** them.

---

## ⚡ Performance
NXCLI is optimized for minimal latency. It uses an intelligent heuristic to decide whether a task requires complex orchestration or can be handled directly.

### Speed Test Results
*Testing prompt: "What is the capital of Japan?"*

| Mode | Path | Total Time | Speedup |
| :--- | :--- | :--- | :--- |
| **Turbo** | Direct to Agent | **~9.6s** | **2.8x Faster** |
| **Standard** | Planning ➔ Execution | **~27.3s** | Baseline |

By skipping the planning phase for simple queries, Turbo Mode eliminates over **65% of the wait time**.

---

## 🏗️ How it Works
NXCLI uses a **Planning-Execution-Piping** loop to solve complex tasks:
1.  **Analyze:** The Master Brain (Gemini 3.1 Pro) decomposes your natural language request into a sequence of specialized steps.
2.  **Assign:** Each step is assigned to the best agent for the job (e.g., Qwen for fast code, OpenCode for security, Gemini for research).
3.  **Pipe:** Output from one agent is automatically fed as context to the next, creating a "mesh" of intelligence.

## ✨ Features

### 🧠 Core Intelligence
-   **v5.0 Intelligence:** Powered by Gemini 3.1 Pro with a **1-million-token** context window for massive multi-agent workflows.
-   **Workspace Pulse:** Automatically scans your project context (Git status, file structure, language detection) to provide agents with "eyes" on your workspace.
-   **Recursive Sub-Planning:** Fractally decompose complex engineering tasks into nested mini-orchestrations for higher reliability.
-   **Reflect & Repair:** Autonomous self-correction loops. If an agent fails or outputs an error, the Master Brain automatically generates a surgical fix.
-   **JIT Tool Synthesis:** Dynamically generates commands for local shell tools (like `docker`, `git`, or `ffmpeg`) even if they aren't pre-configured.

### 🛠️ Developer Productivity
-   **Turbo Mode:** Bypasses planning for simple queries to provide near-instant responses.
-   **Named Checkpoints:** Use `save <name>` and `load <name>` commands to version your agent sessions and branch off alternative approaches.
-   **Session Persistence:** Automatically saves and restores your last orchestration state across terminal restarts.
-   **Command History:** Persistent REPL history with full Up/Down arrow support.
-   **Direct-to-Result:** Strict directives ensure agents skip the "I will search for..." filler and jump straight to the answer.

### 🎨 Premium UI/UX
-   **Rich UI:** High-contrast TrueColor gradients (Crimson Blaze) and full Markdown rendering using the `rich` engine.
-   **Interactive Shell:** A persistent REPL mode that lets you build complex projects without re-typing `nxcli`.
-   **Live Step Timer:** Real-time counter for every execution step, giving you instant feedback on agent latency.
-   **Noise Suppression (Deep Silence):** Completely suppresses technical noise, EPERM errors, and YOLO mode warnings for a pure, branded output.

## 🚀 Getting Started

### 1. Prerequisites
You must have the following AI agents installed and available in your `PATH`:
- [Gemini CLI](https://geminicli.com)
- [Qwen Code](https://github.com/QwenLM/Qwen-Agent)
- [OpenCode](https://opencode.ai)

### 2. Installation
Clone the repository and run the installation script:
```bash
git clone https://github.com/Rexzepter/NXCLI.git
cd nxcli
./install.sh
```

### 3. Usage
- **Direct Mode:** `nxcli "Write a secure Python scraper for example.com"`
- **Interactive Mode:** Simply type `nxcli` to enter the persistent shell.
- **Dry Run:** `nxcli "Your Task" --dry-run` to see the plan without executing agents.

## ⚙️ Configuration
Customize your agents and their "Strengths" in `~/.config/nxcli/nxcli_config.json`. You can add any CLI-based agent by simply adding its command and capabilities to the registry.

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.

---
*Built for the next generation of Vibe Coders.*
