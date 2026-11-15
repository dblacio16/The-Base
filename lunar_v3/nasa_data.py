"""NASA DONKI real-observation client. No network calls in the Pygame main thread."""
from __future__ import annotations
import json,os,threading,queue
from datetime import datetime,timedelta,timezone
from pathlib import Path
import requests
from .settings import NASA_CACHE
KINDS=('FLR','GST','SEP','CME')
BASE='https://api.nasa.gov/DONKI'


def empty_snapshot(message='NASA unavailable; simulated offline conditions.'):
 return {'source':'NASA DONKI','status':'offline','fetched_at':'','events':{k:[] for k in KINDS},'message':message}


def read_cache():
 try:
  s=json.loads(NASA_CACHE.read_text(encoding='utf-8'))
  if not all(isinstance(s['events'][k],list) for k in KINDS):return None
  s['status']='cached'
  return s
 except (OSError,ValueError,TypeError,KeyError):return None


def fetch(force=False,get=requests.get):
 cache=read_cache()
 if cache and not force:
  try:
   old=datetime.fromisoformat(cache['fetched_at'])
   if (datetime.now(timezone.utc)-old).total_seconds()<3*3600:return cache
  except (KeyError,ValueError,TypeError):pass
 today=datetime.now(timezone.utc).date()
 params={'startDate':str(today-timedelta(days=7)),'endDate':str(today),'api_key':os.getenv('NASA_API_KEY','DEMO_KEY')}
 try:
  events={}
  for kind in KINDS:
   response=get(f'{BASE}/{kind}',params=params,timeout=5)
   response.raise_for_status()
   content=response.json()
   if not isinstance(content,list):raise ValueError('NASA response was not a list')
   events[kind]=content
  snap={'source':'NASA DONKI','status':'online','fetched_at':datetime.now(timezone.utc).isoformat(),
        'startDate':params['startDate'],'endDate':params['endDate'],'events':events,'message':''}
  NASA_CACHE.parent.mkdir(parents=True,exist_ok=True)
  tmp=NASA_CACHE.with_suffix('.tmp')
  tmp.write_text(json.dumps(snap),encoding='utf-8')
  tmp.replace(NASA_CACHE)
  return snap
 except (requests.RequestException,ValueError,OSError) as err:
  if cache:
   cache['status']='cached';cache['message']=f'Live request unavailable ({type(err).__name__}).'
   return cache
  return empty_snapshot(f'Live request unavailable ({type(err).__name__}).')


def risk_score(snapshot):
 """Transparent game-only space weather index, NOT a NASA measurement or lunar dose."""
 events=snapshot.get('events',{})
 if not isinstance(events,dict):return 12
 flr=events.get('FLR',[]); sep=events.get('SEP',[]);gst=events.get('GST',[]);cme=events.get('CME',[])
 strength=0
 for f in flr:
  if not isinstance(f,dict):continue
  kind=str(f.get('classType','C1'))[:1].upper()
  strength=max(strength,{'A':1,'B':2,'C':4,'M':13,'X':28}.get(kind,3))
 kp=0
 for event in gst:
  if not isinstance(event,dict):continue
  for item in event.get('allKpIndex') or []:
   if isinstance(item,dict):
    try:kp=max(kp,float(item.get('kpIndex') or 0))
    except (ValueError,TypeError):pass
 return int(max(0,min(100,strength+min(28,len(sep)*17)+max(0,kp-3)*3+min(16,len(cme)*2)+min(12,len(flr)))))


class NASAWorker:
 def __init__(self):
  self.queue=queue.Queue(maxsize=2)
  self.thread=None
 def start(self,force=False):
  if self.thread and self.thread.is_alive():return False
  self.thread=threading.Thread(target=lambda:self.queue.put(fetch(force)),daemon=True)
  self.thread.start()
  return True
 def poll(self):
  try:return self.queue.get_nowait()
  except queue.Empty:return None
