import os
import time
import onetimepass as otp
import shutil
import sqlite3
from pathlib import Path

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.event import ItemEnterEvent
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction


class TfaExtension(Extension):

    def __init__(self):
        super(TfaExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, CustomActionListener())

        db_path = f"{get_preferences_path()}/data.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            name TEXT PRIMARY KEY,
            last_used INTEGER
        )
        """)

        self.conn.commit()

        print(f"🌠 init")

def mark_used(name):
    cursor.execute("""
        INSERT INTO services (name, last_used)
        VALUES (?, ?)
        ON CONFLICT(name)
        DO UPDATE SET last_used=excluded.last_used
    """, (name, int(time.time())))
    
    conn.commit()

def get_items():
    cursor.execute("""
        SELECT name
        FROM services
        ORDER BY last_used DESC
    """)
    
    return [row[0] for row in cursor.fetchall()]

def get_preferences_path():
    basename = os.path.basename(os.path.dirname(__file__))
    return Path.home() / f'~/.config/ulauncher/{basename}'

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        print(f"🌠 on_event")
        items = []
        query = event.get_argument()
        if query:
            query = query.strip().lower()

        providers_raw = extension.preferences.get('tfa_providers', '')
        providers = providers_raw.split(';')

        max_items = int(extension.preferences.get('tfa_max_providers') or 7)

        matching_items = []

        # Absolute path to the extension's images folder
        custom_images_path = f"{get_preferences_path()}/images"

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
                description=f'Expires in {remaining}s',
                on_enter=ExtensionCustomAction({
                    "action": "update_last_used",
                    "token": token,
                    "name": name,
                }, keep_app_open=False)
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

class CustomActionListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()

        if data.get("action") != "update_last_used":
            return

        token = data["token"]
        name = data["name"]

        mark_used(name)

        return CopyToClipboardAction(token)

if __name__ == '__main__':
    print(f"🌠 run")
    TfaExtension().run()
