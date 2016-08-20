#! /usr/bin/env python
# Author: Mateusz Janda (mateusz.janda [at] gmail [dot] com)
# Ad maiorem Dei gloriam

"""
Knowledge base:
http://crypto.stackexchange.com/questions/59/taking-advantage-of-one-time-pad-key-reuse
http://www.data-compression.com/english.html

Hamming distance:
https://picoctf.com/crypto_mats/#multi_byte_xor
https://en.wikipedia.org/wiki/Hamming_weight
https://en.wikipedia.org/wiki/Hamming_distance

https://en.wikipedia.org/wiki/Most_common_words_in_English
https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists
"""

from __future__ import division
import itertools
from collections import Counter
from collections import namedtuple
import operator
import string
import math


# http://www.data-compression.com/english.html
ENGLISH_LETTERS = {
    'a': 0.0651738,
    'b': 0.0124248,
    'c': 0.0217339,
    'd': 0.0349835,
    'e': 0.1041442,
    'f': 0.0197881,
    'g': 0.0158610,
    'h': 0.0492888,
    'i': 0.0558094,
    'j': 0.0009033,
    'k': 0.0050529,
    'l': 0.0331490,
    'm': 0.0202124,
    'n': 0.0564513,
    'o': 0.0596302,
    'p': 0.0137645,
    'q': 0.0008606,
    'r': 0.0497563,
    's': 0.0515760,
    't': 0.0729357,
    'u': 0.0225134,
    'v': 0.0082903,
    'w': 0.0171272,
    'x': 0.0013692,
    'y': 0.0145984,
    'z': 0.0007836,
    ' ': 0.1918182,
}


class LettersDistributor:
    @staticmethod
    def distribution(lettersDist=ENGLISH_LETTERS):
        freqTab = {}

        chars = sorted(lettersDist.keys())
        for pos, ch1 in enumerate(chars):
            for ch2 in chars[pos+1:]:
                freqTab[(ch1, ch2)] = lettersDist[ch1] * lettersDist[ch2]

        freqSum = sum([freq for freq in freqTab.values()])
        for lettersPair, freq in freqTab.items():
            freqTab[lettersPair] = freq / freqSum

        return freqTab

    def printDebug(self, lettersDist=ENGLISH_LETTERS):
        print('[i] Second order letters distribution')
        freqTab = self.distribution()
        sortedTab = sorted(freqTab.items(), key=operator.itemgetter(1), reverse=True)
        for letters, freq in sortedTab:
            print('[i] ' + str(letters) + ': ' + str(freq))

        freqSum = sum([freq for freq in freqTab.values()])
        print('[i] Sum \'m1^m2\' probabilities: ' + str(freqSum * 2))

        countFreqM = sum([f for f in lettersDist.values()])
        print('[i] Sum \'m\' probabilities:     ' + str(countFreqM))
        print('[i] ------')


class Cracker:
    def __init__(self, charBase, msgBytesMatcher):
        self._analyzer = EncDataAnalyzer()
        self._charBase = charBase
        self._matchMsgBytesByFreq = msgBytesMatcher

    def run(self, encMsgs):
        encData = self._analyzer.count(encMsgs)
        keys = self._getKeyBytes(encData)
        keys = self._filterKeys(encData, keys)
        return keys

    def _getKeyBytes(self, encData):
        keyCombinations = [self._predictKeyFotTwoEncMsgs(enc1, enc2, encData.xorsFreqs)
                                for pos, enc1 in enumerate(encData.encMsgs)
                                    for enc2 in encData.encMsgs[pos+1:]]

        keys = self._mergeKeyBytesPerPos(keyCombinations)
        return keys

    def _predictKeyFotTwoEncMsgs(self, enc1, enc2, xorsFreqs):
        keys = []
        for c1, c2 in zip(enc1, enc2):
            xorResult = c1 ^ c2
            if xorResult == 0:
                keys.append(set())
            else:
                msgBytes = self._matchMsgBytesByFreq(xorsFreqs[xorResult])
                keys.append(self._matchKeyBytesByMsgBytes(c1, c2, msgBytes))

        return keys

    def _matchKeyBytesByMsgBytes(self, c1, c2, msgBytes):
        keyBytes = [c1 ^ m for m in msgBytes]
        keyBytes += [c2 ^ m for m in msgBytes]
        return set(keyBytes)

    def _mergeKeyBytesPerPos(self, keyCombinations):
        possibleKeys = []
        for comb in keyCombinations:
            for pos, keys in enumerate(comb):
                if pos >= len(possibleKeys):
                    possibleKeys.append(set())
                possibleKeys[pos].update(keys)

        return possibleKeys

    def _filterKeys(self, encData, keysPerPos):
        possibleKeys = []
        for pos, keys in enumerate(keysPerPos):
            possibleKeys.append([])
            for k in keys:
                if self._testColumn(pos, k, encData.encMsgs):
                    possibleKeys[-1].append(k)

        return possibleKeys

    def _testColumn(self, pos, key, encMsgs):
        for encMsg in encMsgs:
            if pos >= len(encMsg):
                continue
            if chr(encMsg[pos] ^ key) not in self._charBase:
                return False

        return True


