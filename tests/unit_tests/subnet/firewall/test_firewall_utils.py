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
import unittest
from collections import defaultdict
from subnet.firewall.firewall_utils import clean_sources
from subnet.firewall.firewall_request import FirewallRequest
from tests.unit_tests.test_utils import get_time


def create_request(request_id, previous_id=None, packets=[]):
    return FirewallRequest.from_dict(
        {
            "request_id": request_id,
            "previous_id": previous_id,
            "packets": packets,
        }
    )


class TestCleanSources(unittest.TestCase):
    def test_given_a_list_of_requests_when_all_are_within_the_time_window_should_return_all_of_them(
        self,
    ):
        # Arrange
        request1 = create_request(
            request_id="a414fd92-434b-11ef-8000-1e7d1928023b",
            packets=[
                {
                    "current_time": get_time(0),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1000,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(1),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1001,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request2 = create_request(
            request_id="a414fd92-434b-11ef-8001-1e7d1928023b",
            previous_id=request1.id,
            packets=[
                {
                    "current_time": get_time(2),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1010,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(3),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1011,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request3 = create_request(
            request_id="a414fd92-434b-11ef-8002-1e7d1928023b",
            previous_id=request2.id,
            packets=[
                {
                    "current_time": get_time(4),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1020,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(5),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1021,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )

        sources = defaultdict(list)
        sources["192.168.0.1:8091:tcp"] = [request1, request2, request3]

        # Action
        old_result, result = clean_sources(sources, get_time(6))

        # Assert
        assert 0 == len(old_result)

        assert 1 == len(result)
        assert 3 == len(result["192.168.0.1:8091:tcp"])
        assert request1.id == result["192.168.0.1:8091:tcp"][0].id
        assert 2 == len(result["192.168.0.1:8091:tcp"][0]._packets)
        assert request2.id == result["192.168.0.1:8091:tcp"][1].id
        assert 2 == len(result["192.168.0.1:8091:tcp"][1]._packets)
        assert request3.id == result["192.168.0.1:8091:tcp"][2].id
        assert 2 == len(result["192.168.0.1:8091:tcp"][2]._packets)

    def test_given_a_list_of_requests_when_some_are_within_the_time_window_and_one_of_them_is_denied_should_return_them(
        self,
    ):
        # Arrange
        request1 = create_request(
            request_id="a414fd92-434b-11ef-8000-1e7d1928023b",
            packets=[
                {
                    "current_time": get_time(0),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1000,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(1),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1001,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request2 = create_request(
            request_id="a414fd92-434b-11ef-8001-1e7d1928023b",
            previous_id=request1.id,
            packets=[
                {
                    "current_time": get_time(2),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1010,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(3),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1011,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request3 = create_request(
            request_id="a414fd92-434b-11ef-8002-1e7d1928023b",
            previous_id=request2.id,
            packets=[
                {
                    "current_time": get_time(4),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1020,
                    "seq": 0,
                    "flags": "S",
                    "status": "deny",
                    "type": "DENY",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(5),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1021,
                    "seq": 1,
                    "flags": "PA",
                    "status": "deny",
                    "type": "DENY",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )

        sources = defaultdict(list)
        sources["192.168.0.1:8091:tcp"] = [request1, request2, request3]

        # Action
        old_result, result = clean_sources(sources, get_time(10))

        # Assert
        assert 1 == len(old_result)
        old_ids = [x.id for x in old_result["192.168.0.1:8091:tcp"]]
        assert 2 == len(old_result["192.168.0.1:8091:tcp"])
        self.assertIn(request1.id, old_ids)
        self.assertIn(request2.id, old_ids)

        assert 1 == len(result)
        assert 1 == len(result["192.168.0.1:8091:tcp"])
        assert request3.id == result["192.168.0.1:8091:tcp"][0].id
        assert None == result["192.168.0.1:8091:tcp"][0].previous_id
        assert 2 == len(result["192.168.0.1:8091:tcp"][0]._packets)

    def test_given_a_list_of_requests_when_some_are_within_the_time_window_and_one_of_them_is_allowed_should_return_them(
        self,
    ):
        # Arrange
        request1 = create_request(
            request_id="a414fd92-434b-11ef-8000-1e7d1928023b",
            packets=[
                {
                    "current_time": get_time(0),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1000,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(1),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1001,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request2 = create_request(
            request_id="a414fd92-434b-11ef-8001-1e7d1928023b",
            previous_id=request1.id,
            packets=[
                {
                    "current_time": get_time(2),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1010,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(3),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1011,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request3 = create_request(
            request_id="a414fd92-434b-11ef-8002-1e7d1928023b",
            previous_id=request2.id,
            packets=[
                {
                    "current_time": get_time(4),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1020,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(5),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1021,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )

        sources = defaultdict(list)
        sources["192.168.0.1:8091:tcp"] = [request1, request2, request3]

        # Action
        old_result, result = clean_sources(sources, get_time(10))

        # Assert
        assert 1 == len(old_result)
        old_ids = [x.id for x in old_result["192.168.0.1:8091:tcp"]]
        assert 2 == len(old_result["192.168.0.1:8091:tcp"])
        self.assertIn(request1.id, old_ids)
        self.assertIn(request2.id, old_ids)

        assert 1 == len(result)
        assert 1 == len(result["192.168.0.1:8091:tcp"])
        assert request3.id == result["192.168.0.1:8091:tcp"][0].id
        assert None == result["192.168.0.1:8091:tcp"][0].previous_id
        assert 2 == len(result["192.168.0.1:8091:tcp"][0]._packets)

    def test_given_a_list_of_requests_when_request_within_the_time_window_are_in_progress_and_an_old_one_is_allowed_should_return_them_with_the_extra_old_one(
        self,
    ):
        # Arrange
        request1 = create_request(
            request_id="a414fd92-434b-11ef-8000-1e7d1928023b",
            packets=[
                {
                    "current_time": get_time(0),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1000,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(1),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1001,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request2 = create_request(
            request_id="a414fd92-434b-11ef-8001-1e7d1928023b",
            previous_id=request1.id,
            packets=[
                {
                    "current_time": get_time(2),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1010,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(3),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1011,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request3 = create_request(
            request_id="a414fd92-434b-11ef-8002-1e7d1928023b",
            previous_id=request2.id,
            packets=[
                {
                    "current_time": get_time(4),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1020,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                }
            ],
        )

        sources = defaultdict(list)
        sources["192.168.0.1:8091:tcp"] = [request1, request2, request3]

        # Action
        old_result, result = clean_sources(sources, get_time(10))

        # Assert
        assert 1 == len(old_result)
        old_ids = [x.id for x in old_result["192.168.0.1:8091:tcp"]]
        assert 1 == len(old_result["192.168.0.1:8091:tcp"])
        self.assertIn(request1.id, old_ids)

        assert 1 == len(result)
        assert 2 == len(result["192.168.0.1:8091:tcp"])
        assert request2.id == result["192.168.0.1:8091:tcp"][0].id
        assert None == result["192.168.0.1:8091:tcp"][0].previous_id
        assert 2 == len(result["192.168.0.1:8091:tcp"][0]._packets)
        assert request3.id == result["192.168.0.1:8091:tcp"][1].id
        assert request2.id == result["192.168.0.1:8091:tcp"][1].previous_id
        assert 1 == len(result["192.168.0.1:8091:tcp"][1]._packets)

    def test_given_a_list_of_requests_when_request_within_the_time_window_are_in_progress_and_an_old_one_is_denied_should_return_them_with_the_extra_old_one(
        self,
    ):
        # Arrange
        request1 = create_request(
            request_id="a414fd92-434b-11ef-8000-1e7d1928023b",
            packets=[
                {
                    "current_time": get_time(0),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1000,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(1),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1001,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request2 = create_request(
            request_id="a414fd92-434b-11ef-8001-1e7d1928023b",
            previous_id=request1.id,
            packets=[
                {
                    "current_time": get_time(2),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1010,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(3),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1011,
                    "seq": 1,
                    "flags": "PA",
                    "status": "deny",
                    "type": "DENY",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request3 = create_request(
            request_id="a414fd92-434b-11ef-8002-1e7d1928023b",
            previous_id=request2.id,
            packets=[
                {
                    "current_time": get_time(4),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1020,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                }
            ],
        )

        sources = defaultdict(list)
        sources["192.168.0.1:8091:tcp"] = [request1, request2, request3]

        # Action
        old_result, result = clean_sources(sources, get_time(10))

        # Assert
        assert 1 == len(old_result)
        old_ids = [x.id for x in old_result["192.168.0.1:8091:tcp"]]
        assert 1 == len(old_result["192.168.0.1:8091:tcp"])
        self.assertIn(request1.id, old_ids)

        assert 1 == len(result)
        assert 2 == len(result["192.168.0.1:8091:tcp"])
        assert request2.id == result["192.168.0.1:8091:tcp"][0].id
        assert None == result["192.168.0.1:8091:tcp"][0].previous_id
        assert 2 == len(result["192.168.0.1:8091:tcp"][0]._packets)
        assert request3.id == result["192.168.0.1:8091:tcp"][1].id
        assert request2.id == result["192.168.0.1:8091:tcp"][1].previous_id
        assert 1 == len(result["192.168.0.1:8091:tcp"][1]._packets)

    def test_given_a_list_of_requests_when_request_within_the_time_window_are_in_progress_and_no_old_one_is_denied_or_allowed_should_return_them_without_any_extra_old_one(
        self,
    ):
        # Arrange
        request1 = create_request(
            request_id="a414fd92-434b-11ef-8000-1e7d1928023b",
            packets=[
                {
                    "current_time": get_time(0),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1000,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                }
            ],
        )
        request2 = create_request(
            request_id="a414fd92-434b-11ef-8001-1e7d1928023b",
            previous_id=request1.id,
            packets=[
                {
                    "current_time": get_time(2),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1010,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                }
            ],
        )
        request3 = create_request(
            request_id="a414fd92-434b-11ef-8002-1e7d1928023b",
            previous_id=request2.id,
            packets=[
                {
                    "current_time": get_time(4),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1020,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                }
            ],
        )

        sources = defaultdict(list)
        sources["192.168.0.1:8091:tcp"] = [request1, request2, request3]

        # Action
        old_result, result = clean_sources(sources, get_time(10))

        # Assert
        assert 1 == len(old_result)
        old_ids = [x.id for x in old_result["192.168.0.1:8091:tcp"]]
        assert 2 == len(old_result["192.168.0.1:8091:tcp"])
        self.assertIn(request1.id, old_ids)
        self.assertIn(request2.id, old_ids)

        assert 1 == len(result)
        assert 1 == len(result["192.168.0.1:8091:tcp"])
        assert request3.id == result["192.168.0.1:8091:tcp"][0].id
        assert None == result["192.168.0.1:8091:tcp"][0].previous_id
        assert 1 == len(result["192.168.0.1:8091:tcp"][0]._packets)

    def test_given_a_list_of_requests_when_request_within_the_time_window_are_in_progress_and_the_first_one_is_denied_should_return_them_with_the_extra_old_one(
        self,
    ):
        # Arrange
        request1 = create_request(
            request_id="a414fd92-434b-11ef-8000-1e7d1928023b",
            packets=[
                {
                    "current_time": get_time(0),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1000,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(1),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1001,
                    "seq": 1,
                    "flags": "PA",
                    "status": "deny",
                    "type": "DENY",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request2 = create_request(
            request_id="a414fd92-434b-11ef-8001-1e7d1928023b",
            previous_id=request1.id,
            packets=[
                {
                    "current_time": get_time(2),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1010,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                }
            ],
        )
        request3 = create_request(
            request_id="a414fd92-434b-11ef-8002-1e7d1928023b",
            previous_id=request2.id,
            packets=[
                {
                    "current_time": get_time(4),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1020,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                }
            ],
        )

        sources = defaultdict(list)
        sources["192.168.0.1:8091:tcp"] = [request1, request2, request3]

        # Action
        old_result, result = clean_sources(sources, get_time(10))

        # Assert
        assert 1 == len(old_result)
        old_ids = [x.id for x in old_result["192.168.0.1:8091:tcp"]]
        assert 1 == len(old_result["192.168.0.1:8091:tcp"])
        self.assertIn(request2.id, old_ids)

        assert 1 == len(result)
        assert 2 == len(result["192.168.0.1:8091:tcp"])
        assert request1.id == result["192.168.0.1:8091:tcp"][0].id
        assert None == result["192.168.0.1:8091:tcp"][0].previous_id
        assert 2 == len(result["192.168.0.1:8091:tcp"][0]._packets)
        assert request3.id == result["192.168.0.1:8091:tcp"][1].id
        assert request1.id == result["192.168.0.1:8091:tcp"][1].previous_id
        assert 1 == len(result["192.168.0.1:8091:tcp"][1]._packets)

    def test_given_a_list_of_requests_when_request_within_the_time_window_are_in_progress_and_the_first_one_is_allowed_should_return_them_with_the_extra_old_one(
        self,
    ):
        # Arrange
        request1 = create_request(
            request_id="a414fd92-434b-11ef-8000-1e7d1928023b",
            packets=[
                {
                    "current_time": get_time(0),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1000,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
                {
                    "current_time": get_time(1),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1001,
                    "seq": 1,
                    "flags": "PA",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                },
            ],
        )
        request2 = create_request(
            request_id="a414fd92-434b-11ef-8001-1e7d1928023b",
            previous_id=request1.id,
            packets=[
                {
                    "current_time": get_time(2),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1010,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                }
            ],
        )
        request3 = create_request(
            request_id="a414fd92-434b-11ef-8002-1e7d1928023b",
            previous_id=request2.id,
            packets=[
                {
                    "current_time": get_time(4),
                    "src_ip": "192.168.0.1",
                    "dst_ip": "192.168.1.1",
                    "dst_port": "8091",
                    "src_port": "7091",
                    "protocol": "tcp",
                    "ack": 1020,
                    "seq": 0,
                    "flags": "S",
                    "status": "allow",
                    "type": "ALLOW",
                    "max_time": 6,
                    "queue_num": 1,
                }
            ],
        )

        sources = defaultdict(list)
        sources["192.168.0.1:8091:tcp"] = [request1, request2, request3]

        # Action
        old_result, result = clean_sources(sources, get_time(10))

        # Assert
        assert 1 == len(old_result)
        old_ids = [x.id for x in old_result["192.168.0.1:8091:tcp"]]
        assert 1 == len(old_result["192.168.0.1:8091:tcp"])
        self.assertIn(request2.id, old_ids)

        assert 1 == len(result)
        assert 2 == len(result["192.168.0.1:8091:tcp"])
        assert request1.id == result["192.168.0.1:8091:tcp"][0].id
        assert None == result["192.168.0.1:8091:tcp"][0].previous_id
        assert 2 == len(result["192.168.0.1:8091:tcp"][0]._packets)
        assert request3.id == result["192.168.0.1:8091:tcp"][1].id
        assert request1.id == result["192.168.0.1:8091:tcp"][1].previous_id
        assert 1 == len(result["192.168.0.1:8091:tcp"][1]._packets)
