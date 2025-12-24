import os
import sys
import urllib.request

url = 'https://bootstrap.pypa.io/get-pip.py'
local_path = os.path.join(os.path.dirname(__file__), 'get-pip-real.py')
print('Downloading get-pip.py...')
urllib.request.urlretrieve(url, local_path)
print('Running get-pip-real.py...')
os.execv(sys.executable, [sys.executable, local_path])
