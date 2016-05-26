#! /usr/bin/env python
# Author: Mateusz Janda (mateusz.janda@gmail.com)
# Ad maiorem Dei gloriam

import unittest
import mock
from mock import mock_open
from mock import call

import mtpc


class TestDecoder(unittest.TestCase):
    def test_decode(self):
        self.assertTrue(True)

# python -m unittest discover --pattern=mtpc_tests.py
if __name__ == '__main__':
    unittest.main()