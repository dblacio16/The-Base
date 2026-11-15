"""Pure Python simulation, savegame, choices and tool/inventory rules.

NASA measurements live in snapshot, never in the generated colony simulation.
"""
from __future__ import annotations
import json,random,secrets
from dataclasses import dataclass,field
from pathlib import Path
from .settings import ROOMS, RESOURCES

TOOLS={
 'sealant':('Thermal Sealant','life'),
 'multimeter':('Multimeter','generator'),
 'wrench':('Maintenance Wrench','generator'),
 'bridge':('Spare Bridge','generator'),
 'scanner':('Radiation Scanner','radiation'),
 'calibrator':('Electronic Calibrator','radiation'),
 'heater':('Portable Heater','hydro'),
 'kit':('Emergency Repair Kit','hub'),
}


def clamp(x,lo=0,hi=100):return min(hi,max(lo,float(x)))


def empty_progress():
 return {
  'life':{'diagnosed':False,'cracks':[False]*3,'valve':0.0,'tested':False},
  'generator':{'diagnosed':False,'panel':False,'bridge_installed':False,'links':[False]*3,'stable':False},
  'radiation':{'scanned':False,'calibrated':[False]*3,'shield':False,'storm_timer':130.,'storm_hit':False},
  'hydro':{'pipes':[False]*3,'water':[False]*3,'lights':False},
 }


