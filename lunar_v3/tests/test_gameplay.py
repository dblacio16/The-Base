import unittest,tempfile,json,sys,types
from pathlib import Path
from unittest.mock import Mock
from lunar_v3.model import State,TOOLS
from lunar_v3.minigames import Puzzle
from lunar_v3.nasa_data import empty_snapshot,risk_score,KINDS,fetch
from lunar_v3.rooms import items,objective

class RulesTests(unittest.TestCase):
 def state(self,seed=111):return State.start(empty_snapshot(),22,seed=seed)
 def test_new_games_differ_and_science_unchanged(self):
  a=self.state(111);b=self.state(112)
  self.assertNotEqual(a.resources,b.resources)
  self.assertEqual(a.nasa_snapshot,b.nasa_snapshot)
  self.assertEqual(a.sol,1)
 def test_power_cap_and_minimum(self):
  s=self.state()
  self.assertRaises(ValueError,s.set_power,{'life':60,'hydro':30,'radiation':30})
  self.assertFalse(s.set_power({'life':20,'hydro':25,'radiation':25}))
  self.assertTrue(s.set_power({'life':30,'hydro':25,'radiation':20}))
 def test_inventory_real_tools_and_charges(self):
  s=self.state();s.acquire('sealant');s.acquire('kit')
  self.assertIn('sealant',s.acquired)
  self.assertTrue(s.equip('sealant'))
  self.assertTrue(s.consume('sealant',25))
  self.assertEqual(s.tool_charge['sealant'],75)
  self.assertFalse(s.consume('kit',30))
  self.assertFalse(s.equip('not_a_tool'))
  self.assertGreaterEqual(len(TOOLS),7)
 def test_life_steps(self):
  s=self.state();self.assertEqual(items(s,'life')[0].action,'puzzle:diagnose')
  s.progress['life']['diagnosed']=True
  self.assertEqual(items(s,'life')[0].action,'take:sealant')
  s.acquire('sealant')
  self.assertEqual(len(items(s,'life')),3)
  s.progress['life']['cracks']=[True]*3
  self.assertEqual(items(s,'life')[0].action,'puzzle:valve')
 def test_power_scene_steps(self):
  s=self.state();self.assertEqual(items(s,'generator')[0].action,'take:multimeter')
  s.acquire('multimeter');s.progress['generator']['diagnosed']=True
  self.assertEqual(items(s,'generator')[0].action,'take:wrench')
  s.acquire('wrench');s.progress['generator']['panel']=True
  self.assertEqual(items(s,'generator')[0].action,'take:bridge')
  s.acquire('bridge');s.progress['generator']['bridge_installed']=True
  self.assertEqual(items(s,'generator')[0].action,'puzzle:wires')
  s.progress['generator']['links']=[True]*3
  self.assertEqual(items(s,'generator')[0].action,'puzzle:grid')
 def test_radiation_and_hydro_progress(self):
  s=self.state();s.acquire('scanner');self.assertEqual(items(s,'radiation')[0].action,'puzzle:scan')
  s.progress['radiation']['scanned']=True;s.acquire('calibrator')
  self.assertEqual(items(s,'radiation')[0].action,'puzzle:coil:0')
  s.progress['radiation']['calibrated']=[True]*3
  self.assertEqual(items(s,'radiation')[0].action,'activate:shield')
  s.acquire('heater')
  self.assertEqual(items(s,'hydro')[0].action,'puzzle:heat:0')
  s.progress['hydro']['pipes']=[True]*3
  self.assertEqual(items(s,'hydro')[0].action,'puzzle:irrigation')
 def test_nasa_offline(self):
  a=empty_snapshot();self.assertEqual(a['status'],'offline')
  self.assertEqual(set(a['events']),set(KINDS))
  self.assertTrue(all(not x for x in a['events'].values()))
 def test_nasa_risk_not_colony_measurement(self):
  snap=empty_snapshot()
  snap['events']['FLR']=[{'classType':'X2.0'}]
  snap['events']['SEP']=[{'eventTime':'2026-11-15T00:00:00Z'}]
  self.assertGreaterEqual(risk_score(snap),40)
  self.assertEqual(snap['events']['FLR'][0]['classType'],'X2.0')
 def test_progress_save_and_resume(self):
  s=self.state();s.scene='radiation';s.player_x=704
  s.acquire('scanner');s.progress['radiation']['scanned']=True
  s.sol=5
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'save.json';s.save(p)
   b=State.load(p)
   self.assertEqual(b.scene,'radiation');self.assertEqual(b.sol,5)
   self.assertTrue(b.progress['radiation']['scanned'])
   self.assertEqual(b.nasa_snapshot,s.nasa_snapshot)
 def test_sols_victory_and_loss(self):
  s=self.state()
  for room in ('life','generator','radiation','hydro'):s.complete(room,92)
  for i in range(29):
   s.pending=None
   self.assertTrue(s.advance())
  self.assertTrue(s.won)
  self.assertFalse(s.advance())
  t=self.state()
  t.modify(life=-1000)
  self.assertTrue(t.lost)
  self.assertEqual(t.resources['life'],0)
 def test_decisions_change_real_resources(self):
  s=self.state();s.pending={'title':'TEST','text':'A','choices':[('Fix',{'energy':-5,'life':4}),('Wait',{'life':-5})]}
  before=dict(s.resources)
  self.assertTrue(s.respond(0));self.assertEqual(s.resources['energy'],before['energy']-5)
  self.assertGreater(s.resources['life'],before['life'])
 def test_seed_reproducible(self):
  a=self.state(449);b=self.state(449)
  self.assertEqual(a.resources,b.resources)
  self.assertEqual(a.random('event').random(),b.random('event').random())

