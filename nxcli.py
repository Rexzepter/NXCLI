import os
import sys
import json
import subprocess
import argparse
import re
import mimetypes
import readline
import time
import signal
import select
import fcntl
import tempfile
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

CONFIG_PATH = os.path.expanduser("~/.config/nxcli/nxcli_config.json")
HISTORY_PATH = os.path.expanduser("~/.nxcli_history")
SESSION_DIR = os.path.expanduser("~/.config/nxcli/sessions")
SESSION_FILE = os.path.join(SESSION_DIR, "default.json")
TURBO_TEMP_DIR = "/tmp/nxcli_empty"
console = Console()

NOISE_PATTERNS = [
    r"YOLO mode is enabled.*",
    r"Loaded cached credentials.*",
    r"Error getting folder structure.*",
    r"at async.*",
    r"errno: -1.*",
    r"code: 'EPERM'.*",
    r"syscall: 'scandir'.*",
    r"path: '/Users/siberia/.Trash'.*",
    r"\{.*",
    r"\}.*",
    r"Attempt \d+ failed.*",
    r"Retrying after.*"
]

LOGO_LINES = [
    "███╗   ██╗██╗  ██╗ ██████╗██╗      ██╗",
    "████╗  ██║╚██╗██╔╝██╔════╝██║      ██║",
    "██╔██╗ ██║ ╚███╔╝ ██║     ██║      ██║",
    "██║╚██╗██║ ██╔██╗ ██║     ██║      ██║",
    "██║ ╚████║██╔╝ ██╗╚██████╗███████╗ ██║",
    "╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝╚══════╝ ╚═╝"
]

def get_animated_logo(offset):
    start_rgb = (255, 0, 0)
    end_rgb = (255, 165, 0)
    full_logo = ""
    for line in LOGO_LINES:
        colored_line = ""
        length = len(line)
        for i, char in enumerate(line):
            if char == ' ':
                colored_line += char
                continue
            ratio = ((i / max(1, length - 1)) + offset) % 1.0
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
            colored_line += f"\033[38;2;{r};{g};{b}m{char}"
        full_logo += colored_line + "\033[0m\n"
    tagline = "The High-Performance Agent Orchestrator"
    version = "v5.6 (Hard Limits)"
    full_logo += f"\n\033[1;37m{tagline}\033[0m \033[1;31m{version}\033[0m\n"
    return Text.from_ansi(full_logo)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        # Default fallback if file is missing
        return {"agents": {"gemini": {"cmd": "gemini -y -p", "enabled": True}}, "master": "gemini"}
    with open(CONFIG_PATH, 'r') as f: return json.load(f)

def clean_output_text(text):
    if not text: return ""
    preambles = [r"(?i)^i will (search|run|begin|start|provide|perform).*", r"(?i)^here is the.*", r"(?i)^based on the.*", r"(?i)^sure, i can.*", r"(?i)^the capital of.*"]
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        if any(re.search(p, line.strip()) for p in NOISE_PATTERNS): continue
        if any(re.match(p, line.strip()) for p in preambles): continue
        if ".Trash" in line and "path:" in line: continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()

def run_agent(agent_name, prompt, cmd_str, status_prefix=None, silent=False, isolation=False, timeout=None):
    # v5.6 Stability: Safe Environment & Timeout Logic
    env = os.environ.copy()
    # Strip potentially conflicting env vars
    for key in ['PYTHONPATH', 'NODE_OPTIONS']:
        env.pop(key, None)
        
    if isolation: 
        if not os.path.exists(TURBO_TEMP_DIR): os.makedirs(TURBO_TEMP_DIR)
        env["HOME"] = TURBO_TEMP_DIR

    full_cmd = f"{cmd_str} \"{prompt.replace('\"', '\\\"')}\""
    
    if silent:
        try:
            # Silent execution still needs a timeout to prevent background hangs
            process = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, env=env, timeout=timeout or 60)
            return clean_output_text(process.stdout)
        except subprocess.TimeoutExpired:
            return None
        except: return None

    start_time = time.time()
    with console.status(f"{status_prefix} [bold white]working... (0.0s)[/bold white]", spinner="dots") as status:
        process = None
        try:
            process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid, env=env)
            fd = process.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            output = []
            
            while process.poll() is None:
                elapsed = time.time() - start_time
                status.update(f"{status_prefix} [bold white]working... ({elapsed:.1f}s)[/bold white]")
                
                # Check for Hard Timeout
                if timeout and elapsed > timeout:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    return f"ERROR: Agent timed out after {timeout}s."

                try:
                    line = process.stdout.readline()
                    if line: output.append(line)
                except BlockingIOError: pass
                time.sleep(0.05)
            
            final_stdout, _ = process.communicate()
            if final_stdout: output.append(final_stdout)
            return "".join(output).strip() if process.returncode == 0 else None
        except KeyboardInterrupt:
            if process: os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            return "CANCELLED"
        except: return None

