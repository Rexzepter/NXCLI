import subprocess
import concurrent.futures
import sys

def ask_agent(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout.strip()
    except: return "Error"

prompt = "You are an expert software architect. Suggest 3 high-impact features for 'NXCLI', a terminal-native AI agent orchestrator. Focus on features that improve developer productivity, system observability, or advanced agent interactions. Be concise."

gemini_cmd = 'gemini -m gemini-3.1-pro-preview -y -p "' + prompt + '"'
qwen_cmd = 'qwen -y -p "' + prompt + '"'

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = {
        executor.submit(ask_agent, gemini_cmd): "GEMINI",
        executor.submit(ask_agent, qwen_cmd): "QWEN"
    }
    for name in ["GEMINI", "QWEN"]:
        # Find the future for this name
        f = next(future for future, n in futures.items() if n == name)
        print(f"\n--- {name} SUGGESTIONS ---")
        print(f.result())
