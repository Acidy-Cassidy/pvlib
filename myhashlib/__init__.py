"""
myhashlib - Educational hashlib implementation
Mirrors Python's hashlib API for learning purposes.
"""

__version__ = "0.1.0"

from .algorithms import (
    Hash,
    new,
    md5,
    sha1,
    sha224,
    sha256,
    sha384,
    sha512,
    sha3_224,
    sha3_256,
    sha3_384,
    sha3_512,
    shake_128,
    shake_256,
    blake2b,
    blake2s,
    algorithms_available,
    algorithms_guaranteed,
    file_digest,
)

from .kdf import pbkdf2_hmac, scrypt

__all__ = [
    # Core functions
    "new",
    "md5",
    "sha1",
    "sha224",
    "sha256",
    "sha384",
    "sha512",
    "sha3_224",
    "sha3_256",
    "sha3_384",
    "sha3_512",
    "shake_128",
    "shake_256",
    "blake2b",
    "blake2s",
    # Module attributes
    "algorithms_available",
    "algorithms_guaranteed",
    # KDF functions
    "pbkdf2_hmac",
    "scrypt",
    # Helpers
    "file_digest",
    # Classes
    "Hash",
]