def orchestrate(task, dry_run=False, verbose=False, initial_context=""):
    if not task.strip(): return initial_context
    
    # v5.6 FAST HEURISTIC
    simple_keywords = ['then', 'and', 'after', 'next', 'follow up', 'using', 'file', 'code', 'git', 'repo']
    is_simple = not any(w in task.lower() for w in simple_keywords) and len(task.split()) < 20

    config = load_config()
    master_agent = config.get('master', 'gemini')
    master_cmd = config['agents'][master_agent]['cmd']

    if is_simple and not verbose:
        # ULTIMATE TURBO: 15s Hard Limit
        prefix = f"[bold red]NXCLI[/bold red] > [bold yellow]TURBO[/bold yellow] [bold white]FLASH[/bold white]"
        # Fallback to master command if turbo is unstable
        cmd = config['agents'][master_agent]['cmd']
        
        output = run_agent("turbo", f"{initial_context}\n\nTask: {task}\n\nSTRICT: No preamble.", cmd, status_prefix=prefix, isolation=False, timeout=60)
        breadcrumb = ["FLASH"]
    else:
        # ORCHESTRATION MODE
        with console.status("[bold red]NXCLI[/bold red] > [bold white]Planning...[/bold white]", spinner="dots") as status:
            orchestration_prompt = f"Plan task as JSON list: {task}\nAgents: {json.dumps(config['agents'])}"
            # 30s timeout for planning
            plan_raw = run_agent(master_agent, orchestration_prompt, master_cmd, silent=True, timeout=30)
            
            if not plan_raw or plan_raw == "CANCELLED" or "ERROR" in plan_raw:
                return initial_context
            try:
                if "```json" in plan_raw: plan_raw = plan_raw.split("```json")[1].split("```")[0].strip()
                plan = json.loads(plan_raw)
            except: plan = [{"agent": master_agent, "task": task}]

        if dry_run: return initial_context

        context = initial_context
        breadcrumb = []
        last_output = ""
        for i, step in enumerate(plan):
            agent_name = step['agent']
            agent_info = config['agents'].get(agent_name, {"cmd": "sh -c"})
            breadcrumb.append(agent_name.upper())
            prefix = f"[bold red]NXCLI[/bold red] > [bold cyan]STEP {i+1}/{len(plan)}[/bold cyan] [bold white]{agent_name.upper()}[/bold white]"
            
            # 120s timeout for execution steps
            output = run_agent(agent_name, f"{step['task']}\n\nContext:\n{context}", agent_info['cmd'], status_prefix=prefix, timeout=120)
            
            if output == "CANCELLED" or not output or "ERROR" in output: break
            context = output
            last_output = output
        output = last_output

    if output and output != "CANCELLED":
        print("\n" + "\033[1;31m" + "─" * 60 + "\033[0m")
        if "ERROR:" in output:
             console.print(f"[bold red]![/bold red] {output}")
        else:
            print(f"\033[1;31m[NXCLI]\033[0m \033[1;33mChain:\033[0m {" ➔ ".join(breadcrumb)}\n")
            console.print(Markdown(clean_output_text(output)))
        print("\033[1;33m" + "─" * 60 + "\033[0m")
    return output

def start_interactive_shell(verbose=False):
    offset = 0
    with Live(get_animated_logo(offset), console=console, refresh_per_second=20) as live:
        for _ in range(15):
            offset += 0.05
            live.update(get_animated_logo(offset))
            time.sleep(0.05)
    
    current_context = ""
    print("Commands: [bold yellow]exit[/bold yellow]\n")
    while True:
        try:
            task = input("\033[1;31mNXCLI\033[0m > ").strip()
            if not task: continue
            if task.lower() == 'exit': break
            current_context = orchestrate(task, verbose=verbose, initial_context=current_context)
        except (KeyboardInterrupt, EOFError):
            print("\n[NXCLI] Come back soon 👋")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NXCLI v5.6")
    parser.add_argument("task", type=str, nargs='?', default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if args.task: orchestrate(args.task, verbose=args.verbose)
    else: start_interactive_shell(verbose=args.verbose)
