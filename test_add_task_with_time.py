"""测试 MCP 服务器添加带时间任务"""
import subprocess
import json
import time
import sys
from datetime import datetime, timedelta

def test_add_task_with_time():
    proc = subprocess.Popen(
        ["python", "-u", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=r"D:\program\ticktick-ai-demo"
    )
    
    time.sleep(2)
    
    # 计算明天的时间 (2026-02-25 14:00:00 +08:00)
    tomorrow = datetime(2026, 2, 25, 14, 0, 0)
    start_date = tomorrow.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    
    print(f"Testing add_task with startDate: {start_date}", file=sys.stderr)
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "add_task",
            "arguments": {
                "title": "测试任务-带明确时间",
                "content": "这是用于测试的带时间任务",
                "startDate": start_date,
                "timeZone": "Asia/Shanghai",
                "isAllDay": False
            }
        }
    }
    
    print("Sending request...", file=sys.stderr)
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()
    
    stdout_lines = []
    stderr_lines = []
    
    start_time = time.time()
    while time.time() - start_time < 30:
        if proc.stderr:
            while True:
                line = proc.stderr.readline()
                if not line:
                    break
                stderr_lines.append(line)
                print(f"[STDERR] {line.rstrip()}")
        
        if proc.stdout:
            line = proc.stdout.readline()
            if line:
                print(f"[STDOUT] {line.rstrip()}")
                stdout_lines.append(line)
                try:
                    response = json.loads(line)
                    if "result" in response:
                        print(f"\n=== SUCCESS ===")
                        print(f"Result: {response['result']}")
                        proc.terminate()
                        return True
                    elif "error" in response:
                        print(f"\n=== ERROR ===")
                        print(f"Error: {response['error']}")
                except:
                    pass
        
        time.sleep(0.1)
    
    print("Timeout!", file=sys.stderr)
    proc.terminate()
    return False

if __name__ == "__main__":
    test_add_task_with_time()
