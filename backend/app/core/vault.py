"""
vault.py — AES-256 (Fernet) encrypt/decrypt/mask for Groq API keys.

RULE: Decrypted keys are NEVER returned via any API response or log.
      Only mask_key() output is safe to expose externally.
"""

from cryptography.fernet import Fernet
from app.config import FERNET_KEY

_fernet = Fernet(FERNET_KEY)


def encrypt_key(plaintext: str) -> str:
    """Encrypt a Groq API key.  Returns a url-safe base64 ciphertext string."""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_key(ciphertext: str) -> str:
    """Decrypt a stored ciphertext back to the plaintext key.
    NEVER expose the return value in API responses or logs."""
    return _fernet.decrypt(ciphertext.encode()).decode()


def mask_key(plaintext: str) -> str:
    """Return a display-safe masked version: 'gsk_ab...xxxx' (last 4 chars)."""
    if len(plaintext) <= 8:
        return "****"
    prefix = plaintext[:7]   # e.g. "gsk_aBc"
    suffix = plaintext[-4:]  # last 4 chars
    return f"{prefix}...{suffix}"
