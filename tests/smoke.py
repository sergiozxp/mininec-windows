"""Windows executable smoke tests for both CLI modes."""
from pathlib import Path
import re
import subprocess
import sys

if __name__ == "__main__":
    exe = sys.argv[1] if len(sys.argv) > 1 else "mininec.exe"
    tests = [
        ("help", [exe, "--help"], ()),
        ("text input file", [exe, "--input", str(Path("examples") / "dipole_free.txt")],
         ("impedance", "frequency")),
    ]
    for name, command, expected in tests:
        r = subprocess.run(command, text=True, capture_output=True, timeout=180)
        output = (r.stdout + r.stderr).lower()
        if r.returncode != 0 or any(word not in output for word in expected):
            print(name, "failed; exit code", r.returncode, r.stdout[-2000:], r.stderr[-2000:])
            sys.exit(1)
        print(name, "OK")
