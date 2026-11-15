"""Lunar Outpost V3 English Edition — Pygame controller and scene orchestration."""
from __future__ import annotations
import math,sys
import pygame
from .settings import *
from .model import State,TOOLS
from .nasa_data import NASAWorker,empty_snapshot,risk_score,read_cache
from .video_background import VideoBackground
from .graphics import Graphics
from .audio_manager import AudioManager
from .hud import HUD
from .minigames import Puzzle
from .rooms import items,objective,HUB_DOORS

ARIA_INITIAL={
 'life':'Alert: duct B is depressurizing. Diagnose the leak, collect the thermal sealant and repair all three cracks before oxygen runs out.',
 'generator':'The power inverter has failed. Diagnose the terminals, remove the burnt fuse and install the spare bridge to restore battery power.',
 'radiation':'Solar activity detected. Scan the field coils and synchronize the emitter before the simulated solar-particle event.',
 'hydro':'The greenhouse temperature has dropped to 2°C. Use the portable heater to thaw the frozen supply pipes, restore irrigation and restart grow lights.',
}
ARIA_SECOND={
 'life':'All leaks sealed. Carefully adjust the purge valve and keep the air pressure stable.',
 'generator':'Circuit repaired. You have a 100 W training budget: distribute power among life support, crops and shielding without overloading the grid.',
 'radiation':'The coils are synchronized. Activate the main switch to deploy the fictional electromagnetic shield.',
 'hydro':'The water is flowing again. Set the photosynthetically active grow lights to safe levels.',
}

class Astronaut:
 def __init__(self):
  self.x=100.0;self.feet=float(GROUND);self.vy=0.0;self.facing=1
  self.speeding=False;self.grounded=True
 def reset(self,x=100):self.__init__();self.x=float(x)
 def jump(self):
  if self.grounded:self.vy=-490;self.grounded=False
 def update(self,dt,keys):
  move=int(keys[pygame.K_d] or keys[pygame.K_RIGHT])-int(keys[pygame.K_a] or keys[pygame.K_LEFT])
  self.speeding=move!=0
  if move:self.facing=move
  self.x=max(55,min(1225,self.x+move*255*dt))
  self.vy+=1110*dt
  self.feet+=self.vy*dt
  if self.feet>=GROUND:self.feet=GROUND;self.vy=0;self.grounded=True

