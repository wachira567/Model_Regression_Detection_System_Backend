import urllib.request
import urllib.error
url = 'https://model-regression-detection-system-backend-git-1034917257664.europe-west3.run.app/api/v1/auth/google'
req = urllib.request.Request(url, method='POST', headers={'Content-Type': 'application/json'}, data=b'{"token": "dummy"}')
try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print(e.code)
    print(e.read().decode())
