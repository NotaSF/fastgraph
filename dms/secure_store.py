import base64
import getpass
import hashlib
import json
import os
import platform
from typing import Optional, Tuple

import keyring
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from keyring.errors import KeyringError


SERVICE_NAME = "com.dmsfastgraph.secure_store"
KEY_NAME = "credential-encryption-key"
BACKEND_NAME = "fernet+keyring"
CURRENT_VERSION = 2


class SecureStoreError(RuntimeError):
    pass


def _get_key_from_keyring() -> Optional[bytes]:
    try:
        key = keyring.get_password(SERVICE_NAME, KEY_NAME)
    except KeyringError as exc:
        raise SecureStoreError("Could not access OS credential store.") from exc

    if key is None:
        return None

    return key.encode("ascii")


def _get_or_create_key() -> bytes:
    key = _get_key_from_keyring()

    if key is not None:
        return key

    key = Fernet.generate_key()

    try:
        keyring.set_password(SERVICE_NAME, KEY_NAME, key.decode("ascii"))
    except KeyringError as exc:
        raise SecureStoreError("Could not save encryption key to OS credential store.") from exc

    return key


def encrypt_credentials(username: str, password: str) -> dict:
    f = Fernet(_get_or_create_key())

    payload = {
        "v": CURRENT_VERSION,
        "username": username,
        "password": password,
    }

    token = f.encrypt(json.dumps(payload).encode("utf-8")).decode("ascii")

    return {
        "v": CURRENT_VERSION,
        "backend": BACKEND_NAME,
        "token": token,
    }


def decrypt_credentials(blob: Optional[dict]) -> Optional[Tuple[str, str]]:
    if not isinstance(blob, dict):
        return None

    if blob.get("backend") == BACKEND_NAME:
        return _decrypt_v2_keyring(blob)

    # Backward compatibility for existing salt/token blobs.
    if "salt" in blob and "token" in blob:
        return _decrypt_v1_machine_bound(blob)

    return None


def should_migrate_credentials(blob: Optional[dict]) -> bool:
    """
    True when credentials are still using the old hostname/username-derived key.
    """
    if not isinstance(blob, dict):
        return False

    return "salt" in blob and "token" in blob and blob.get("backend") != BACKEND_NAME


def clear_stored_key() -> None:
    try:
        keyring.delete_password(SERVICE_NAME, KEY_NAME)
    except KeyringError:
        pass


def _decrypt_v2_keyring(blob: dict) -> Optional[Tuple[str, str]]:
    token = blob.get("token")

    if not isinstance(token, str):
        return None

    try:
        key = _get_key_from_keyring()
        if key is None:
            return None

        f = Fernet(key)
        raw_payload = f.decrypt(token.encode("ascii"))
        payload = json.loads(raw_payload.decode("utf-8"))

        username = payload.get("username")
        password = payload.get("password")

        if not isinstance(username, str) or not isinstance(password, str):
            return None

        return username, password

    except (
        InvalidToken,
        SecureStoreError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):
        return None


# ---- Legacy v1 support below. Keep temporarily for migration!!!! ----

def _machine_secret() -> bytes:
    node = platform.node() or ""
    user = getpass.getuser() or ""
    raw = f"DMSFastgraph|{user}|{node}".encode("utf-8")
    return hashlib.sha256(raw).digest()


def _build_legacy_fernet(salt_b64: str) -> Fernet:
    salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=250_000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(_machine_secret()))
    return Fernet(key)


def _decrypt_v1_machine_bound(blob: dict) -> Optional[Tuple[str, str]]:
    salt = blob.get("salt")
    token = blob.get("token")

    if not isinstance(salt, str) or not isinstance(token, str):
        return None

    try:
        f = _build_legacy_fernet(salt)
        payload = f.decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return None

    parts = payload.split("\n", 1)

    if len(parts) != 2:
        return None

    return parts[0], parts[1]
