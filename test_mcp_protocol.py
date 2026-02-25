"""测试 MCP 协议握手和工具调用"""
import subprocess
import json
import time
import sys

def test_mcp():
    # 启动 MCP 服务器
    proc = subprocess.Popen(
        ["python", "-u", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=r"D:\program\ticktick-ai-demo",
        bufsize=1
    )
    
    def send_request(req):
        print(f"==> Sending: {json.dumps(req)[:100]}...", file=sys.stderr)
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
    
    def read_response(timeout=5):
        start = time.time()
        while time.time() - start < timeout:
            line = proc.stdout.readline()
            if line:
                try:
                    resp = json.loads(line)
                    print(f"<== Received: {json.dumps(resp)[:200]}...", file=sys.stderr)
                    return resp
                except:
                    print(f"<== Raw: {line[:100]}...", file=sys.stderr)
            time.sleep(0.1)
        return None
    
    # 等待服务器启动
    time.sleep(2)
    
    # 1. 发送 initialize 请求
    init_request = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    send_request(init_request)
    resp = read_response(timeout=10)
    if resp:
        print(f"Initialize response: {resp}", file=sys.stderr)
    
    # 2. 发送 initialized 通知
    send_request({"jsonrpc": "2.0", "method": "initialized", "params": {}})
    
    # 3. 列出工具
    time.sleep(1)
    list_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    send_request(list_request)
    resp = read_response(timeout=10)
    if resp:
        print(f"Tools list: {resp}", file=sys.stderr)
    
    # 4. 调用 get_tasks
    time.sleep(1)
    call_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "get_tasks",
            "arguments": {}
        }
    }
    send_request(call_request)
    resp = read_response(timeout=30)
    if resp:
        print(f"Get tasks result: {resp}", file=sys.stderr)
        if "result" in resp:
            print("\n=== SUCCESS ===")
            print(resp["result"])
    else:
        print("No response received!", file=sys.stderr)
    
    proc.terminate()

if __name__ == "__main__":
    test_mcp()
