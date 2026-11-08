import os
import time
import base64
import binascii
import shutil
import onetimepass as otp
import sqlite3
import subprocess
import secrets

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import ItemEnterEvent
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

ENCRYPTED_PREFIX = 'enc:v1:'
PASSWORD_CACHE_SECONDS = 60


def message(text):
    return RenderResultListAction([ExtensionResultItem(
        icon='images/icon.png', name=text, on_enter=None
    )])


def error_message(error):
    if isinstance(error, InvalidToken):
        return 'Wrong password or encrypted services were modified'
    if isinstance(error, (OSError, subprocess.SubprocessError)):
        return 'Could not open the password dialog or access the clipboard'
    return str(error)


def prompt_for_password(title):
    result = subprocess.run(
        ['zenity', '--password', '--title', title],
        capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return None
    password = result.stdout.rstrip('\n')
    if not password:
        raise ValueError('Password cannot be empty')
    return password


def derive_fernet(password, salt):
    key = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600_000
    ).derive(password.encode('utf-8'))
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_services(services, password):
    salt = secrets.token_bytes(16)
    token = derive_fernet(password, salt).encrypt(services.encode('utf-8'))
    envelope = base64.urlsafe_b64encode(salt + token).decode('ascii')
    return ENCRYPTED_PREFIX + envelope


def decrypt_services(value, password):
    try:
        envelope = base64.b64decode(
            value[len(ENCRYPTED_PREFIX):], altchars=b'-_', validate=True
        )
    except (ValueError, binascii.Error) as error:
        raise ValueError('Encrypted Services value is malformed') from error
    if len(envelope) <= 16:
        raise ValueError('Encrypted Services value is malformed')
    salt, token = envelope[:16], envelope[16:]
    return derive_fernet(password, salt).decrypt(token).decode('utf-8')


def copy_to_clipboard(value):
    subprocess.run(['xclip', '-selection', 'clipboard'], input=value.encode(),
                   check=True)


class TfaExtension(Extension):

    def __init__(self):
        super(TfaExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, CustomActionListener())

        db_path = f'{get_preferences_path()}/data.db'
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            name TEXT PRIMARY KEY,
            last_used INTEGER
        )
        """)

        self.conn.commit()
        self._session_password = None
        self._session_password_at = 0


def mark_used(extension, name):
    extension.cursor.execute("""
        INSERT INTO services (name, last_used)
        VALUES (?, ?)
        ON CONFLICT(name)
        DO UPDATE SET last_used=excluded.last_used
    """, (name, int(time.time())))

    extension.conn.commit()


def get_items(extension):
    extension.cursor.execute("""
        SELECT name
        FROM services
        ORDER BY last_used DESC
    """)

    return [row[0] for row in extension.cursor.fetchall()]


def get_preferences_path():
    basename = os.path.basename(os.path.dirname(__file__))
    return os.path.expanduser(f'~/.config/ulauncher/{basename}')


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        keyword = event.get_keyword()
        if keyword == extension.preferences.get('tfa_encrypt_kw', 'encrypt'):
            return self.convert_services(extension, encrypt=True)
        if keyword == extension.preferences.get('tfa_decrypt_kw', 'decrypt'):
            return self.convert_services(extension, encrypt=False)

        query = (event.get_argument() or '').strip()
        query_lower = query.lower()
        providers_raw = extension.preferences.get('tfa_providers', '')
        try:
            if providers_raw.startswith(ENCRYPTED_PREFIX):
                password = self.get_session_password(extension)
                if password is None:
                    return message('Password entry cancelled')
                try:
                    providers_raw = decrypt_services(providers_raw, password)
                except InvalidToken:
                    password = prompt_for_password('Unlock 2FA services')
                    if password is None:
                        return message('Password entry cancelled')
                    providers_raw = decrypt_services(providers_raw, password)
                    extension._session_password = password
                extension._session_password_at = time.time()
        except (ValueError, InvalidToken, OSError, subprocess.SubprocessError) as error:
            return message(error_message(error))

        providers = providers_raw.split(';')

        max_items = int(extension.preferences.get('tfa_max_providers') or 7)

        matching_items = []

        # Absolute path to the extension's images folder
        custom_images_path = f"{get_preferences_path()}/images"

        if not os.path.exists(custom_images_path):
            default_images_path = os.path.join(
                os.path.dirname(__file__), 'images')
            shutil.copytree(default_images_path, custom_images_path)

        for provider in providers:
            if '=' not in provider:
                continue
            name, secret = map(str.strip, provider.split('=', 1))

            if query_lower and query_lower not in name.lower():
                continue

            # Add the symbol = at the end to ensure it has the correct length for base32
            missing_padding = len(secret) % 8
            if missing_padding:
                paddings_to_add = '=' * (8 - missing_padding)
                secret += paddings_to_add

            # Get the first word of the name to look for the icon
            first_word = name.split()[0].lower()
            custom_icon_path = os.path.join(
                custom_images_path, f'{first_word}.png')

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
                on_enter=ExtensionCustomAction(
                    {
                        "action": "update_last_used",
                        "token": token,
                        "name": name,
                    },
                    keep_app_open=False
                ),
            )
            matching_items.append((name, item))

        # Order by last_used from DB (most recent first); unknown ones go to the end, then by name
        usage_order = {n: idx for idx, n in enumerate(get_items(extension))}

        matching_items.sort(
            key=lambda pair: (usage_order.get(
                pair[0], float('inf')), pair[0].lower())
        )

        # Drop names, keep only items
        ordered_items = [item for _, item in matching_items]

        if len(ordered_items) > max_items:
            items.extend(ordered_items[:max_items - 1])
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='[...]',
                description='More services available',
                on_enter=None
            ))
        else:
            items.extend(ordered_items)

        return RenderResultListAction(items)

    @staticmethod
    def get_session_password(extension):
        if (extension._session_password and
                time.time() - extension._session_password_at < PASSWORD_CACHE_SECONDS):
            return extension._session_password
        extension._session_password = None
        return prompt_for_password('Unlock 2FA services')

    def convert_services(self, extension, encrypt):
        providers_raw = extension.preferences.get('tfa_providers', '')
        if not providers_raw.strip():
            return message('Services setting is empty')

        if encrypt == providers_raw.startswith(ENCRYPTED_PREFIX):
            state = 'already encrypted' if encrypt else 'already plain text'
            return message(f'Services are {state}')

        try:
            password = prompt_for_password(
                'Encrypt services' if encrypt else 'Decrypt services')
            if password is None:
                return message('Password entry cancelled')
            converted = (encrypt_services(providers_raw, password) if encrypt
                         else decrypt_services(providers_raw, password))
            copy_to_clipboard(converted)
        except (ValueError, InvalidToken, OSError, subprocess.SubprocessError) as error:
            return message(f'Could not convert services: {error_message(error)}')

        action = 'Encrypted' if encrypt else 'Decrypted'
        return message(
            f'{action} services copied. Paste the result into the Services setting.')


class CustomActionListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()

        if data.get("action") != "update_last_used":
            return

        token = data["token"]
        name = data["name"]

        mark_used(extension, name)

        copy_to_clipboard(token)


if __name__ == '__main__':
    TfaExtension().run()
