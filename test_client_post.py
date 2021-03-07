import requests
url = 'http://127.0.0.1:9000/'
files = {'media': open('test.jpg', 'rb')}
r = requests.post(url, files=files)
print(r.__dict__)
#requests.get(url)