import os
import errno
import paramiko
import bittensor as bt


def generate_key(name: str):
    # Generate a new RSA key pair
    private_key = paramiko.RSAKey.generate(bits=2048)

    # Save the private key to a file
    private_key_file = f'{name}.key'
    private_key.write_private_key_file(private_key_file)

    # Get the public key
    public_key = f"{private_key.get_name()} {private_key.get_base64()}"

    return public_key, private_key


def generate_ssh_key(public_key):
    # Define the path to the .ssh directory and authorized_keys file
    ssh_dir = os.path.expanduser(os.path.join('~', '.ssh'))
    authorized_keys_file = os.path.join(ssh_dir, 'authorized_keys')

    # Ensure the .ssh directory exists
    if not os.path.exists(ssh_dir):
        try:
            os.makedirs(ssh_dir, mode=0o700)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    # Ensure the .ssh directory has the correct permissions
    os.chmod(ssh_dir, 0o700)

    # Append the public key to the authorized_keys file
    with open(authorized_keys_file, 'a') as f:
        bt.logging.info(f"Write {public_key} in file {authorized_keys_file}")
        f.write(public_key + '\n')

    # Ensure the authorized_keys file has the correct permissions
    os.chmod(authorized_keys_file, 0o600)

    bt.logging.info("Ssh key saved")


def clean_ssh_key(public_key):
    # Define the path to the .ssh directory and authorized_keys file
    ssh_dir = os.path.expanduser(os.path.join('~', '.ssh'))
    authorized_keys_file = os.path.join(ssh_dir, 'authorized_keys')

    # Ensure the .ssh directory exists
    if not os.path.exists(ssh_dir):
        try:
            os.makedirs(ssh_dir, mode=0o700)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    # Ensure the .ssh directory has the correct permissions
    os.chmod(ssh_dir, 0o700)

    # Read all lines from the file
    with open(authorized_keys_file, 'r') as file:
        lines = file.readlines()

    # Filter out the line we want to remove
    lines = [line for line in lines if line.strip("\n") != public_key]

    # Write the remaining lines back to the file
    with open(authorized_keys_file, 'w') as file:
        file.writelines(lines)

    # Ensure the authorized_keys file has the correct permissions
    os.chmod(authorized_keys_file, 0o600)

    bt.logging.info("Ssh key removed")