class PuzzleTests(unittest.TestCase):
 def run_hold(self,puzzle,steps=500):
  for i in range(steps):
   if puzzle.finished:break
   # Head toward target, then hold use.
   delta=puzzle.target-puzzle.cursor
   puzzle.update(.02,{'left':delta<-1,'right':delta>1,'use':abs(delta)<5})
  return puzzle.finished
 def test_gauge_puzzles(self):
  for kind in ('seal','heat','valve','frequency','tracking','stability'):
   p=Puzzle.create(kind,2,120)
   self.assertTrue(self.run_hold(p),kind)
 def test_timing(self):
  p=Puzzle.create('timing')
  p.cursor=p.target
  p.input_action('trigger')
  self.assertTrue(p.finished)
 def test_diagnostics_and_scanner(self):
  p=Puzzle.create('diagnose');p.input_action('choose',0)
  self.assertFalse(p.finished)
  p.input_action('choose',1)
  self.assertTrue(p.finished)
  p=Puzzle.create('scan');p.input_action('choose',2);self.assertTrue(p.finished)
 def test_screws_sequence(self):
  p=Puzzle.create('screws')
  for i in (2,0,3,1):p.input_action('choose',i)
  self.assertTrue(p.finished)
 def test_connect_wires(self):
  p=Puzzle.create('wires')
  for i in range(3):p.input_action('socket',i);p.input_action('socket',i+3)
  self.assertTrue(p.finished)
 def test_irrigation_sequence(self):
  p=Puzzle.create('irrigation')
  for i in (2,0,1):p.input_action('choose',i)
  self.assertTrue(p.finished)
 def test_light_control(self):
  p=Puzzle.create('uv');p.input_action('confirm');self.assertFalse(p.finished)
  p.config.update(intensity=75,red=65,blue=45)
  p.input_action('confirm');self.assertTrue(p.finished)

if __name__=='__main__':unittest.main()

class MigrationTests(unittest.TestCase):
 def test_legacy_v1_save(self):
  from lunar_v3.model import State
  obj={'version':1,'state':{
   'resources':{'life':79,'energy':63,'food':72,'integrity':81},
   'operational':{'life':True,'generator':False,'radiation':False,'hydro':False},
   'progress':{'life':{'tool':True,'fissures':[True]*3,'valve':3},
               'generator':{'stage':2,'configured':False},
               'radiation':{'coils':[1,2,3],'targets':[2,4,3],'shield':False},
               'hydro':{'tool':True,'heat':1.0,'lamps':[False]*3}},
   'science':{'source':'NASA DONKI','events':{}},'seed':77,'risk':28,'sol':7,
   'inventory':['sellador','calentador'],'allocation':{'life':35,'hydro':30,'radiation':20},
   'player_x':550,'current_scene':'life'}}
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'old.json';path.write_text(json.dumps(obj))
   s=State.load(path)
   self.assertEqual(s.sol,7)
   self.assertTrue(s.operational['life'])
   self.assertIn('sealant',s.acquired)
   self.assertEqual(s.player_x,550)
   self.assertEqual(s.progress['generator']['panel'],True)
