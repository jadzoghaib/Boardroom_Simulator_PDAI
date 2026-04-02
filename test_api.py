import urllib.request as urllib2
import json

try:
    req = urllib2.Request('http://127.0.0.1:8001/api/boardroom_turn', data=json.dumps({'thread_id':'test1','budget':0,'burn_rate':0,'revenue':0,'founder_experience':0,'sector':'string','pitch':'string','action':'start'}).encode(), headers={'Content-Type':'application/json'})
    response = urllib2.urlopen(req)
    print(response.read().decode())
except urllib2.HTTPError as e:
    print('HTTPError:', e.code)
    print('Body:', e.read().decode())
except Exception as e:
    print('Other error:', e)
