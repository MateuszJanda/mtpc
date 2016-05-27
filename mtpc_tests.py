#! /usr/bin/env python
# Author: Mateusz Janda (mateusz.janda@gmail.com)
# Ad maiorem Dei gloriam

import unittest
import mock
from mock import mock_open
from mock import call

import mtpc


def encryptOtp(text, key):
    result = []
    for t, k in zip(text, key):
        result.append(ord(t) ^ ord(k))

    return result


class TestCracker(unittest.TestCase):
    def test_crack_whenSameLetter_resultIsUnknown(self):
        lettersDist = {
            'a': 1,
        }
        charBase = 'a'
        freqTab = mtpc.LettersDistributor.distribution(lettersDist)
        c = mtpc.Cracker(freqTab, charBase)

        encTexts = [
            encryptOtp(text='a', key='a'),
            encryptOtp(text='a', key='a')
        ]

        keysCandidates = c.run(encTexts)
        self.assertItemsEqual(keysCandidates, [[]])

    def test_crack_whenTextMathLanguagePattern_returnProposal(self):
        lettersDist = {
            'a': 0.75,
            'b': 0.25
        }
        charBase = 'ab'
        freqTab = mtpc.LettersDistributor.distribution(lettersDist)
        c = mtpc.Cracker(freqTab, charBase)

        encTexts = [
            encryptOtp(text='a', key='b'),
            encryptOtp(text='b', key='b')
        ]

        keysCandidates = c.run(encTexts)
        self.assertItemsEqual(keysCandidates, [[ord('a'), ord('b')]])

    def test_crack_whenFreqInDifferentOrder_returnProposal(self):
        lettersDist = {
            'a': 0.25,
            'b': 0.75
        }
        charBase = 'ab'
        freqTab = mtpc.LettersDistributor.distribution(lettersDist)
        c = mtpc.Cracker(freqTab, charBase)

        encTexts = [
            encryptOtp(text='a', key='b'),
            encryptOtp(text='b', key='b')
        ]

        keysCandidates = c.run(encTexts)
        self.assertItemsEqual(keysCandidates, [[ord('a'), ord('b')]])

    def test_crack_whenTextIsLonger(self):
        lettersDist = {
            'a': 0.75,
            'b': 0.25
        }
        charBase = 'ab'
        freqTab = mtpc.LettersDistributor.distribution(lettersDist)
        c = mtpc.Cracker(freqTab, charBase)

        encTexts = [
            encryptOtp(text='aaba', key='abaa'),
            encryptOtp(text='baaa', key='abaa')
        ]

        keysCandidates = c.run(encTexts)
        self.assertItemsEqual(keysCandidates, [[ord('a'), ord('b')],
                                               [],
                                               [ord('a'), ord('b')],
                                               []])

    # def test_crack_whenThreeLettersInDistTable(self):
    #     lettersDist = {
    #         'a': 0.6,
    #         'b': 0.3,
    #         'c': 0.1
    #     }
    #     charBase = 'abc'
    #     freqTab = mtpc.LettersDistributor.distribution(lettersDist)
    #     c = mtpc.Cracker(freqTab, charBase)
    #
    #     encTexts = [
    #         encryptOtp(text='aababbacaa', key='abaaacaabb'),
    #         encryptOtp(text='bcaaabbaaa', key='abaaacaabb')
    #     ]
    #
    #     keysCandidates = c.run(encTexts)
    #     self.assertItemsEqual(keysCandidates, [[ord('a'), ord('b')],
    #                                            [],
    #                                            [ord('a'), ord('b')],
    #                                            [],
    #                                            [],
    #                                            [],
    #                                            [],
    #                                            [],
    #                                            [],
    #                                            []])


class TestLettersDistributor(unittest.TestCase):
    def test(self):
        d = mtpc.LettersDistributor.distribution()
        freqSum = sum([f for f in d.values()])
        self.assertAlmostEqual(freqSum, 1.0)


# python -m unittest discover --pattern=mtpc_tests.py
if __name__ == '__main__':
    unittest.main()