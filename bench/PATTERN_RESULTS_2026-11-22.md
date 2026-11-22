# Pattern and gain-grid comparison — 2026-11-22

## Provenance

- GitHub Actions run: https://github.com/sergiozxp/mininec-windows/actions/runs/45048408826
- Artifact `independent-three-case-validation` contains input decks and **both raw native far-field outputs** at density 1 and 2.
- Engines: MININEC Windows v1.1.0 (PyMININEC), NEC2C Windows v1.3-win64.
- Both sampled theta 0°–90° at 5° increments, phi 0°–360° at 5° increments. NEC2 may omit invalid/horizon/null rows, so compare only the common coordinates.
- These are the native `TOTAL` gain fields in dB. No matching loss or realized-gain transformation is applied. Do not interpret these as measured realized gain or efficiency.
- For pattern RMS the comparison excludes points more than 30 dB below **either** engine's peak, and uses only shared coordinates. This excludes ill-conditioned nulls; the number of retained points is reported.

## Fine-mesh numerical results

| Case | MININEC total-gain peak (dB) | Peak angle (theta,phi) | NEC2 total-gain peak (dB) | Peak angle | Peak delta (dB) | RMS absolute-pattern difference (dB) | RMS peak-normalized difference (dB) | Accepted angular samples |
|---|---:|---|---:|---|---:|---:|---:|---:|
| Dipole, free space | 2.1131 | (90°,270°) | 2.12 | (90°,270°) | -0.0069 | 0.0088 | 0.0081 | 1384 |
| Dipole, real soil | 5.3794 | (40°,270°) | 8.92 | (55°,270°) | -3.5406 | 7.8131 | 9.4764 | 1309 |
| Vertical, elevated radials | -0.2709 | (65°,360°) | 4.36 | (45°,315°) | -4.6309 | 7.7389 | 5.0910 | 1241 |

## Mesh 1 (independent sensitivity)

| Case | MININEC peak (dB) | NEC2 peak (dB) | Peak delta (dB) | Pattern RMS absolute (dB) |
|---|---:|---:|---:|---:|
| Dipole free | 2.1090 | 2.12 | -0.0110 | 0.0156 |
| Dipole ground | 5.3764 | 8.92 | -3.5436 | 7.8125 |
| Vertical radials | -0.2700 | 4.38 | -4.6500 | 7.7540 |

## Conclusion and cautions

1. **Free-space dipole:** excellent consistency of native total-gain patterns and peak positions. The ≈2.11 dB peak is consistent with the familiar ≈2.15 dBi directivity scale for a nearly half-wave dipole. This is numerical agreement, not experimental measurement.
2. **Soil dipole:** both impedance and far-field differences remain large even with mesh refinement. PyMININEC's homogeneous ground and NEC2's GN 2 ground are not mathematically identical. No ranking of which motor is correct can be inferred from this comparison.
3. **Vertical radials:** the five-wire feed-point junction and pulse-vs-segment excitation are not physically equivalent; the discrepancies are diagnostic only.
4. The theta range is restricted to the upper hemisphere for meaningful ground comparisons. Phi=360° duplicates 0°; the tabulated RMS includes common grid rows and is a descriptive measure, not a rigorously solid-angle-weighted spherical norm.
5. Different output rounding is present (NEC2 prints 0.01 dB, MININEC more precision). The small free-space differences are close to that reporting precision.
6. Further formal verification would require feed/ground equivalence, additional segment refinements, cross-section changes, angular quadrature and, ideally, a physically measured reference.

See [impedance validation](VALIDATION_RESULTS_2026-11-22.md).
