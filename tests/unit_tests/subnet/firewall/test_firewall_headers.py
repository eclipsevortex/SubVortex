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
import base64
import unittest
from subnet.firewall.firewall_packet import FirewallHeaders


class TestFirewallHeaders(unittest.TestCase):
    def test_when_content_is_a_string_should_parse_correctly(self):
        payload = "UE9TVCAvUW5BVGFzayBIVFRQLzEuMQ0KSG9zdDogMTY3Ljg2Ljc5Ljg2OjgwOTENCm5hbWU6IFFuQVRhc2sNCnRpbWVvdXQ6IDEyLjANCmJ0X2hlYWRlcl9heG9uX2lwOiAxNjcuODYuNzkuODYNCmJ0X2hlYWRlcl9heG9uX3BvcnQ6IDgwOTENCmJ0X2hlYWRlcl9heG9uX2hvdGtleTogNUNxdzNHcDNLMmpMR0JEZFJGZGRUMjlnS0w0eGRSeTY1RlVwYVFiS1VOUGhzU1F0DQpidF9oZWFkZXJfZGVuZHJpdGVfaXA6IDE5Mi4xNTAuMjUzLjEyMg0KYnRfaGVhZGVyX2RlbmRyaXRlX3ZlcnNpb246IDcyMA0KYnRfaGVhZGVyX2RlbmRyaXRlX25vbmNlOiAxNDkxNjM3NTQxNzI4NjENCmJ0X2hlYWRlcl9kZW5kcml0ZV91dWlkOiAxODMwZTliNi0zZDQzLTExZWYtYjRkNy1lN2IwMmJlZDJiNTcNCmJ0X2hlYWRlcl9kZW5kcml0ZV9ob3RrZXk6IDVFMld1OFNzcEZIZEtlMUJSdmZNNUNwU3hjalFmenBReFlLR1ZFWUs1Mkc0bWJEdg0KYnRfaGVhZGVyX2RlbmRyaXRlX3NpZ25hdHVyZTogMHg5NjM2MzJlMmEwMDkzZjQ2NDczYmE1NzA5MWNlZmExNWI3M2Y4NGQxOGRjODAzYjY0YjFmOGE3NzUxMjZjYjUyYzc0Y2Y5M2I3MGE5YzliNjA5MjY2NzM0NWViMzY4MmJjMmE1OWRlMDU4NTI4OWQ4ZTBlYzEwYWFjOTVmYjE4Nw0KaGVhZGVyX3NpemU6IDY0MA0KdG90YWxfc2l6ZTogODcxMQ0KY29tcHV0ZWRfYm9keV9oYXNoOiBhN2ZmYzZmOGJmMWVkNzY2NTFjMTQ3NTZhMDYxZDY2MmY1ODBmZjRkZTQzYjQ5ZmE4MmQ4MGE0YjgwZjg0MzRhDQpBY2NlcHQ6ICovKg0KQWNjZXB0LUVuY29kaW5nOiBnemlwLCBkZWZsYXRlLCBicg0KVXNlci1BZ2VudDogUHl0aG9uLzMuMTAgYWlvaHR0cC8zLjkuMGIwDQpDb250ZW50LUxlbmd0aDogMjEzNA0KQ29udGVudC1UeXBlOiBhcHBsaWNhdGlvbi9qc29uDQoNCg"
        missing_padding = len(payload) % 4
        if missing_padding:
            payload += "=" * (4 - missing_padding)

        # Action
        result = FirewallHeaders.from_payload(base64.b64decode(payload))

        # # Assert
        assert "QnATask" == result.synapse_name
        assert "167.86.79.86" == result.axon_ip
        assert "5Cqw3Gp3K2jLGBDdRFddT29gKL4xdRy65FUpaQbKUNPhsSQt" == result.axon_hotkey
        assert 8091 == result.axon_port
        assert (
            "5E2Wu8SspFHdKe1BRvfM5CpSxcjQfzpQxYKGVEYK52G4mbDv" == result.dendrite_hotkey
        )
        assert "192.150.253.122" == result.dendrite_ip
        assert None == result.dendrite_neuron_version
        assert 149163754172861 == result.dendrite_nonce
        assert None == result.dendrite_port
        assert (
            "0x963632e2a0093f46473ba57091cefa15b73f84d18dc803b64b1f8a775126cb52c74cf93b70a9c9b6092667345eb3682bc2a59de0585289d8e0ec10aac95fb187"
            == result.dendrite_signature
        )
        assert "1830e9b6-3d43-11ef-b4d7-e7b02bed2b57" == result.dendrite_uuid
        assert 720 == result.dendrite_version
        assert (
            "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"
            == result.computed_body_hash
        )

    def test_when_content_is_a_json_should_parse_correctly(self):
        # Arrange
        payload = "eyJuYW1lIjogIlFuQVRhc2siLCAidGltZW91dCI6IDEyLjAsICJ0b3RhbF9zaXplIjogODMxOCwgImhlYWRlcl9zaXplIjogMCwgImRlbmRyaXRlIjogeyJzdGF0dXNfY29kZSI6IG51bGwsICJzdGF0dXNfbWVzc2FnZSI6IG51bGwsICJwcm9jZXNzX3RpbWUiOiBudWxsLCAiaXAiOiAiMTkyLjE1MC4yNTMuMTIyIiwgInBvcnQiOiBudWxsLCAidmVyc2lvbiI6IDcyMCwgIm5vbmNlIjogMTQ5MjY1NTkyMzIwOTkwLCAidXVpZCI6ICIxODMwZTliNi0zZDQzLTExZWYtYjRkNy1lN2IwMmJlZDJiNTciLCAiaG90a2V5IjogIjVFMld1OFNzcEZIZEtlMUJSdmZNNUNwU3hjalFmenBReFlLR1ZFWUs1Mkc0bWJEdiIsICJzaWduYXR1cmUiOiAiMHg2MGZlOGIyODgzMDRiYTljNjIyNTE2ZTk1YmM4NjY5MTk4Yjk0ZTk5YjU3MzUzY2JmMjQ4YjUzMDYyYzRlZTdiZTk2YzY5OThiOGE3YzdjNGZhMGUyYzdjNmQ4ZmIzNTUyNmEzNTEzOThmODU0YmM2MmY1MTIzZDhhZWY5Yjk4MSJ9LCAiYXhvbiI6IHsic3RhdHVzX2NvZGUiOiBudWxsLCAic3RhdHVzX21lc3NhZ2UiOiBudWxsLCAicHJvY2Vzc190aW1lIjogbnVsbCwgImlwIjogIjE2Ny44Ni43OS44NiIsICJwb3J0IjogODA5MSwgInZlcnNpb24iOiBudWxsLCAibm9uY2UiOiBudWxsLCAidXVpZCI6IG51bGwsICJob3RrZXkiOiAiNUNxdzNHcDNLMmpMR0JEZFJGZGRUMjlnS0w0eGRSeTY1RlVwYVFiS1VOUGhzU1F0IiwgInNpZ25hdHVyZSI6IG51bGx9LCAiY29tcHV0ZWRfYm9keV9oYXNoIjogIiIsICJyZXF1aXJlZF9oYXNoX2ZpZWxkcyI6IFtdLCAidXJscyI6IFtdLCAiZGF0YXMiOiBbXSwgInRvb2xzIjogW3sibmFtZSI6ICJmaW5kX2J1c2llc3RfYWlzbGUiLCAiZGVzY3JpcHRpb24iOiAiRmluZHMgdGhlIGJ1c2llc3QgYWlzbGUgaW4gdGhlIHN0b3JlIGJhc2VkIG9uIHRoZSBwcm92aWRlZCBzdG9yZSBsYXlvdXQgZGF0YS4iLCAiYXJndW1lbnRzIjoge319XSwgIm5vdGVzIjogIk5vIE5vdGVzIiwgInByb21wdCI6ICIiLCAibWVzc2FnZXMiOiBbeyJyb2xlIjogInVzZXIiLCAiY29udGVudCI6ICJXaGF0IGlzIHRoZSBidXNpZXN0IGFpc2xlIGluIHRoZWV4YW1wbGVfc3RvcmUgb24gYSBGcmlkYXkgYWZ0ZXJub29uLCBhY2NvcmRpbmcgdG8gdGhlIHN0b3JlIGxheW91dCBkYXRhPyJ9XSwgIm1lc3NhZ2VfaGlzdG9yeSI6IHsibWVzc2FnZXMiOiBbeyJyb2xlIjogInVzZXIiLCAiY29udGVudCI6ICJXaGF0IGlzIHRoZSBidXNpZXN0IGFpc2xlIGluIHRoZWV4YW1wbGVfc3RvcmUgb24gYSBGcmlkYXkgYWZ0ZXJub29uLCBhY2NvcmRpbmcgdG8gdGhlIHN0b3JlIGxheW91dCBkYXRhPyJ9XX0sICJyZXNwb25zZSI6IHt9LCAibWluZXJfdWlkcyI6IFtdfQ"
        missing_padding = len(payload) % 4
        if missing_padding:
            payload += "=" * (4 - missing_padding)

        # Action
        result = FirewallHeaders.from_payload(base64.b64decode(payload))

        # # Assert
        assert "QnATask" == result.synapse_name
        assert "167.86.79.86" == result.axon_ip
        assert "5Cqw3Gp3K2jLGBDdRFddT29gKL4xdRy65FUpaQbKUNPhsSQt" == result.axon_hotkey
        assert 8091 == result.axon_port
        assert (
            "5E2Wu8SspFHdKe1BRvfM5CpSxcjQfzpQxYKGVEYK52G4mbDv" == result.dendrite_hotkey
        )
        assert "192.150.253.122" == result.dendrite_ip
        assert None == result.dendrite_neuron_version
        assert 149265592320990 == result.dendrite_nonce
        assert None == result.dendrite_port
        assert (
            "0x60fe8b288304ba9c622516e95bc8669198b94e99b57353cbf248b53062c4ee7be96c6998b8a7c7c4fa0e2c7c6d8fb35526a351398f854bc62f5123d8aef9b981"
            == result.dendrite_signature
        )
        assert "1830e9b6-3d43-11ef-b4d7-e7b02bed2b57" == result.dendrite_uuid
        assert 720 == result.dendrite_version
        assert "" == result.computed_body_hash
