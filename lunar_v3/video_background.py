"""Non-blocking MP4 background decoder; never alters hitboxes or gameplay.

One worker decodes one video at native rate; the pygame main thread owns surfaces.
If decoder unavailable/damaged, the background PNG is used instead.
"""
from __future__ import annotations
from threading import Thread,Event,Lock
import time

class VideoBackground:
 def __init__(self):
  self.thread=None
  self.stop_signal=Event()
  self.pause_signal=Event()
  self.lock=Lock()
  self.latest=None
  self.sequence=0
  self.read_seq=-1
  self.active_path=None
  self.error=''
  self.loaded=False

 def open(self,path):
  self.close()
  self.stop_signal=Event()
  self.pause_signal=Event()
  with self.lock:
   self.latest=None
   self.sequence=0
   self.read_seq=-1
  self.active_path=str(path)
  self.loaded=False
  self.error=''
  self.thread=Thread(target=self._decode,args=(str(path),self.stop_signal,self.pause_signal),daemon=True)
  self.thread.start()

 def _decode(self,path,stop_signal,pause_signal):
  try:
   import cv2
   capture=cv2.VideoCapture(path)
   if not capture.isOpened():
    self.error='Unable to open video.'
    return
   try:
    rate=capture.get(cv2.CAP_PROP_FPS)
    fps=float(rate) if rate and 5<=rate<=120 else 24.0
    dt=1.0/fps
    deadline=time.monotonic()
    self.loaded=True
    while not stop_signal.is_set():
     if pause_signal.is_set():
      stop_signal.wait(.025)
      deadline=time.monotonic()
      continue
     ok,frame=capture.read()
     if not ok:
      capture.set(cv2.CAP_PROP_POS_FRAMES,0)
      ok,frame=capture.read()
      if not ok:
       self.error='Video ended unexpectedly.'
       break
     frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
     h,w=frame.shape[:2]
     with self.lock:
      self.latest=(frame.tobytes(),(w,h))
      self.sequence+=1
     deadline+=dt
     wait=max(0,min(.25,deadline-time.monotonic()))
     if wait:stop_signal.wait(wait)
     if deadline<time.monotonic()-.5:deadline=time.monotonic()
   finally:capture.release()
  except Exception as err:
   self.error=f'Video decoding unavailable ({type(err).__name__})'

 def frame(self,pygame):
  # Main thread returns a new surface, only when video frame changed.
  with self.lock:
   if self.latest is None or self.sequence==self.read_seq:return None
   raw,size=self.latest
   self.read_seq=self.sequence
  try:
   return pygame.image.frombuffer(raw,size,'RGB').convert().copy()
  except (pygame.error,ValueError):return None

 def pause(self,value):
  if value:self.pause_signal.set()
  else:self.pause_signal.clear()

 def close(self):
  self.stop_signal.set()
  if self.thread and self.thread.is_alive():self.thread.join(timeout=1.5)
  self.thread=None
  self.latest=None
  self.active_path=None
  self.loaded=False
