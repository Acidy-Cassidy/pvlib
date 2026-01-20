"""
Key derivation functions.
"""

import hashlib as _hashlib


def pbkdf2_hmac(hash_name, password, salt, iterations, dklen=None):
    """
    PKCS#5 v2.0 PBKDF2 key derivation using HMAC.

    Args:
        hash_name: Hash algorithm name (e.g., 'sha256')
        password: Password bytes
        salt: Salt bytes
        iterations: Number of iterations
        dklen: Derived key length (None = hash digest size)

    Returns:
        bytes: Derived key
    """
    if isinstance(password, str):
        raise TypeError("Password must be bytes")
    if isinstance(salt, str):
        raise TypeError("Salt must be bytes")
    if iterations < 1:
        raise ValueError("Iterations must be >= 1")

    return _hashlib.pbkdf2_hmac(hash_name, password, salt, iterations, dklen)


def scrypt(password, *, salt, n, r, p, maxmem=0, dklen=64):
    """
    Scrypt key derivation function.

    Args:
        password: Password bytes
        salt: Salt bytes
        n: CPU/memory cost parameter (must be power of 2)
        r: Block size parameter
        p: Parallelization parameter
        maxmem: Maximum memory to use (0 = default)
        dklen: Derived key length (default 64)

    Returns:
        bytes: Derived key
    """
    if isinstance(password, str):
        raise TypeError("Password must be bytes")
    if isinstance(salt, str):
        raise TypeError("Salt must be bytes")
    if n < 2 or (n & (n - 1)) != 0:
        raise ValueError("n must be a power of 2 greater than 1")
    if r < 1:
        raise ValueError("r must be >= 1")
    if p < 1:
        raise ValueError("p must be >= 1")

    return _hashlib.scrypt(password, salt=salt, n=n, r=r, p=p, maxmem=maxmem, dklen=dklen)
