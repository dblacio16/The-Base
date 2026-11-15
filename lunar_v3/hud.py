"""Readable English HUD, panel controls, buttons and ARIA dialogue."""
from .settings import *

class HUD:
 def __init__(self,pygame):
  self.pg=pygame
  self.fonts={'tiny':pygame.font.SysFont('consolas',13), 'small':pygame.font.SysFont('consolas',17),
              'normal':pygame.font.SysFont('consolas',21), 'medium':pygame.font.SysFont('consolas',25,bold=True),
              'big':pygame.font.SysFont('consolas',39,bold=True),'hero':pygame.font.SysFont('consolas',63,bold=True)}
  self.actions=[]
  self.mouse=(0,0)

 def reset(self,mouse):self.actions=[];self.mouse=mouse

 def text(self,s,msg,x,y,font='normal',color=WHITE,center=False,right=False):
  im=self.fonts[font].render(str(msg),True,color)
  if center:x-=im.get_width()/2
  if right:x-=im.get_width()
  s.blit(im,(round(x),round(y)))
  return im.get_width()

 def wrap(self,s,msg,x,y,width=700,font='normal',color=WHITE,limit=5):
  row='';lines=[];f=self.fonts[font]
  for word in str(msg).replace('\n',' \n ').split():
   if word=='\\n':lines.append(row);row='';continue
   candidate=(row+' '+word).strip()
   if f.size(candidate)[0]<width:row=candidate
   else:
    if row:lines.append(row)
    row=word
  if row:lines.append(row)
  for i,line in enumerate(lines[:limit]):self.text(s,line,x,y+i*(f.get_linesize()+5),font,color)

 def panel(self,s,rect,fill=PANEL,border=EDGE,alpha=240,radius=9):
  pg=self.pg;rect=pg.Rect(rect)
  if alpha>=255:pg.draw.rect(s,fill,rect,border_radius=radius)
  else:
   lay=pg.Surface(rect.size,pg.SRCALPHA)
   pg.draw.rect(lay,(*fill,alpha),(0,0,*rect.size),border_radius=radius)
   s.blit(lay,rect.topleft)
  if border:pg.draw.rect(s,border,rect,2,border_radius=radius)

 def button(self,s,title,rect,action,color=CYAN,enabled=True):
  r=self.pg.Rect(rect)
  hover=enabled and r.collidepoint(self.mouse)
  self.panel(s,r,(26,63,79) if hover else (17,35,51),color if hover else EDGE,250)
  self.text(s,title,r.centerx,r.centery-11,'normal',WHITE if enabled else MUTED,center=True)
  if enabled:self.actions.append((r,action))

 def dim(self,s,opacity=185):
  lay=self.pg.Surface((WIDTH,HEIGHT),self.pg.SRCALPHA)
  lay.fill((1,7,16,opacity))
  s.blit(lay,(0,0))

 def resources(self,s,state,scene_title):
  self.pg.draw.rect(s,(7,18,29),(0,0,WIDTH,104))
  self.pg.draw.line(s,EDGE,(0,103),(WIDTH,103),2)
  self.text(s,'LUNAR',25,23,'medium',WHITE)
  self.text(s,'OUTPOST',25,49,'medium',CYAN)
  self.text(s,'V3.0 / NASA',25,78,'tiny',MUTED)
  for i,name in enumerate(RESOURCES):
   x=205+i*225
   val=state.resources[name]
   col=COLORS[name] if val>25 else RED
   self.text(s,RES_NAMES[name],x,25,'tiny',MUTED)
   self.text(s,f'{round(val)}%',x+175,21,'small',col,right=True)
   self.pg.draw.rect(s,(44,58,73),(x,63,175,13),border_radius=6)
   if val>0:self.pg.draw.rect(s,col,(x,63,round(175*val/100),13),border_radius=6)
  self.text(s,'SOL',1132,21,'tiny',MUTED)
  self.text(s,f'{state.sol}/30',1131,43,'medium',WHITE)
  self.panel(s,(20,111,440,43),(8,20,33),None,210,3)
  self.text(s,scene_title.upper(),39,120,'normal',WHITE)

 def aria(self,s,graphics,msg,robot='normal',hint=''):
  self.panel(s,(0,576,WIDTH,144),(7,22,35),CYAN,250,0)
  # Show robot's panel at the lower left; avoid huge source textures.
  frame=graphics.aria.get(robot) or graphics.aria.get('normal')
  if frame:
   im=self.pg.transform.scale(frame,(176,106))
   s.blit(im,(14,588))
  self.text(s,'A.R.I.A.   //   MISSION ASSISTANT',204,588,'tiny',CYAN)
  self.wrap(s,msg,204,611,915,'small',WHITE,3)
  if hint:self.text(s,hint,204,690,'tiny',GREEN)

 def modal(self,s,title,subtitle=''):
  self.dim(s,195)
  self.panel(s,(194,130,892,477),(9,26,39),CYAN,252,14)
  self.text(s,title,640,155,'big',WHITE,center=True)
  if subtitle:self.wrap(s,subtitle,246,209,788,'small',MUTED,3)

 def meter(self,s,x,y,w,label,value,color=CYAN):
  self.text(s,f'{label}  {int(value)}%',x,y,'small',WHITE)
  self.pg.draw.rect(s,(42,64,77),(x,y+29,w,14),border_radius=6)
  if value>0:self.pg.draw.rect(s,color,(x,y+29,round(w*clamp(value)/100),14),border_radius=6)


def clamp(v):return max(0,min(100,v))
