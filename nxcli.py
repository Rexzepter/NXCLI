import os
import sys
import json
import subprocess
import argparse
import re
import mimetypes
import readline
import time
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.table import Table

CONFIG_PATH = os.path.expanduser("~/.config/nxcli/nxcli_config.json")
HISTORY_PATH = os.path.expanduser("~/.nxcli_history")
SESSION_DIR = os.path.expanduser("~/.config/nxcli/sessions")
SESSION_FILE = os.path.join(SESSION_DIR, "default.json")
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
    start_rgb = (255, 0, 0)
    end_rgb = (255, 165, 0)
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
    version = "v4.3 (HUD & Branching)"
    print(f"\n\033[1;37m{tagline}\033[0m \033[1;31m{version}\033[0m\n")

def ensure_config():
    if not os.path.exists(SESSION_DIR): os.makedirs(SESSION_DIR)
    config_dir = os.path.dirname(CONFIG_PATH)
    if not os.path.exists(config_dir): os.makedirs(config_dir)
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "agents": {
                "gemini": {"cmd": "gemini -m gemini-3.1-pro-preview -y -p", "strength": "Planning, search, orchestration.", "capabilities": ["text", "vision", "search"], "enabled": True},
                "qwen": {"cmd": "qwen -y -p", "strength": "Fast code, refactoring.", "capabilities": ["text", "code"], "enabled": True},
                "opencode": {"cmd": "opencode run", "strength": "Security, privacy audits.", "capabilities": ["text", "audit"], "enabled": True}
            },
            "master": "gemini",
            "fast_mode_threshold": 50,
            "interactive_clarification": True
        }
        with open(CONFIG_PATH, 'w') as f: json.dump(default_config, f, indent=2)

def load_config():
    ensure_config()
    with open(CONFIG_PATH, 'r') as f: return json.load(f)

def is_noise(line):
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, line.strip()): return True
    return False

def clean_output_text(text):
    if not text: return ""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        if is_noise(line): continue
        if ".Trash" in line and "path:" in line: continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()

def save_session(context, agents_used, name="default"):
    try:
        path = os.path.join(SESSION_DIR, f"{name}.json")
        with open(path, 'w') as f:
            json.dump({"context": context, "agents": agents_used, "timestamp": time.time()}, f)
        return True
    except: return False

def load_session(name="default"):
    path = os.path.join(SESSION_DIR, f"{name}.json")
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except: return None
    return None

def run_agent(agent_name, prompt, agent_info, status_prefix=None, silent=False):
    # Support for JIT Tool Synthesis: Use 'sh -c' if no command is provided
    base_cmd = agent_info.get('cmd', 'sh -c')
    cmd = f"{base_cmd} \"{prompt.replace('\"', '\\\"')}\""
    
    if silent:
        try:
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return clean_output_text(process.stdout)
        except: return None

    display_name = agent_name.upper()
    label = status_prefix or f"[bold red]NXCLI[/bold red] > [bold white]{display_name}"
    start_time = time.time()
    with console.status(f"{label} [bold white]is working... (0.0s)[/bold white]", spinner="dots") as status:
        try:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            output = []
            while True:
                line = process.stdout.readline()
                elapsed = time.time() - start_time
                status.update(f"{label} [bold white]is working... ({elapsed:.1f}s)[/bold white]")
                if not line and process.poll() is not None: break
                if line and not is_noise(line): output.append(line)
            process.wait()
            return "".join(output).strip() if process.returncode == 0 else None
        except: return None

