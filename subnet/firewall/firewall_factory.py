# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
from subnet.firewall.firewall_linux_tool import FirewallLinuxTool
from subnet.firewall.firewall_observer import FirewallObserver
from subnet.firewall.firewall_linux_observer import FirewallLinuxObserver
from subnet.firewall.firewall_tool import FirewallTool
from subnet.shared.platform import is_linux_platform, get_os


def create_firewall_tool(*args, **kwargs) -> FirewallTool:
    if is_linux_platform():
        return FirewallLinuxTool(*args, **kwargs)

    raise ValueError(f"No firewall tool implemented for {get_os()}")


def create_firewall_observer(*args, **kwargs) -> FirewallObserver:
    if is_linux_platform():
        return FirewallLinuxObserver(*args, **kwargs)

    raise ValueError(f"No firewall observer implemented for {get_os()}")
