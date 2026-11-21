"""Simple non-interactive executable check."""
import subprocess
import sys

if __name__ == '__main__':
    command = [sys.argv[1] if len(sys.argv) > 1 else 'mininec.exe', '--help']
    r = subprocess.run(command, text=True, capture_output=True, timeout=120)
    combined = (r.stdout + r.stderr).lower()
    if r.returncode != 0 or not ('frequency' in combined and 'wire' in combined):
        print('Smoke test failed', r.returncode, r.stdout[-2000:], r.stderr[-2000:])
        sys.exit(1)
    print('MININEC executable: CLI --help passed.')
