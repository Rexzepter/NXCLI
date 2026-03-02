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
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

CONFIG_PATH = os.path.expanduser("~/.config/nxcli/nxcli_config.json")
HISTORY_PATH = os.path.expanduser("~/.nxcli_history")
SESSION_DIR = os.path.expanduser("~/.config/nxcli/sessions")
SESSION_FILE = os.path.join(SESSION_DIR, "default.json")
console = Console()

NOISE_PATTERNS = [
    r"YOLO mode is enabled.*",
    r"All tool calls will be automatically approved.*",
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
    version = "v5.6.3"
    full_logo += f"\n\033[1;37m{tagline}\033[0m \033[1;31m{version}\033[0m\n"
    return Text.from_ansi(full_logo)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"agents": {"gemini": {"cmd": "gemini -y -p", "enabled": True}}, "master": "gemini"}
    with open(CONFIG_PATH, 'r') as f: return json.load(f)

def is_noise(line):
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, line.strip()): return True
    return False

def clean_output_text(text):
    if not text: return ""
    preambles = [r"(?i)^i will (search|run|begin|start|provide|perform).*", r"(?i)^here is the.*", r"(?i)^based on the.*", r"(?i)^sure, i can.*", r"(?i)^the capital of.*"]
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        if is_noise(line): continue
        if any(re.match(p, line.strip()) for p in preambles): continue
        if ".Trash" in line and "path:" in line: continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()

def run_agent(agent_name, prompt, cmd_str, status_prefix=None, silent=False):
    env = os.environ.copy()
    full_cmd = f"{cmd_str} \"{prompt.replace('\"', '\\\"')}\""
    
    if silent:
        try:
            # Capturing stdout AND stderr to ensure clean context
            process = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, env=env, timeout=120)
            return clean_output_text(process.stdout)
        except: return None

    start_time = time.time()
    with console.status(f"{status_prefix} [bold white]starting...[/bold white]", spinner="dots") as status:
        process = None
        try:
            process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid, env=env)
            fd = process.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            output = []
            while process.poll() is None:
                elapsed = time.time() - start_time
                status.update(f"{status_prefix} [bold white]working... ({elapsed:.1f}s) [dim]ESC to Cancel[/dim][/bold white]")
                try:
                    line = process.stdout.readline()
                    if line and not is_noise(line): output.append(line)
                except BlockingIOError: pass
                time.sleep(0.05)
            final_stdout, _ = process.communicate()
            if final_stdout:
                for l in final_stdout.splitlines():
                    if not is_noise(l): output.append(l + "\n")
            return "".join(output).strip() if process.returncode == 0 else None
        except KeyboardInterrupt:
            if process: os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            return "CANCELLED"
        except: return None

def orchestrate(task, dry_run=False, verbose=False, initial_context=""):
    if not task.strip(): return initial_context
    config = load_config()
    master_agent = config.get('master', 'gemini')
    master_cmd = config['agents'][master_agent]['cmd']

    simple_keywords = ['then', 'and', 'after', 'next', 'follow up', 'using']
    is_simple = not any(w in task.lower() for w in simple_keywords) and len(task.split()) < 20

    if is_simple and not verbose:
        breadcrumb = ["TURBO"]
        output = run_agent("turbo", f"{initial_context}\n\nTask: {task}", master_cmd, status_prefix=f"[bold red]NXCLI[/bold red] > [bold yellow]TURBO[/bold yellow]")
    else:
        with console.status("[bold red]NXCLI[/bold red] > [bold white]Planning...[/bold white]", spinner="dots") as status:
            agent_desc = "\n".join([f"- {name}: {info['strength']}" for name, info in config['agents'].items() if info['enabled']])
            orchestration_prompt = f"Plan task as JSON list: {task}\nAgents: {agent_desc}"
            plan_raw = run_agent(master_agent, orchestration_prompt, master_cmd, silent=True)
            if not plan_raw or plan_raw == "CANCELLED": return initial_context
            try:
                if "```json" in plan_raw: plan_raw = plan_raw.split("```json")[1].split("```")[0].strip()
                elif "```" in plan_raw: plan_raw = plan_raw.split("```")[1].split("```")[0].strip()
                plan = json.loads(plan_raw)
            except: plan = [{"agent": master_agent, "task": task}]

        if dry_run: return initial_context

        context = initial_context
        breadcrumb = []
        last_output = ""
        for i, step in enumerate(plan):
            if not isinstance(step, dict): continue
            name = step['agent']
            cmd = config['agents'].get(name, config['agents'][master_agent])['cmd']
            breadcrumb.append(name.upper())
            prefix = f"[bold red]NXCLI[/bold red] > [bold cyan]STEP {i+1}/{len(plan)}[/bold cyan] [bold white]{name.upper()}[/bold white]"
            output = run_agent(name, f"{step['task']}\n\nContext:\n{context}", cmd, status_prefix=prefix)
            if output == "CANCELLED" or not output: break
            context = output
            last_output = output
        output = last_output

    if output and output != "CANCELLED":
        console.print("\n" + "\033[1;31m" + "─" * 60 + "\033[0m")
        console.print(f"\033[1;31m[NXCLI]\033[0m \033[1;33mChain:\033[0m {" ➔ ".join(breadcrumb)}\n")
        final_text = clean_output_text(output)
        try:
            console.print(Markdown(final_text))
        except:
            console.print(final_text)
        console.print("\033[1;33m" + "─" * 60 + "\033[0m")
    return output

def start_interactive_shell(verbose=False):
    offset = 0
    with Live(get_animated_logo(offset), console=console, refresh_per_second=20) as live:
        for _ in range(15):
            offset += 0.05
            live.update(get_animated_logo(offset))
            time.sleep(0.05)
    if os.path.exists(HISTORY_PATH):
        try: readline.read_history_file(HISTORY_PATH)
        except: pass
    console.print("Commands: [bold yellow]exit[/bold yellow]\n")
    while True:
        try:
            task = input("\033[1;31mNXCLI\033[0m > ").strip()
            if not task: continue
            if task.lower() == 'exit': break
            
            # v5.6.3 - Restore Agents command if missing
            if task.lower() == 'agents':
                config = load_config()
                console.print("\n[bold white]Available Agents:[/bold white]")
                for name in sorted(config['agents'].keys()):
                    status = "[bold green]ONLINE[/bold green]" if config['agents'][name].get('enabled', False) else "[bold red]OFFLINE[/bold red]"
                    console.print(f" - {name.upper():<10} {status}")
                continue

            orchestrate(task, verbose=verbose)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[NXCLI] Come back soon 👋")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NXCLI v5.6.2")
    parser.add_argument("task", type=str, nargs='?', default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.task: orchestrate(args.task, dry_run=args.dry_run, verbose=args.verbose)
    else: start_interactive_shell(verbose=args.verbose)
