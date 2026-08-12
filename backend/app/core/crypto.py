"""Envelope encryption for the credential vault (services/credentials.py).

Layout: one master key (settings.credential_master_key, env-injected — see
config.py) encrypts a per-user data key generated at registration and stored
encrypted on the user document (auth.py). Each connected credential is then
encrypted with its owning user's data key, not the master key directly, so
rotating a single user's key never touches anyone else's credentials.

Only services/credentials.py decrypts anything, and only in memory for the
single call that needs it — see that module's docstring for the boundary
this is meant to hold.
"""
from functools import lru_cache

from cryptography.fernet import Fernet

from ..config import settings


@lru_cache(maxsize=1)
def _master_fernet() -> Fernet:
    return Fernet(settings.credential_master_key.encode())


def generate_data_key() -> bytes:
    return Fernet.generate_key()


def encrypt_data_key(data_key: bytes) -> str:
    return _master_fernet().encrypt(data_key).decode()


def decrypt_data_key(encrypted_data_key: str) -> bytes:
    return _master_fernet().decrypt(encrypted_data_key.encode())


def encrypt_with_data_key(data_key: bytes, plaintext: str) -> str:
    return Fernet(data_key).encrypt(plaintext.encode()).decode()


def decrypt_with_data_key(data_key: bytes, ciphertext: str) -> str:
    return Fernet(data_key).decrypt(ciphertext.encode()).decode()
