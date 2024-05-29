import unittest
import bittensor as bt


class TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()
        bt.logging.off()

    @classmethod
    def tearDownClass(cls):
        bt.logging.off()
        super(TestCase, cls).tearDownClass()
