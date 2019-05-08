#! /usr/bin/env python3

"""
Author: Mateusz Janda <mateusz janda at gmail com>
Site: github.com/MateuszJanda
Ad maiorem Dei gloriam
"""

import unittest
from unittest import mock
from unittest.mock import mock_open
from unittest.mock import call

import mtpc


def encrypt_otp(msg, key):
    result = []
    for m, k in zip(msg, key):
        result.append(ord(m) ^ ord(k))

    return result


def encrypt_otp_int(msg, key):
    result = []
    for m, k in zip(msg, key):
        result.append(ord(m) ^ k)

    return result


class TestCracker(unittest.TestCase):
    def test_crack_whenSameLetter_resultIsUnknown(self):
        letters_dist = {
            'a': 1,
        }
        char_base = 'a'
        matcher = mtpc.FreqMatcher(letters_dist, delta=0.15)
        c = mtpc.Cracker(char_base, matcher)

        enc_msgs = [
            encrypt_otp(msg='a', key='a'),
            encrypt_otp(msg='a', key='a')
        ]

        keys_candidates = c.run(enc_msgs)
        self.assertCountEqual(keys_candidates, [[None]])

    def test_crack_whenTextMathLanguagePattern_returnProposal(self):
        letters_dist = {
            'a': 0.75,
            'b': 0.25
        }
        char_base = 'ab'
        matcher = mtpc.FreqMatcher(letters_dist, delta=0.15)
        c = mtpc.Cracker(char_base, matcher)

        enc_msgs = [
            encrypt_otp(msg='a', key='b'),
            encrypt_otp(msg='b', key='b')
        ]

        keys_candidates = c.run(enc_msgs)
        self.assertCountEqual(keys_candidates, [[ord('a'), ord('b')]])

    def test_crack_whenFreqInDifferentOrder_returnProposal(self):
        letters_dist = {
            'a': 0.25,
            'b': 0.75
        }
        char_base = 'ab'
        matcher = mtpc.FreqMatcher(letters_dist, delta=0.15)
        c = mtpc.Cracker(char_base, matcher)

        enc_msgs = [
            encrypt_otp(msg='a', key='b'),
            encrypt_otp(msg='b', key='b')
        ]

        keys_candidates = c.run(enc_msgs)
        self.assertCountEqual(keys_candidates, [[ord('a'), ord('b')]])

    def test_crack_whenTextIsLonger(self):
        letters_dist = {
            'a': 0.75,
            'b': 0.25
        }
        char_base = 'ab'
        matcher = mtpc.FreqMatcher(letters_dist, delta=0.15)
        c = mtpc.Cracker(char_base, matcher)

        enc_msgs = [
            encrypt_otp(msg='aaba', key='abaa'),
            encrypt_otp(msg='baaa', key='abaa')
        ]

        keys_candidates = c.run(enc_msgs)
        self.assertCountEqual(keys_candidates, [[ord('a'), ord('b')],
                                                [None],
                                                [ord('a'), ord('b')],
                                                [None]])

    def test_crack_whenCharBaseIsLargerThanKeysInDistributionTable(self):
        letters_dist = {
            'a': 0.75,
            'b': 0.25
        }
        char_base = 'abc'
        matcher = mtpc.FreqMatcher(letters_dist, delta=0.51)
        c = mtpc.Cracker(char_base, matcher)

        enc_msgs = [
            encrypt_otp(msg='aaca', key='abaa'),
            encrypt_otp(msg='baaa', key='abaa')
        ]

        keys_candidates = c.run(enc_msgs)
        self.assertCountEqual(keys_candidates, [[ord('a'), ord('b')],
                                                [None],
                                                [ord('a'), ord('c')],
                                                [None]])

    def test_crack_whenThreeLettersInDistTable(self):
        letters_dist = {
            'a': 0.6,
            'b': 0.3,
            'c': 0.1
        }
        char_base = 'abc'
        matcher = mtpc.FreqMatcher(letters_dist, delta=0.15)
        c = mtpc.Cracker(char_base, matcher)

        enc_msgs = [
            encrypt_otp(msg='aababbacaa', key='abaaacaabb'),
            encrypt_otp(msg='bcaaabbaaa', key='abaaacaabb')
        ]

        keys_candidates = c.run(enc_msgs)
        self.assertCountEqual(keys_candidates, [[ord('a'), ord('b')],
                                                [96, ord('b')],
                                                [ord('a'), ord('b')],
                                                [None],
                                                [ord('a'), ord('b')],
                                                [None],
                                                [ord('a'), ord('b')],
                                                [ord('a'), ord('c')],
                                                [None],
                                                [None]])


class TestCrackStream(unittest.TestCase):
    def test_hammingDistance(self):
        enc_msg = '9887702584b28e6c71b7bb997e7195bf817a3884bf98353889fa9f7d34c7bc8a7625c7ae837425cbfa9e7b258e' \
                  'b6cb73308ea8876c7195bf88703f93b69239718eaecb623094fa9b673e85bb897928c798997c2586b3853222c7' \
                  'b88e6625c7b18e6525c7a98e762382aec535058fb398353894fa89703286af98707188bccb613982fa98703295' \
                  'bf886c7194af99673e92b48f7c3f80fa8a793dc7ae83707186b99f7c278eae827022c7b98a67238ebf8f353e89' \
                  'fa83702382fa8f60238eb48c350688a8877171b0bb99350590b5cb623094fa84737191b39f743dc7b386653e95' \
                  'ae8a7b3282fa9f7a7188af99353f86ae827a3f86b6cb663484af997c259efa8a7b35c7af8761388abb9f707191' \
                  'b388613e95a3c5'

        e = [b for b in bytes.fromhex(enc_msg)]

        self.assertAlmostEqual(mtpc.hamming_distance(e, 5), 3)
        self.assertAlmostEqual(mtpc.hamming_distance(e, 2), 3.5)
        self.assertAlmostEqual(mtpc.hamming_distance(e, 3), 3.67, delta=0.01)
        self.assertAlmostEqual(mtpc.hamming_distance(e, 6), 3.83, delta=0.01)

    def test_keyLenHighBits(self):
        enc_msg = encrypt_otp_int(msg='aababcaa', key=[0x00, 0xff, 0xff, 0x00, 0xff, 0xff, 0x00, 0xff])
        self.assertCountEqual(mtpc.key_len_high_bits(enc_msg, key_len_range=range(1, 4)), [3])


class TestCrackBlock(unittest.TestCase):
    def test_findKeyByMostCommonChar(self):
        enc_msgs = [
            encrypt_otp(msg=' a a', key='vxyz'),
            encrypt_otp(msg='  ab', key='vxyz'),
            encrypt_otp(msg='b ab', key='vxyz')
        ]

        keys_candidates = mtpc.find_key_by_most_common_char(enc_msgs)
        self.assertCountEqual(keys_candidates, [[ord('v')],
                                                [ord('x')],
                                                [ord('a') ^ ord('y') ^ ord(' ')],
                                                [ord('b') ^ ord('z') ^ ord(' ')]])


class TestLettersDistributor(unittest.TestCase):
    def test_distribution(self):
        d = mtpc.LettersDistributor.distribution()
        freq_sum = sum([f for f in d.values()])
        self.assertAlmostEqual(freq_sum, 1.0)


if __name__ == '__main__':
    """ python -m unittest discover --pattern=mtpc_tests.py """
    unittest.main()
