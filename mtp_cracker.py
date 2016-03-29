#! /usr/bin/env python2

import base64
import string
import itertools
from collections import Counter
from collections import namedtuple
import operator


def main():
    # encTexts = convertInputToHex()
    encTexts = convertInputToHex2()
    showHexArrays('Trimmed sequences:', encTexts)

    ld = LettersDistribution()
    freqTab = ld.english()
    # ld.info()

    print('')
    d = TtpDecoder(freqTab)
    keysCandidates = d.decode(encTexts)

    # d = Decoder()
    # d.decode(encTexts)

    v = Viewer()
    v.show(encTexts, keysCandidates)


class LettersDistribution:
    ENG_FREQ = {
        'a': 8.167 / 100.0,
        'b': 1.492 / 100.0,
        'c': 2.782 / 100.0,
        'd': 4.253 / 100.0,
        'e': 12.702 / 100.0,
        'f': 2.228 / 100.0,
        'g': 2.015 / 100.0,
        'h': 6.094 / 100.0,
        'i': 6.966 / 100.0,
        'j': 0.153 / 100.0,
        'k': 0.772 / 100.0,
        'l': 4.025 / 100.0,
        'm': 2.406 / 100.0,
        'n': 6.749 / 100.0,
        'o': 7.507 / 100.0,
        'p': 1.929 / 100.0,
        'q': 0.095 / 100.0,
        'r': 5.987 / 100.0,
        's': 6.327 / 100.0,
        't': 9.056 / 100.0,
        'u': 2.758 / 100.0,
        'v': 0.978 / 100.0,
        'w': 2.360 / 100.0,
        'x': 0.150 / 100.0,
        'y': 1.974 / 100.0,
        'z': 0.074 / 100.0,
    }

    def english(self):
        result = {}

        chars = sorted(self.ENG_FREQ.keys())
        for pos, ch1 in enumerate(chars):
            for ch2 in chars[pos+1:]:
                result[(ch1, ch2)] = self.ENG_FREQ[ch1] * self.ENG_FREQ[ch2]

        return result

    def info(self):
        self.infoEnglish()

    def infoEnglish(self):
        print('[i] English - second order letters distribution')
        freqTab = self.english()
        sortedTab = sorted(freqTab.items(), key=operator.itemgetter(1), reverse=True)
        for letters, freq in sortedTab:
            print('[i] ' + str(letters) + ': ' + str(freq))

        freqSum = sum([freq for freq in freqTab.values()])
        print('[i] Sum \'m^m\' probabilities: ' + str(freqSum * 2))

        count_freq_m = sum([f for f in self.ENG_FREQ.values()])
        print('[i] Sum \'m\' probabilities:   ' + str(count_freq_m))
        print('[i] ------')


class Decoder:
    def __init__(self):
        self._xor_keys = {}

    def decode(self, encTexts):
        encTexts = self._prepare(encTexts)

        for num, s1 in enumerate(encTexts):
            for s2 in encTexts[num+1:]:

                keys_per_pos = []
                for c1, c2 in zip(s1, s2):
                    xorResult = c1 ^ c2

                    # get keys
                    if xorResult not in self._xor_keys:
                        self._xor_keys[xorResult] = []

                        for num, m1 in enumerate(string.letters + string.digits):
                            for m2 in (string.letters + string.digits)[num+1:]:
                                if ord(m1) ^ ord(m2) == xorResult:
                                    key1 = c1 ^ c2 ^ ord(m1)
                                    key2 = c1 ^ c2 ^ ord(m2)
                                    self._xor_keys[xorResult].append(key1)
                                    self._xor_keys[xorResult].append(key2)

                    keys_per_pos.append(self._xor_keys[xorResult])

                # check keys in column
                valid_keys_per_pos = []
                for pos, keys in enumerate(keys_per_pos):
                    valid_keys = []
                    for k in keys:
                        for s in encTexts:
                            if chr(s[pos] ^ k) in string.letters + string.digits:
                                valid_keys.append(k)

                    valid_keys_per_pos.append(valid_keys)

        output = ''
        for valid_keys in valid_keys_per_pos:
            output += str(len(valid_keys))

        print 'output ', output

    def _prepare(self, encTexts):
        encTexts = trim_to_equal_length(encTexts)
        showHexArrays('Trimmed sequences:', encTexts)

        return encTexts


class TtpDecoder:
    def __init__(self, freqTab):
        self._analyzer = TtpAnalyzer()
        self._matcher = TtpBestFreqMatcher(freqTab, 0.3)
        self._charBase = string.letters + string.digits

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
    def show(self, encTexts, keysCandidates):
        key = self._get_key(keysCandidates)
        for encText in encTexts:
            output = ''
            for c, k in zip(encText, key):
                if c:
                    output += ''

        print('final: ' + output)

    def _get_key(self, keysCandidates):
        key = [k[0] if k else None for k in keysCandidates]
        return key

if __name__ == '__main__':
    main()