from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from template.utils.key import create_seed, create_private_key, create_public_key

def run():
    # Create the validator's private key
    private_key, pem_private_key = create_private_key()
    print(f"Validator private key {pem_private_key}")

    # Create the validator's public key
    public_key, pem_public_key = create_public_key(private_key)
    print(f"Validator public key {pem_public_key}")

    message = "Romain Diegoni"

    encrypted_message = public_key.encrypt(
        message.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    original_message = private_key.decrypt(
        encrypted_message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    print(f"Message {message}")
    print(f"Encrypted message {encrypted_message}")
    print(f"Decrypted message {original_message.decode('utf-8')}")


if __name__ == "__main__":
    run()