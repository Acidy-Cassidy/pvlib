"""
Hash algorithm implementations.
Wraps Python's hashlib for educational facade.
"""

import hashlib as _hashlib

# Export available and guaranteed algorithms
algorithms_available = frozenset(_hashlib.algorithms_available)
algorithms_guaranteed = frozenset(_hashlib.algorithms_guaranteed)


class Hash:
    """
    Custom Hash class that wraps a real hash object.
    Provides the same interface as hashlib hash objects.
    """

    def __init__(self, name, data=b"", **kwargs):
        """
        Initialize a hash object.

        Args:
            name: Algorithm name (e.g., 'sha256', 'md5')
            data: Initial data to hash (optional)
            **kwargs: Additional algorithm-specific arguments
        """
        self._name = name.lower()
        self._hash = _hashlib.new(self._name, data, **kwargs)

    def update(self, data):
        """
        Update the hash object with bytes-like object.

        Args:
            data: Bytes-like object to hash
        """
        if isinstance(data, str):
            raise TypeError("Unicode-objects must be encoded before hashing")
        self._hash.update(data)

    def digest(self):
        """
        Return the digest of the data passed to update().

        Returns:
            bytes: The hash digest
        """
        return self._hash.digest()

    def hexdigest(self):
        """
        Return the digest as a string of hexadecimal digits.

        Returns:
            str: The hex-encoded hash digest
        """
        return self._hash.hexdigest()

    def copy(self):
        """
        Return a copy of the hash object.

        Returns:
            Hash: A new Hash object with the same state
        """
        new_hash = Hash.__new__(Hash)
        new_hash._name = self._name
        new_hash._hash = self._hash.copy()
        return new_hash

    @property
    def name(self):
        """Algorithm name."""
        return self._name

    @property
    def digest_size(self):
        """Size of the resulting hash in bytes."""
        return self._hash.digest_size

    @property
    def block_size(self):
        """Internal block size of the algorithm in bytes."""
        return self._hash.block_size


class ShakeHash(Hash):
    """
    Hash class for SHAKE algorithms with variable-length output.
    """

    def digest(self, length):
        """
        Return the digest with specified length.

        Args:
            length: Desired length of digest in bytes

        Returns:
            bytes: The hash digest of specified length
        """
        return self._hash.digest(length)

    def hexdigest(self, length):
        """
        Return the hex digest with specified length.

        Args:
            length: Desired length of digest in bytes (hex will be 2x)

        Returns:
            str: The hex-encoded hash digest
        """
        return self._hash.hexdigest(length)


def new(name, data=b"", **kwargs):
    """
    Create a new hash object.

    Args:
        name: Algorithm name
        data: Initial data to hash (optional)
        **kwargs: Additional arguments

    Returns:
        Hash: A new hash object
    """
    name_lower = name.lower()
    if name_lower in ("shake_128", "shake_256"):
        return ShakeHash(name, data, **kwargs)
    return Hash(name, data, **kwargs)


def md5(data=b"", **kwargs):
    """Return a new MD5 hash object."""
    return Hash("md5", data, **kwargs)


def sha1(data=b"", **kwargs):
    """Return a new SHA-1 hash object."""
    return Hash("sha1", data, **kwargs)


def sha224(data=b"", **kwargs):
    """Return a new SHA-224 hash object."""
    return Hash("sha224", data, **kwargs)


def sha256(data=b"", **kwargs):
    """Return a new SHA-256 hash object."""
    return Hash("sha256", data, **kwargs)


def sha384(data=b"", **kwargs):
    """Return a new SHA-384 hash object."""
    return Hash("sha384", data, **kwargs)


def sha512(data=b"", **kwargs):
    """Return a new SHA-512 hash object."""
    return Hash("sha512", data, **kwargs)


def sha3_224(data=b"", **kwargs):
    """Return a new SHA3-224 hash object."""
    return Hash("sha3_224", data, **kwargs)


def sha3_256(data=b"", **kwargs):
    """Return a new SHA3-256 hash object."""
    return Hash("sha3_256", data, **kwargs)


def sha3_384(data=b"", **kwargs):
    """Return a new SHA3-384 hash object."""
    return Hash("sha3_384", data, **kwargs)


def sha3_512(data=b"", **kwargs):
    """Return a new SHA3-512 hash object."""
    return Hash("sha3_512", data, **kwargs)


def shake_128(data=b"", **kwargs):
    """Return a new SHAKE-128 hash object."""
    return ShakeHash("shake_128", data, **kwargs)


def shake_256(data=b"", **kwargs):
    """Return a new SHAKE-256 hash object."""
    return ShakeHash("shake_256", data, **kwargs)


def blake2b(data=b"", *, digest_size=64, **kwargs):
    """
    Return a new BLAKE2b hash object.

    Args:
        data: Initial data to hash
        digest_size: Size of output digest (1-64 bytes, default 64)
        **kwargs: Additional arguments (key, salt, person)
    """
    return Hash("blake2b", data, digest_size=digest_size, **kwargs)


def blake2s(data=b"", *, digest_size=32, **kwargs):
    """
    Return a new BLAKE2s hash object.

    Args:
        data: Initial data to hash
        digest_size: Size of output digest (1-32 bytes, default 32)
        **kwargs: Additional arguments (key, salt, person)
    """
    return Hash("blake2s", data, digest_size=digest_size, **kwargs)


def file_digest(fileobj, digest, *, _bufsize=2**18):
    """
    Hash the contents of a file-like object.

    Args:
        fileobj: File-like object opened in binary mode
        digest: Hash algorithm name or constructor
        _bufsize: Buffer size for reading (default 256KB)

    Returns:
        Hash: Hash object with file contents hashed
    """
    if callable(digest):
        hash_obj = digest()
    else:
        hash_obj = new(digest)

    buf = bytearray(_bufsize)
    view = memoryview(buf)
    while True:
        size = fileobj.readinto(buf)
        if size == 0:
            break
        hash_obj.update(view[:size])

    return hash_obj
