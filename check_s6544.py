import json, urllib.request

url = 'http://localhost:9000/api/issues/search?componentKeys=karpathy_wiki_api&rules=typescript:S6544&statuses=OPEN,REOPENED,CONFIRMED&ps=200'
req = urllib.request.Request(url)
req.add_header('Authorization', 'Bearer sqa_fe4b774b40e19eca12e0f46a2f2f771f2d1a23bd')
d = json.load(urllib.request.urlopen(req))
print(f'Total S6544 issues: {d["total"]}')
for i in d.get('issues', []):
    line = i.get('line', '?')
    print(f'  {i["component"]}:{line} - {i["message"]}')