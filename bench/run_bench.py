#!/usr/bin/env python3
"""Reproducible three-case MININEC/NEC2 impedance comparison bench.

No numeric equality is assumed for non-identical feed/ground implementations.
"""
import argparse
import csv
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

CASES = {
    "dipole_free": {"description": "10 m dipole in free space", "ground": None, "vertical": False},
    "dipole_ground": {"description": "10 m dipole 6 m over representative real ground", "ground": (13, .005), "vertical": False},
    "vertical_radials": {"description": "Elevated 1/4-wave-style vertical with 4 elevated radials (provisional)", "ground": (13, .005), "vertical": True},
}
FREQUENCIES = (7.1, 14.2)
# For the vertical, use 7.1 MHz only; 10 m monopole at 14.2 MHz is not a quarter-wave.
FREQS = {"dipole_free": (14.2,), "dipole_ground": (14.2,), "vertical_radials": (7.1,)}

def geometry(case, density=1):
    """Return (tag, nseg, x1,y1,z1,x2,y2,z2,radius) tuples, in meters."""
    if case != "vertical_radials":
        return [(1, 21*density, -5,0,6, 5,0,6, .001)]
    # The vertical has a small initial feed stub; radial connection is a 5-wire junction.
    # Cross-engine impedance at that junction is a *diagnostic*, not a reference truth.
    wires = [(1, 41*density, 0,0,2, 0,0,12, .002)]
    for tag,(dx,dy) in enumerate(((1,0),(-1,0),(0,1),(0,-1)), start=2):
        wires.append((tag, 21*density, 0,0,2, 10*dx,10*dy,2, .002))
    return wires

def mininec_command(exe, case, freq, density):
    a = [str(exe), "-f", str(freq)]
    for w in geometry(case,density):
        a.extend(["-w", ",".join(str(v) for v in w)])
    # Pulse 10 for 21 segments: a near-centre dipole excitation.
    # With denser mesh, use the central pulse number.
    a.append("--excitation-pulse=" + (str(10*density) if case != "vertical_radials" else "1"))
    g = CASES[case]["ground"]
    if g:
        a.append(f"--medium={g[0]},{g[1]},0")
    a.append("--option=none")
    return a

def nec_text(case, freq, density):
    wires = geometry(case,density)
    lines = ["CM Three-case comparison benchmark", "CM Source: mininec-windows/bench", "CE"]
    for w in wires:
        tag,n,*coords=w
        lines.append("GW " + " ".join(map(str,(tag,n,*coords))))
    lines.append("GE 0")
    g = CASES[case]["ground"]
    lines.append("GN -1" if g is None else f"GN 2 0 0 {g[0]} {g[1]}")
    # NEC feed is at segment centre; MININEC uses a pulse boundary.
    # At the vertical multi-wire junction source placement differs substantially.
    seg = (21*density+1)//2 if case != "vertical_radials" else 1
    lines.append(f"EX 0 1 {seg} 0 1 0")
    lines.append(f"FR 0 1 0 0 {freq} 0")
    lines.extend(["XQ", "EN"])
    return "\n".join(lines)+"\n"

FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
MINI_Z = re.compile(r"IMPEDANCE\s*=\s*\(\s*("+FLOAT+r")\s*,\s*("+FLOAT+r")\s*J\s*\)", re.I)
MINI_F = re.compile(r"FREQUENCY\s*(?:\(\s*MHZ\s*\))?\s*[:=]?\s*("+FLOAT+r")",re.I)

def parse_mininec(s):
    matches=list(MINI_Z.finditer(s))
    if not matches:
        raise ValueError("No MININEC feed-point impedance found; inspect raw output")
    m=matches[-1]
    return float(m.group(1)),float(m.group(2))

