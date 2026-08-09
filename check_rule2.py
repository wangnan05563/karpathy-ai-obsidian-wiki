import json, urllib.request

url = 'http://localhost:9000/api/issues/search?componentKeys=karpathy_wiki_api&rules=typescript:S6544&ps=5'
req = urllib.request.Request(url)
req.add_header('Authorization', 'Bearer sqa_fe4b774b40e19eca12e0f46a2f2f771f2d1a23bd')
d = json.load(urllib.request.urlopen(req))
for issue in d.get('issues', []):
    print(f'File: {issue.get("component")}, Line: {issue.get("line")}')
    print(f'Message: {issue.get("message")}')
    print(f'---')