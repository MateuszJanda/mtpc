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
        self._msgBytesMatcher = msgBytesMatcher

    def run(self, encMsgs):
        encData = self._analyzer.count(encMsgs)
        self._msgBytesMatcher.setXorsFreqs(encData.xorsFreqs)
        keys = self._getKeyBytes(encData.encMsgs)
        keys = self._filterKeys(encData, keys)
        return keys

    def _getKeyBytes(self, encMsgs):
        keyCombinations = []
        for pos, enc1 in enumerate(encMsgs):
            for enc2 in encMsgs[pos + 1:]:
                keyCombinations.append(self._predictKeyFotTwoEncMsgs(enc1, enc2))

        keys = self._mergeKeyBytesPerPos(keyCombinations)
        return keys

    def _predictKeyFotTwoEncMsgs(self, enc1, enc2):
        keys = []
        for c1, c2 in zip(enc1, enc2):
            xorResult = c1 ^ c2
            if xorResult == 0:
                keys.append(set())
            else:
                msgBytes = self._msgBytesMatcher.match(xorResult)
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
    def __init__(self, langStats, delta):
        self._freqTab = LettersDistributor.distribution(langStats)
        self._delta = delta
        # Must be set by setXorsFreqs()
        self._xorsFreqs = None

    def setXorsFreqs(self, xorsFreqs):
        self._xorsFreqs = xorsFreqs

    def match(self, xoredBytes):
        freq = self._xorsFreqs[xoredBytes]
        probLetters = [letters for letters, f in self._freqTab.items()
                       if (f - self._delta) < freq < (f + self._delta)]
        uniqueLetters = set([ord(l) for l in itertools.chain(*probLetters)])
        return uniqueLetters


class FreqOrderMatcher:
    def __init__(self, langStats):
        self._freqTab = LettersDistributor.distribution(langStats)
        # Must be set by setXorsFreqs()
        self._orderdFreqs = None

    def setXorsFreqs(self, xorsFreqs):
        sorrtedXorsFreq = sorted(xorsFreqs.items(), key=operator.itemgetter(1), reverse=True)
        sortedLangFreqs = sorted(self._freqTab.items(), key=operator.itemgetter(1), reverse=True)

        self._orderdFreqs = {}
        for z in zip(sorrtedXorsFreq, sortedLangFreqs):
            self._orderdFreqs[z[0][0]] = z[1][0]

    def match(self, xoredBytes):
        uniqueLetters = set([ord(l) for l in self._orderdFreqs[xoredBytes]])
        return uniqueLetters


class ResultView:
    def show(self, encMsgs, keysCandidates, charBase):
        key = self._getKey(keysCandidates)

        self._printKeysCounts(keysCandidates)
        self._printIndex(key)
        self._printSecretMsgs(encMsgs, key)
        self._printSecretKeyStr(key, charBase)
        self._printSecretKeyHex(key)

    def _getKey(self, keysCandidates):
        key = [k[0] if k else None for k in keysCandidates]
        return key

    def _printKeysCounts(self, keysCandidates):
        print('[*] Keys counts: ' + ''.join(['*' if len(keys) >= 10 else str(len(keys)) for keys in keysCandidates]))

    def _printSecretMsgs(self, encMsgs, key):
        for num, encMsg in enumerate(encMsgs):
            output = ''
            for c, k in zip(encMsg, key):
                if k is not None and chr(c ^ k) in string.printable:
                    output += chr(c ^ k)
                else:
                    output += '_'
            space = '.....'
            if num >= 10:
                space = '....'
            print('[*] Plain' + space + str(num) + ': ' + output)

    def _printIndex(self, key):
        output = ''
        for i in xrange(len(key)):
            output += str(i % 10)
        print('[*] Index......: ' + output)

    def _printSecretKeyStr(self, key, charBase):
        result = ''
        for k in key:
            if k is None:
                result += '_'
            elif chr(k) not in charBase:
                result += '?'
            else:
                result += chr(k)

        print('[*] Key (str)..: ' + result)

    def _printSecretKeyHex(self, key):
        result = ''
        for k in key:
            if k is None:
                result += '__'
            else:
                result += hex(k)[2:]

        print('[*] Key (hex)..: ' + result)


