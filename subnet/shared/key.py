import os
import errno
import bittensor as bt


def generate_ssh_key(public_key):
    # Define the path to the .ssh directory and authorized_keys file
    ssh_dir = os.path.expanduser(os.path.join('~', '.ssh'))
    authorized_keys_file = os.path.join(ssh_dir, 'authorized_keys')
    bt.logging.info(f"Authorized key files {authorized_keys_file}")

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


def clean_ssh_key(public_key):
    # Define the path to the .ssh directory and authorized_keys file
    ssh_dir = os.path.expanduser(os.path.join('~', '.ssh'))
    authorized_keys_file = os.path.join(ssh_dir, 'authorized_keys')
    bt.logging.info(f"Authorized key files {authorized_keys_file}")

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