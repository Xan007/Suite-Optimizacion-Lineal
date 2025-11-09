import hashlib
import hmac
from typing import Optional


def hash_api_key(api_key: str) -> str:
    """Hash una API key usando SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """Verifica si una API key coincide con su hash."""
    return hmac.compare_digest(hash_api_key(api_key), api_key_hash)


def is_valid_api_key_format(api_key: str) -> bool:
    """Valida que la API key tenga un formato mínimo válido."""
    return isinstance(api_key, str) and len(api_key) > 0
