import os
import time
import onetimepass as otp

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

        # Caminho absoluto da pasta images da extensão
        images_path = os.path.join(os.path.dirname(__file__), 'images')

        for provider in providers:
            if '=' not in provider:
                continue
            name, secret = map(str.strip, provider.split('=', 1))

            if query and not name.lower().startswith(query):
                continue

            # Acrescenta o símbolo = no fim para garantir que ele tenha o comprimento correto para o base32
            missing_padding = len(secret) % 8
            if missing_padding:
                paddings_to_add = '=' * (8 - missing_padding)
                secret += paddings_to_add

            # Pega a primeira palavra do nome para buscar o ícone
            first_word = name.split()[0].lower()
            custom_icon_path = os.path.join(images_path, f'{first_word}.png')

            # Verifica se o arquivo existe, se não, usa o padrão
            if os.path.isfile(custom_icon_path):
                icon_path = custom_icon_path
            else:
                icon_path = 'images/icon.png'

            token = str(otp.get_totp(secret)).zfill(6)
            remaining = 30 - int(time.time()) % 30

            item = ExtensionResultItem(
                icon=icon_path,
                name=f'{name}',
                description=f'(expira em {remaining}s)',
                on_enter=CopyToClipboardAction(token)
            )
            matching_items.append(item)

        if len(matching_items) > max_items:
            items.extend(matching_items[:max_items - 1])
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='[...]',
                description='Mais serviços disponíveis',
                on_enter=None
            ))
        else:
            items.extend(matching_items)

        return RenderResultListAction(items)


if __name__ == '__main__':
    TfaExtension().run()
