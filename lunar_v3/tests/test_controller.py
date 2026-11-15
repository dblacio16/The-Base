"""Cross-room controller tests without importing or initializing the Pygame window."""
import sys,types,unittest
from unittest.mock import Mock

try:
 import pygame
except ImportError:
 pygame=types.ModuleType('pygame');sys.modules['pygame']=pygame

from lunar_v3.game import LunarGame
from lunar_v3.model import State
from lunar_v3.nasa_data import empty_snapshot

class ControllerIntegrationTests(unittest.TestCase):
 def setUp(self):
  g=LunarGame.__new__(LunarGame)
  g.state=State.start(empty_snapshot(),20,seed=28)
  g.scene='hub'
  g.popup=None
  g.puzzle=None
  g.puzzle_action=''
  g.message=''
  g.robot='normal'
  g.video=Mock()
  g.save=Mock()
  g.alert=Mock()
  g.check_end=Mock()
  g.player=Mock()
  self.g=g
 def finish_gauge(self,kind,index=0):
  g=self.g
  g.open_puzzle(kind,index)
  p=g.puzzle
  for j in range(400):
   if p.finished:break
   diff=p.target-p.cursor
   p.update(.04,{'left':diff<-.8,'right':diff>.8,'use':abs(diff)<4.8})
  self.assertTrue(p.finished,kind)
  g.check_puzzle()
 def test_life_complete(self):
  g=self.g;g.scene='life'
  g.open_puzzle('diagnose');g.puzzle.input_action('choose',1);g.check_puzzle()
  g.take_action('take:sealant')
  for i in range(3):self.finish_gauge('seal',i)
  self.finish_gauge('valve')
  self.assertTrue(g.state.operational['life'])
 def test_generator_complete(self):
  g=self.g;g.scene='generator'
  g.take_action('take:multimeter')
  g.open_puzzle('diagnose');g.puzzle.input_action('choose',1);g.check_puzzle()
  g.take_action('take:wrench')
  g.open_puzzle('screws')
  for i in (2,0,3,1):g.puzzle.input_action('choose',i)
  g.check_puzzle()
  g.take_action('take:bridge');g.take_action('install:bridge')
  g.state.equip('wrench')
  g.open_puzzle('wires')
  for i in range(3):g.puzzle.input_action('socket',i);g.puzzle.input_action('socket',i+3)
  g.check_puzzle()
  g.open_puzzle('grid')
  g.take_action('confirm_grid')
  self.assertEqual(g.puzzle.kind,'stability')
  for _ in range(200):
   p=g.puzzle
   if p is None:break
   diff=p.target-p.cursor
   p.update(.04,{'left':diff<-.8,'right':diff>.8,'use':abs(diff)<4.8})
   g.check_puzzle()
  self.assertTrue(g.state.operational['generator'])
 def test_radiation_complete(self):
  g=self.g;g.scene='radiation'
  g.take_action('take:scanner');g.open_puzzle('scan')
  g.puzzle.input_action('choose',2);g.check_puzzle()
  g.take_action('take:calibrator')
  self.finish_gauge('coil',0)
  g.open_puzzle('coil',1);g.puzzle.cursor=g.puzzle.target
  g.puzzle.input_action('trigger');g.check_puzzle()
  self.finish_gauge('coil',2)
  g.take_action('activate:shield')
  self.assertTrue(g.state.operational['radiation'])
 def test_hydro_complete(self):
  g=self.g;g.scene='hydro'
  g.take_action('take:heater')
  for i in range(3):self.finish_gauge('heat',i)
  g.open_puzzle('irrigation')
  for i in (2,0,1):g.puzzle.input_action('choose',i)
  g.check_puzzle()
  g.open_puzzle('uv')
  g.puzzle.config.update(intensity=75,red=65,blue=45)
  g.take_action('confirm_uv')
  self.assertTrue(g.state.operational['hydro'])
 def test_emergency_kit_has_effect_and_runs_out(self):
  g=self.g;g.scene='life'
  g.take_action('take:kit')
  before=g.state.resources['life']
  for _ in range(3):g.use_kit()
  self.assertGreater(g.state.resources['life'],before)
  self.assertEqual(g.state.tool_charge['kit'],32)
  g.use_kit()
  self.assertEqual(g.state.tool_charge['kit'],32)

if __name__=='__main__':unittest.main()
