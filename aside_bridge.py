"""Send a task to the installed Aside AI through its official MCP server.
No browser restart, private API, credential copying or shell command building.
"""
import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prompt', nargs='?')
    parser.add_argument('--session', help='Continue a session returned by Aside')
    parser.add_argument('--tools', action='store_true')
    parser.add_argument('--timeout', type=int, default=180)
    local = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local')))
    parser.add_argument('--aside-cli', type=Path,
                        default=local / 'Aside/CLI/current/aside.exe')
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    if not args.tools and not args.prompt:
        parser.error('Provide a prompt or --tools')
    cli = args.aside_cli
    if not cli.is_file():
        parser.error('Official Aside CLI is not installed at its expected path')
    process = subprocess.Popen([str(cli), 'mcp', '--host', 'local'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding='utf-8')
    lines = queue.Queue()
    def read():
        for line in process.stdout:
            lines.put(line)
        lines.put(None)
    threading.Thread(target=read, daemon=True).start()
    def send(message):
        process.stdin.write(json.dumps(message, ensure_ascii=False) + '\n')
        process.stdin.flush()
    def request(identifier, method, params=None):
        send(dict(jsonrpc='2.0', id=identifier, method=method, params=params or {}))
        import time
        deadline = time.monotonic() + args.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Aside response timed out; task may still be running')
            line = lines.get(timeout=remaining)
            if line is None:
                raise RuntimeError('Aside MCP exited before responding')
            try:
                response = json.loads(line)
            except ValueError:
                continue
            if response.get('id') != identifier:
                continue
            if 'error' in response:
                raise RuntimeError(str(response['error']))
            return response.get('result', {})
    try:
        request(1, 'initialize', {'protocolVersion': '2024-11-05',
            'capabilities': {}, 'clientInfo': {'name': 'codex-aside-bridge', 'version': '1.0'}})
        send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        if args.tools:
            result = request(2, 'tools/list')
            print(json.dumps({'tools': [item['name'] for item in result['tools']]}, ensure_ascii=False))
            return 0
        arguments = {'prompt': args.prompt}
        if args.session:
            arguments['session_id'] = args.session
        result = request(2, 'tools/call', {'name': 'exec', 'arguments': arguments})
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result.get('isError') else 0
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Close only the MCP process we own; never terminate Aside Browser.
            process.terminate()
            process.wait(timeout=5)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    try:
        sys.exit(main())
    except (RuntimeError, TimeoutError, queue.Empty) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
