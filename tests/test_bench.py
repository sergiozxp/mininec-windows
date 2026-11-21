"""Offline tests: input generation, parser behavior and run orchestration."""
import importlib.util
import pathlib
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("bench",ROOT/"bench"/"run_bench.py")
bench=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)

class BenchTests(unittest.TestCase):
    def test_cases_and_ground(self):
        self.assertEqual(len(bench.CASES),3)
        for name in bench.CASES:
            text=bench.nec_text(name,bench.FREQS[name][0],1)
            self.assertIn("GW ",text)
            self.assertIn("EX 0",text)
            if name=="dipole_free":
                self.assertIn("GN -1",text)
                self.assertNotIn("--medium",bench.mininec_command("mini",name,14.2,1))
            else:
                self.assertIn("GN 2",text)
                self.assertTrue(any(x.startswith("--medium=") for x in bench.mininec_command("mini",name,bench.FREQS[name][0],1)))

    def test_different_segmentation(self):
        self.assertEqual(bench.geometry("dipole_free",2)[0][1],42)
        self.assertEqual(len(bench.geometry("vertical_radials")),5)

    def test_mininec_impedance(self):
        self.assertEqual(bench.parse_mininec(" IMPEDANCE = ( 73.25 , -21.3 J)"),(73.25,-21.3))
        with self.assertRaises(ValueError):
            bench.parse_mininec("garbled")

    def test_nec_parser_rejects_unknown(self):
        with self.assertRaises(ValueError):
            bench.parse_nec("No INPUT PARAMETERS present")

if __name__=="__main__":
    unittest.main()
