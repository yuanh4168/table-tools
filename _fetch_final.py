"""Fetch PCL-CE XAML files via API (branch=dev)."""
import ssl, urllib.request, json, urllib.parse, base64

ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0'}
REPO = 'PCL-Community/PCL-CE'
BRANCH = 'dev'
DIR = 'Plain Craft Launcher 2'

def gh_api(rel_path):
    """Get file content via GitHub API (returns decoded text)."""
    url = f'https://api.github.com/repos/{REPO}/contents/{urllib.parse.quote(rel_path)}?ref={BRANCH}'
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode('utf-8'))
    if data.get('encoding') == 'base64':
        return base64.b64decode(data['content']).decode('utf-8')
    return str(data)


files = [
    f'{DIR}/Application.xaml',
    f'{DIR}/FormMain.xaml',
    f'{DIR}/Controls/MinecraftServerQuery.xaml',
    f'{DIR}/Controls/MinecraftServer.xaml',
    f'{DIR}/Controls/MyButton.xaml',
    f'{DIR}/Controls/MyCheckBox.xaml',
    f'{DIR}/Controls/MyCard.cs',
    f'{DIR}/Controls/ControlVisualHelpers.cs',
    f'{DIR}/Controls/MyIconButton.xaml',
    f'{DIR}/Controls/MyIconTextButton.xaml',
    f'{DIR}/Controls/MyListItem.xaml',
    f'{DIR}/Controls/MyLoading.xaml',
    f'{DIR}/Controls/MyHint.xaml',
    f'{DIR}/Controls/MyComboBox.cs',
]

for p in files:
    try:
        content = gh_api(p)
        print(f'===== {p} =====')
        print(content[:6000])
        if len(content) > 6000:
            print(f'\n... ({len(content) - 6000} more bytes)')
        print()
    except Exception as e:
        print(f'FAILED {p}: {e}')
        print()
