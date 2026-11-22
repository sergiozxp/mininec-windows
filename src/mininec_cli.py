"""Command-line launcher for Dr. Ralf Schlatterbeck's upstream PyMININEC.

Adds --input FILE with a small, explicit text format. The solver is untouched.
"""
from __future__ import annotations

import contextlib
import io
import math
from pathlib import Path
import sys

GRAMMAR = """Input file format (whitespace-separated, # for comments):
  FREQ MHz
  WIRE tag segments x1 y1 z1 x2 y2 z2 radius_m
  EXCITATION pulse
  GROUND epsilon_r conductivity_S_per_m height_m
  THETA start_deg step_deg point_count
  PHI start_deg step_deg point_count
  SWEEP increment_MHz point_count
For FREE SPACE omit GROUND; GROUND 0 0 0 selects perfect ground.
Example: mininec.exe --input examples/dipole_ground.txt > result.txt
Other PyMININEC CLI options are supported unchanged *without* --input.
"""


class InputError(ValueError):
    """A line-specific input syntax/validation error."""


def _number(raw: str, line: int, name: str, *, positive=False, nonnegative=False):
    try:
        value = float(raw)
    except ValueError as exc:
        raise InputError(f"line {line}: {name} must be a number, got {raw!r}") from exc
    if not math.isfinite(value) or (positive and value <= 0) or (nonnegative and value < 0):
        raise InputError(f"line {line}: invalid {name}: {raw!r}")
    return raw


def _integer(raw: str, line: int, name: str, *, minimum=1):
    try:
        value = int(raw)
    except ValueError as exc:
        raise InputError(f"line {line}: {name} must be an integer") from exc
    if str(value) != raw and raw != f"+{value}":
        raise InputError(f"line {line}: {name} must be an integer without decimals")
    if value < minimum:
        raise InputError(f"line {line}: {name} must be >= {minimum}")
    return value


def translate_file(path: str | Path) -> list[str]:
    """Translate the strictly documented mini-deck to upstream CLI arguments."""
    source = Path(path)
    try:
        content = source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise InputError(f"cannot read {source}: {exc}") from exc

    commands = []
    seen = set()
    tags = set()
    wires = 0
    excitation = None
    for lineno, text in enumerate(content.splitlines(), 1):
        tokens = text.split("#", 1)[0].split()
        if not tokens:
            continue
        kind = tokens[0].upper()
        fields = tokens[1:]
        lengths = {"FREQ": 1, "WIRE": 9, "EXCITATION": 1,
                   "GROUND": 3, "THETA": 3, "PHI": 3, "SWEEP": 2}
        if kind not in lengths:
            raise InputError(f"line {lineno}: unknown instruction {kind!r}")
        if len(fields) != lengths[kind]:
            raise InputError(f"line {lineno}: {kind} expects {lengths[kind]} values, got {len(fields)}")
        if kind != "WIRE":
            if kind in seen:
                raise InputError(f"line {lineno}: duplicate {kind}")
            seen.add(kind)
        if kind == "FREQ":
            _number(fields[0], lineno, "frequency MHz", positive=True)
            commands.extend(["-f", fields[0]])
        elif kind == "WIRE":
            tag = _integer(fields[0], lineno, "wire tag")
            _integer(fields[1], lineno, "segments", minimum=2)
            if tag in tags:
                raise InputError(f"line {lineno}: duplicate wire tag {tag}")
            tags.add(tag)
            for index, val in enumerate(fields[2:8], 1):
                _number(val, lineno, f"coordinate {index}")
            _number(fields[8], lineno, "wire radius", positive=True)
            if fields[2:5] == fields[5:8]:
                raise InputError(f"line {lineno}: wire has identical endpoints")
            commands.append("--wire=" + ",".join(fields))
            wires += 1
        elif kind == "EXCITATION":
            excitation = _integer(fields[0], lineno, "excitation pulse")
            commands.append("--excitation-pulse=" + fields[0])
        elif kind == "GROUND":
            vals = [float(_number(v, lineno, name)) for v, name in zip(
                fields, ("permittivity", "conductivity", "ground height"))]
            if vals != [0, 0, 0] and (vals[0] < 1 or vals[1] < 0 or vals[2] != 0):
                raise InputError(f"line {lineno}: GROUND must be 0 0 0 or epsilon>=1 conductivity>=0 height=0")
            commands.append("--medium=" + ",".join(fields))
        elif kind in {"THETA", "PHI"}:
            _number(fields[0], lineno, "angle start")
            _number(fields[1], lineno, "angle step", positive=True)
            _integer(fields[2], lineno, "point count")
            commands.append("--" + kind.lower() + "=" + ",".join(fields))
        elif kind == "SWEEP":
            _number(fields[0], lineno, "frequency increment", positive=True)
            count = _integer(fields[1], lineno, "frequency point count")
            commands.extend(["--frequency-increment=" + fields[0],
                             "--frequency-steps=" + str(count)])
    if "FREQ" not in seen:
        raise InputError("missing FREQ")
    if not wires:
        raise InputError("missing WIRE")
    if excitation is None:
        raise InputError("missing EXCITATION")
    # Validate pulse numbering only with the numerical engine, which knows
    # junction pulse ownership and complex connected geometry.
    return commands


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    output_dir = None
    reference_ohm = 50.0
    cleaned = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--output":
            if i + 1 >= len(argv): raise InputError("--output requires a directory")
            output_dir = argv[i + 1]; i += 2; continue
        if arg.startswith("--output="):
            output_dir = arg.split("=", 1)[1]; i += 1; continue
        if arg == "--reference-impedance":
            if i + 1 >= len(argv): raise InputError("--reference-impedance requires ohms")
            raw = argv[i + 1]; i += 2
        elif arg.startswith("--reference-impedance="):
            raw = arg.split("=", 1)[1]; i += 1
        else:
            cleaned.append(arg); i += 1; continue
        try: reference_ohm = float(raw)
        except ValueError as exc: raise InputError("reference impedance must be a number") from exc
        if not math.isfinite(reference_ohm) or reference_ohm <= 0:
            raise InputError("reference impedance must be positive")

    argv = cleaned
    if argv and (argv[0] == "--input" or argv[0].startswith("--input=")):
        if argv[0] == "--input":
            if len(argv) != 2: raise InputError("usage: mininec.exe --input FILE")
            filename = argv[1]
        else:
            if len(argv) != 1 or not argv[0].split("=", 1)[1]:
                raise InputError("usage: mininec.exe --input=FILE")
            filename = argv[0].split("=", 1)[1]
        argv = translate_file(filename)
    elif any(arg == "--input" or arg.startswith("--input=") for arg in argv):
        raise InputError("--input must be the first model option")

    from mininec.mininec import main as upstream_main
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        result = upstream_main(argv)
    native = captured.getvalue()
    sys.stdout.write(native)
    if output_dir is not None:
        from postprocess import parse_native, write_exports, PostprocessError
        try:
            metrics = parse_native(native, reference_ohm)
            write_exports(output_dir, native, metrics)
        except PostprocessError as exc:
            raise InputError(f"cannot post-process native output: {exc}") from exc
    return result


if __name__ == "__main__":
    try:
        main()
    except InputError as exc:
        print(f"MININEC input error: {exc}", file=sys.stderr)
        sys.exit(2)
