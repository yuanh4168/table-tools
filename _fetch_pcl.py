"""Fetch PCL-CE UI source code for style reference."""
import ssl
import urllib.request
import json

ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0'}
BASE = 'https://raw.githubusercontent.com/PCL-Community/PCL-CE/main/Plain%20Craft%20Launcher%202'
API_BASE = 'https://api.github.com/repos/PCL-Community/PCL-CE/contents/Plain%20Craft%20Launcher%202'


def get(path):
    req = urllib.request.Request(f'{API_BASE}/{path}', headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))


def get_file(path):
    req = urllib.request.Request(f'{BASE}/{path}', headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8')


def fetch_xaml_files():
    """Fetch all XAML files from the Controls directory."""
    print("=== Controls ===")
    items = get('Controls')
    for item in sorted(items, key=lambda x: x['name']):
        print(f"{'DIR' if item['type']=='dir' else 'FILE'}: {item['name']}")
        if item['type'] == 'file' and item['name'].endswith(('.xaml', '.cs')):
            content = get_file(f'Controls/{item["name"]}')
            print(f"  Content ({len(content)} bytes):")
            print(content[:2000])
            print("---")

    # Also check Resources
    print("\n=== Resources ===")
    items = get('Resources')
    for item in sorted(items, key=lambda x: x['name']):
        print(f"{'DIR' if item['type']=='dir' else 'FILE'}: {item['name']}")
        if item['type'] == 'file' and item['name'].endswith(('.xaml', '.cs', '.json')):
            content = get_file(f'Resources/{item["name"]}')
            print(f"  Content ({len(content)} bytes):")
            print(content[:3000])
            print("---")


if __name__ == '__main__':
    fetch_xaml_files()
