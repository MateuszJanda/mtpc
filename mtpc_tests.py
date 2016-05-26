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
        print str(ord(t) ^ ord(k))
        result.append(ord(t) ^ ord(k))

    return result


class TestCracker(unittest.TestCase):
    def test_crack_whenSameLetterResultIsUnknown(self):
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

    def test_crack2(self):
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
        self.assertItemsEqual(keysCandidates, [[]])

    # def test_crack3(self):
    #     freqTab = {
    #         'a': 0.75,
    #         'b': 0.25
    #     }
    #     charBase = 'ab'
    #     c = mtpc.Cracker(freqTab, charBase)
    #
    #     encTexts = [
    #         encryptOtp(text='a', key='a'),
    #         encryptOtp(text='b', key='a')
    #     ]
    #
    #     keysCandidates = c.run(encTexts)
    #     self.assertItemsEqual(keysCandidates, [[98]])

# python -m unittest discover --pattern=mtpc_tests.py
if __name__ == '__main__':
    unittest.main()