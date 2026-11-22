"""Post-process native PyMININEC text output without changing the solver."""
from __future__ import annotations
import csv, math, re
from pathlib import Path

NUM=r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
IMPEDANCE_RE=re.compile(r"IMPEDANCE\s*=\s*\(\s*(%s)\s*,\s*(%s)\s*J\s*\)"%(NUM,NUM),re.I)
FREQ_RE=re.compile(r"FREQUENCY\s*\(\s*MHZ\s*\)\s*:\s*(%s)"%NUM,re.I)
PATTERN_RE=re.compile(r"^\s*(%s)\s+(%s)\s+(%s)\s+(%s)\s+(%s)\s*$"%(NUM,NUM,NUM,NUM,NUM))

class PostprocessError(ValueError): pass

def _finite(value,name):
    if not math.isfinite(value): raise PostprocessError(f"non-finite {name}")
    return value

def parse_native(text: str, reference_ohm: float=50.0):
    if reference_ohm <= 0 or not math.isfinite(reference_ohm):
        raise PostprocessError("reference impedance must be positive")
    im=IMPEDANCE_RE.search(text)
    if not im: raise PostprocessError("native output has no feed-point impedance")
    r,x=map(float,im.groups()); _finite(r,"resistance"); _finite(x,"reactance")
    z=complex(r,x); gamma=(z-reference_ohm)/(z+reference_ohm)
    gm=abs(gamma)
    if gm >= 1:
        vswr=math.inf
        mismatch=math.inf
    else:
        vswr=(1+gm)/(1-gm)
        mismatch=-10*math.log10(max(1-gm*gm,1e-300))
    rows=[]
    in_pattern=False
    for line in text.splitlines():
        if "PATTERN DATA" in line.upper(): in_pattern=True; continue
        if not in_pattern: continue
        m=PATTERN_RE.match(line)
        if not m: continue
        zen,azi,vert,horiz,total=map(float,m.groups())
        if total <= -998: continue
        rows.append({"zenith_deg":zen,"azimuth_deg":azi,"vertical_dBi":vert,
                     "horizontal_dBi":horiz,"total_dBi":total})
    if not rows:
        raise PostprocessError("native output has no usable far-field pattern rows")
    peak=max(rows,key=lambda row:row["total_dBi"])
    fm=FREQ_RE.search(text)
    return {
      "frequency_MHz": float(fm.group(1)) if fm else None,
      "resistance_ohm":r,"reactance_ohm":x,"reference_ohm":reference_ohm,
      "reflection_coefficient_real":gamma.real,"reflection_coefficient_imag":gamma.imag,
      "reflection_coefficient_magnitude":gm,"vswr":vswr,
      "mismatch_loss_dB":mismatch,"max_gain_dBi":peak["total_dBi"],
      "max_gain_zenith_deg":peak["zenith_deg"],
      "max_gain_azimuth_deg":peak["azimuth_deg"],
      "pattern_points":len(rows),"pattern":rows,
    }

def write_exports(output_dir, native_text, metrics):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"native_output.txt").write_text(native_text,encoding="utf-8")
    params={k:v for k,v in metrics.items() if k!="pattern"}
    with (out/"parameters.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["parameter","value","unit"])
        units={"frequency_MHz":"MHz","resistance_ohm":"ohm","reactance_ohm":"ohm",
        "reference_ohm":"ohm","reflection_coefficient_real":"1",
        "reflection_coefficient_imag":"1","reflection_coefficient_magnitude":"1",
        "vswr":"1","mismatch_loss_dB":"dB","max_gain_dBi":"dBi",
        "max_gain_zenith_deg":"deg","max_gain_azimuth_deg":"deg","pattern_points":"count"}
        for k,v in params.items(): w.writerow([k,v,units.get(k,"")])
    fields=["zenith_deg","azimuth_deg","vertical_dBi","horizontal_dBi","total_dBi"]
    with (out/"pattern.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(metrics["pattern"])
    lines=["MININEC postprocessed results","", "Values extracted from native_output.txt; solver equations unchanged.",
           f"Frequency: {metrics['frequency_MHz']} MHz","Impedance: {metrics['resistance_ohm']} + j{metrics['reactance_ohm']} ohm",
           f"Reference impedance: {metrics['reference_ohm']} ohm",
           f"Reflection coefficient: {metrics['reflection_coefficient_real']} + j{metrics['reflection_coefficient_imag']} (magnitude {metrics['reflection_coefficient_magnitude']})",
           f"VSWR: {metrics['vswr']}","Mismatch loss: {metrics['mismatch_loss_dB']} dB",
           f"Maximum total gain: {metrics['max_gain_dBi']} dBi",
           f"Maximum direction: zenith {metrics['max_gain_zenith_deg']} deg, azimuth {metrics['max_gain_azimuth_deg']} deg",
           f"Pattern points: {metrics['pattern_points']}","",
           "Limitations: values depend on the PyMININEC model, segmentation, ground model and requested angular grid.",
           "Gain is the maximum total far-field pattern value reported by PyMININEC; it is not an independent measurement."]
    (out/"summary.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
