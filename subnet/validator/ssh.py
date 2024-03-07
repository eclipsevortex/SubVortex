import paramiko
import bittensor as bt


def check_connection(ip, private_key):
    '''
    Check the ssh connection with <ip>/<private_key> is working
    '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(ip, username='root', pkey=private_key)
        return True
    except paramiko.AuthenticationException:
        bt.logging.error("Authentication failed, please verify your credentials")
    except paramiko.SSHException as sshException:
        bt.logging.error("Unable to establish SSH connection: %s" % sshException)
    except paramiko.BadHostKeyException as badHostKeyException:
        bt.logging.error("Unable to verify server's host key: %s" % badHostKeyException)
    except Exception as e:
        bt.logging.error(e)
    finally:
        # Close the SSH connection
        ssh.close()

    return False