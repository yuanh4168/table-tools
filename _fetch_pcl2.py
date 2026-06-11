"""Fetch PCL-CE UI source code - just XAML and key files."""
import ssl
import urllib.request
import json

ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def gh_list(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))


def gh_file(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8')


REPO = 'PCL-Community/PCL-CE'
BRANCH = 'main'
PREFIX = 'Plain Craft Launcher 2'

# Files we want to check
paths = [
    f'{PREFIX}/Application.xaml',
    f'{PREFIX}/FormMain.xaml',
    f'{PREFIX}/Resources/Themes/Colors.xaml',
    f'{PREFIX}/Resources/Themes/Styles.xaml',
    f'{PREFIX}/Resources/Themes.xaml',
]

for p in paths:
    url = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}/{p}'
    try:
        content = gh_file(url)
        print(f'===== {p} =====')
        print(content[:4000])
        print()
    except Exception as e:
        print(f'FAILED {p}: {e}')

# Also try to search for theme/color files by listing Resources
print('\n=== Resources directory ===')
url = f'https://api.github.com/repos/{REPO}/contents/{PREFIX}/Resources'
try:
    items = gh_list(url)
    for item in sorted(items, key=lambda x: x['name']):
        print(f"{'DIR' if item['type']=='dir' else 'FILE'}: {item['name']}")
except Exception as e:
    print(f'FAILED: {e}')
