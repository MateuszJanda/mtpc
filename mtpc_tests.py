#! /usr/bin/env python
# Author: Mateusz Janda (mateusz.janda [at] gmail [dot] com)
# Ad maiorem Dei gloriam

import unittest
import mock
from mock import mock_open
from mock import call

import mtpc


def encryptOtp(msg, key):
    result = []
    for m, k in zip(msg, key):
        result.append(ord(m) ^ ord(k))

    return result


class TestCracker(unittest.TestCase):
    def test_crack_whenSameLetter_resultIsUnknown(self):
        lettersDist = {
            'a': 1,
        }
        charBase = 'a'
        matcher = mtpc.FreqMatcher(lettersDist, delta=0.15).match
        c = mtpc.Cracker(charBase, matcher)

        encMsgs = [
            encryptOtp(msg='a', key='a'),
            encryptOtp(msg='a', key='a')
        ]

        keysCandidates = c.run(encMsgs)
        self.assertItemsEqual(keysCandidates, [[]])

    def test_crack_whenTextMathLanguagePattern_returnProposal(self):
        lettersDist = {
            'a': 0.75,
            'b': 0.25
        }
        charBase = 'ab'
        matcher = mtpc.FreqMatcher(lettersDist, delta=0.15).match
        c = mtpc.Cracker(charBase, matcher)

        encMsgs = [
            encryptOtp(msg='a', key='b'),
            encryptOtp(msg='b', key='b')
        ]

        keysCandidates = c.run(encMsgs)
        self.assertItemsEqual(keysCandidates, [[ord('a'), ord('b')]])

    def test_crack_whenFreqInDifferentOrder_returnProposal(self):
        lettersDist = {
            'a': 0.25,
            'b': 0.75
        }
        charBase = 'ab'
        matcher = mtpc.FreqMatcher(lettersDist, delta=0.15).match
        c = mtpc.Cracker(charBase, matcher)

        encMsgs = [
            encryptOtp(msg='a', key='b'),
            encryptOtp(msg='b', key='b')
        ]

        keysCandidates = c.run(encMsgs)
        self.assertItemsEqual(keysCandidates, [[ord('a'), ord('b')]])

    def test_crack_whenTextIsLonger(self):
        lettersDist = {
            'a': 0.75,
            'b': 0.25
        }
        charBase = 'ab'
        matcher = mtpc.FreqMatcher(lettersDist, delta=0.15).match
        c = mtpc.Cracker(charBase, matcher)

        encMsgs = [
            encryptOtp(msg='aaba', key='abaa'),
            encryptOtp(msg='baaa', key='abaa')
        ]

        keysCandidates = c.run(encMsgs)
        self.assertItemsEqual(keysCandidates, [[ord('a'), ord('b')],
                                               [],
                                               [ord('a'), ord('b')],
                                               []])

    def test_crack_whenCharBaseIsLargerThanKeysInDistributionTable(self):
        lettersDist = {
            'a': 0.75,
            'b': 0.25
        }
        charBase = 'abc'
        matcher = mtpc.FreqMatcher(lettersDist, delta=0.51).match
        c = mtpc.Cracker(charBase, matcher)

        encMsgs = [
            encryptOtp(msg='aaca', key='abaa'),
            encryptOtp(msg='baaa', key='abaa')
        ]

        keysCandidates = c.run(encMsgs)
        self.assertItemsEqual(keysCandidates, [[ord('a'), ord('b')],
                                               [],
                                               [ord('a'), ord('c')],
                                               []])

    def test_crack_whenThreeLettersInDistTable(self):
        lettersDist = {
            'a': 0.6,
            'b': 0.3,
            'c': 0.1
        }
        charBase = 'abc'
        matcher = mtpc.FreqMatcher(lettersDist, delta=0.15).match
        c = mtpc.Cracker(charBase, matcher)

        encMsgs = [
            encryptOtp(msg='aababbacaa', key='abaaacaabb'),
            encryptOtp(msg='bcaaabbaaa', key='abaaacaabb')
        ]

        keysCandidates = c.run(encMsgs)
        self.assertItemsEqual(keysCandidates, [[ord('a'), ord('b')],
                                               [96, ord('b')],
                                               [ord('a'), ord('b')],
                                               [],
                                               [ord('a'), ord('b')],
                                               [],
                                               [ord('a'), ord('b')],
                                               [ord('a'), ord('c')],
                                               [],
                                               []])


class TestCrackStream(unittest.TestCase):
    def test_hammingDistance(self):
        encMsg = '9887702584b28e6c71b7bb997e7195bf817a3884bf98353889fa9f7d34c7bc8a7625c7ae837425cbfa9e7b258e' \
                 'b6cb73308ea8876c7195bf88703f93b69239718eaecb623094fa9b673e85bb897928c798997c2586b3853222c7' \
                 'b88e6625c7b18e6525c7a98e762382aec535058fb398353894fa89703286af98707188bccb613982fa98703295' \
                 'bf886c7194af99673e92b48f7c3f80fa8a793dc7ae83707186b99f7c278eae827022c7b98a67238ebf8f353e89' \
                 'fa83702382fa8f60238eb48c350688a8877171b0bb99350590b5cb623094fa84737191b39f743dc7b386653e95' \
                 'ae8a7b3282fa9f7a7188af99353f86ae827a3f86b6cb663484af997c259efa8a7b35c7af8761388abb9f707191' \
                 'b388613e95a3c5'

        e = [ord(ch) for ch in encMsg.decode('hex')]

        self.assertAlmostEqual(mtpc.hammingDistance(e, 5), 3)
        self.assertAlmostEqual(mtpc.hammingDistance(e, 2), 3.5)
        self.assertAlmostEqual(mtpc.hammingDistance(e, 3), 3.67, delta=0.01)
        self.assertAlmostEqual(mtpc.hammingDistance(e, 6), 3.83, delta=0.01)


class TestLettersDistributor(unittest.TestCase):
    def test(self):
        d = mtpc.LettersDistributor.distribution()
        freqSum = sum([f for f in d.values()])
        self.assertAlmostEqual(freqSum, 1.0)


if __name__ == '__main__':
    """ python -m unittest discover --pattern=mtpc_tests.py """
    unittest.main()