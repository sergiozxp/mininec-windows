# MININEC for Windows (unofficial packaging)

A command-line Windows executable of [PyMININEC](https://github.com/schlatterbeck/pymininec), the Python rewrite of MININEC3 by **Dr. Ralf Schlatterbeck**.

**This project packages PyMININEC; it does not claim to implement a new electromagnetic solver, and it is not MMANA-GAL.** The numerical engine belongs to its upstream author. This repository is intended for reproducible hobbyist simulations and NEC2 vs. MININEC studies.

## Download

Once the GitHub Actions workflow has succeeded, download its `mininec-windows-win64` build artifact. On a `v*` tag, the workflow also attempts to create a GitHub Release containing `mininec-windows-win64.zip`.

## Usage (PowerShell / CMD)

```powershell
.\mininec.exe --help
.\mininec.exe -f 14 -w 21,0,0,5,0,0,15,0.001 --excitation-pulse=11 > result.txt
```

The example illustrates the command-line format. It is **not** presented as a validated reference antenna. Frequencies are MHz; lengths are meters. Review the upstream manual for excitation pulse indexing, ground configuration, segmentation and far-field options.

`.nec` files from NEC2 cannot simply be passed to PyMININEC; an explicit geometry/command-line adapter would be needed.

## Build on Windows

Requires Python 3.12 and Git on PATH:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --clean --onefile --console --name mininec src/mininec_cli.py
.\.venv\Scripts\python.exe tests/smoke.py dist/mininec.exe
```

The workflow builds on `windows-latest` using pinned PyMININEC commit `3b0b3b836f0c785c30a6d78bf30028b8eff88c5b` (2025-07-28). This is **source revision pinning**, not a claim of comprehensive electromagnetic validation.

## Validation scope

Initial automated smoke test checks that the executable starts and exposes CLI help. **Do not treat this as verification of electromagnetic accuracy.** Before stable `v1.0.0`, add numerical regression tests against published PyMININEC upstream examples, record tolerances, and test Windows 10/11.

## Credits and license

PyMININEC is copyright (C) 2022–2025 Dr. Ralf Schlatterbeck and is provided under the MIT license. See `THIRD_PARTY_NOTICES.md`. Packaging scripts and documentation in this repository are under MIT (`LICENSE`).