EncData = namedtuple('EncData', ['encMsgs', 'xorsCounts', 'xorsFreqs'])


class EncDataAnalyzer:
    def __init__(self, verbose=False):
        self._verbose = verbose

    def count(self, encMsgs):
        xorsCounts = self._countXors(encMsgs)
        xorsFreqs = self._countFreq(xorsCounts)

        encData = EncData(encMsgs, xorsCounts, xorsFreqs)
        if self._verbose:
            self._printStats(encData)

        return encData

    def _countXors(self, encMsgs):
        xorsCounts = Counter()
        for num, enc1 in enumerate(encMsgs):
            for enc2 in encMsgs[num+1:]:
                self._countXorsInPair(xorsCounts, enc1, enc2)

        return xorsCounts

    def _countXorsInPair(self, xorsCounts, enc1, enc2):
        for c1, c2 in zip(enc1, enc2):
            xorResult = c1 ^ c2
            # xor-ing same characters give as 0, and we can't determine what this character are
            if xorResult == 0:
                continue
            xorsCounts[xorResult] += 1

    def _countFreq(self, xorsCounts):
        xorsFreqs = {}
        total = sum([count for _, count in xorsCounts.iteritems()])
        for mm, count in xorsCounts.iteritems():
            xorsFreqs[mm] = count / total

        return xorsFreqs

    def _printStats(self, encData):
        print('[i] Frequencies (c1^c2 -> freq):')
        for cc, f in encData.xorsFreqs.items():
            print('[i] ' + '0x' + '{:02x}'.format(cc) + ': ' + str(f))

        print('[i] Unique \'c1^c2\' elements: ' + str(len(encData.xorsCounts)))
        freqSum = sum([f for f in encData.xorsFreqs.values()])
        print('[i] Sum \'c1^c2\' probabilities: ' + str(freqSum))
        print('\n')


class FreqMatcher:
    def __init__(self, freqTab, delta):
        self._freqTab = freqTab
        self._delta = delta

    def match(self, xorFreq):
        probLetters = [letters for letters, f in self._freqTab.items()
                       if (f - self._delta) < xorFreq < (f + self._delta)]
        uniqueLetters = set([ord(l) for l in itertools.chain(*probLetters)])
        return uniqueLetters


class ResultView:
    def show(self, encMsgs, keysCandidates, charBase):
        key = self._getKey(keysCandidates)

        self._printKeysCounts(keysCandidates)
        self._printIndex(key)
        self._printSecretMsgs(encMsgs, key, charBase)
        self._printSecretKey(key, charBase)

    def _getKey(self, keysCandidates):
        key = [k[0] if k else None for k in keysCandidates]
        return key

    def _printKeysCounts(self, keysCandidates):
        print('[*] Keys counts  : ' + ''.join(['*' if len(keys) >= 10 else str(len(keys)) for keys in keysCandidates]))

    def _printSecretMsgs(self, encMsgs, key, charBase):
        for num, encMsg in enumerate(encMsgs):
            output = ''
            for c, k in zip(encMsg, key):
                if k is not None and chr(c ^ k) in string.printable:
                    output += chr(c ^ k)
                else:
                    output += '_'
            space = '  '
            if num >= 10:
                space = ' '
            print('[*] Secret msg' + space + str(num) + ': ' + output)

    def _printIndex(self, key):
        output = ''
        for i in xrange(len(key)):
            output += str(i % 10)
        print('[+] Index        : ' + output)

    def _printSecretKey(self, key, charBase):
        result = ''
        for k in key:
            if k is None:
                result += '_'
            elif chr(k) not in charBase:
                result += '?'
            else:
                result += chr(k)

        print('[*] Secret key   : ' + result)


def crackStream(encMsg):
    print len(encMsg)
    print encMsg

    dh = {}

    for keyLength in range(2, 120):
        dh[keyLength] = hammingDistance(encMsg, keyLength)

        print 'keyLength(' + str(keyLength) + '), HD: ' + str(dh[keyLength])

    sortedTab = sorted(dh.items(), key=operator.itemgetter(1), reverse=True)
    for k, v in sortedTab:
        print('[i] ' + str(k) + ': ' + str(v))

    # print 'DH ' + str(min_dh)
    # print 'KL ' + str(kl_dh)


def hammingDistance(encMsg, keyLength):
    """ Normalized Hamming Distance """
    bits = 0
    block1 = encMsg[:keyLength]
    block2 = encMsg[keyLength:2*keyLength]

    for l in range(keyLength):
        bits += bin(block1[l] ^ block2[l]).count('1')

    # normalized Hamming distance
    return bits / keyLength


def crack(encMsgs):
    freqTab = LettersDistributor.distribution(ENGLISH_LETTERS)
    msgBytesMatcher = FreqMatcher(freqTab, delta=0.3).match

    charBase = string.letters + ' '
    cracker = Cracker(charBase, msgBytesMatcher)
    keysCandidates = cracker.run(encMsgs)

    v = ResultView()
    v.show(encMsgs, keysCandidates, charBase)

