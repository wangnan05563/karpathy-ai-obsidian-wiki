import json, urllib.request

url = 'http://localhost:9000/api/rules/show?key=typescript:S6544'
req = urllib.request.Request(url)
req.add_header('Authorization', 'Bearer sqa_fe4b774b40e19eca12e0f46a2f2f771f2d1a23bd')
d = json.load(urllib.request.urlopen(req))
rule = d.get('rule', {})
# Try to get the description HTML
desc = rule.get('descriptionSections', [])
for section in desc:
    print(f'Section key: {section.get("key")}')
    content = section.get('content', '')[:1000]
    print(f'Content: {content}')
    print('---')