def orchestrate(task, dry_run=False, verbose=False, initial_context=""):
    if not task.strip(): return initial_context
    config = load_config()
    agents = config['agents']
    master_agent = config['master']

    multi_step_words = ['then', 'and', 'after', 'next', 'then ask', 'follow up']
    is_simple = len(task.split()) < config.get('fast_mode_threshold', 50) and not any(w in task.lower() for w in multi_step_words)

    if is_simple and not verbose and not initial_context:
        plan = [{"agent": master_agent, "task": f"{task}\n\nSTRICT: No introductory preambles."}]
    else:
        with console.status("[bold red]NXCLI[/bold red] > [bold white]Identifying path...[/bold white]", spinner="dots") as status:
            status.update("[bold red]NXCLI[/bold red] > [bold cyan]ORCHESTRATION MODE[/bold cyan] [bold white]planning...[/bold white]")
            agent_desc = "\n".join([f"- {name}: {info['strength']}" for name, info in agents.items() if info['enabled']])
            
            # v4.3 JIT Tool Synthesis Directive
            orchestration_prompt = f"""
            Plan this task as a JSON list: {task}
            Agents: {agent_desc}
            If a local tool is needed but not in the list, use "local_shell" as the agent name.
            If the task is critically vague, return exactly: {{\"clarify\": \"Your question here\"}}
            Response format: JSON list only (or clarify object).
            """
            plan_raw = run_agent(master_agent, orchestration_prompt, agents[master_agent], silent=True)
            try:
                if "```json" in plan_raw: plan_raw = plan_raw.split("```json")[1].split("```")[0].strip()
                elif "```" in plan_raw: plan_raw = plan_raw.split("```")[1].split("```")[0].strip()
                res = json.loads(plan_raw)
                if isinstance(res, dict) and "clarify" in res:
                    status.stop()
                    console.print(Panel(res['clarify'], title="[bold red]Clarification Needed[/bold red]", border_style="red"))
                    user_answer = input("\033[1;33mYour Answer\033[0m > ").strip()
                    return orchestrate(f"{task}\n\nUser Clarification: {user_answer}", dry_run, verbose, initial_context)
                plan = res if isinstance(res, list) else [{"agent": master_agent, "task": task}]
            except: plan = [{"agent": master_agent, "task": task}]

    if dry_run: return initial_context

    context = initial_context
    last_output = ""
    agents_used = []
    
    # HUD Start
    total_start = time.time()
    for i, step in enumerate(plan):
        agent_name = step['agent']
        agents_used.append(agent_name.upper())
        full_prompt = f"{step['task']}\n\nContext:\n{context}" if context else step['task']
        
        mode_label = "[bold yellow]TURBO[/bold yellow]" if len(plan) == 1 else f"[bold cyan]STEP {i+1}/{len(plan)}[/bold cyan]"
        step_prefix = f"[bold red]NXCLI[/bold red] > {mode_label} [bold white]{agent_name.upper()}"
        
        agent_info = agents.get(agent_name, {"cmd": "sh -c", "strength": "Local Shell"})
        output = run_agent(agent_name, full_prompt, agent_info, status_prefix=step_prefix, silent=False)
        
        if output:
            context = output
            last_output = output
            save_session(context, agents_used)
        else:
            console.print(f"\n[bold red]![/bold red] Agent {agent_name.upper()} failed. Initiating Recovery...")
            recovery_prompt = f"The agent {agent_name} failed: {step['task']}. Suggest correction."
            correction = run_agent(master_agent, recovery_prompt, agents[master_agent], silent=True)
            if correction:
                context = f"Recovery attempt: {correction}\n\nPrevious: {context}"
            else: break
    
    if last_output:
        total_time = time.time() - total_start
        print("\n" + "\033[1;31m" + "─" * 60 + "\033[0m")
        print(f"\033[1;31m[NXCLI]\033[0m \033[1;33mChain:\033[0m {" ➔ ".join(agents_used)} \033[1;34m({total_time:.1f}s total)\033[0m\n")
        console.print(Markdown(clean_output_text(last_output)))
        print("\033[1;33m" + "─" * 60 + "\033[0m")
    
    return context

def start_interactive_shell(verbose=False):
    print_logo()
    if os.path.exists(HISTORY_PATH):
        try: readline.read_history_file(HISTORY_PATH)
        except: pass
    
    session = load_session()
    current_context = ""
    if session:
        console.print(Panel(f"Last Session: {', '.join(session['agents'])}\nStatus: [bold green]Ready to resume[/bold green]", title="[bold cyan]Session Restored[/bold cyan]", border_style="cyan"))
        current_context = session['context']

    print("Commands: [bold yellow]save <name>[/bold yellow], [bold yellow]load <name>[/bold yellow], [bold yellow]exit[/bold yellow]\n")
    while True:
        try:
            task = input("\033[1;31mNXCLI\033[0m > ").strip()
            if not task: continue
            
            if task.lower() in ['exit', 'quit']:
                print("\n[NXCLI] Come back soon 👋")
                try: readline.write_history_file(HISTORY_PATH)
                except: pass
                break
            
            # named checkpoint logic
            if task.lower().startswith("save "):
                name = task[5:].strip()
                if save_session(current_context, ["CHECKPOINT"], name):
                    console.print(f"[bold green]✓[/bold green] Checkpoint '{name}' saved.")
                continue
            
            if task.lower().startswith("load "):
                name = task[5:].strip()
                s = load_session(name)
                if s:
                    current_context = s['context']
                    console.print(f"[bold green]✓[/bold green] Checkpoint '{name}' restored.")
                else:
                    console.print(f"[bold red]![/bold red] Checkpoint '{name}' not found.")
                continue

            current_context = orchestrate(task, verbose=verbose, initial_context=current_context)
            try: readline.write_history_file(HISTORY_PATH)
            except: pass
        except (KeyboardInterrupt, EOFError):
            print("\n[NXCLI] Come back soon 👋")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NXCLI v4.3 Advanced")
    parser.add_argument("task", type=str, nargs='?', default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if args.task: orchestrate(args.task, dry_run=args.dry_run, verbose=args.verbose)
    else: start_interactive_shell(verbose=args.verbose)
