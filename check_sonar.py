import json, urllib.request

url = 'http://localhost:9000/api/issues/search?componentKeys=karpathy_wiki_api&statuses=OPEN,REOPENED,CONFIRMED&ps=1'
req = urllib.request.Request(url)
req.add_header('Authorization', 'Bearer sqa_fe4b774b40e19eca12e0f46a2f2f771f2d1a23bd')
d = json.load(urllib.request.urlopen(req))
print(f'Total OPEN issues: {d["total"]}')

url2 = 'http://localhost:9000/api/qualitygates/project_status?projectKey=karpathy_wiki_api'
req2 = urllib.request.Request(url2)
req2.add_header('Authorization', 'Bearer sqa_fe4b774b40e19eca12e0f46a2f2f771f2d1a23bd')
d2 = json.load(urllib.request.urlopen(req2))
print(f'Quality Gate: {d2["projectStatus"]["status"]}')