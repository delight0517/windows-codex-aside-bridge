"""Register or remove the official Aside MCP server in local Codex config."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tomllib


def configure(action, config, cli, name):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
        raise ValueError('Server name must contain only letters, numbers, _ or -')
    if action == 'install' and not cli.is_file():
        raise ValueError('Install the official Aside CLI first, or supply --aside-cli')
    expected = {
        'command': str(cli.resolve()),
        'args': ['mcp', '--host', 'local'],
        'startup_timeout_sec': 30,
        'tool_timeout_sec': 180,
        'enabled_tools': ['exec', 'repl'],
    }
    config.parent.mkdir(parents=True, exist_ok=True)
    lock = config.with_name(config.name + '.aside-bridge.lock')
    # Exclusive create serializes this utility; never delete somebody else's lock.
    with lock.open('x'):
        pass
    try:
        original = config.read_bytes() if config.exists() else b''
        text = original.decode('utf-8-sig')
        before = tomllib.loads(text)
        current = before.get('mcp_servers', {}).get(name)
        if action == 'install' and current == expected:
            return {'status': 'already configured', 'server': name}
        if action == 'uninstall' and current is None:
            return {'status': 'already absent', 'server': name}
        if current is not None and current != expected:
            raise ValueError('Existing server differs from this registration. '
                             'Choose another --name or review it manually; nothing changed.')
        heading = f'[mcp_servers.{name}]'
        if action == 'install':
            lines = [heading] + [f'{key} = {json.dumps(value)}'
                                 for key, value in expected.items()]
            changed = text.rstrip() + '\n\n' + '\n'.join(lines) + '\n'
        else:
            # Remove only the exact table this installer owns. Nested/custom
            # settings make the equality check above fail rather than deleting them.
            pattern = re.compile(r'^\[mcp_servers\.' + re.escape(name) +
                                 r'\][^\r\n]*\r?\n.*?(?=^\[|\Z)', re.M | re.S)
            changed, count = pattern.subn('', text)
            if count != 1:
                raise ValueError('Cannot isolate the registration safely; nothing changed.')
        after = tomllib.loads(changed)
        remainder = dict(after)
        remainder['mcp_servers'] = dict(after.get('mcp_servers', {}))
        remainder['mcp_servers'].pop(name, None)
        prior = dict(before)
        prior['mcp_servers'] = dict(before.get('mcp_servers', {}))
        prior['mcp_servers'].pop(name, None)
        if remainder != prior:
            raise ValueError('Unrelated config would change; nothing written.')
        backup = config.with_name(config.name + '.before-windows-aside')
        if not backup.exists():
            with backup.open('xb') as stream:
                stream.write(original)
        # Respect concurrent edits from Codex or another configuration utility.
        now = config.read_bytes() if config.exists() else b''
        if now != original:
            raise ValueError('Config changed concurrently; retry after editing finishes.')
        prefix = b'\xef\xbb\xbf' if original.startswith(b'\xef\xbb\xbf') else b''
        temporary = config.with_name(config.name + '.aside-bridge.tmp')
        temporary.write_bytes(prefix + changed.encode('utf-8'))
        temporary.replace(config)
        return {'status': 'installed' if action == 'install' else 'removed',
                'server': name, 'config': str(config), 'backup': str(backup)}
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'uninstall'])
    parser.add_argument('--name', default='aside')
    codex_dir = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    parser.add_argument('--config', type=Path, default=codex_dir / 'config.toml')
    local = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local')))
    parser.add_argument('--aside-cli', type=Path,
                        default=local / 'Aside/CLI/current/aside.exe')
    args = parser.parse_args()
    try:
        result = configure(args.action, args.config, args.aside_cli, args.name)
        print(json.dumps(result))
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
