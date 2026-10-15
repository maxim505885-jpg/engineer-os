import unittest
from dataclasses import replace
from engineering.calculation.section_control import RectangleInput, calculate_rectangle
class SectionTests(unittest.TestCase):
 def test_rectangle(self):
  r=calculate_rectangle(RectangleInput(.2,.4,'a'*64,('synthetic:rectangle',)));self.assertEqual(r['status'],'PASS');self.assertAlmostEqual(r['results']['area_m2'],.08);self.assertAlmostEqual(r['results']['iz_m4'],.2*.4**3/12);self.assertAlmostEqual(r['results']['iy_m4'],.4*.2**3/12)
 def test_invalid(self):
  s=RectangleInput(.2,.4,'a'*64,('synthetic:rectangle',))
  for c in ({'width_m':-1},{'height_m':float('inf')},{'units':'mm'},{'source_sha256':''},{'evidence_ids':()}):self.assertEqual(calculate_rectangle(replace(s,**c))['status'],'BLOCK')
 def test_section_modulus_and_binding(self):
  s=RectangleInput(.2,.4,'a'*64,('synthetic:rectangle',));r=calculate_rectangle(s)
  self.assertAlmostEqual(r['results']['wz_m3'],r['results']['iz_m4']/(.4/2))
  self.assertNotEqual(r['input_sha256'],calculate_rectangle(replace(s,width_m=.3))['input_sha256'])
 def test_duplicate_evidence_and_underflow(self):
  s=RectangleInput(.2,.4,'a'*64,('synthetic:rectangle',))
  for c in ({'evidence_ids':('x','x')},{'width_m':True},{'height_m':1e-300}):self.assertEqual(calculate_rectangle(replace(s,**c))['status'],'BLOCK')
