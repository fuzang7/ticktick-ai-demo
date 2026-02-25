"""测试 MCP 服务器调用"""
import subprocess
import json
import time
import sys

def test_mcp_call():
    # 启动 MCP 服务器
    proc = subprocess.Popen(
        ["python", "-u", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=r"D:\program\ticktick-ai-demo"
    )
    
    # 等待服务器初始化
    time.sleep(2)
    
    # 发送 MCP 请求
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_tasks",
            "arguments": {}
        }
    }
    
    print("Sending request...", file=sys.stderr)
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()
    
    # 读取响应
    import select
    stdout_lines = []
    stderr_lines = []
    
    start_time = time.time()
    while time.time() - start_time < 30:
        # 检查 stderr
        if proc.stderr:
            while True:
                line = proc.stderr.readline()
                if not line:
                    break
                stderr_lines.append(line)
                print(f"[STDERR] {line.rstrip()}")
        
        # 检查 stdout
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
    test_mcp_call()
