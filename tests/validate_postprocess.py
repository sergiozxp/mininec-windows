"""End-to-end numerical checks for the Windows postprocessor."""
from __future__ import annotations
import csv, math, subprocess, sys
from pathlib import Path

def read_params(path):
    with path.open(newline="",encoding="utf-8") as f:
        return {row["parameter"]: float(row["value"]) for row in csv.DictReader(f)}

def check(exe, deck, out):
    out.mkdir(parents=True,exist_ok=True)
    p=subprocess.run([str(exe),"--input",str(deck),"--output",str(out)],
                     capture_output=True,text=True,timeout=240)
    if p.returncode:
        raise AssertionError(f"{deck}: exit {p.returncode}\n{p.stdout}\n{p.stderr}")
    required=["native_output.txt","summary.txt","parameters.csv","pattern.csv"]
    for name in required:
        if not (out/name).is_file() or (out/name).stat().st_size == 0:
            raise AssertionError(f"{deck}: missing/empty {name}")
    m=read_params(out/"parameters.csv")
    for key in ("resistance_ohm","reactance_ohm","reflection_coefficient_magnitude",
                "vswr","mismatch_loss_dB","max_gain_dBi",
                "max_gain_zenith_deg","max_gain_azimuth_deg","pattern_points"):
        if key not in m or not math.isfinite(m[key]):
            raise AssertionError(f"{deck}: missing/non-finite {key}: {m.get(key)}")
    if m["reference_ohm"] != 50 or m["pattern_points"] < 1:
        raise AssertionError(f"{deck}: invalid reference or pattern count")
    if not 0 <= m["reflection_coefficient_magnitude"] < 1:
        raise AssertionError(f"{deck}: reflection coefficient outside [0,1)")
    if m["vswr"] < 1 or m["mismatch_loss_dB"] < 0:
        raise AssertionError(f"{deck}: invalid VSWR/mismatch loss")
    expected=(1+m["reflection_coefficient_magnitude"])/(1-m["reflection_coefficient_magnitude"])
    if abs(expected-m["vswr"]) > 1e-9*max(1,expected):
        raise AssertionError(f"{deck}: VSWR equation mismatch")
    print(deck.name, "OK", "Z=",m["resistance_ohm"],"+j",m["reactance_ohm"],
          "VSWR=",m["vswr"],"Gmax=",m["max_gain_dBi"],"dBi")

if __name__=="__main__":
    root=Path(__file__).resolve().parents[1]
    exe=Path(sys.argv[1]) if len(sys.argv)>1 else root/"dist"/"mininec.exe"
    check(exe,root/"examples"/"dipole_free.txt",Path("test-results")/"free")
    check(exe,root/"examples"/"dipole_ground.txt",Path("test-results")/"ground")
