import json, urllib.request

url = 'http://localhost:9000/api/issues/search?componentKeys=karpathy_wiki_api&rules=typescript:S6544&ps=100'
req = urllib.request.Request(url)
req.add_header('Authorization', 'Bearer sqa_fe4b774b40e19eca12e0f46a2f2f771f2d1a23bd')
d = json.load(urllib.request.urlopen(req))
print(f'Total S6544 issues: {d["total"]}')
for i in d.get('issues', []):
    comp = i['component']
    line = i.get('line', 'N/A')
    text_range = i.get('textRange', {})
    start_line = text_range.get('startLine', '?')
    print(f'  {comp}:{line} (startLine={start_line}) - {i["message"]}')