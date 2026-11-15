"""Gameplay object locations and repair steps, independent of the video frames."""
from dataclasses import dataclass
from .settings import ROOMS

@dataclass(frozen=True)
class Hotspot:
 x:int
 label:str
 action:str
 required:str=''

HUB_DOORS={'life':210,'generator':480,'radiation':750,'hydro':1010}


def items(state,room):
 p=state.progress[room]
 if state.operational[room]:return []
 have=state.acquired
 if room=='life':
  if not p['diagnosed']:return [Hotspot(360,'INSPECT AIR DUCT','puzzle:diagnose')]
  if 'sealant' not in have:return [Hotspot(190,'TAKE THERMAL SEALANT','take:sealant')]
  cracks=[Hotspot(x,f'REPAIR LEAK {i+1}',f'puzzle:seal:{i}','sealant') for i,x in enumerate((460,675,895)) if not p['cracks'][i]]
  return cracks or [Hotspot(1070,'PURGE VALVE','puzzle:valve')]
 if room=='generator':
  if 'multimeter' not in have:return [Hotspot(180,'TAKE MULTIMETER','take:multimeter')]
  if not p['diagnosed']:return [Hotspot(380,'TEST ELECTRICAL PANEL','puzzle:diagnose','multimeter')]
  if 'wrench' not in have:return [Hotspot(245,'TAKE MAINTENANCE WRENCH','take:wrench')]
  if not p['panel']:return [Hotspot(540,'OPEN POWER PANEL','puzzle:screws','wrench')]
  if 'bridge' not in have:return [Hotspot(300,'TAKE SPARE BRIDGE','take:bridge')]
  if not p['bridge_installed']:return [Hotspot(575,'INSTALL BRIDGE','install:bridge','bridge')]
  if not all(p['links']):return [Hotspot(805,'REWIRE THE CIRCUIT','puzzle:wires','wrench')]
  return [Hotspot(1060,'POWER DISTRIBUTION','puzzle:grid')]
 if room=='radiation':
  if 'scanner' not in have:return [Hotspot(185,'TAKE RADIATION SCANNER','take:scanner')]
  if not p['scanned']:return [Hotspot(365,'SCAN EMITTER','puzzle:scan','scanner')]
  if 'calibrator' not in have:return [Hotspot(268,'TAKE CALIBRATOR','take:calibrator')]
  for i,x in enumerate((492,728,932)):
   if not p['calibrated'][i]:return [Hotspot(x,f'CALIBRATE COIL {i+1}',f'puzzle:coil:{i}','calibrator')]
  return [Hotspot(1110,'ACTIVATE SHIELD','activate:shield')]
 if room=='hydro':
  if 'heater' not in have:return [Hotspot(190,'TAKE PORTABLE HEATER','take:heater')]
  for i,x in enumerate((450,690,905)):
   if not p['pipes'][i]:return [Hotspot(x,f'THAW PIPE {i+1}',f'puzzle:heat:{i}','heater')]
  if not all(p['water']):return [Hotspot(1020,'REPAIR WATER FLOW','puzzle:irrigation')]
  return [Hotspot(1110,'GROW LIGHT CONTROL','puzzle:uv')]
 return []


def objective(state,room):
 p=state.progress[room]
 if state.operational[room]:return 'System restored. Return to the outpost.'
 if room=='life':
  if not p['diagnosed']:return 'Identify the leaking air duct.'
  if 'sealant' not in state.acquired:return 'Collect the thermal sealant.'
  return 'Seal all three cracks.' if not all(p['cracks']) else 'Stabilize the purge valve.'
 if room=='generator':
  if 'multimeter' not in state.acquired:return 'Collect the multimeter.'
  if not p['diagnosed']:return 'Find the failed electrical terminal.'
  if 'wrench' not in state.acquired:return 'Collect the maintenance wrench.'
  if not p['panel']:return 'Open the electrical panel in the correct sequence.'
  if 'bridge' not in state.acquired:return 'Pick up the spare circuit bridge.'
  if not p['bridge_installed']:return 'Install the spare circuit bridge.'
  if not all(p['links']):return 'Connect the colored power terminals.'
  return 'Allocate no more than 100 W and stabilize the grid.'
 if room=='radiation':
  if 'scanner' not in state.acquired:return 'Collect a scanner and inspect the emitter.'
  if not p['scanned']:return 'Scan the field and locate the failing coil.'
  if 'calibrator' not in state.acquired:return 'Collect the electronic calibrator.'
  if not all(p['calibrated']):return f'Calibrate the remaining coils ({sum(p["calibrated"])}/3).'
  return 'Activate the shield before solar impact.'
 if room=='hydro':
  if 'heater' not in state.acquired:return 'Collect the portable heater.'
  if not all(p['pipes']):return f'Thaw the frozen pipes ({sum(p["pipes"])}/3).'
  if not all(p['water']):return 'Open irrigation valves in the correct sequence.'
  return 'Balance the grow lights to restore crops.'
 return ''
