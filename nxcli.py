import os
import sys
import json
import subprocess
import argparse
import re
import mimetypes
from rich.console import Console
from rich.markdown import Markdown

CONFIG_PATH = os.path.expanduser("~/.config/nxcli/nxcli_config.json")
console = Console()

NOISE_PATTERNS = [
    r"YOLO mode is enabled.*",
    r"Loaded cached credentials.*",
    r"Error getting folder structure.*",
    r"at async.*",
    r"errno: -1.*",
    r"code: 'EPERM'.*",
    r"syscall: 'scandir'.*",
    r"\{.*",
    r"\}.*",
    r"Attempt \d+ failed.*",
    r"Retrying after.*"
]

def print_logo():
    logo_lines = [
        "███╗   ██╗██╗  ██╗ ██████╗██╗      ██╗",
        "████╗  ██║╚██╗██╔╝██╔════╝██║      ██║",
        "██╔██╗ ██║ ╚███╔╝ ██║     ██║      ██║",
        "██║╚██╗██║ ██╔██╗ ██║     ██║      ██║",
        "██║ ╚████║██╔╝ ██╗╚██████╗███████╗ ██║",
        "╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝╚══════╝ ╚═╝"
    ]
    start_rgb = (255, 36, 0)   # Scarlet
    end_rgb = (255, 140, 0)   # Neon Orange
    print("") 
    for line in logo_lines:
        colored_line = ""
        length = len(line)
        for i, char in enumerate(line):
            if char == ' ':
                colored_line += char
                continue
            ratio = i / max(1, length - 1)
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
            colored_line += f"\033[38;2;{r};{g};{b}m{char}"
        print(colored_line + "\033[0m")
    tagline = "The Multimodal Agent Orchestrator"
    version = "v2.9 Deep Silence"
    print(f"\n\033[1;37m{tagline}\033[0m \033[1;34m{version}\033[0m\n")

def ensure_config():
    config_dir = os.path.dirname(CONFIG_PATH)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "agents": {
                "gemini": {"cmd": "gemini -y -p", "strength": "Planning, search, orchestration.", "capabilities": ["text", "vision", "search"], "enabled": True},
                "qwen": {"cmd": "qwen -y -p", "strength": "Fast code, refactoring.", "capabilities": ["text", "code"], "enabled": True},
                "opencode": {"cmd": "opencode run", "strength": "Security, privacy audits.", "capabilities": ["text", "audit"], "enabled": True}
            },
            "master": "gemini",
            "fast_mode_threshold": 50
        }
        with open(CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=2)

def load_config():
    ensure_config()
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def is_noise(line):
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, line.strip()):
            return True
    return False

def run_agent(agent_name, prompt, agent_info, silent=False):
    cmd = f"{agent_info['cmd']} \"{prompt.replace('\"', '\\\"')}\""
    
    # Use a spinner for all visible agent tasks
    status_msg = f"[bold cyan]NXCLI[/bold cyan] > [bold white]{agent_name.upper()} is working...[/bold white]"
    
    try:
        if silent:
            # Capture both stdout and stderr to prevent noise leak
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = []
            for line in process.stdout.splitlines():
                if not is_noise(line):
                    output.append(line)
            return "\n".join(output).strip()
        else:
            with console.status(status_msg, spinner="dots"):
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                output = []
                for line in process.stdout:
                    if not is_noise(line):
                        output.append(line)
                process.wait()
                return "".join(output).strip() if process.returncode == 0 else None
    except:
        return None

def orchestrate(task, dry_run=False, verbose=False):
    if not task.strip(): return
    config = load_config()
    agents = config['agents']
    master_agent = config['master']

    multi_step_words = ['then', 'and', 'after', 'next', 'then ask', 'follow up']
    is_simple = len(task.split()) < config.get('fast_mode_threshold', 50) and not any(w in task.lower() for w in multi_step_words)

    if is_simple and not verbose:
        direct_task = f"{task}\n\nSTRICT: No introductory preambles. Start the answer immediately."
        plan = [{"agent": master_agent, "task": direct_task}]
    else:
        agent_desc = "\n".join([f"- {name}: {info['strength']}" for name, info in agents.items() if info['enabled']])
        orchestration_prompt = f"""
        Plan this task as a JSON list: {task}
        Agents:
        {agent_desc}
        
        STRICT DIRECTIVE: For the final step, the agent MUST NOT use any introductory preambles like "I will search for...", "I will begin by...", or "Here is the result...". 
        Jump directly into the answer or code. 
        Response format: JSON list only.
        """
        
        if verbose: print(f"[NXCLI] 🧠 Planning...")
        plan_raw = run_agent(master_agent, orchestration_prompt, agents[master_agent], silent=True)
        
        try:
            if "```json" in plan_raw:
                plan_raw = plan_raw.split("```json")[1].split("```")[0].strip()
            elif "```" in plan_raw:
                plan_raw = plan_raw.split("```")[1].split("```")[0].strip()
            plan = json.loads(plan_raw)
            # Ensure plan is a list of dicts
            if not isinstance(plan, list) or (len(plan) > 0 and not isinstance(plan[0], dict)):
                raise ValueError("Invalid JSON format")
        except:
            plan = [{"agent": master_agent, "task": task}]

    if dry_run: return

    context = ""
    last_output = ""
    agents_used = []
    for step in plan:
        if not isinstance(step, dict) or 'agent' not in step: continue
        
        agent_name = step['agent']
        agents_used.append(agent_name.upper())
        full_prompt = f"{step['task']}\n\nContext:\n{context}" if context else step['task']
        
        output = run_agent(agent_name, full_prompt, agents[agent_name], silent=not verbose)
        if output:
            context = output
            last_output = output
        else:
            break
    
    if last_output:
        print("\n" + "\033[1;36m" + "─" * 60 + "\033[0m")
        summary = " ➔ ".join(agents_used)
        print(f"\033[1;35m[NXCLI]\033[0m \033[1;36mChain of Command:\033[0m {summary}\n")
        
        clean_lines = [l for l in last_output.splitlines() if not is_noise(l)]
        console.print(Markdown("\n".join(clean_lines)))
        print("\033[1;35m" + "─" * 60 + "\033[0m")

def start_interactive_shell(verbose=False):
    print_logo()
    print("Type your task and press Enter. (Exit with 'exit')\n")
    while True:
        try:
            task = input("\033[1;36mNXCLI\033[0m > ").strip()
            if task.lower() in ['exit', 'quit']:
                print("\n[NXCLI] Come back soon 👋")
                break
            if task: orchestrate(task, verbose=verbose)
            print("\n" + "-"*20 + "\n")
        except (KeyboardInterrupt, EOFError):
            print("\n[NXCLI] Come back soon 👋")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NXCLI v2.9 Deep Silence")
    parser.add_argument("task", type=str, nargs='?', default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if args.task: orchestrate(args.task, dry_run=args.dry_run, verbose=args.verbose)
    else: start_interactive_shell(verbose=args.verbose)
