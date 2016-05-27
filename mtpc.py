#! /usr/bin/env python
# Author: Mateusz Janda (mateusz.janda@gmail.com)
# Ad maiorem Dei gloriam

import itertools
from collections import Counter
from collections import namedtuple
import operator
import math


class LettersDistributor:
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

    @staticmethod
    def distribution(lettersDist):
        result = {}

        chars = sorted(lettersDist.keys())
        for pos, ch1 in enumerate(chars):
            for ch2 in chars[pos+1:]:
                result[(ch1, ch2)] = math.fabs(lettersDist[ch1] ** 2 - lettersDist[ch2] ** 2) * 2

        return result

    def info(self):
        print('[i] Second order letters distribution')
        freqTab = self.distribution()
        sortedTab = sorted(freqTab.items(), key=operator.itemgetter(1), reverse=True)
        for letters, freq in sortedTab:
            print('[i] ' + str(letters) + ': ' + str(freq))

        freqSum = sum([freq for freq in freqTab.values()])
        print('[i] Sum \'m1^m2\' probabilities: ' + str(freqSum * 2))

        countFreqM = sum([f for f in self.ENGLISH_LETTERS.values()])
        print('[i] Sum \'m\' probabilities:     ' + str(countFreqM))
        print('[i] ------')


class Cracker:
    def __init__(self, freqTab, charBase):
        self._analyzer = Analyzer()
        self._charBase = charBase
        self._possibleLettersByFreq = FreqMatcher(freqTab, 0.3).match

    def run(self, encTexts):
        encData = self._analyzer.count(encTexts)
        keysPairsCombination = self._keysCombinationsForAllParis(encData)
        keysCombination = self._keysCombinationPerPos(keysPairsCombination)
        return self._filterKeys(encData, keysCombination)

    def _keysCombinationsForAllParis(self, encData):
        keysCombinations = [self._possibleKeysForTwoEncTexts(enc1, enc2, encData.xorsFreqs)
                                for pos, enc1 in enumerate(encData.encTexts)
                                    for enc2 in encData.encTexts[pos+1:]]

        return keysCombinations

    def _possibleKeysForTwoEncTexts(self, enc1, enc2, xorsFreqs):
        keys = []
        for c1, c2 in zip(enc1, enc2):
            xorResult = c1 ^ c2
            if xorResult == 0:
                keys.append(set())
            else:
                letters = self._possibleLettersByFreq(xorsFreqs[xorResult])
                keys.append(self._possibleKeysByLetters(c1, c2, letters))

        return keys

    def _possibleKeysByLetters(self, c1, c2, letters):
        return set([c1 ^ c2 ^ ord(l) for l in letters])

    def _keysCombinationPerPos(self, keysCombinations):
        possibleKeys = []
        for comb in keysCombinations:
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
                if self._testColumn(pos, k, encData.encTexts):
                    possibleKeys[-1].append(k)

        return possibleKeys

    def _testColumn(self, pos, key, encTexts):
        for enc in encTexts:
            if pos >= len(enc):
                continue
            if chr(enc[pos] ^ key) not in self._charBase:
                return False

        return True


EncData = namedtuple('EncData', ['encTexts', 'xorsCounts', 'xorsFreqs'])


class Analyzer:
    def __init__(self, verbose=False):
        self._verbose = verbose

    def count(self, encTexts):
        xorsCounts = self._countXors(encTexts)
        xorsFreqs = self._countFreq(xorsCounts)

        encData = EncData(encTexts, xorsCounts, xorsFreqs)
        if self._verbose:
            self._printStats(encData)

        return encData

    def _countXors(self, encTexts):
        xorsCounts = Counter()
        for num, enc1 in enumerate(encTexts):
            for enc2 in encTexts[num+1:]:
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
            xorsFreqs[mm] = count / float(total)

        return xorsFreqs

    def _printStats(self, encData):
        print('[i] Frequencies (c^c -> freq):')
        for cc, f in encData.xorsFreqs.items():
            print('[i] ' + '0x' + '{:02x}'.format(cc) + ': ' + str(f))

        print('[i] Unique \'c1^c2\' elements: ' + str(len(encData.xorsCounts)))
        freqSum = sum([f for f in encData.xorsFreqs.values()])
        print('[i] Sum \'c1^c2\' probabilities: ' + str(freqSum))
        print('-----')


class FreqMatcher:
    def __init__(self, freqTab, delta):
        self._freqTab = freqTab
        self._delta = delta

    def match(self, xorFreq):
        letters = [letters for letters, f in self._freqTab.items()
                   if xorFreq > (f - self._delta) and xorFreq < (f + self._delta)]
        uniqueLetters = set([l for l in itertools.chain(*letters)])
        return uniqueLetters


class ResultView:
    def show(self, encTexts, keysCandidates, charBase):
        key = self._getKey(keysCandidates)
        for encText in encTexts:
            output = ''
            for c, k in zip(encText, key):
                if k and chr(c ^ k) in charBase:
                    output += chr(c ^ k)
                else:
                    output += '_'

        print('Keys counts:', ''.join(['*' if len(keys) >= 10 else str(len(keys)) for keys in keysCandidates]))
        print('Secret key :', output)

    def _getKey(self, keysCandidates):
        key = [k[0] if k else None for k in keysCandidates]
        return key
