import platform

def get_os():
    return platform.system()

def is_linux_platform():
    return get_os() == "Linux"

def is_macos_platform():
    return get_os() == "Darwin"