def crackStream(encMsg, method='spaces', keyLenMethod='high-bits', langStats=ENGLISH_LETTERS,
                charBase=(string.letters+' _{}'), keyLengthRange=(2, 100), checks=5):
    """
    Crack byte stream, where key was reused more than one (key length is shorter than stream length)
    :param encMsg: each character should be encoded as int
    :param method: cracking method: 'best-freq', 'first-order-freq', 'spaces'
    :param keyLenMethod: method to determine key length: 'hamming', 'high-bits'
    :param langStats: character frequencies distribution in specific language: default ENGLISH_LETTERS
    :param charBase: expected characters in output message
    :param keyLengthRange: key length ranges to check
    :param checks: number of best result to show
    """
    if keyLenMethod == 'hamming':
        proposedKeyLengths = keyLenHammingDist(encMsg, keyLengthRange)
    elif keyLenMethod == 'high-bits':
        proposedKeyLengths = keyLenHighBits(encMsg, keyLengthRange)
    else:
        raise Exception

    for n in range(min(len(proposedKeyLengths), checks)):
        keyLength = proposedKeyLengths[n]
        encMsgChunks = [encMsg[i:keyLength+i] for i in range(0, len(encMsg), keyLength)]
        print('\n[+] Check for key length: ' + str(keyLength))
        crackBlocks(encMsgChunks, method, langStats, charBase)


def keyLenHammingDist(encMsg, keyLengthRange):
    keysHD = {}

    for keyLength in range(*keyLengthRange):
        keysHD[keyLength] = hammingDistance(encMsg, keyLength)

    sortedTab = sorted(keysHD.items(), key=operator.itemgetter(1), reverse=True)
    print('Hamming distance from worst to best:')
    result = []
    for k, hd in sortedTab:
        print('[+] Length [' + str(k) + '] : ' + str(hd))
        result.append(k)

    result.reverse()
    return result


def keyLenHighBits(encMsg, keyLengthRange):
    """ Works only when key contain high bits (key is not build from printable characters) """
    HIGH_BIT_MASK = 0x80
    result = []
    for keyLength in range(*keyLengthRange):
        goodKey = True
        for ix in range(keyLength):
            bytesPerPos = encMsg[ix::keyLength]

            searchedBit = bytesPerPos[0] & HIGH_BIT_MASK
            for b in bytesPerPos:
                if b & HIGH_BIT_MASK != searchedBit:
                    goodKey = False
                    break
            if not goodKey:
                break

        if goodKey:
            result.append(keyLength)

    return result


def hammingDistance(encMsg, keyLength):
    """ Normalized Hamming Distance """
    bits = 0
    block1 = encMsg[:keyLength]
    block2 = encMsg[keyLength:2*keyLength]

    for l in range(keyLength):
        bits += bin(block1[l] ^ block2[l]).count('1')

    # normalized Hamming distance
    return bits / keyLength


def crackBlocks(encMsgs, method='spaces', langStats=ENGLISH_LETTERS, charBase=(string.letters+' _{}')):
    """
    Crack blocks of bytes stream, where key was reused for each block.
    :param encMsgs: encoded messages each character should be encoded as int
    :param method: cracking method: 'best-freq', 'first-order-freq', 'spaces'
    :param langStats: character frequencies distribution in specific language: default ENGLISH_LETTERS
    :param charBase: expected characters in output message
    """
    if method == 'best-freq':
        msgBytesMatcher = FreqMatcher(langStats, delta=0.3)
        cracker = Cracker(charBase, msgBytesMatcher)
        keysCandidates = cracker.run(encMsgs)
    elif method == 'first-order-freq':
        msgBytesMatcher = FreqOrderMatcher(langStats)
        cracker = Cracker(charBase, msgBytesMatcher)
        keysCandidates = cracker.run(encMsgs)
    elif method == 'spaces':
        keysCandidates = findKeyByMostCommonChar(encMsgs)
    else:
        raise Exception

    v = ResultView()
    v.show(encMsgs, keysCandidates, charBase)


def findKeyByMostCommonChar(encMsg, mostCommonCh=' '):
    """ Find key by most common character (be default space) """
    counters = []
    for e in encMsg:
        for ix in range(len(e)):
            if ix == len(counters):
                counters.append(Counter())
            counters[ix][e[ix]] += 1

    mostCommonByte = ord(mostCommonCh)
    keysCandidates = []
    for ix in range(len(counters)):
        keysCandidates.append([counters[ix].most_common(1)[0][0] ^ mostCommonByte])

    return keysCandidates



