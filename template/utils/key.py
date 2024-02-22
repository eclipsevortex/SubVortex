import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# The string (passphrase) you want to use to generate the key pair
# passphrase = "my_secret_passphrase"

# Generate a salt (should be securely generated and stored)
salt = os.urandom(16)

# Use a key derivation function (KDF) to derive a secure seed from the passphrase
# WARNING: This is a simplified example. In a real application, you should also use a salt and proper key stretching.
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
    backend=default_backend()
)


def create_seed(validator_uid, miner_uid):
    passphrase = f"{validator_uid}-{miner_uid}"
    return kdf.derive(passphrase.encode())


def create_private_key():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
        
    return private_key, pem_private_key


def create_public_key(private_key: rsa.RSAPrivateKey):
    public_key = private_key.public_key()

    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
        
    return public_key, pem_public_key