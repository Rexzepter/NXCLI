import subprocess
import concurrent.futures

def ask_agent(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout.strip()
    except: return "Error"

prompt = "You are an expert software architect. Suggest 3 high-impact features for 'NXCLI', a terminal-native AI agent orchestrator. Focus on features that improve developer workflow or system autonomy. Be concise."

gemini_cmd = f'gemini -m gemini-3.1-pro-preview -y -p "{prompt}"'
qwen_cmd = f'qwen -y -p "{prompt}"'

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = {
        executor.submit(ask_agent, gemini_cmd): "GEMINI",
        executor.submit(ask_agent, qwen_cmd): "QWEN"
    }
    for future in concurrent.futures.as_completed(futures):
        print(f"\n--- {futures[future]} SUGGESTIONS ---")
        print(future.result())
