import os
import time
import onetimepass as otp
import shutil

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction


class TfaExtension(Extension):

    def __init__(self):
        super(TfaExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        query = event.get_argument()
        if query:
            query = query.strip().lower()

        providers_raw = extension.preferences.get('tfa_providers', '')
        providers = providers_raw.split(';')

        max_items = int(extension.preferences.get('tfa_max_providers') or 7)

        matching_items = []

        # Absolute path to the extension's images folder
        basename = os.path.basename(os.path.dirname(__file__))
        custom_images_path = os.path.expanduser(f'~/.config/ulauncher/{basename}/images')

        if not os.path.exists(custom_images_path):
            default_images_path = os.path.join(os.path.dirname(__file__), 'images')
            shutil.copytree(default_images_path, custom_images_path)

        for provider in providers:
            if '=' not in provider:
                continue
            name, secret = map(str.strip, provider.split('=', 1))

            if query and query not in name.lower():
                continue

            # Add the symbol = at the end to ensure it has the correct length for base32
            missing_padding = len(secret) % 8
            if missing_padding:
                paddings_to_add = '=' * (8 - missing_padding)
                secret += paddings_to_add

            # Get the first word of the name to look for the icon
            first_word = name.split()[0].lower()
            custom_icon_path = os.path.join(custom_images_path, f'{first_word}.png')

            # Check if the custom icon exists, if not, use the default icon
            if os.path.isfile(custom_icon_path):
                icon_path = custom_icon_path
            else:
                icon_path = 'images/icon.png'

            token = str(otp.get_totp(secret)).zfill(6)
            remaining = 30 - int(time.time()) % 30

            item = ExtensionResultItem(
                icon=icon_path,
                name=f'{name}',
                # description=f'(expira em {remaining}s)',
                description=f'Expires in {remaining}s',
                on_enter=CopyToClipboardAction(token)
            )
            matching_items.append(item)

        if len(matching_items) > max_items:
            items.extend(matching_items[:max_items - 1])
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='[...]',
                description='More services available',
                on_enter=None
            ))
        else:
            items.extend(matching_items)

        return RenderResultListAction(items)


if __name__ == '__main__':
    TfaExtension().run()
