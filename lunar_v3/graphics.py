"""Pixel-art astronaut, ARIA robot portraits, background and pixel tool icons."""
from pathlib import Path
from .settings import *

class Graphics:
 def __init__(self,pygame):
  self.pg=pygame
  self.backgrounds={}
  self.astronaut={}
  self.aria={}
  for room in ('menu','hub')+ROOMS:
   p=ASSETS/'backgrounds'/f'{room}.png'
   if p.exists():
    try:self.backgrounds[room]=pygame.transform.scale(pygame.image.load(str(p)).convert(),(WIDTH,HEIGHT))
    except (pygame.error,OSError):pass
  for path in (ASSETS/'astronaut').glob('*.png'):
   try:
    surface=pygame.image.load(str(path)).convert_alpha()
    # The improved V3 sprites are 96x96 and have different transparent
    # margins. Anchor the visible boots at the same y coordinate for every
    # pose without smoothing or stretching the pixel-art original.
    frame=pygame.Surface((112,104),pygame.SRCALPHA)
    bounds=surface.get_bounding_rect(min_alpha=16)
    offset_x=(112-surface.get_width())//2
    offset_y=97-bounds.bottom
    frame.blit(surface,(offset_x,offset_y))
    self.astronaut[path.stem.replace('astronauta_','')]=frame
   except (pygame.error,OSError):pass
  for path in (ASSETS/'aria').glob('*.png'):
   try:
    image=pygame.image.load(str(path)).convert()
    self.aria[path.stem.replace('robot_','').replace('_pixelado','')]=pygame.transform.scale(image,(250,150))
   except (pygame.error,OSError):pass

 def background(self,canvas,scene):
  image=self.backgrounds.get(scene)
  if image:canvas.blit(image,(0,0))
  else:canvas.fill(DARK)

 def astronaut_frame(self,player,clock):
  side='derecha' if player.facing>0 else 'izquierda'
  if not player.grounded:return self.astronaut.get('saltar_'+side)
  if player.speeding:return self.astronaut.get('correr_'+side+'_p'+str(1+int(clock*7)%2))
  return self.astronaut.get('stand_'+side)

 def astronaut_draw(self,canvas,player,clock):
  frame=self.astronaut_frame(player,clock)
  if frame:
   canvas.blit(frame,(round(player.x-56),round(player.feet-104)))
  else:
   p=self.pg
   p.draw.circle(canvas,WHITE,(int(player.x),int(player.feet-64)),21)
   p.draw.rect(canvas,CYAN,(int(player.x-18),int(player.feet-49),36,40),border_radius=8)

 def aria_draw(self,canvas,x,y,state='normal'):
  frame=self.aria.get(state) or self.aria.get('normal')
  if frame:canvas.blit(frame,(x,y))

 def tool_icon(self,canvas,key,rect,color=CYAN):
  p=self.pg
  x,y,w,h=rect
  p.draw.rect(canvas,(14,29,43),(x,y,w,h),border_radius=6)
  p.draw.rect(canvas,color,(x,y,w,h),1,border_radius=6)
  mx,my=x+w//2,y+h//2
  if key=='sealant':
   p.draw.rect(canvas,color,(mx-5,my-13,10,24),border_radius=3)
   p.draw.polygon(canvas,YELLOW,[(mx-7,my-14),(mx,my-22),(mx+7,my-14)])
  elif key=='heater':
   p.draw.rect(canvas,color,(mx-12,my-11,22,14),border_radius=3)
   p.draw.line(canvas,YELLOW,(mx+11,my-8),(mx+20,my-8),4)
  elif key=='wrench':
   p.draw.line(canvas,color,(mx-11,my+13),(mx+7,my-12),6)
   p.draw.circle(canvas,color,(mx+8,my-14),6,3)
  elif key=='multimeter':
   p.draw.rect(canvas,color,(mx-12,my-17,24,33),border_radius=4)
   p.draw.rect(canvas,DARK,(mx-9,my-12,18,11))
   p.draw.line(canvas,RED,(mx-3,my+3),(mx+12,my+3),2)
  elif key=='scanner':
   p.draw.arc(canvas,color,(mx-19,my-19,38,38),.1,2.9,3)
   p.draw.circle(canvas,YELLOW,(mx,my),5)
  elif key=='calibrator':
   p.draw.circle(canvas,color,(mx,my),15,3)
   p.draw.line(canvas,YELLOW,(mx,my),(mx+13,my-9),3)
  elif key=='bridge':
   p.draw.line(canvas,color,(mx-17,my),(mx+17,my),8)
   for dx in (-17,17):p.draw.circle(canvas,YELLOW,(mx+dx,my),6)
  else:
   p.draw.rect(canvas,color,(mx-13,my-9,26,18),border_radius=3)
   p.draw.line(canvas,WHITE,(mx,my-6),(mx,my+6),3)
   p.draw.line(canvas,WHITE,(mx-6,my),(mx+6,my),3)