def parse_nec(s):
    """Parse first input impedance table of a nec2c *single frequency* output.

    Strictly expects the standard NEC-2 INPUT PARAMETERS table. Never silently
    match an arbitrary pair of numbers.
    """
    lines=s.splitlines()
    for i,line in enumerate(lines):
        if "INPUT PARAMETERS" not in line.upper():
            continue
        for j in range(i+1,min(i+25,len(lines))):
            hdr=lines[j].upper()
            if "IMPEDANCE" in hdr and "REAL" in hdr and "IMAG" in hdr:
                # Standard NEC-2: TAG SEG VOLT_REAL VOLT_IMAG CUR_REAL CUR_IMAG
                # IMP_REAL IMP_IMAG ADMIT_REAL ADMIT_IMAG POWER
                for line2 in lines[j+1:j+8]:
                    vals=re.findall(FLOAT,line2)
                    if len(vals)>=11 and re.match(r"^\s*\d+\s+\d+\s+",line2):
                        return float(vals[6]),float(vals[7])
    raise ValueError("NEC2 impedance table not recognized; inspect raw .out and extend parser")

def run_command(command, stdout_file, timeout):
    done=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
    stdout_file.write_text(done.stdout,encoding="utf-8",errors="replace")
    if done.stderr:
        stdout_file.with_suffix(stdout_file.suffix+".stderr.txt").write_text(done.stderr,encoding="utf-8")
    if done.returncode:
        raise RuntimeError(f"Command failed (code={done.returncode}): {command!r}")
    return done.stdout

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mininec", default="mininec.exe",help="Path to MININEC executable, or omit to generate inputs")
    ap.add_argument("--nec2c",help="Path to optional nec2c executable (may require input and output filenames)")
    ap.add_argument("--output",default="bench/results")
    ap.add_argument("--density",type=int,choices=(1,2),default=1)
    ap.add_argument("--timeout",type=int,default=180)
    ap.add_argument("--generate-only",action="store_true")
    args=ap.parse_args()
    out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for case in CASES:
        for freq in FREQS[case]:
            stem=f"{case}_{freq:g}MHz_N{args.density}"
            nec=out/(stem+".nec")
            nec.write_text(nec_text(case,freq,args.density),encoding="utf-8")
            mini_cmd=mininec_command(args.mininec,case,freq,args.density)
            (out/(stem+".mininec.args.json")).write_text(json.dumps(mini_cmd[1:],indent=2)+"\n",encoding="utf-8")
            row={"case":case,"freq_MHz":freq,"density":args.density,"ground":str(CASES[case]["ground"]),
                 "comparison_status":"not_run","mini_R_ohm":"","mini_X_ohm":"","nec_R_ohm":"","nec_X_ohm":"","delta_R_ohm":"","delta_X_ohm":""}
            if not args.generate_only:
                try:
                    mini=run_command(mini_cmd,out/(stem+".mininec.txt"),args.timeout)
                    row["mini_R_ohm"],row["mini_X_ohm"]=parse_mininec(mini)
                    row["comparison_status"]="mininec_only"
                except Exception as exc:
                    row["comparison_status"]="mininec_error"
                    row["error"]=str(exc)
                if args.nec2c:
                    try:
                        necout=out/(stem+".nec.out")
                        # Standard nec2c CLI: nec2c -i model.nec -o output.out
                        completed=subprocess.run([args.nec2c,"-i",str(nec),"-o",str(necout)],capture_output=True,text=True,timeout=args.timeout)
                        if completed.returncode:
                            raise RuntimeError(completed.stderr.strip() or str(completed.returncode))
                        nr,nx=parse_nec(necout.read_text(encoding="utf-8",errors="replace"))
                        row["nec_R_ohm"],row["nec_X_ohm"]=nr,nx
                        if row["mini_R_ohm"] != "":
                            row["delta_R_ohm"]=round(row["mini_R_ohm"]-nr,6)
                            row["delta_X_ohm"]=round(row["mini_X_ohm"]-nx,6)
                            row["comparison_status"]="paired_provisional" if case=="vertical_radials" else "paired"
                        else:
                            row["comparison_status"]="nec_only"
                    except Exception as exc:
                        row["comparison_status"]+="+nec_error"
                        row["error"]=str(row.get("error",""))+"; "+str(exc)
            rows.append(row)
    keys=["case","freq_MHz","density","ground","comparison_status","mini_R_ohm","mini_X_ohm","nec_R_ohm","nec_X_ohm","delta_R_ohm","delta_X_ohm","error"]
    with (out/"summary.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} cases to {out/'summary.csv'}")
    for row in rows:
        print(row["case"],row["comparison_status"])
    if any("error" in r["comparison_status"] for r in rows):
        raise SystemExit(1)

if __name__=="__main__":
    main()
