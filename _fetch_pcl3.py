"""Fetch PCL-CE UI source code with proper URL encoding."""
import ssl
import urllib.request
import urllib.parse
import json

ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0'}

REPO = 'PCL-Community/PCL-CE'
BRANCH = 'main'
DIR = 'Plain Craft Launcher 2'


def gh_api(path):
    url = f'https://api.github.com/repos/{REPO}/contents/{urllib.parse.quote(path)}'
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))


def gh_raw(path):
    url = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}/{urllib.parse.quote(path)}'
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8')


# List the top-level directory
print("=== Root files ===")
items = gh_api(DIR)
for item in sorted(items, key=lambda x: x['name']):
    print(f"{'DIR' if item['type']=='dir' else 'FILE'}: {item['name']}")

# List Resources directory
print("\n=== Resources ===")
items = gh_api(f'{DIR}/Resources')
for item in sorted(items, key=lambda x: x['name']):
    print(f"{'DIR' if item['type']=='dir' else 'FILE'}: {item['name']}")
    if item['type'] == 'file' and item['name'].endswith('.xaml'):
        try:
            content = gh_raw(f'{DIR}/Resources/{item["name"]}')
            print(f"  Content:")
            print(content[:4000])
            print("---")
        except Exception as e:
            print(f"  Error: {e}")

# List Controls
print("\n=== Controls ===")
items = gh_api(f'{DIR}/Controls')
for item in sorted(items, key=lambda x: x['name']):
    print(f"{'DIR' if item['type']=='dir' else 'FILE'}: {item['name']}")
