"""
Crypto Only: AES-256-GCM with a passphrase
--------------------------------------------
Requirements:
    pip install cryptography

Usage:
    python crypto_aes_gcm.py encrypt "secret message" "my passphrase"
    python crypto_aes_gcm.py decrypt "<ciphertext>" "my passphrase"
"""

import sys
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SALT_SIZE = 16     # bytes, random per encryption
NONCE_SIZE = 12    # bytes, standard size for GCM, random per encryption
ITERATIONS = 200_000
DECRYPT_ERROR = "Wrong passphrase or invalid ciphertext."


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Turn any passphrase into a 32-byte (256-bit) AES key."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_message(plaintext: str, passphrase: str) -> str:
    if not plaintext or not passphrase:
        raise ValueError("Enter both a message and a passphrase.")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(passphrase, salt)

    # GCM output = ciphertext + 16-byte authentication tag (appended automatically)
    encrypted = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)

    # Package as: salt | nonce | ciphertext+tag, then base64 so it is easy to copy/paste
    return base64.b64encode(salt + nonce + encrypted).decode("ascii")


def decrypt_message(ciphertext: str, passphrase: str) -> str:
    if not ciphertext or not passphrase:
        raise ValueError("Enter both a ciphertext and a passphrase.")

    try:
        raw = base64.b64decode(ciphertext.encode("ascii"))
        salt = raw[:SALT_SIZE]
        nonce = raw[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
        encrypted = raw[SALT_SIZE + NONCE_SIZE:]

        key = _derive_key(passphrase, salt)
        plaintext = AESGCM(key).decrypt(nonce, encrypted, None)
        return plaintext.decode("utf-8")
    except Exception:
        # Wrong passphrase, tampered data, or invalid ciphertext all land here
        return DECRYPT_ERROR


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    mode, text, passphrase = sys.argv[1], sys.argv[2], sys.argv[3]

    if mode == "encrypt":
        print("Ciphertext:", encrypt_message(text, passphrase))
    elif mode == "decrypt":
        print("Plaintext:", decrypt_message(text, passphrase))
    else:
        print(__doc__)