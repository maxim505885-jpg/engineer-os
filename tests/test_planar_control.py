import unittest
import importlib.util
from dataclasses import replace
from engineering.calculation.planar_control import Node, Member, PlanarInput, calculate_planar
requires_pynite=unittest.skipUnless(importlib.util.find_spec('Pynite'),'optional requirements-calculation.txt not installed')
class PlanarTests(unittest.TestCase):
 def sample(self,kind='frame'):
  return PlanarInput((Node('a',0,0,True,True,True),Node('b',2,0)),(Member('ab','a','b',200e9,.01,1e-5),),(('b',0.,-1000.,0.),),'a'*64,('synthetic:cantilever',),kind=kind)
 @requires_pynite
 def test_cantilever(self):
  r=calculate_planar(self.sample());self.assertEqual(r['status'],'PASS',r);self.assertAlmostEqual(r['results']['nodes']['b']['dy_m'],-1000*8/(3*200e9*1e-5),places=10);self.assertAlmostEqual(r['results']['nodes']['a']['reaction_mz_nm'],2000,places=5);self.assertFalse(r['acceptance_granted'])
 @requires_pynite
 def test_truss(self):
  s=self.sample('truss');s=replace(s,nodes=(s.nodes[0],Node('b',2,0,False,True)),loads=(('b',1000.,0.,0.),));r=calculate_planar(s);self.assertEqual(r['status'],'PASS',r);self.assertAlmostEqual(r['results']['nodes']['b']['dx_m'],1e-6,places=12)
 @requires_pynite
 def test_unstable(self):
  s=self.sample();self.assertEqual(calculate_planar(replace(s,nodes=(Node('a',0,0),Node('b',2,0))))['status'],'BLOCK')
 def test_invalid(self):
  s=self.sample()
  for c in ({'units':'kN_mm'},{'source_sha256':''},{'evidence_ids':()},{'kind':'shell'},{'loads':(('b',float('nan'),0.,0.),)},{'members':(replace(s.members[0],area_m2=-1),)},{'nodes':(s.nodes[0],Node('b',0,0))}):self.assertEqual(calculate_planar(replace(s,**c))['status'],'BLOCK',c)

class ExtendedPlanarTests(PlanarTests):
 @requires_pynite
 def test_triangle(self):
  import math
  nodes=(Node('a',0,0,True,True),Node('b',2,0,False,True),Node('c',1,1))
  members=tuple(Member(name,a,b,200e9,.01,1e-5) for name,a,b in (('ab','a','b'),('ac','a','c'),('bc','b','c')))
  s=replace(self.sample('truss'),nodes=nodes,members=members,loads=(('c',0.,-1000.,0.),))
  r=calculate_planar(s);self.assertEqual(r['status'],'PASS',r)
  self.assertAlmostEqual(r['results']['nodes']['a']['reaction_fy_n'],500,places=7)
  # Virtual work: diagonals P/sqrt(2), base P/2; sum(N*n*L/EA).
  self.assertAlmostEqual(r['results']['nodes']['c']['dy_m'],-1000*(math.sqrt(2)+.5)/(200e9*.01),places=11)
 @requires_pynite
 def test_vertical_frame(self):
  s=replace(self.sample(),nodes=(Node('a',0,0,True,True,True),Node('b',0,2)),loads=(('b',1000.,0.,0.),))
  r=calculate_planar(s);self.assertEqual(r['status'],'PASS',r)
  self.assertAlmostEqual(r['results']['nodes']['b']['dx_m'],1000*8/(3*200e9*1e-5),places=10)
 def test_source_binding(self):
  a=calculate_planar(self.sample());b=calculate_planar(replace(self.sample(),source_sha256='b'*64))
  self.assertNotEqual(a['input_sha256'],b['input_sha256']);self.assertEqual(a['source_sha256'],'a'*64)
 @requires_pynite
 def test_nonfinite_solver_block(self):
  from unittest.mock import patch
  from Pynite import FEModel3D
  original=FEModel3D.analyze_linear
  def corrupt(model,*args,**kwargs):
   original(model,*args,**kwargs);model.nodes['b'].DY['control']=float('nan')
  with patch.object(FEModel3D,'analyze_linear',corrupt):self.assertEqual(calculate_planar(self.sample())['status'],'BLOCK')
 def test_invalid_connectivity_and_data(self):
  s=self.sample()
  for c in ({'nodes':(s.nodes[0],s.nodes[0])},{'members':(replace(s.members[0],end='missing'),)},{'members':(replace(s.members[0],elastic_modulus_pa=float('inf')),)},{'loads':(('missing',1,0,0),)},{'evidence_ids':('same','same')},{'nodes':(s.nodes[0],replace(s.nodes[1],fix_x=1))}):self.assertEqual(calculate_planar(replace(s,**c))['status'],'BLOCK',c)
 def test_truss_moment_block(self):
  self.assertEqual(calculate_planar(replace(self.sample('truss'),loads=(('b',0.,0.,1.),)))['status'],'BLOCK')
 @requires_pynite
 def test_two_member_frame(self):
  # Rigid elbow: vertical 2 m + horizontal 1 m, downward tip load.
  # Castigliano bending integral: P*(1^2*2 + 1^3/3)/EI; axial PL/EA in column.
  s=self.sample();s=replace(s,nodes=(s.nodes[0],Node('b',0,2),Node('c',1,2)),members=(replace(s.members[0],end='b'),replace(s.members[0],name='bc',start='b',end='c')),loads=(('c',0.,-1000.,0.),))
  r=calculate_planar(s);self.assertEqual(r['status'],'PASS',r)
  self.assertAlmostEqual(r['results']['nodes']['c']['dy_m'],-1000*(2+1/3)/(200e9*1e-5)-1000*2/(200e9*.01),places=10)
 @requires_pynite
 def test_large_moment_cannot_mask_force_imbalance(self):
  from unittest.mock import patch
  from Pynite import FEModel3D
  original=FEModel3D.analyze_linear
  def corrupt(model,*args,**kwargs):
   original(model,*args,**kwargs);model.nodes['a'].RxnFX['control']+=1000
  s=replace(self.sample(),loads=(('b',0.,0.,1e12),))
  with patch.object(FEModel3D,'analyze_linear',corrupt):
   self.assertEqual(calculate_planar(s)['status'],'BLOCK')
