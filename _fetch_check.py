"""Debug PCL-CE file access."""
import ssl, urllib.request, json, urllib.parse

ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0'}
REPO = 'PCL-Community/PCL-CE'
DIR = 'Plain Craft Launcher 2'

def gh_api(rel_path):
    url = f'https://api.github.com/repos/{REPO}/contents/{urllib.parse.quote(rel_path)}'
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'error': str(e), 'url': url}

# Get download URL for Application.xaml
result = gh_api(f'{DIR}/Application.xaml')
if 'error' in result:
    print(f"API Error: {result['error']}")
    print(f"URL: {result['url']}")
else:
    print(f"Name: {result.get('name')}")
    print(f"Download URL: {result.get('download_url')}")
    print(f"Size: {result.get('size')}")
    if result.get('download_url'):
        dl_url = result['download_url'].replace('https://api.github.com/repos/', '')
        print(f"Parsed path: {dl_url}")
        # Try to fetch it
        req2 = urllib.request.Request(result['download_url'], headers=HEADERS)
        with urllib.request.urlopen(req2, timeout=15) as r:
            content = r.read().decode('utf-8')
            print(f"\nContent ({len(content)} bytes):")
            print(content[:4000])

# Also try FormMain.xaml
print("\n\n--- FormMain.xaml ---")
result2 = gh_api(f'{DIR}/FormMain.xaml')
if 'error' in result2:
    print(f"API Error: {result2['error']}")
else:
    print(f"Download URL: {result2.get('download_url')}")

# List Pages directory for server monitoring
print("\n\n--- PageTools ---")
result3 = gh_api(f'{DIR}/Pages/PageTools')
if 'error' in result3:
    print(f"API Error: {result3['error']}")
else:
    for item in result3:
        print(f"{'DIR' if item['type']=='dir' else 'FILE'}: {item['name']}")

# List PageSetup
print("\n\n--- PageSetup ---")
result4 = gh_api(f'{DIR}/Pages/PageSetup')
if 'error' in result4:
    print(f"API Error: {result4['error']}")
else:
    for item in result4:
        print(f"{'DIR' if item['type']=='dir' else 'FILE'}: {item['name']}")