@dataclass
class State:
 sol:int=1
 resources:dict=field(default_factory=lambda:{'life':85.,'energy':82.,'food':88.,'integrity':90.})
 operational:dict=field(default_factory=lambda:{room:False for room in ROOMS})
 progress:dict=field(default_factory=empty_progress)
 acquired:list=field(default_factory=list)
 equipped:str=''
 tool_charge:dict=field(default_factory=lambda:{'sealant':100.,'multimeter':100.,'wrench':100.,'scanner':100.,'calibrator':100.,'heater':100.,'kit':100.})
 power:dict=field(default_factory=lambda:{'life':35,'hydro':30,'radiation':20})
 seed:int=0
 nasa_risk:int=15
 nasa_snapshot:dict=field(default_factory=dict)
 difficulty:str='Cadet'
 quality:dict=field(default_factory=dict)
 work_scores:dict=field(default_factory=lambda:{room:[] for room in ROOMS})
 events:list=field(default_factory=list)
 pending:dict|None=None
 scene:str='hub'
 player_x:float=90
 lost:bool=False
 won:bool=False
 failure_reason:str=''

 @classmethod
 def start(cls,snapshot:dict,risk:int,difficulty='Cadet',seed:int|None=None):
  if seed is None:seed=secrets.randbits(48)
  rng=random.Random(seed)
  init={'life':86-rng.randrange(11)-risk*.045,'energy':88-rng.randrange(10)-risk*.065,
        'food':88-rng.randrange(9)-risk*.02,'integrity':91-rng.randrange(9)-risk*.045}
  s=cls(resources={k:clamp(v) for k,v in init.items()},seed=seed,
        nasa_risk=int(clamp(risk)),nasa_snapshot=snapshot,difficulty=difficulty)
  s.record('Mission initialized. Colony values are simulated; NASA telemetry is separate.')
  return s

 def record(self,msg):
  self.events.insert(0,{'sol':self.sol,'message':msg})
  self.events=self.events[:80]

 def random(self,tag):
  tag_sum=sum((i+1)*ord(ch) for i,ch in enumerate(tag))
  return random.Random(self.seed+self.sol*100003+tag_sum)

 def acquire(self,name):
  if name not in TOOLS:raise ValueError(name)
  if name not in self.acquired:self.acquired.append(name)
  self.equipped=name
  self.record(f'{TOOLS[name][0]} acquired.')

 def equip(self,name):
  if name not in self.acquired:return False
  self.equipped=name
  return True

 def consume(self,name,amount):
  if name not in self.acquired or self.equipped!=name:return False
  current=self.tool_charge.get(name,100.)
  if current<amount:return False
  self.tool_charge[name]=clamp(current-amount)
  return True

 def modify(self,**changes):
  for key,val in changes.items():
   if key not in RESOURCES:raise KeyError(key)
   self.resources[key]=clamp(self.resources[key]+float(val))
  self.check_end()

 def check_end(self):
  if self.lost or self.won:return
  zeros=[name for name in RESOURCES if self.resources[name]<=0]
  if zeros:
   self.lost=True
   self.failure_reason=f'{zeros[0].replace("life","life support").title()} reached zero.'
  elif self.sol>=30 and all(self.operational.values()) and self.pending is None:
   self.won=True

 def complete(self,room,accuracy=75):
  if room not in ROOMS:raise ValueError(room)
  if self.operational[room]:return False
  self.operational[room]=True
  self.quality[room]=round(clamp(accuracy))
  key={'life':'life','generator':'energy','radiation':'integrity','hydro':'food'}[room]
  self.modify(**{key:20+accuracy*.07})
  self.record(f'{room} restored; repair quality {round(accuracy)}%.')
  self.check_end()
  return True

 def set_power(self,values):
  keys=('life','hydro','radiation')
  updated={k:int(values.get(k,0)) for k in keys}
  if min(updated.values())<0 or sum(updated.values())>100:raise ValueError('Grid allocation exceeds 100 W')
  self.power=updated
  self.record('Power allocated: '+', '.join(f'{k}={v} W' for k,v in updated.items()))
  return all(updated[k]>=goal for k,goal in {'life':30,'hydro':25,'radiation':20}.items())

 def advance(self):
  if self.pending or self.won or self.lost:return False
  mult={'Cadet':.72,'Engineer':1.,'Commander':1.22}.get(self.difficulty,1.)
  deltas={
   'life':-(.50 if self.operational['life'] else 2.45)*mult,
   'energy':-(.65 if self.operational['generator'] else 2.95)*mult,
   'food':(-.50 if self.operational['hydro'] else -2.15)*mult,
   'integrity':-(.40 if self.operational['radiation'] else 1.75)*mult,
  }
  # Poor repairs have a measurable long-term cost.
  for room,res in [('life','life'),('generator','energy'),('hydro','food'),('radiation','integrity')]:
   if self.operational[room] and self.quality.get(room,75)<60:deltas[res]-=.70
  minimum={'life':30,'hydro':25,'radiation':20}
  deltas['life']-=max(0,minimum['life']-self.power['life'])*.16
  deltas['food']-=max(0,minimum['hydro']-self.power['hydro'])*.16
  deltas['integrity']-=max(0,minimum['radiation']-self.power['radiation'])*.13
  self.modify(**deltas)
  if self.lost:return True
  self.sol+=1
  self.record(f'Sol {self.sol}: colony reserves recalculated.')
  # Controlled event frequency increases under higher simulated risk.
  if self.sol<30:
   r=self.random('event')
   chance={'Cadet':.17,'Engineer':.26,'Commander':.34}.get(self.difficulty,.26)+self.nasa_risk*.0013
   if r.random()<chance:
    kind=r.choice(['solar','leak','power','freeze'])
    self.pending={
     'solar':{'title':'SOLAR PARTICLE ALERT','text':'Space-weather-inspired training event. Choose a response.',
              'choices':[('Power the shield',{'energy':-7.,'integrity':+2.}),('Save the battery',{'integrity':-8.,'energy':+2.})]},
     'leak':{'title':'SECONDARY PRESSURE LEAK','text':'A minor leak is detected near a maintenance joint.',
             'choices':[('Seal immediately',{'energy':-5.,'life':+4.}),('Delay repairs',{'life':-7.,'energy':+2.})]},
     'power':{'title':'POWER DISTRIBUTION FAULT','text':'A voltage transient threatens the outpost.',
              'choices':[('Protect the inverter',{'energy':-6.,'integrity':+3.}),('Keep running',{'integrity':-5.,'energy':+2.})]},
     'freeze':{'title':'HYDROPONIC FREEZE ALERT','text':'The irrigation system needs additional heating.',
              'choices':[('Run heaters',{'energy':-6.,'food':+3.}),('Conserve power',{'food':-6.,'energy':+2.})]}
    }[kind]
    self.pending['kind']=kind
  self.check_end()
  return True

 def respond(self,choice_index):
  if self.pending is None:return False
  if choice_index not in (0,1):return False
  choice,changes=self.pending['choices'][choice_index]
  self.record('Event: '+choice+' | '+str(changes))
  self.pending=None
  self.modify(**changes)
  self.check_end()
  return True

 def serialize(self):
  return {'version':2,'state':{key:getattr(self,key) for key in self.__dataclass_fields__}}

 def save(self,path:Path):
  path.parent.mkdir(parents=True,exist_ok=True)
  temp=path.with_suffix('.tmp')
  temp.write_text(json.dumps(self.serialize(),indent=2,ensure_ascii=False),encoding='utf-8')
  temp.replace(path)

 @classmethod
 def load(cls,path:Path):
  raw=json.loads(path.read_text(encoding='utf-8'))
  if raw.get('version')==1:
   return cls.migrate_v1(raw.get('state',{}))
  if raw.get('version')!=2:raise ValueError('Unsupported save version')
  obj=raw['state']
  s=cls(**{key:val for key,val in obj.items() if key in cls.__dataclass_fields__})
  if not all(name in s.resources for name in RESOURCES):raise ValueError('Save data damaged')
  s.check_end()
  return s

 @classmethod
 def migrate_v1(cls,legacy):
  """Best-effort migration from V1 educational prototype saves.

  Old save file remains unchanged; newly saved state uses version 2.
  """
  if not isinstance(legacy,dict) or not all(k in legacy for k in ('resources','operational','progress')):
   raise ValueError('Old save data incomplete')
  snapshot=legacy.get('science') or {}
  snapshot.setdefault('status', 'cached' if snapshot.get('events') else 'offline')
  s=cls.start(snapshot,legacy.get('risk',15),seed=legacy.get('seed',None))
  s.sol=max(1,min(30,int(legacy.get('sol',1))))
  s.resources={k:clamp(legacy['resources'].get(k,75)) for k in RESOURCES}
  old=legacy.get('progress',{})
  s.operational={room:bool(legacy['operational'].get(room,False)) for room in ROOMS}
  lp=old.get('life',{})
  s.progress['life']['diagnosed']=bool(lp.get('tool') or any(lp.get('fissures',[])))
  s.progress['life']['cracks']=list(lp.get('fissures',[False]*3))[:3]
  s.progress['life']['valve']=float(lp.get('valve',0))
  gp=old.get('generator',{})
  stage=int(gp.get('stage',0))
  s.progress['generator'].update(diagnosed=stage>=1,panel=stage>=2,bridge_installed=stage>=3,
                                  links=[stage>=3]*3,stable=bool(gp.get('configured',False)))
  rp=old.get('radiation',{})
  s.progress['radiation'].update(scanned=bool(rp.get('coils')),
      calibrated=[a==b for a,b in zip(rp.get('coils',[1,1,1]),rp.get('targets',[2,4,3]))],
      shield=bool(rp.get('shield',False)),storm_timer=float(rp.get('storm_clock',130)),
      storm_hit=bool(rp.get('storm_hit',False)))
  hp=old.get('hydro',{})
  ready=bool(hp.get('heat',0)>=3)
  s.progress['hydro'].update(pipes=[ready]*3,water=[ready]*3,lights=all(hp.get('lamps',[False]*3)))
  mapping={'sellador':'sealant','calentador':'heater','puente':'bridge'}
  s.acquired=[mapping.get(name,name) for name in legacy.get('inventory',[]) if mapping.get(name,name) in TOOLS]
  if lp.get('tool') and 'sealant' not in s.acquired:s.acquired.append('sealant')
  if hp.get('tool') and 'heater' not in s.acquired:s.acquired.append('heater')
  s.equipped=s.acquired[-1] if s.acquired else ''
  power=legacy.get('allocation',{})
  if isinstance(power,dict) and all(k in power for k in ('life','hydro','radiation')):
   try:s.set_power(power)
   except (ValueError,TypeError):pass
  s.scene=legacy.get('current_scene','hub')
  if s.scene not in ROOMS+('hub',):s.scene='hub'
  s.player_x=float(legacy.get('player_x',95))
  s.lost=bool(legacy.get('lost',False))
  s.won=bool(legacy.get('won',False))
  s.failure_reason=str(legacy.get('reason',''))
  s.quality={room:75 for room in ROOMS if s.operational[room]}
  for entry in legacy.get('events',[]):
   if isinstance(entry,dict):
    s.events.append({'sol':entry.get('sol',s.sol),'message':entry.get('text',entry.get('message',''))})
  pending=legacy.get('pending_event')
  if isinstance(pending,dict):
   choices=[]
   for item in pending.get('choices',[]):
    if isinstance(item,(list,tuple)) and len(item)>=5:
     choices.append((str(item[0]),{str(item[1]):float(item[2]),str(item[3]):float(item[4])}))
   if len(choices)==2:
    s.pending={'title':pending.get('title','MISSION EVENT'),
               'text':pending.get('body','Select an emergency response.'),'choices':choices}
  s.record('Legacy V1 save migrated into V2 state.')
  s.check_end()
  return s
