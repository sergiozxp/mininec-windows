# Three-case MININEC / NEC2 validation bench

This is an **experimental reproducibility harness**, not a scientific validation certificate.

## Cases

| Case | Frequency | Geometry | Environment |
|---|---|---|---|
| `dipole_free` | 14.2 MHz | 10 m horizontal wire, Z=6 m | Free space (Z has no physical ground-height significance) |
| `dipole_ground` | 14.2 MHz | Same 10 m dipole at 6 m | Example soil: εr=13, σ=0.005 S/m |
| `vertical_radials` | 7.1 MHz | 10 m vertical with 4 × 10 m horizontal elevated wires at Z=2 m | Example soil: εr=13, σ=0.005 S/m |

The third case models **four explicit elevated radial wires**; it does not claim to reproduce PyMININEC's special buried/on-ground radial-system options. It should be treated as **provisional** because NEC2 feeds a segment centre while MININEC excites a pulse; source placement near the five-wire junction cannot be assumed equivalent. Do not use its differences as evidence of numerical superiority without feed-geometry convergence checks.

## Run

Generate inputs without installed engines (Python 3.10+):

```powershell
python bench/run_bench.py --generate-only
```

With MININEC available:

```powershell
python bench/run_bench.py --mininec .\mininec.exe
```

With both engines installed:

```powershell
python bench/run_bench.py --mininec .\mininec.exe --nec2c C:\tools\nec2c.exe
```

For segmentation sensitivity:

```powershell
python bench/run_bench.py --mininec .\mininec.exe --nec2c C:\tools\nec2c.exe --density 2 --output bench/results_fine
```

The harness writes **NEC input decks**, JSON lists of PyMININEC command-line arguments, raw outputs, and a `summary.csv` with impedance components R and X. If an engine is missing, generate-only mode does not invent its results; running mode records an error and exits nonzero. `nec2c` must support the standard `-i input -o output` arguments.

## Interpretation

- `delta_R_ohm = R_MININEC - R_NEC2`; analogous for X.
- No gain or radiation-pattern comparison is implemented in this first bench. The current metric is **input impedance only**. A full validation requires far-field sampling on an identical grid with an agreed normalization, loss convention and numerical tolerances.
- No matched 50-Ω load is imposed; both engines solve input impedance from a voltage excitation.
- The source placement differs between segment-centre NEC2 and pulse-based MININEC; especially in the vertical case.
- Inspect `.mininec.txt` and `.nec.out`. The parser expects characteristic text headings; it fails on unrecognized formats rather than fabricating results.
- NEC2's `GN 2` finite-ground solution and PyMININEC's `--medium` are not identical formulations. Matching numeric εr and σ is only a controlled input, not identical underlying physical approximations.
- Incremental segmentation (density 1 vs 2) is a necessary but not sufficient convergence check. Other field-region, topology, ground and source sensitivities remain.

## Provenance

MININEC engine: [Ralf Schlatterbeck / PyMININEC](https://github.com/schlatterbeck/pymininec), original MIT license. NEC2 is a separate numerical solver; the benchmark does not bundle NEC2 binaries.
