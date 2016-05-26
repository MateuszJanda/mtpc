#! /usr/bin/env python
# Author: Mateusz Janda (mateusz.janda@gmail.com)
# Ad maiorem Dei gloriam

import base64
import string
import itertools
from collections import Counter
from collections import namedtuple
import operator


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

    def distribution(self):
        result = {}

        chars = sorted(self.ENGLISH_LETTERS.keys())
        for pos, ch1 in enumerate(chars):
            for ch2 in chars[pos+1:]:
                result[(ch1, ch2)] = self.ENGLISH_LETTERS[ch1] * self.ENGLISH_LETTERS[ch2]

        return result

    def info(self):
        print('[i] English - second order letters distribution')
        freqTab = self.distribution()
        sortedTab = sorted(freqTab.items(), key=operator.itemgetter(1), reverse=True)
        for letters, freq in sortedTab:
            print('[i] ' + str(letters) + ': ' + str(freq))

        freqSum = sum([freq for freq in freqTab.values()])
        print('[i] Sum \'m^m\' probabilities: ' + str(freqSum * 2))

        countFreqM = sum([f for f in self.ENGLISH_LETTERS.values()])
        print('[i] Sum \'m\' probabilities:   ' + str(countFreqM))
        print('[i] ------')


class TtpDecoder:
    def __init__(self, freqTab, charBase):
        self._analyzer = TtpAnalyzer()
        self._matcher = TtpBestFreqMatcher(freqTab, 0.3)
        self._charBase = charBase

    def decode(self, encTexts):
        ttpData = self._analyzer.count(encTexts)
        keysPairsCombination = self._keysCombinationsForAllParis(ttpData)
        keysCombination = self._keysCombinationPerPos(keysPairsCombination)
        return self._filterKeys(ttpData, keysCombination)

    def _keysCombinationsForAllParis(self, ttpData):
        keysCombinations = [self._possibleKeysForTwoEncTexts(enc1, enc2, ttpData.xorsFreqs)
                                for pos, enc1 in enumerate(ttpData.encTexts)
                                    for enc2 in ttpData.encTexts[pos+1:]]

        return keysCombinations

    def _possibleKeysForTwoEncTexts(self, enc1, enc2, xorsFreqs):
        keys = []
        for c1, c2 in zip(enc1, enc2):
            xorResult = c1 ^ c2
            if xorResult == 0:
                keys.append(set())
            else:
                letters = self._matcher.possibleLettersByFreq(xorsFreqs[xorResult])
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

    def _filterKeys(self, ttpData, keysPerPos):
        possibleKeys = []
        for pos, keys in enumerate(keysPerPos):
            possibleKeys.append([])
            for k in keys:
                if self._testColumn(pos, k, ttpData.encTexts):
                    possibleKeys[-1].append(k)

        print 'output ', ''.join([str(len(keys)) for keys in possibleKeys])

        return possibleKeys

    def _testColumn(self, pos, key, encTexts):
        for enc in encTexts:
            if pos >= len(enc):
                continue
            if chr(enc[pos] ^ key) not in self._charBase:
                return False

        return True


TtpData = namedtuple('TtpData', ['encTexts', 'xorsCounts', 'xorsFreqs'])


class TtpAnalyzer:
    def __init__(self, verbose=False):
        self._verbose = verbose

    def count(self, encTexts):
        xorsCounts = self._countXors(encTexts)
        xorsFreqs = self._countFreq(xorsCounts)

        ttpData = TtpData(encTexts, xorsCounts, xorsFreqs)
        if self._verbose:
            self._printStats(ttpData)

        return ttpData

    def _countXors(self, encTexts):
        xorsCounts = Counter()
        for num, enc1 in enumerate(encTexts):
            for enc2 in encTexts[num+1:]:
                self._countXorsInPair(xorsCounts, enc1, enc2)

        return xorsCounts

    def _countXorsInPair(self, xorsCounts, enc1, enc2):
        for c1, c2 in zip(enc1, enc2):
            xorResult = c1 ^ c2
            # xor-owanie tych samych znakow daje 0 i nie mozna stwierdzic co to za znaki
            if xorResult == 0:
                continue
            xorsCounts[xorResult] += 1

    def _countFreq(self, xorsCounts):
        xorsFreqs = {}
        total = sum([count for _, count in xorsCounts.iteritems()])
        for mm, count in xorsCounts.iteritems():
            xorsFreqs[mm] = count / float(total)

        return xorsFreqs

    def _printStats(self, ttpData):
        print('[i] Frequencies (c^c -> freq):')
        for cc, f in ttpData.xorsFreqs.items():
            print('[i] ' + '0x' + '{:02x}'.format(cc) + ': ' + str(f))

        print('[i] Unique \'c^c\' elements: ' + str(len(ttpData.xorsCounts)))
        freqSum = sum([f for f in ttpData.xorsFreqs.values()])
        print('[i] Sum \'c^c\' probabilities: ' + str(freqSum))
        print('-----')


class TtpBestFreqMatcher:
    def __init__(self, freqTab, delta):
        self._freqTab = freqTab
        self._delta = delta

    def possibleLettersByFreq(self, xorFreq):
        letters = [letters for letters, f in self._freqTab.items()
                   if xorFreq > (f - self._delta) and xorFreq < (f + self._delta)]
        uniqueLetters = set([l for l in itertools.chain(*letters)])
        return uniqueLetters


def showHexArrays(text, encTexts):
    print(text)
    for e in encTexts:
        print(['0x' + '{:02x}'.format(x) for x in e])


class Viewer:
    def show(self, encTexts, keysCandidates, charBase):
        key = self._get_key(keysCandidates)
        for encText in encTexts:
            output = ''
            for c, k in zip(encText, key):
                if k and chr(c ^ k) in charBase:
                    output += chr(c ^ k)
                else:
                    output += '_'

        print('final: ' + output)

    def _get_key(self, keysCandidates):
        key = [k[0] if k else None for k in keysCandidates]
        return key

if __name__ == '__main__':
    main()
