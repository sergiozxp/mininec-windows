"""Smoke test the packaged EXE with an inclusive 3–30 MHz, 50-point sweep."""
from __future__ import annotations
import csv
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    exe = Path(sys.argv[1]).resolve()
    example = ROOT / "examples" / "dipole_sweep_50.txt"
    with tempfile.TemporaryDirectory(prefix="mininec-sweep-") as tmp:
        out = Path(tmp) / "results"
        run = subprocess.run(
            [str(exe), "--input", str(example), "--output", str(out), "--timings"],
            cwd=ROOT, text=True, capture_output=True, timeout=900,
        )
        if run.returncode:
            raise SystemExit(f"EXE returned {run.returncode}\nSTDOUT:\n{run.stdout}\nSTDERR:\n{run.stderr}")
        with (out / "parameters.csv").open(encoding="utf-8-sig", newline="") as f:
            parameters = list(csv.DictReader(f))
        assert len(parameters) == 50, f"expected 50 parameters, found {len(parameters)}"
        frequencies = [float(row["frequency_MHz"]) for row in parameters]
        assert math.isclose(frequencies[0], 3.0, rel_tol=0, abs_tol=1e-8), frequencies[0]
        assert math.isclose(frequencies[-1], 30.0, rel_tol=0, abs_tol=1e-8), frequencies[-1]
        assert all(b > a for a, b in zip(frequencies, frequencies[1:])), "frequency grid is not increasing"
        for row in parameters:
            assert math.isfinite(float(row["resistance_ohm"]))
            assert math.isfinite(float(row["reactance_ohm"]))
        with (out / "timings.csv").open(encoding="utf-8-sig", newline="") as f:
            timings = list(csv.DictReader(f))
        per_frequency = [row for row in timings if row["scope"] == "per_frequency_compute"]
        total = [row for row in timings if row["scope"] == "total_engine_call"]
        assert len(per_frequency) == 50, f"expected 50 per-frequency timings, got {len(per_frequency)}"
        assert len(total) == 1, f"expected one total timing row, got {len(total)}"
        seconds = [float(row["solver_seconds"]) for row in per_frequency]
        total_s = float(total[0]["solver_seconds"])
        assert all(math.isfinite(value) and value >= 0 for value in seconds)
        assert math.isfinite(total_s) and total_s > 0
        assert total_s + 1e-6 >= sum(seconds), "total engine-call time is less than measured solver calls"
        native = (out / "native_output.txt").read_text(encoding="utf-8")
        assert len(re.findall(r"^FREQUENCY\s*\(\s*MHZ\s*\):", native, re.I | re.M)) == 50
        print(f"PASS: 50 frequencies 3–30 MHz in one EXE process; total {total_s:.6f} s")

if __name__ == "__main__":
    main()
