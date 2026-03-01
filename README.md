# NXCLI: The Multimodal Agent Orchestrator 🚀

**NXCLI** is a high-performance terminal orchestrator designed to unify your local AI agents (Gemini, Qwen, Claude, OpenCode) into a single, cohesive "Super-Agent." 

It doesn't just "talk" to models; it **conducts** them.

---

## 🏗️ How it Works
NXCLI uses a **Planning-Execution-Piping** loop to solve complex tasks:
1.  **Analyze:** The Master Brain (Gemini 2.0) decomposes your natural language request into a sequence of specialized steps.
2.  **Assign:** Each step is assigned to the best agent for the job (e.g., Qwen for fast code, OpenCode for security, Gemini for research).
3.  **Pipe:** Output from one agent is automatically fed as context to the next, creating a "mesh" of intelligence.

## ✨ Features
-   **Turbo Mode:** Bypasses planning for simple queries to provide near-instant responses.
-   **Multimodal Aware:** Automatically detects file paths (images, PDFs) in your prompt and routes them to vision-capable agents.
-   **Rich UI:** High-contrast TrueColor gradients and full Markdown rendering using the `rich` engine.
-   **Interactive Shell:** A persistent REPL mode that lets you build complex projects without re-typing `nxcli`.
-   **Noise Suppression:** Automatically filters technical system errors and YOLO mode warnings for a clean interface.

## 🚀 Getting Started

### 1. Prerequisites
You must have the following AI agents installed and available in your `PATH`:
- [Gemini CLI](https://geminicli.com)
- [Qwen Code](https://github.com/QwenLM/Qwen-Agent)
- [OpenCode](https://opencode.ai)

### 2. Installation
Clone the repository and run the installation script:
```bash
git clone https://github.com/your-username/nxcli.git
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