class LunarGame:
 def __init__(self):
  pygame.mixer.pre_init(44100,-16,2,512)
  pygame.init()
  self.window=pygame.display.set_mode((WIDTH,HEIGHT),pygame.RESIZABLE)
  pygame.display.set_caption('Lunar Outpost V3.0 | A.R.I.A. | English Edition')
  self.screen=pygame.Surface((WIDTH,HEIGHT)).convert()
  self.clock=pygame.time.Clock()
  self.hud=HUD(pygame)
  self.gfx=Graphics(pygame)
  self.audio=AudioManager(pygame)
  self.video=VideoBackground()
  self.video_frame=None
  self.video_enabled=True
  self.player=Astronaut()
  self.nasa=NASAWorker()
  self.preview=read_cache() or empty_snapshot('Telemetry not yet fetched.')
  self.state:State|None=None
  self.scene='menu'
  self.return_scene='menu'
  self.popup=None
  self.puzzle:Puzzle|None=None
  self.puzzle_action=''
  self.message='A.R.I.A. online. Welcome to the lunar outpost.'
  self.robot='normal'
  self.hint=''
  self.elapsed=0.0
  self.notice=''
  self.notice_timer=0.0
  self.difficulty='Cadet'
  self.drag_slider=None
  self.puzzle_hold=False
  self.active=True

 def mouse(self):
  ww,hh=self.window.get_size()
  scale=min(ww/WIDTH,hh/HEIGHT)
  ox=(ww-WIDTH*scale)/2;oy=(hh-HEIGHT*scale)/2
  x,y=pygame.mouse.get_pos()
  return (x-ox)/scale,(y-oy)/scale

 def change_scene(self,scene):
  if hasattr(self,'audio'):self.audio.resume_music()
  self.video.close()
  self.video_frame=None
  self.scene=scene
  if self.state and scene in ROOMS+('hub',):
   self.state.scene=scene
   self.state.player_x=self.player.x
  name=ROOM_VIDEOS.get(scene)
  if name and self.video_enabled:
   p=ASSETS/'video'/name
   if p.is_file():self.video.open(p)

 def new_game(self):
  self.state=None
  self.popup=None
  self.change_scene('intro')
  self.message='Welcome to Apollo 5 training. You must keep the outpost alive for 30 mission sols.'
  self.robot='hablando'

 def save_sources(self):
  """V3 saves in its own folder; V1 and V2 saves are read-only migration sources."""
  return (SAVE, ROOT/'lunar_v2'/'user_data'/'save_v2.json', ROOT/'data'/'save_v2.json', ROOT/'data'/'savegame.json', DATA/'savegame.json')

 def save_available(self):
  return any(path.is_file() for path in self.save_sources())

 def load_game(self):
  try:
   # Old V1/V2 saves are read, never overwritten by V3.
   source=next((path for path in self.save_sources() if path.is_file()),SAVE)
   self.state=State.load(source)
   self.player.reset(self.state.player_x)
   self.change_scene(self.state.scene if self.state.scene in ROOMS+('hub',) else 'hub')
   if self.state.won or self.state.lost:self.change_scene('result')
   self.popup='event' if self.state and self.state.pending else None
   self.message='Saved mission restored. Continue your repair objectives.'
   self.robot='normal'
  except (OSError,ValueError,KeyError,TypeError) as exc:
   self.alert(f'Could not load the saved mission: {type(exc).__name__}')

 def save(self):
  if not self.state:return
  if self.scene in ROOMS+('hub',):
   self.state.scene=self.scene
   self.state.player_x=self.player.x
  try:self.state.save(SAVE)
  except (OSError,ValueError):self.alert('Save failed. Check folder permissions.')

 def alert(self,text):self.notice=text;self.notice_timer=3.5

 def start_loading(self):
  self.change_scene('loading')
  self.nasa.start()

 def start_from_data(self,snapshot):
  if self.scene!='loading':
   self.preview=snapshot
   return
  self.preview=snapshot
  self.state=State.start(snapshot,risk_score(snapshot),self.difficulty)
  self.player.reset(95)
  self.change_scene('hub')
  self.message='The four main systems need repairs. Manage resources to survive 30 mission sols.'
  self.robot='hablando'
  self.save()

 def enter_room(self,room):
  if not self.state:return
  self.change_scene(room)
  self.player.reset(95)
  self.state.player_x=95
  self.popup=None
  self.message=ARIA_INITIAL[room] if not self.state.operational[room] else 'This module is operational. Return to Mission Control.'
  self.robot='hablando'
  self.save()

 def hub(self):
  self.change_scene('hub')
  self.player.reset(95)
  self.popup=None
  self.message='Repair systems and advance sols from Mission Control.'
  self.robot='normal'
  self.save()

 def toolkit(self):
  if not self.state or not self.state.acquired:self.alert('No tools collected yet.');return
  self.popup='inventory'

 def rotate_tool(self,sign):
  s=self.state
  if not s or not s.acquired:return
  try:i=s.acquired.index(s.equipped)
  except ValueError:i=0
  s.equip(s.acquired[(i+sign)%len(s.acquired)])
  self.alert('Equipped: '+TOOLS[s.equipped][0])

 def take_action(self,action):
  if getattr(self,'audio',None):self.audio.play('tap')
  if action=='quit':self.active=False
  elif action=='new':self.new_game()
  elif action=='continue':self.load_game()
  elif action=='begin':self.start_loading()
  elif action=='offline':self.start_from_data(empty_snapshot('Offline training explicitly selected.'))
  elif action=='menu':self.popup=None;self.change_scene('menu')
  elif action=='hub':self.hub()
  elif action=='resume':self.popup=None;self.video.pause(False);self.audio.resume_music()
  elif action=='save':self.save();self.popup=None;self.alert('Mission saved.')
  elif action=='inventory':self.toolkit()
  elif action=='close':self.popup=None;self.video.pause(False);self.audio.resume_music()
  elif action=='help':self.popup='objectives'
  elif action=='show_telemetry':
   self.return_scene=self.scene;self.popup=None;self.change_scene('telemetry')
  elif action=='back_telemetry':
   self.change_scene(self.return_scene)
  elif action=='refresh_nasa':
   if self.nasa.start(force=True):self.alert('Requesting new NASA observations...')
  elif action=='advance':self.advance_sol()
  elif action=='sound_toggle':
   if self.audio:self.alert('SOUND EFFECTS: '+('ON' if self.audio.toggle() else 'OFF'))
  elif action=='music_toggle':
   if self.audio:
    active=self.audio.toggle_music()
    if active and self.popup=='pause':self.audio.pause_music()
    self.alert('SURFACE TENSION MUSIC: '+('ON' if active else 'OFF'))
  elif action=='music_down':
   if self.audio:self.alert(f'MUSIC VOLUME: {round(self.audio.adjust_music_volume(-0.1)*100)}%')
  elif action=='music_up':
   if self.audio:self.alert(f'MUSIC VOLUME: {round(self.audio.adjust_music_volume(+0.1)*100)}%')
  elif action=='video_toggle':
   self.video_enabled=not self.video_enabled
   self.change_scene(self.scene)
   self.alert('Animated backgrounds: '+('ON' if self.video_enabled else 'OFF'))
  elif action.startswith('difficulty:'):
   self.difficulty=action.split(':',1)[1]
   self.alert('Difficulty: '+self.difficulty)
  elif action.startswith('enter:'):
   room=action.split(':',1)[1]
   if abs(self.player.x-HUB_DOORS[room])<96:self.enter_room(room)
   else:self.alert('Walk closer to the module entrance.')
  elif action.startswith('equip:'):
   if self.state and self.state.equip(action.split(':',1)[1]):self.popup=None;self.alert('Tool equipped.')
  elif action.startswith('take:'):
   name=action.split(':',1)[1]
   self.state.acquire(name)
   self.alert(TOOLS[name][0]+' collected and equipped.')
   if getattr(self,'audio',None):self.audio.play('collect')
   self.robot='hablando'
   self.message='Use Q/R to switch tools. Press TAB to view your inventory.'
   self.save()
  elif action=='install:bridge':
   if self.state.equipped!='bridge':self.alert('Equip the spare bridge first (TAB).')
   else:
    self.state.progress['generator']['bridge_installed']=True
    self.message='The bridge is installed. Connect all three matching wire pairs.'
    self.save()
  elif action=='use_kit':
   self.use_kit()
  elif action=='activate:shield':
   self.state.progress['radiation']['shield']=True
   self.finish_room('radiation')
  elif action.startswith('puzzle:'):
   bits=action.split(':')
   kind=bits[1]
   idx=int(bits[2]) if len(bits)>2 else 0
   self.open_puzzle(kind,idx)
  elif action.startswith('event:'):
   self.state.respond(int(action.split(':')[1]))
   self.popup=None
   self.robot='hablando'
   self.message='Your decision changed the colony reserves. Check the HUD.'
   self.check_end();self.save()
  elif action.startswith('choose:') and self.puzzle:
   self.puzzle.input_action('choose',int(action.split(':')[1]))
   self.check_puzzle()
  elif action.startswith('socket:') and self.puzzle:
   self.puzzle.input_action('socket',int(action.split(':')[1]))
   self.check_puzzle()
  elif action=='trigger' and self.puzzle:
   self.puzzle.input_action('trigger');self.check_puzzle()
  elif action=='confirm_grid':
   try:
    valid=self.state.set_power(self.state.power)
    if valid:
     self.open_puzzle('stability')
     self.alert('Power allocation accepted. Maintain the test signal.')
    else:self.fail('Power below safe minimums. Try another distribution.')
   except ValueError:self.fail('The grid cannot exceed 100 W.')
  elif action=='confirm_uv' and self.puzzle:
   self.puzzle.input_action('confirm')
   if not self.puzzle.finished:self.fail('Light levels are outside the safe operating ranges.')
   self.check_puzzle()

 def fail(self,text):
  if self.state and not self.state.lost:
   key={'life':'life','generator':'energy','hydro':'food','radiation':'integrity'}.get(self.scene,'energy')
   self.state.modify(**{key:-1.2})
  self.robot='peligro';self.alert(text)
  if getattr(self,'audio',None):self.audio.play('error')
  self.check_end()

 def open_puzzle(self,kind,index=0):
  if kind=='grid':
   self.puzzle=Puzzle.create('grid',seed=self.state.seed)
  elif kind=='coil':
   key=('frequency','timing','tracking')[index]
   self.puzzle=Puzzle.create(key,index,self.state.seed)
  else:
   self.puzzle=Puzzle.create(kind,index,self.state.seed)
  self.popup='puzzle'
  self.puzzle_action=f'{kind}:{index}'
  self.robot='hablando'
  self.message=('Identify the leaking duct, then collect a sealant tool.' if kind=='diagnose' and self.scene=='life' else self.puzzle.reason())
  # Leave the MP4 background running behind the minigame UI.
  self.video.pause(False)

 def finish_room(self,room):
  score_list=self.state.work_scores[room]
  quality=round(sum(score_list)/len(score_list)) if score_list else 75
  if self.state.complete(room,quality):
   self.message=room.replace('_',' ').title()+' restored. Excellent work, astronaut.'
   self.robot='mision_completada'
   self.alert('SYSTEM RESTORED: '+NAMES[room])
   if getattr(self,'audio',None):self.audio.play('success')
  self.save()
  self.check_end()

 def check_puzzle(self):
  p=self.puzzle
  if not p or not p.finished:return
  state=self.state; room=self.scene
  action=self.puzzle_action.split(':')
  kind=action[0];idx=int(action[1])
  state.work_scores[room].append(p.score)
  tool_required={'seal':'sealant','heat':'heater','diagnose':'multimeter' if room=='generator' else None,
                 'screws':'wrench','wires':'wrench','scan':'scanner','coil':'calibrator'}.get(kind)
  if tool_required and tool_required in state.acquired and state.equipped==tool_required:
   state.consume(tool_required,2)
  if room=='life':
   if kind=='diagnose':state.progress['life']['diagnosed']=True
   if kind=='seal':
    state.progress['life']['cracks'][idx]=True
    state.consume('sealant',6+2*idx)
   if kind=='valve':
    state.progress['life']['valve']=1
    self.finish_room(room)
  if room=='generator':
   if kind=='diagnose':state.progress['generator']['diagnosed']=True
   elif kind=='screws':state.progress['generator']['panel']=True
   elif kind=='wires':state.progress['generator']['links']=[True]*3
   elif kind=='grid':pass
   elif p.kind=='stability':
    state.progress['generator']['stable']=True
    self.finish_room(room)
  if room=='radiation':
   if kind=='scan':state.progress['radiation']['scanned']=True
   elif kind=='coil':state.progress['radiation']['calibrated'][idx]=True
  if room=='hydro':
   if kind=='heat':
    state.progress['hydro']['pipes'][idx]=True
    state.consume('heater',9+2*idx)
   elif kind=='irrigation':state.progress['hydro']['water']=[True]*3
   elif kind=='uv':
    state.progress['hydro']['lights']=True
    self.finish_room(room)
  self.puzzle=None
  self.popup=None
  self.video.pause(False)
  if not state.operational[room]:
   self.message='Step completed. '+objective(state,room)
   if room=='life' and all(state.progress['life']['cracks']):self.message=ARIA_SECOND['life']
   elif room=='generator' and all(state.progress['generator']['links']):self.message=ARIA_SECOND['generator']
   elif room=='radiation' and all(state.progress['radiation']['calibrated']):self.message=ARIA_SECOND['radiation']
   elif room=='hydro' and all(state.progress['hydro']['pipes']):self.message=ARIA_SECOND['hydro']
   self.robot='mision_completada'
  self.alert('REPAIR STEP COMPLETED')
  self.save()

 def progress_hint(self):
  if self.scene in ROOMS:
   self.robot='pista'
   self.hint=objective(self.state,self.scene)
   self.alert('A.R.I.A. hint: '+self.hint)
  else:self.alert('Visit a module to receive repair hints.')

 def advance_sol(self):
  if not self.state:return
  if not self.state.advance():self.alert('Resolve the emergency or finish the current mission first.');return
  if self.state.pending:self.popup='event';self.robot='peligro';self.message='Warning: mission event requires a decision.'
  else:self.alert(f'Sol {self.state.sol}/30. Supplies updated.')
  self.check_end();self.save()

 def check_end(self):
  if self.state is not None and (self.state.won or self.state.lost):
   self.popup=None;self.change_scene('result')
   self.robot='mision_completada' if self.state.won else 'triste'
   self.save()

 def use_kit(self):
  if not self.state or self.scene not in ROOMS:
   self.alert('The emergency kit can only be used in a damaged module.')
   return
  if self.state.operational[self.scene]:
   self.alert('This module is already stable; save the kit for later.')
   return
  if not self.state.consume('kit',34):
   self.alert('Equip a charged emergency repair kit first.')
   return
  key={'life':'life','generator':'energy','hydro':'food','radiation':'integrity'}[self.scene]
  self.state.modify(**{key:7})
  self.state.record('Emergency kit temporarily stabilized '+self.scene+' (simulated).')
  self.robot='hablando'
  self.alert('Temporary stabilization: +7 '+RES_NAMES[key]+'. Complete the full repair!')
  self.save()

 def interact(self):
  if not self.state or self.scene not in ROOMS+('hub',):return
  if self.scene=='hub':
   nearest=min(HUB_DOORS,key=lambda r:abs(HUB_DOORS[r]-self.player.x))
   if abs(HUB_DOORS[nearest]-self.player.x)<95:self.enter_room(nearest)
   elif abs(self.player.x-1120)<80:self.take_action('take:kit')
   else:self.alert('Move near a module entrance and press E.')
   return
  possible=[obj for obj in items(self.state,self.scene) if abs(obj.x-self.player.x)<95]
  if not possible:self.alert('Move closer to a highlighted device.');return
  nearest=min(possible,key=lambda o:abs(o.x-self.player.x))
  if nearest.required and self.state.equipped!=nearest.required:
   self.alert('Equip the '+TOOLS[nearest.required][0]+' first (TAB).');return
  self.take_action(nearest.action)

 def event(self,event):
  if event.type==pygame.QUIT:self.active=False;return
  if event.type==pygame.VIDEORESIZE:
   self.window=pygame.display.set_mode(event.size,pygame.RESIZABLE);return
  if event.type==pygame.MOUSEBUTTONUP and event.button==1:self.drag_slider=None;return
  if event.type==pygame.MOUSEMOTION and self.drag_slider:self.set_slider(self.mouse())
  if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
   x,y=self.mouse()
   if self.popup=='puzzle' and self.puzzle and self.puzzle.kind in ('grid','uv'):
    for row in range(3):
     yy=290+row*80
     if 440<=x<=880 and yy-22<=y<=yy+32:
      self.drag_slider=row
      self.set_slider((x,y))
      return
   for rect,action in reversed(self.hud.actions):
    if rect.collidepoint(x,y):self.take_action(action);return
  if event.type!=pygame.KEYDOWN:return
  key=event.key
  if key==pygame.K_ESCAPE:
   if self.popup=='event':self.alert('Choose a response to this event.');return
   if self.popup=='puzzle':
    self.popup=None;self.puzzle=None;self.video.pause(False);return
   if self.popup:self.popup=None;self.video.pause(False);self.audio.resume_music();return
   if self.scene=='telemetry':self.take_action('back_telemetry');return
   if self.scene in ROOMS+('hub',):self.popup='pause';self.video.pause(True);self.audio.pause_music();return
   if self.scene in ('intro','result'):self.change_scene('menu');return
   if self.scene=='menu':self.active=False;return
  if self.popup=='puzzle':
   if key==pygame.K_SPACE and self.puzzle and self.puzzle.kind=='timing':
    self.puzzle.input_action('trigger');self.check_puzzle()
   if key==pygame.K_RETURN and self.puzzle:
    if self.puzzle.kind=='grid':self.take_action('confirm_grid')
    elif self.puzzle.kind=='uv':self.take_action('confirm_uv')
   return
  if self.popup:return
  if self.scene=='intro' and key==pygame.K_RETURN:self.start_loading();return
  if self.scene=='loading' and key==pygame.K_RETURN:self.take_action('offline');return
  if self.scene in ROOMS+('hub',):
   if key==pygame.K_SPACE:self.player.jump()
   elif key==pygame.K_e:self.interact()
   elif key==pygame.K_f and self.state and self.state.equipped=='kit':self.use_kit()
   elif key==pygame.K_TAB:self.toolkit()
   elif key==pygame.K_q:self.rotate_tool(-1)
   elif key==pygame.K_r:self.rotate_tool(+1)
   elif key==pygame.K_h:self.progress_hint()
   elif key==pygame.K_t:self.take_action('show_telemetry')
   elif key==pygame.K_m:self.take_action('music_toggle')
   elif key==pygame.K_b:self.take_action('sound_toggle')
   elif key==pygame.K_n and self.scene=='hub':self.advance_sol()

 def set_slider(self,point):
  if not self.puzzle:return
  p=self.puzzle
  row=self.drag_slider
  if row is None:return
  new=round(max(0,min(100,(point[0]-440)/440*100))/5)*5
  if p.kind=='grid':
   key=('life','hydro','radiation')[row]
   used_other=sum(v for k,v in self.state.power.items() if k!=key)
   self.state.power[key]=int(min(100-used_other,new))
  elif p.kind=='uv':
   key=('intensity','red','blue')[row]
   p.config[key]=float(new)

 def update(self,dt):
  self.elapsed+=dt
  self.notice_timer=max(0,self.notice_timer-dt)
  if self.notice_timer==0:self.notice=''
  fetched=self.nasa.poll()
  if fetched is not None:
   if self.scene=='loading':self.start_from_data(fetched)
   else:self.preview=fetched;self.alert('NASA data refreshed for future missions.')
  if self.popup=='puzzle' and self.puzzle:
   keys=pygame.key.get_pressed()
   move={'left':keys[pygame.K_a] or keys[pygame.K_LEFT],
         'right':keys[pygame.K_d] or keys[pygame.K_RIGHT],
         'use':keys[pygame.K_f]}
   old_errors=self.puzzle.errors
   self.puzzle.update(dt,move)
   if self.puzzle.errors>old_errors:self.fail('Tool overheated / unstable signal. Adjust and retry.')
   self.check_puzzle()
   return
  if self.popup or self.scene not in ROOMS+('hub',) or not self.state:return
  self.player.update(dt,pygame.key.get_pressed())
  if self.scene=='life' and not self.state.operational['life']:
   self.state.modify(life=-dt*.020)
  if self.scene=='generator' and not self.state.operational['generator']:
   self.state.modify(energy=-dt*.019)
  if self.scene=='radiation' and not self.state.operational['radiation']:
   pr=self.state.progress['radiation']
   pr['storm_timer']-=dt
   if pr['storm_timer']<=0 and not pr['storm_hit']:
    pr['storm_hit']=True
    self.state.modify(integrity=-16-self.state.nasa_risk*.09)
    self.robot='peligro'
    self.alert('Simulated solar particle impact! Shield still needs repair.')
  if self.scene=='hydro' and not self.state.operational['hydro']:
   self.state.modify(food=-dt*.015)
  self.check_end()

 def draw_background(self):
  fallback={'intro':'menu','loading':'menu','result':'menu','telemetry':'hub'}.get(self.scene,self.scene)
  self.gfx.background(self.screen,fallback)
  if self.scene in ROOM_VIDEOS and self.video_enabled:
   fresh=self.video.frame(pygame)
   if fresh is not None:
    self.video_frame=pygame.transform.scale(fresh,(WIDTH,HEIGHT))
   if self.video_frame is not None:
    self.screen.blit(self.video_frame,(0,0))

 def draw_menu(self):
  u=self.hud;s=self.screen
  self.draw_background()
  u.panel(s,(0,70,730,650),(5,18,29),None,220,0)
  u.text(s,'TRANSMISSION // LUNAR TRAINING',73,156,'small',MUTED)
  u.text(s,'LUNAR',68,204,'hero',WHITE)
  u.text(s,'OUTPOST',68,276,'hero',CYAN)
  u.text(s,'A.R.I.A.  /  VERSION 3.0',76,372,'medium',WHITE)
  u.button(s,'START NEW MISSION',(77,417,481,57),'new')
  u.button(s,'CONTINUE',(77,481,481,53),'continue',enabled=self.save_available())
  u.button(s,'NASA TELEMETRY',(77,545,481,53),'show_telemetry')
  u.button(s,'EXIT GAME',(77,607,481,53),'quit',RED)
  u.text(s,'DIFFICULTY',765,566,'tiny',CYAN)
  for i,name in enumerate(('Cadet','Engineer','Commander')):
   u.button(s,name.upper(),(762+i*157,592,148,48),'difficulty:'+name,
            YELLOW if self.difficulty==name else EDGE)
  self.gfx.aria_draw(s,852,219,'normal')
  u.text(s,'SOUNDTRACK  /  SURFACE TENSION',755,538,'tiny',CYAN)

 def draw_intro(self):
  s=self.screen;u=self.hud;self.draw_background();u.dim(s,95)
  u.panel(s,(55,415,1168,253),(9,29,45),CYAN,242,14)
  self.gfx.aria_draw(s,870,211,'hablando')
  u.text(s,'APOLLO 5 // TRAINING TRANSMISSION',90,437,'small',CYAN)
  u.wrap(s,'Welcome to Apollo 5 training. Your mission: repair a fictional lunar outpost and keep its crew alive for 30 mission sols.',90,475,1060,'medium',WHITE,4)
  u.button(s,'BEGIN TRAINING',(790,584,375,57),'begin',GREEN)
  u.button(s,'BACK',(90,584,198,57),'menu')

 def draw_loading(self):
  s=self.screen;u=self.hud;self.draw_background();u.dim(s,170)
  u.panel(s,(254,177,772,358),(10,29,43),CYAN,248,13)
  u.text(s,'CONNECTING TO NASA DONKI',640,215,'big',WHITE,center=True)
  u.wrap(s,'Retrieving available space-weather observations. NASA reports are kept separate from simulated colony resources.',292,291,680,'normal',MUTED,4)
  u.text(s,'Loading telemetry'+'.'*(1+int(self.elapsed*2)%3),640,392,'medium',CYAN,center=True)
  u.button(s,'PLAY WITHOUT NASA DATA',(356,453,570,58),'offline',YELLOW)

 def draw_hub(self):
  s=self.screen;u=self.hud;g=self.gfx
  self.draw_background()
  shade=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA);shade.fill((0,10,20,68));s.blit(shade,(0,0))
  for room,x in HUB_DOORS.items():
   status=self.state.operational[room]
   col=GREEN if status else YELLOW
   u.panel(s,(x-106,318,214,167),(10,31,44),col,214,10)
   u.text(s,NAMES[room],x,332,'tiny',WHITE,center=True)
   pygame.draw.circle(s,col,(x,403),25,3)
   u.text(s,'OK' if status else '!',x,389,'medium',col,center=True)
   u.text(s,'STABLE' if status else 'NEEDS REPAIR',x,449,'tiny',col,center=True)
   if abs(self.player.x-x)<96:
    u.text(s,'PRESS E TO ENTER',x,293,'tiny',CYAN,center=True)
   u.actions.append((pygame.Rect(x-106,318,214,167),'enter:'+room))
  pygame.draw.rect(s,(20,39,54),(0,GROUND,WIDTH,26))
  g.astronaut_draw(s,self.player,self.elapsed)
  u.resources(s,self.state,'MISSION CONTROL')
  u.panel(s,(25,174,612,83),(8,27,39),EDGE,220)
  u.text(s,'OBJECTIVE: SURVIVE 30 SOLS',42,190,'small',WHITE)
  u.text(s,'Repair the four systems. Each choice affects reserves.',42,225,'tiny',MUTED)
  u.button(s,'ADVANCE ONE SOL  [N]',(930,500,302,54),'advance',GREEN)
  if 'kit' not in self.state.acquired:
   self.gfx.tool_icon(s,'kit',(1130,432,48,49))
   u.text(s,'REPAIR KIT [E]',1129,413,'tiny',CYAN)
  u.aria(s,self.gfx,self.message,self.robot,'E: interact   TAB: inventory   T: NASA   ESC: pause')

 def draw_room(self):
  s=self.screen;u=self.hud;room=self.scene
  self.draw_background()
  # Floor and overlays are logical game entities; they don't depend on video pixels.
  pygame.draw.rect(s,(16,31,42),(0,GROUND,WIDTH,26))
  progress=self.state.progress[room]
  if room=='life':
   for i,x in enumerate((460,675,895)):
    if progress['diagnosed']:
     col=GREEN if progress['cracks'][i] else RED
     pygame.draw.line(s,col,(x-10,385),(x+10,420),4)
     if not progress['cracks'][i]:pygame.draw.line(s,RED,(x+7,384),(x-5,401),3)
  elif room=='generator':
   if progress['diagnosed']:
    pygame.draw.circle(s,GREEN if progress['panel'] else RED,(580,380),9)
   if progress['bridge_installed']:
    u.text(s,'BRIDGE INSTALLED',454,275,'tiny',GREEN)
  elif room=='radiation':
   timer=max(0,round(progress['storm_timer']))
   u.panel(s,(1005,174,235,69),(38,20,37),RED,232)
   u.text(s,'SOLAR IMPACT (SIM.)',1019,183,'tiny',WHITE)
   u.text(s,f'{timer} SECONDS',1019,204,'medium',RED)
   for i,x in enumerate((492,728,932)):
    if progress['scanned']:
     col=GREEN if progress['calibrated'][i] else PURPLE
     pygame.draw.circle(s,col,(x,380),19,3)
  elif room=='hydro':
   if 'heater' in self.state.acquired:
    for i,x in enumerate((450,690,905)):
     col=GREEN if progress['pipes'][i] else CYAN
     pygame.draw.line(s,col,(x-27,431),(x+27,431),6)
  self.gfx.astronaut_draw(s,self.player,self.elapsed)
  u.resources(s,self.state,NAMES[room])
  if room in ROOM_VIDEOS:
   live = self.video_enabled and self.video_frame is not None and self.video.loaded
   u.text(s,'MP4 LIVE' if live else 'PNG FALLBACK',1226,152,'tiny',GREEN if live else YELLOW,right=True)
  u.panel(s,(24,163,795,64),(8,26,43),EDGE,225)
  u.text(s,objective(self.state,room),41,181,'small',WHITE)
  from .rooms import items
  for item in items(self.state,room):
   x=item.x;y=489
   if item.action.startswith('take:'):
    key=item.action.split(':',1)[1]
    self.gfx.tool_icon(s,key,(x-25,405,50,51))
   near=abs(self.player.x-x)<94
   pygame.draw.circle(s,CYAN if near else YELLOW,(x,y),22,3)
   pygame.draw.circle(s,WHITE,(x,y),5)
   label=item.label
   width=min(275,max(150,u.fonts['tiny'].size(label)[0]+26))
   u.panel(s,(max(0,min(WIDTH-width,x-width//2)),515,width,29),(7,22,34),CYAN if near else EDGE,246,4)
   u.text(s,label,max(0,min(WIDTH-width,x-width//2))+width//2,521,'tiny',WHITE,center=True)
   if near:u.text(s,'[E]',x,457,'small',GREEN,center=True)
  if self.state.operational[room]:u.text(s,'● SYSTEM OPERATIONAL',970,252,'small',GREEN)
  u.aria(s,self.gfx,self.message,self.robot,'H: hint   Q/R: switch tool   F: use')

 def draw_telemetry(self):
  s=self.screen;u=self.hud;self.draw_background();u.dim(s,209)
  u.panel(s,(74,81,1133,569),(8,27,40),CYAN,252,13)
  u.text(s,'NASA SPACE WEATHER TELEMETRY',101,110,'big',WHITE)
  snapshot=self.state.nasa_snapshot if self.state else self.preview
  mode=snapshot.get('status','offline')
  col={'online':GREEN,'cached':YELLOW,'offline':RED}.get(mode,RED)
  u.text(s,'DATA MODE: '+mode.upper(),109,189,'medium',col)
  u.text(s,'SOURCE: NASA DONKI  |  LAST FETCH: '+str(snapshot.get('fetched_at') or 'NOT AVAILABLE')[:24],109,230,'small',WHITE)
  counts=snapshot.get('events',{})
  for i,name in enumerate(('FLR','GST','SEP','CME')):
   value=len(counts.get(name,[]))
   u.panel(s,(102+i*268,283,249,86),(15,43,56),EDGE,250)
   u.text(s,name,123+i*268,295,'small',CYAN)
   u.text(s,str(value)+' EVENTS',123+i*268,324,'medium',WHITE)
  risk=self.state.nasa_risk if self.state else risk_score(snapshot)
  u.text(s,f'EDUCATIONAL SPACE-WEATHER SCORE: {risk}/100',108,404,'medium',YELLOW)
  u.wrap(s,'This is a game-generated score, NOT a NASA index. Oxygen, power, food, colony integrity and local radiation damage are simulated.',108,450,940,'small',MUTED,4)
  u.button(s,'REFRESH NASA',(784,564,371,58),'refresh_nasa',CYAN)
  u.button(s,'BACK',(110,563,255,58),'back_telemetry')

 def draw_result(self):
  s=self.screen;u=self.hud;self.draw_background();u.dim(s,204)
  success=self.state.won
  col=GREEN if success else RED
  u.panel(s,(225,152,831,496),(8,30,43),col,251,16)
  self.gfx.aria_draw(s,736,222,'mision_completada' if success else 'triste')
  u.text(s,'MISSION SUCCESS' if success else 'MISSION FAILED',285,198,'big',col)
  u.text(s,f'FINAL SOL: {self.state.sol}/30',293,307,'medium',WHITE)
  u.text(s,f'SYSTEMS: {sum(self.state.operational.values())}/4',293,351,'medium',WHITE)
  if not success:u.wrap(s,self.state.failure_reason,294,405,670,'small',RED,3)
  else:u.wrap(s,'The outpost survived. Your engineering decisions kept the colony operational.',294,412,660,'small',WHITE,4)
  u.button(s,'NEW MISSION',(286,538,331,64),'new',GREEN)
  u.button(s,'MAIN MENU',(635,538,331,64),'menu')

 def draw_puzzle(self):
  p=self.puzzle;s=self.screen;u=self.hud
  u.dim(s,207)
  u.panel(s,(144,108,992,503),(9,29,44),CYAN,250,12)
  titles={'seal':'THERMAL SEALANT REPAIR','heat':'PIPE HEAT CONTROL','valve':'PRESSURE PURGE VALVE',
          'frequency':'COIL FREQUENCY CALIBRATION','timing':'SIGNAL SYNCHRONIZATION',
          'tracking':'FIELD STABILITY TRACKING','stability':'POWER GRID STABILITY',
          'diagnose':'MULTIMETER DIAGNOSTICS' if self.scene=='generator' else 'AIR DUCT DIAGNOSTICS',
          'scan':'RADIATION FIELD SCAN','screws':'OPEN THE MAINTENANCE PANEL',
          'wires':'CONNECT THE POWER CIRCUIT','irrigation':'RESTORE IRRIGATION FLOW',
          'grid':'POWER DISTRIBUTION','uv':'GROW LIGHT CONTROLLER'}
  u.text(s,titles.get(p.kind,'SYSTEM REPAIR'),640,139,'big',WHITE,center=True)
  u.wrap(s,p.reason(),210,208,854,'small',MUTED,3)
  if p.kind in ('seal','heat','valve','frequency','tracking','stability','timing'):
   x=326;y=340;w=620
   u.text(s,'TARGET  /  LIVE CONTROL',326,298,'small',WHITE)
   pygame.draw.rect(s,(54,70,81),(x,y,w,31),border_radius=8)
   tx=x+int(p.target/100*w);cx=x+int(p.cursor/100*w)
   pygame.draw.rect(s,(36,126,80),(tx-32,y,64,31),border_radius=6)
   pygame.draw.line(s,YELLOW,(cx,y-13),(cx,y+45),6)
   if p.kind=='timing':
    u.button(s,'SYNC  [SPACE]',(490,466,286,61),'trigger',GREEN)
    u.text(s,f'FAILED ATTEMPTS: {p.errors}',490,540,'small',YELLOW)
   else:
    amount={'seal':1.6+p.index*.55,'heat':2+p.index*.45,'valve':2.5,'frequency':2.,'tracking':2.3,'stability':3.}[p.kind]
    u.meter(s,343,419,570,'REPAIR PROGRESS',100*p.progress/amount,GREEN)
    u.meter(s,343,487,570,'TOOL HEAT',p.heat,RED if p.heat>80 else YELLOW)
    u.text(s,'A / D: ADJUST    HOLD F: WORK    KEEP THE CURSOR IN THE GREEN ZONE',640,562,'tiny',CYAN,center=True)
  elif p.kind in ('diagnose','scan'):
   u.text(s,'CHOOSE THE FAULTY TERMINAL / COIL',640,302,'medium',WHITE,center=True)
   names=(['DUCT A: OK','DUCT B: LEAK','DUCT C: OK'] if self.scene=='life' else ['24.3 V','0.0 V','24.5 V']) if p.kind=='diagnose' else ['COIL A: OK','COIL B: OK','COIL C: ERROR']
   for i,label in enumerate(names):
    u.button(s,label,(234+i*285,365,260,91),f'choose:{i}',GREEN if i==p.selected else CYAN)
   u.text(s,f'INCORRECT ATTEMPTS: {p.errors}',637,507,'small',YELLOW,center=True)
  elif p.kind in ('screws','irrigation'):
   if p.kind=='screws':sequence='3 → 1 → 4 → 2';labels=['SCREW 1','SCREW 2','SCREW 3','SCREW 4'];n=4
   else:sequence='3 → 1 → 2';labels=['VALVE 1','VALVE 2','VALVE 3'];n=3
   u.text(s,'REQUIRED ORDER: '+sequence,641,290,'medium',YELLOW,center=True)
   for i in range(n):
    x=220+i*(840//n)
    col=GREEN if i in p.solved else CYAN
    u.button(s,labels[i],(x,370,210,91),f'choose:{i}',col)
   u.text(s,f'COMPLETED: {len(p.solved)}/{n}  |  ERRORS: {p.errors}',640,505,'small',WHITE,center=True)
  elif p.kind=='wires':
   colors=(CYAN,YELLOW,GREEN)
   u.text(s,'CLICK ONE LEFT SOCKET, THEN ITS MATCHING RIGHT SOCKET',640,275,'small',MUTED,center=True)
   for i,col in enumerate(colors):
    y=321+i*77
    if p.solved[i]:pygame.draw.line(s,col,(451,y+19),(851,y+19),5)
    u.button(s,f'INPUT {i+1}',(267,y,185,46),f'socket:{i}',col)
    u.button(s,f'OUTPUT {i+1}',(853,y,190,46),f'socket:{i+3}',col)
   u.text(s,f'SELECTED INPUT: {p.selected+1 if p.selected>=0 else "NONE"}  ·  ERRORS: {p.errors}',641,570,'small',WHITE,center=True)
  elif p.kind in ('grid','uv'):
   if p.kind=='grid':
    values=self.state.power; rows=(('life','LIFE SUPPORT',CYAN),('hydro','GREENHOUSE',GREEN),('radiation','SHIELDS',PURPLE))
    total=sum(values.values()); u.text(s,f'TOTAL: {total}/100 W  ·  AVAILABLE: {100-total} W',640,261,'medium',YELLOW,center=True)
   else:
    values=p.config;rows=(('intensity','LIGHT INTENSITY',CYAN),('red','RED LIGHT',YELLOW),('blue','BLUE LIGHT',PURPLE))
    u.text(s,'SAFE RANGES: INTENSITY 65–85  |  RED 55–75  |  BLUE 35–55',640,261,'small',YELLOW,center=True)
   for i,(key,label,col) in enumerate(rows):
    y=290+i*80
    u.text(s,label,222,y-6,'small',WHITE)
    pygame.draw.rect(s,(48,66,78),(440,y,440,18),border_radius=7)
    if values[key]:pygame.draw.rect(s,col,(440,y,int(values[key]*4.4),18),border_radius=7)
    pygame.draw.circle(s,WHITE,(440+int(values[key]*4.4),y+9),13)
    u.text(s,(f'{int(values[key])} W' if p.kind=='grid' else f'{int(values[key])}%'),911,y-4,'medium',col)
   u.button(s,'APPLY & TEST GRID' if p.kind=='grid' else 'ACTIVATE GROW LIGHTS',(650,542,380,52),'confirm_grid' if p.kind=='grid' else 'confirm_uv',GREEN)
  u.text(s,'ESC: EXIT REPAIR PANEL',163,585,'tiny',MUTED)

 def draw_inventory(self):
  s=self.screen;u=self.hud
  u.dim(s,194);u.panel(s,(194,127,889,500),(11,31,46),CYAN,253)
  u.text(s,'TOOL INVENTORY',640,154,'big',WHITE,center=True)
  u.text(s,'CLICK A TOOL TO EQUIP. USE IT NEAR THE CORRECT DEVICE.',640,215,'small',MUTED,center=True)
  for i,key in enumerate(self.state.acquired):
   x=238+(i%3)*280;y=265+(i//3)*99
   u.panel(s,(x,y,252,81),(17,40,54),GREEN if key==self.state.equipped else EDGE,250)
   self.gfx.tool_icon(s,key,(x+8,y+13,54,54))
   u.text(s,TOOLS[key][0][:18],x+70,y+15,'tiny',WHITE)
   u.text(s,f'CHARGE: {round(self.state.tool_charge.get(key,100))}%',x+70,y+45,'tiny',GREEN)
   u.actions.append((pygame.Rect(x,y,252,81),'equip:'+key))
  u.button(s,'CLOSE',(810,564,226,49),'close')

 def draw_pause(self):
  s=self.screen;u=self.hud
  u.dim(s,196)
  u.panel(s,(304,56,674,613),(9,29,44),CYAN,252,12)
  u.text(s,'MISSION PAUSED',640,87,'big',WHITE,center=True)
  music_state=('ON' if self.audio.music_enabled else 'OFF') if self.audio else 'OFF'
  music_volume=round(self.audio.music_volume*100) if self.audio else 0
  music_ok=bool(self.audio and self.audio.music_available)
  lines=[
    ('RESUME','resume'),
    ('SAVE MISSION','save'),
    ('ANIMATED BACKGROUNDS: '+('ON' if self.video_enabled else 'OFF'),'video_toggle'),
    ('SOUND EFFECTS: '+('ON' if self.audio.enabled else 'OFF'),'sound_toggle'),
    (f'SURFACE TENSION MUSIC: {music_state}' if music_ok else 'MUSIC UNAVAILABLE','music_toggle'),
    (f'MUSIC VOLUME -  ({music_volume}%)','music_down'),
    (f'MUSIC VOLUME +  ({music_volume}%)','music_up'),
    ('RETURN TO BASE','hub'),
    ('MAIN MENU','menu'),
  ]
  for i,(label,action) in enumerate(lines):
   u.button(s,label,(375,148+i*54,533,45),action,GREEN if i==0 else CYAN)
  u.text(s,'M: MUSIC  |  B: SOUND EFFECTS  |  ESC: RESUME',641,643,'tiny',MUTED,center=True)

 def draw_event(self):
  s=self.screen;u=self.hud
  e=self.state.pending
  if not e:return
  u.dim(s,204);u.panel(s,(219,159,838,479),(39,25,34),RED,251,12)
  u.text(s,e['title'],639,193,'big',RED,center=True)
  u.wrap(s,e['text'],260,267,742,'normal',WHITE,4)
  for i,(title,changes) in enumerate(e['choices']):
   u.button(s,title.upper(),(280,347+i*114,720,56),'event:'+str(i),CYAN if i==0 else YELLOW)
   u.text(s,'GAME EFFECTS: '+', '.join(f'{k} {v:+g}' for k,v in changes.items()),297,408+i*114,'small',MUTED)

 def draw_objectives(self):
  s=self.screen;u=self.hud
  u.dim(s,194);u.panel(s,(239,152,802,459),(8,28,44),CYAN,252)
  u.text(s,'MISSION OBJECTIVES',640,181,'big',WHITE,center=True)
  for i,room in enumerate(ROOMS):
   name=NAMES[room];ok=self.state.operational[room]
   u.text(s,('✓ ' if ok else '○ ')+name,306,267+i*50,'medium',GREEN if ok else YELLOW)
  u.text(s,'SURVIVE THROUGH SOL 30 WITH ALL MODULES OPERATIONAL',304,501,'small',MUTED)
  u.button(s,'CLOSE',(790,552,194,47),'close')

 def draw(self):
  u=self.hud;s=self.screen
  u.reset(self.mouse())
  if self.scene=='menu':self.draw_menu()
  elif self.scene=='intro':self.draw_intro()
  elif self.scene=='loading':self.draw_loading()
  elif self.scene=='hub':self.draw_hub()
  elif self.scene in ROOMS:self.draw_room()
  elif self.scene=='telemetry':self.draw_telemetry()
  elif self.scene=='result':self.draw_result()
  if self.popup:
   u.actions.clear()
   if self.popup=='puzzle':self.draw_puzzle()
   elif self.popup=='inventory':self.draw_inventory()
   elif self.popup=='pause':self.draw_pause()
   elif self.popup=='event':self.draw_event()
   elif self.popup=='objectives':self.draw_objectives()
  if self.notice_timer>0:
   u.panel(s,(220,102,840,43),(23,46,56),YELLOW,250)
   u.text(s,self.notice,640,111,'small',WHITE,center=True)
  sw,sh=self.window.get_size()
  scale=min(sw/WIDTH,sh/HEIGHT)
  tw=max(1,int(WIDTH*scale));th=max(1,int(HEIGHT*scale))
  ox=(sw-tw)//2;oy=(sh-th)//2
  self.window.fill((1,5,10))
  target=pygame.transform.scale(s,(tw,th)) if (tw,th)!=(WIDTH,HEIGHT) else s
  self.window.blit(target,(ox,oy))
  pygame.display.flip()

 def run(self):
  try:
   while self.active:
    dt=min(.05,self.clock.tick(FPS)/1000.0)
    for event in pygame.event.get():self.event(event)
    self.update(dt)
    self.draw()
  finally:
   self.video.close()
   self.audio.stop()
   pygame.quit()


# Optional compatibility name with V1; run_v3.py starts the independent V3 package.
Game = LunarGame
