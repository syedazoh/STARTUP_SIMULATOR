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


async def rewrap_user_keys(db, old_master_key: str, new_master_key: str) -> int:
    """Rewraps all users' data keys with a new master key.

    When replacing the fallback master key with a deployment-specific
    master key, this re-encrypts stored user data keys without exposing or
    modifying the credentials encrypted under each user's data key.
    """
    old_f = Fernet(old_master_key.encode() if isinstance(old_master_key, str) else old_master_key)
    new_f = Fernet(new_master_key.encode() if isinstance(new_master_key, str) else new_master_key)

    count = 0
    cursor = db["users"].find({"encrypted_data_key": {"$exists": True}})
    async for user in cursor:
        raw_key = old_f.decrypt(user["encrypted_data_key"].encode())
        re_encrypted = new_f.encrypt(raw_key).decode()
        await db["users"].update_one(
            {"_id": user["_id"]},
            {"$set": {"encrypted_data_key": re_encrypted}},
        )
        count += 1
    return count
