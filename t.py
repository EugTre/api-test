import requests

r = requests.models.Response()
r.url = 'http://someurl.com'
r.headers.update({"header1": "value1", "header2": "value2"})
r.cookies.update({"cookie1": "value1"})
r.status_code = 200
r.encoding = 'utf-8'
r._content = b'{"foo":"bar"}'
r.elapsed = 1500330343

print(r)
print(r.text)
print(r.status_code)
print(r.headers)
print(r.cookies)
print(r.json())