"""PC Flip Hunter: cautious public-page polling; no login, bypasses or hidden APIs."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import json, re, time, threading

BASE='https://mymarket.ge'
PAGES={
 'pc':BASE+'/en/products/electronics-appliances/computers/desktop-computer/',
 'part':BASE+'/en/products/electronics-appliances/computers/computer-parts/'
}
CACHE={'items':[], 'updated':None, 'errors':[], 'status':'waiting'}
LOCK=threading.Lock()
INTERVAL=900
PRICE=re.compile(r'(?<!\d)(\d{1,3}(?:[\s,]\d{3})*|\d{1,6})(?:\.\d{1,2})?\s*₾')
ID=re.compile(r'(\d{7,10})(?:/|\?|$)')

def scrape(category,url):
 req=Request(url,headers={'User-Agent':'PCFlipHunter/1.0 (+personal price research; contact site for access)', 'Accept-Language':'en'})
 with urlopen(req,timeout=20) as response:
  if response.status!=200: raise RuntimeError('HTTP '+str(response.status))
  html=response.read(3_000_000).decode('utf-8','replace')
 soup=BeautifulSoup(html,'html.parser')
 found={}
 for a in soup.select('a[href]'):
  href=urljoin(BASE,a.get('href',''))
  if not href.startswith(BASE+'/') or not ('/product/' in href or '/pr/' in href):continue
  match=ID.search(href.split('#')[0]);
  if not match:continue
  itemid=match.group(1)
  node=a
  # Walk a few ancestors to find a listing price, without scanning entire page.
  for _ in range(4):
   if node is None:break
   snippet=node.get_text(' ',strip=True)[:500]
   prices=PRICE.findall(snippet)
   if prices:break
   node=node.parent
  if not prices:continue
  try:price=float(prices[0].replace(' ','').replace(',',''))
  except ValueError:continue
  if not 0<price<=800:continue
  title=a.get('title') or a.get_text(' ',strip=True)
  title=re.sub(r'\s+',' ',title).strip()
  if not title or len(title)<5 or PRICE.search(title):
   title=re.sub(r'\s+',' ',snippet).strip()
   title=PRICE.sub('',title).strip()[:130]
  if len(title)<5:continue
  found[itemid]={'id':'mm'+itemid,'title':title[:160], 'category':category,'price':price,'market':price,'cost':30,'risk':'medium','url':href,'unverifiedMarket':True,'source':'live'}
 return list(found.values())

def update():
 while True:
  combined=[];errors=[]
  for category,url in PAGES.items():
   try:combined.extend(scrape(category,url))
   except Exception as exc:errors.append(category+': '+str(exc)[:180])
   time.sleep(3)
  with LOCK:
   CACHE.update(items=combined,updated=int(time.time()),errors=errors,status='ok' if combined else 'no_data')
  time.sleep(INTERVAL)

class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path.split('?')[0]=='/api/listings':
   with LOCK: data=json.dumps(CACHE,ensure_ascii=False).encode('utf-8')
   self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  else:super().do_GET()

if __name__=='__main__':
 import os
 os.chdir(Path(__file__).resolve().parent)
 threading.Thread(target=update,daemon=True).start()
 print('Open http://localhost:8765 — live monitoring every 15 minutes')
 ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','8765'))),Handler).serve_forever()
