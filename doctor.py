"""Read-only Windows/Aside permission preflight. Never reads credentials."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', required=True, type=Path)
    local = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local')))
    parser.add_argument('--aside-cli', type=Path,
                        default=local / 'Aside/CLI/current/aside.exe')
    args = parser.parse_args()
    requested = args.folder.absolute()
    folder = requested.resolve()
    report = {'requestedFolder': str(requested), 'physicalFolder': str(folder),
              'pathRedirected': str(requested).casefold() != str(folder).casefold(),
              'hostDirectoryExists': folder.is_dir(),
              'cliExists': args.aside_cli.is_file(),
              'credentialsRead': False, 'settingsChanged': False,
              'runtimeWriteVerified': False, 'readyForCredentialSave': False}
    if not report['cliExists']:
        report['nextAction'] = 'Install the official Aside CLI.'
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    # Only selected non-secret settings are returned; never dump getAll().
    code = """
const diagPermission = aside.settings.get('permission');
const diagTarget = __TARGET__;
const diagNormalize = x => String(x).replace(/\\\\/g, '/').toLowerCase().replace(/[/]$/, '');
const diagContains = (root, target) => target === root || target.startsWith(root + '/');
console.log(JSON.stringify({
  defaultMode: aside.settings.get('defaultPermissionMode'),
  sandboxEnabled: diagPermission.sandbox?.enabled,
  outsideRead: diagPermission.files?.outsideRead,
  outsideWrite: diagPermission.files?.outsideWrite,
  savedWriteGrantCoversFolder: (diagPermission.files?.writableRoots || []).some(
    root => diagContains(diagNormalize(root), diagNormalize(diagTarget))),
  neutralReplWorkingFolder: pwd,
  neutralReplSessionContainsFolder: diagContains(diagNormalize(pwd), diagNormalize(diagTarget))
}));
""".replace('__TARGET__', json.dumps(str(folder)))
    try:
        result = subprocess.run([str(args.aside_cli), 'repl', '--host', 'local', code],
                                capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=40)
        clean = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', result.stdout)
        metadata = None
        for line in clean.splitlines():
            try:
                candidate = json.loads(line)
            except ValueError:
                continue
            if isinstance(candidate, dict) and 'savedWriteGrantCoversFolder' in candidate:
                metadata = candidate
        if result.returncode != 0 or metadata is None:
            report['nextAction'] = 'Aside metadata could not be read. Check CLI sign-in and host connection.'
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2
        report['aside'] = metadata
        report['nextAction'] = (
            'Check that the explicitly approved grant names the physical folder, '
            'then verify a harmless disposable write in the intended AI task. '
            'If that task still reports a project/session boundary error, use the '
            'supported Working folder control. Neutral REPL scope does not by '
            'itself establish the scope of a separate AI task.')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        # Diagnosis only: never claim a real write passed based on configuration.
        return 2
    except (OSError, subprocess.TimeoutExpired):
        report['nextAction'] = 'CLI unavailable or timed out; no credential operation was attempted.'
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
