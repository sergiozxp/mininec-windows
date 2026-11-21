"""Tests for the text input deck launcher, without requiring the solver."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mininec_cli", ROOT / "src" / "mininec_cli.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class InputTests(unittest.TestCase):
    def test_ground_deck(self):
        args = mod.translate_file(ROOT / "examples" / "dipole_ground.txt")
        self.assertEqual(args[:2], ["-f", "14.2"])
        self.assertIn("--medium=13,0.005,0", args)
        self.assertIn("--excitation-pulse=10", args)
        self.assertIn("--wire=1,21,-5,0,6,5,0,6,0.001", args)
        self.assertIn("--theta=0,5,37", args)

    def test_free_space(self):
        args = mod.translate_file(ROOT / "examples" / "dipole_free.txt")
        self.assertFalse(any(x.startswith("--medium") for x in args))

    def test_sweep(self):
        args = mod.translate_file(ROOT / "examples" / "dipole_sweep.txt")
        self.assertIn("--frequency-increment=0.1", args)
        self.assertIn("--frequency-steps=4", args)

    def test_errors(self):
        base="FREQ 14.2\nWIRE 1 21 -5 0 6 5 0 6 0.001\nEXCITATION 10\n"
        for invalid in ("GROUND 13 0.005\n", "BLAH 1\n", "FREQ 7\n", "WIRE 1 21 0 0 0 0 0 0 -1\n", "SWEEP no 4\n"):
            with self.subTest(invalid=invalid):
                with tempfile.TemporaryDirectory() as tmp:
                    path=Path(tmp)/"case.txt"
                    path.write_text(base+invalid,encoding="utf-8")
                    with self.assertRaises(mod.InputError):
                        mod.translate_file(path)

    def test_missing_excitation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"case.txt"
            path.write_text("FREQ 7\nWIRE 1 20 0 0 1 0 0 10 0.001\n")
            with self.assertRaisesRegex(mod.InputError,"EXCITATION"):
                mod.translate_file(path)

if __name__=="__main__":
    unittest.main()
