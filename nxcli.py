import os
import sys
import json
import subprocess
import argparse
import re
import mimetypes
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

import time

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
    start_rgb = (255, 0, 0)   # Bright Red
    end_rgb = (255, 165, 0)   # Orange
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
    tagline = "The High-Performance Agent Orchestrator"
    version = "v3.5 Turbo"
    print(f"\n\033[1;37m{tagline}\033[0m \033[1;31m{version}\033[0m\n")

def ensure_config():
    config_dir = os.path.dirname(CONFIG_PATH)
    if not os.path.exists(config_dir): os.makedirs(config_dir)
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "agents": {
                "gemini": {"cmd": "gemini -y -p", "strength": "Planning, search, orchestration.", "capabilities": ["text", "vision", "search"], "enabled": true},
                "qwen": {"cmd": "qwen -y -p", "strength": "Fast code, refactoring.", "capabilities": ["text", "code"], "enabled": true},
                "opencode": {"cmd": "opencode run", "strength": "Security, privacy audits.", "capabilities": ["text", "audit"], "enabled": true}
            },
            "master": "gemini",
            "fast_mode_threshold": 50,
            "interactive_clarification": true
        }
        with open(CONFIG_PATH, 'w') as f: json.dump(default_config, f, indent=2)

def load_config():
    ensure_config()
    with open(CONFIG_PATH, 'r') as f: return json.load(f)

def is_noise(line):
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, line.strip()): return True
    return False

def run_agent(agent_name, prompt, agent_info, status_prefix=None, silent=False):
    cmd = f"{agent_info['cmd']} \"{prompt.replace('\"', '\\\"')}\""
    
    if silent:
        try:
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = [l for l in process.stdout.splitlines() if not is_noise(l)]
            return "\n".join(output).strip()
        except: return None

    # NXCLI v3.6 - Live Timer Spinner
    display_name = agent_name.upper()
    label = status_prefix or f"[bold red]NXCLI[/bold red] > [bold white]{display_name}"
    
    start_time = time.time()
    with console.status(f"{label} [bold white]is working... (0.0s)[/bold white]", spinner="dots") as status:
        try:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            output = []
            
            # Use a while loop to update the timer while waiting for output
            while True:
                line = process.stdout.readline()
                elapsed = time.time() - start_time
                status.update(f"{label} [bold white]is working... ({elapsed:.1f}s)[/bold white]")
                
                if not line and process.poll() is not None:
                    break
                if line and not is_noise(line):
                    output.append(line)
            
            process.wait()
            return "".join(output).strip() if process.returncode == 0 else None
        except: return None

def clean_output_text(text):
    """Deep cleans the final output text from any persistent system leaks."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        if is_noise(line): continue
        # Specific brute-force check for the .Trash leak
        if ".Trash" in line and "path:" in line: continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()

def orchestrate(task, dry_run=False, verbose=False):
    if not task.strip(): return
    config = load_config()
    agents = config['agents']
    master_agent = config['master']

    # NXCLI v3.3 - Start with Path Identification
    with console.status("[bold red]NXCLI[/bold red] > [bold white]Identifying path...[/bold white]", spinner="dots") as status:
        multi_step_words = ['then', 'and', 'after', 'next', 'then ask', 'follow up']
        is_simple = len(task.split()) < config.get('fast_mode_threshold', 50) and not any(w in task.lower() for w in multi_step_words)

        if is_simple and not verbose:
            status.update("[bold red]NXCLI[/bold red] > [bold yellow]TURBO MODE[/bold yellow] [bold white]activated...[/bold white]")
            plan = [{"agent": master_agent, "task": f"{task}\n\nSTRICT: No introductory preambles."}]
        else:
            status.update("[bold red]NXCLI[/bold red] > [bold cyan]ORCHESTRATION MODE[/bold cyan] [bold white]planning...[/bold white]")
            agent_desc = "\n".join([f"- {name}: {info['strength']}" for name, info in agents.items() if info['enabled']])
            clarify_instruction = "If the task is critically vague, return exactly: {\"clarify\": \"Your question here\"}" if config.get('interactive_clarification', True) else ""
            
            orchestration_prompt = f"""
            Plan this task as a JSON list: {task}
            Agents: {agent_desc}
            {clarify_instruction}
            Response format: JSON list only (or clarify object).
            """
            
            # Internal call for the plan
            plan_raw = run_agent(master_agent, orchestration_prompt, agents[master_agent], silent=True)
            
            try:
                if "```json" in plan_raw: plan_raw = plan_raw.split("```json")[1].split("```")[0].strip()
                elif "```" in plan_raw: plan_raw = plan_raw.split("```")[1].split("```")[0].strip()
                res = json.loads(plan_raw)
                
                if isinstance(res, dict) and "clarify" in res:
                    status.stop() # Pause spinner for user input
                    print("\n" + "\033[1;31m" + "─" * 60 + "\033[0m")
                    console.print(Panel(res['clarify'], title="[bold red]Clarification Needed[/bold red]", border_style="red"))
                    user_answer = input("\033[1;33mYour Answer\033[0m > ").strip()
                    return orchestrate(f"{task}\n\nUser Clarification: {user_answer}", dry_run, verbose)
                
                plan = res if isinstance(res, list) else [{"agent": master_agent, "task": task}]
            except: plan = [{"agent": master_agent, "task": task}]

    if dry_run: return

    # Execution phase with active status
    context = ""
    last_output = ""
    agents_used = []
    for step in plan:
        if not isinstance(step, dict) or 'agent' not in step: continue
        agent_name = step['agent']
        agents_used.append(agent_name.upper())
        full_prompt = f"{step['task']}\n\nContext:\n{context}" if context else step['task']
        
        # Determine specific status message for this step
        mode_label = "[bold yellow]TURBO[/bold yellow]" if len(plan) == 1 else "[bold cyan]ORCH[/bold cyan]"
        step_prefix = f"[bold red]NXCLI[/bold red] > {mode_label} [bold white]{agent_name.upper()}"
        
        output = run_agent(agent_name, full_prompt, agents[agent_name], status_prefix=step_prefix, silent=False)
        if output:
            context = output
            last_output = output
        else: break
    
    if last_output:
        print("\n" + "\033[1;31m" + "─" * 60 + "\033[0m")
        print(f"\033[1;31m[NXCLI]\033[0m \033[1;33mChain of Command:\033[0m {" ➔ ".join(agents_used)}\n")
        
        # NXCLI v3.4 - Apply Deep Clean
        cleaned_markdown = clean_output_text(last_output)
        console.print(Markdown(cleaned_markdown))
        print("\033[1;33m" + "─" * 60 + "\033[0m")

def start_interactive_shell(verbose=False):
    print_logo()
    print("Type your task and press Enter. (Exit with 'exit')\n")
    while True:
        try:
            task = input("\033[1;31mNXCLI\033[0m > ").strip()
            if task.lower() in ['exit', 'quit']:
                print("\n[NXCLI] Come back soon 👋")
                break
            if task: orchestrate(task, verbose=verbose)
            # Removed redundant separator
        except (KeyboardInterrupt, EOFError):
            print("\n[NXCLI] Come back soon 👋")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NXCLI v3.3 Mode Aware")
    parser.add_argument("task", type=str, nargs='?', default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if args.task: orchestrate(args.task, dry_run=args.dry_run, verbose=args.verbose)
    else: start_interactive_shell(verbose=args.verbose)
