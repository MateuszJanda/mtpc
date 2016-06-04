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
        freqTab = mtpc.LettersDistributor.distribution(lettersDist)
        matcher = mtpc.FreqMatcher(freqTab, delta=0.15).match
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
        freqTab = mtpc.LettersDistributor.distribution(lettersDist)
        matcher = mtpc.FreqMatcher(freqTab, delta=0.15).match
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
        freqTab = mtpc.LettersDistributor.distribution(lettersDist)
        matcher = mtpc.FreqMatcher(freqTab, delta=0.15).match
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
        freqTab = mtpc.LettersDistributor.distribution(lettersDist)
        matcher = mtpc.FreqMatcher(freqTab, delta=0.15).match
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
        freqTab = mtpc.LettersDistributor.distribution(lettersDist)
        matcher = mtpc.FreqMatcher(freqTab, delta=0.51).match
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
        freqTab = mtpc.LettersDistributor.distribution(lettersDist)
        matcher = mtpc.FreqMatcher(freqTab, delta=0.15).match
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


class TestLettersDistributor(unittest.TestCase):
    def test(self):
        d = mtpc.LettersDistributor.distribution()
        freqSum = sum([f for f in d.values()])
        self.assertAlmostEqual(freqSum, 1.0)


if __name__ == '__main__':
    """ python -m unittest discover --pattern=mtpc_tests.py """
    unittest.main()