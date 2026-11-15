"""Actual skill/puzzle mechanics; never depend on video pixels."""
from __future__ import annotations
import math,random
from dataclasses import dataclass,field

@dataclass
class Puzzle:
 kind:str
 index:int=0
 target:float=65.0
 cursor:float=50.0
 progress:float=0.0
 heat:float=12.0
 errors:int=0
 timer:float=0.0
 selected:int=-1
 solved:list=field(default_factory=list)
 order:list=field(default_factory=list)
 config:dict=field(default_factory=dict)
 finished:bool=False
 score:int=80

 @classmethod
 def create(cls,kind:str,index=0,seed=0):
  rng=random.Random(seed+index*1129)
  base={'seal':45+index*12,'valve':64,'frequency':40+index*17,
        'timing':50,'tracking':55,'heat':62,'stability':50}.get(kind,50)
  p=cls(kind,index,base)
  p.config={'answers':[24.3,0.,24.5], 'fault':1} if kind=='diagnose' else {}
  if kind=='screws':p.order=[2,0,3,1]
  if kind=='wires':p.solved=[False,False,False]
  if kind=='irrigation':p.order=[2,0,1]
  if kind=='uv':p.config={'intensity':40.,'red':40.,'blue':30.}
  return p

 def adjust(self,sign,delta=2):
  self.cursor=max(0,min(100,self.cursor+sign*delta))

 def update(self,dt,keys):
  """keys = {'left':bool,'right':bool,'use':bool}. Returns success/fail flag."""
  if self.finished:return
  self.timer+=dt
  move=int(bool(keys.get('right')))-int(bool(keys.get('left')))
  hold=bool(keys.get('use'))
  if self.kind in ('seal','heat','valve','frequency','tracking','stability'):
   # Track moving signal in tracking mode, constant target otherwise.
   if self.kind=='tracking':self.target=50+22*math.sin(self.timer*2.2)
   self.adjust(move,dt*(55 if self.kind in ('seal','heat') else 42))
   difference=abs(self.cursor-self.target)
   tolerance={'seal':11-self.index*2,'heat':14,'valve':9,
              'frequency':8,'tracking':13,'stability':15}[self.kind]
   correct=difference<=tolerance
   if hold:
    self.heat+=dt*(17 if self.kind in ('seal','heat') else 4)
    if correct:self.progress+=dt
    else:self.progress=max(0,self.progress-dt*.85)
   else:
    self.heat=max(0,self.heat-dt*22)
    if self.kind in ('tracking','stability','valve'):
     self.progress=max(0,self.progress-dt*.3)
   if self.heat>100:
    self.heat=35
    self.progress=max(0,self.progress-.8)
    self.errors+=1
   duration={'seal':1.6+self.index*.55,'heat':2.0+self.index*.45,'valve':2.5,
             'frequency':2.,'tracking':2.3,'stability':3.0}[self.kind]
   if self.progress>=duration:
    self.finished=True
    self.score=max(20,100-15*self.errors)
  elif self.kind=='timing':
   self.cursor=50+45*math.sin(self.timer*3.5)

 def input_action(self,kind,index=None):
  """Processes non-hold controls. Successful puzzles set finished=True."""
  if self.finished:return
  if self.kind=='timing' and kind=='trigger':
   if abs(self.cursor-self.target)<10:
    self.finished=True;self.score=max(35,95-10*self.errors)
   else:self.errors+=1
  elif self.kind in ('diagnose','scan') and kind=='choose':
   desired=1 if self.kind=='diagnose' else 2
   if index==desired:self.finished=True;self.score=max(45,95-10*self.errors)
   else:self.errors+=1
  elif self.kind=='screws' and kind=='choose':
   expected=self.order[len(self.solved)]
   if index==expected:
    self.solved.append(index)
    if len(self.solved)==len(self.order):self.finished=True;self.score=max(40,100-10*self.errors)
   else:self.errors+=1
  elif self.kind=='wires' and kind=='socket':
   if index<3:self.selected=index
   elif self.selected>=0:
    dest=index-3
    if dest==self.selected:
     self.solved[dest]=True
     if all(self.solved):self.finished=True;self.score=max(45,98-13*self.errors)
    else:self.errors+=1
    self.selected=-1
  elif self.kind=='irrigation' and kind=='choose':
   expected=self.order[len(self.solved)]
   if index==expected:
    self.solved.append(index)
    if len(self.solved)==3:self.finished=True;self.score=max(40,100-15*self.errors)
   else:self.errors+=1
  elif self.kind=='uv' and kind=='confirm':
   c=self.config
   if 65<=c['intensity']<=85 and 55<=c['red']<=75 and 35<=c['blue']<=55:
    self.finished=True;self.score=max(55,100-10*self.errors)
   else:self.errors+=1

 def reason(self):
  if self.kind in ('seal','heat','valve','frequency','tracking','stability'):
   return 'Move A/D into the highlighted target band; hold F to work. Avoid overheating.'
  return {
   'timing':'Press SPACE when the moving signal crosses the target zone.',
   'diagnose':'Use the multimeter: choose the terminal with the abnormal voltage.',
   'scan':'Choose the marked anomalous coil after scanning.',
   'screws':'Remove the four screws in the highlighted sequence.',
   'wires':'Connect each colored socket on the left to the matching one on the right.',
   'irrigation':'Open irrigation valves in the displayed order.',
   'uv':'Set light intensity, red and blue light levels within their safe bands.'
  }.get(self.kind,'Complete this repair.')
