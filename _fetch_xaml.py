"""Fetch PCL-CE XAML files for UI style reference."""
import ssl, urllib.request, json

ssl._create_default_https_context = ssl._create_unverified_context
HEADERS = {'User-Agent': 'Mozilla/5.0'}
REPO = 'PCL-Community/PCL-CE'
BRANCH = 'main'
DIR = 'Plain Craft Launcher 2'

def gh_raw(rel_path):
    import urllib.parse
    url = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}/{urllib.parse.quote(rel_path)}'
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8')

files = [
    f'{DIR}/Application.xaml',
    f'{DIR}/FormMain.xaml',
    f'{DIR}/Controls/MinecraftServer.xaml',
    f'{DIR}/Controls/MinecraftServerQuery.xaml',
    f'{DIR}/Controls/MyButton.xaml',
    f'{DIR}/Controls/MyCheckBox.xaml',
    f'{DIR}/Controls/MyExtraButton.xaml',
    f'{DIR}/Controls/MyIconButton.xaml',
    f'{DIR}/Controls/MyIconTextButton.xaml',
    f'{DIR}/Controls/MyListItem.xaml',
    f'{DIR}/Controls/MyLoading.xaml',
    f'{DIR}/Controls/MySlider.xaml',
    f'{DIR}/Controls/MyRadioBox.xaml',
    f'{DIR}/Controls/MySearchBox.xaml',
    f'{DIR}/Controls/MyCard.cs',
    f'{DIR}/Controls/MyComboBox.cs',
    f'{DIR}/Controls/MyTextBox.cs',
    f'{DIR}/Controls/FontSelector.xaml',
    f'{DIR}/Controls/MyHint.xaml',
    f'{DIR}/Controls/ControlVisualHelpers.cs',
]

for p in files:
    try:
        content = gh_raw(p)
        print(f'===== {p} =====')
        print(content[:5000])
        print('\n... (truncated)' if len(content) > 5000 else '')
        print()
    except Exception as e:
        print(f'FAILED {p}: {e}')
        print()
