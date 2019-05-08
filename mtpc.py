#! /usr/bin/env python3

"""
Author: Mateusz Janda <mateusz janda at gmail com>
Site: github.com/MateuszJanda
"""

"""
References:
http://crypto.stackexchange.com/questions/59/taking-advantage-of-one-time-pad-key-reuse
http://www.data-compression.com/english.html

Hamming distance:
https://picoctf.com/crypto_mats/#multi_byte_xor
https://en.wikipedia.org/wiki/Hamming_weight
https://en.wikipedia.org/wiki/Hamming_distance

https://en.wikipedia.org/wiki/Most_common_words_in_English
https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists
"""

import itertools
from collections import Counter
from collections import namedtuple
import operator
import string


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
    """ Calculate occurrence frequencies for each pairs of letters (e.g. 'a' ^ 'b') """
    @staticmethod
    def distribution(letters_dist=ENGLISH_LETTERS):
        freq_tab = {}

        chars = sorted(letters_dist.keys())
        for pos, ch1 in enumerate(chars):
            for ch2 in chars[pos+1:]:
                freq_tab[(ch1, ch2)] = letters_dist[ch1] * letters_dist[ch2]

        freq_sum = sum([freq for freq in freq_tab.values()])
        for letters_pair, freq in freq_tab.items():
            freq_tab[letters_pair] = freq / freq_sum

        return freq_tab

    def print_debug(self, letters_dist=ENGLISH_LETTERS):
        print('[i] Second order letters distribution')
        freq_tab = self.distribution()
        sorted_tab = sorted(freq_tab.items(), key=operator.itemgetter(1), reverse=True)
        for letters, freq in sorted_tab:
            print('[i] ' + str(letters) + ': ' + str(freq))

        freq_sum = sum([freq for freq in freq_tab.values()])
        print('[i] Sum \'m1^m2\' probabilities: ' + str(freq_sum * 2))

        count_freq_m = sum([f for f in letters_dist.values()])
        print('[i] Sum \'m\' probabilities:     ' + str(count_freq_m))
        print('[i] ------')


class Cracker:
    def __init__(self, char_base, msg_bytes_matcher):
        self._analyzer = EncDataAnalyzer()
        self._char_base = char_base
        self._msg_bytes_matcher = msg_bytes_matcher

    def run(self, enc_msgs):
        enc_data = self._analyzer.count(enc_msgs)
        self._msg_bytes_matcher.set_xors_freqs(enc_data.xors_freqs)
        keys = self._get_key_bytes(enc_data.enc_msgs)
        keys = self._filter_keys(enc_data, keys)
        return keys

    def _get_key_bytes(self, enc_msgs):
        key_combinations = []
        for pos, enc1 in enumerate(enc_msgs):
            for enc2 in enc_msgs[pos + 1:]:
                key_combinations.append(self._predict_key_for_two_enc_msgs(enc1, enc2))

        keys = self._merge_key_bytes_per_pos(key_combinations)
        return keys

    def _predict_key_for_two_enc_msgs(self, enc1, enc2):
        keys = []
        for c1, c2 in zip(enc1, enc2):
            xor_result = c1 ^ c2
            if xor_result == 0:
                keys.append(set())
            else:
                msg_bytes = self._msg_bytes_matcher.match(xor_result)
                keys.append(self._match_key_bytes_by_msg_bytes(c1, c2, msg_bytes))

        return keys

    def _match_key_bytes_by_msg_bytes(self, c1, c2, msg_bytes):
        key_bytes = [c1 ^ m for m in msg_bytes]
        key_bytes += [c2 ^ m for m in msg_bytes]
        return set(key_bytes)

    def _merge_key_bytes_per_pos(self, key_combinations):
        possible_keys = []
        for comb in key_combinations:
            for pos, keys in enumerate(comb):
                if pos >= len(possible_keys):
                    possible_keys.append(set())
                possible_keys[pos].update(keys)

        return possible_keys

    def _filter_keys(self, enc_data, keys_per_pos):
        possible_keys = []
        for pos, keys in enumerate(keys_per_pos):
            possible_keys.append([])
            for k in keys:
                if self._test_column(pos, k, enc_data.enc_msgs):
                    possible_keys[-1].append(k)

            # If no proposals for this position, replace it by [None] (easier to use be itertools.product)
            if not possible_keys[-1]:
                possible_keys[-1] = [None]

        return possible_keys

    def _test_column(self, pos, key, enc_msgs):
        for enc_msg in enc_msgs:
            if pos >= len(enc_msg):
                continue
            if chr(enc_msg[pos] ^ key) not in self._char_base:
                return False

        return True


EncData = namedtuple('EncData', ['enc_msgs', 'xors_counts', 'xors_freqs'])


class EncDataAnalyzer:
    def __init__(self, verbose=False):
        self._verbose = verbose

    def count(self, enc_msgs):
        xors_counts = self._count_xors(enc_msgs)
        xors_freqs = self._count_freq(xors_counts)

        enc_data = EncData(enc_msgs, xors_counts, xors_freqs)
        if self._verbose:
            self._print_stats(enc_data)

        return enc_data

    def _count_xors(self, enc_msgs):
        xors_counts = Counter()
        for num, enc1 in enumerate(enc_msgs):
            for enc2 in enc_msgs[num+1:]:
                self._count_xors_in_pair(xors_counts, enc1, enc2)

        return xors_counts

    def _count_xors_in_pair(self, xors_counts, enc1, enc2):
        for c1, c2 in zip(enc1, enc2):
            xor_result = c1 ^ c2
            # xor-ing same characters give as 0, and we can't determine what this character are
            if xor_result == 0:
                continue
            xors_counts[xor_result] += 1

    def _count_freq(self, xors_counts):
        """ Calculate frequency for each bytes pairs in encrypted message. """
        xors_freqs = {}
        total = sum([count for _, count in xors_counts.items()])
        for mm, count in xors_counts.items():
            xors_freqs[mm] = count / total

        return xors_freqs

    def _print_stats(self, enc_data):
        print('[i] Frequencies (c1^c2 -> freq):')
        for cc, f in enc_data.xors_freqs.items():
            print('[i] ' + '0x' + '{:02x}'.format(cc) + ': ' + str(f))

        print('[i] Unique \'c1^c2\' elements: ' + str(len(enc_data.xors_counts)))
        freq_sum = sum([f for f in enc_data.xors_freqs.values()])
        print('[i] Sum \'c1^c2\' probabilities: ' + str(freq_sum))
        print('\n')


class FreqMatcher:
    """ Match xor-ed value (of two encrypted bytes) with pair of letters.
    xor-ed value should be calculated as: xor_value=e1^e2=(k^m1)^(k^m2)=m1^m2
    - where e1 and e2 are two bytes from two encrypted messages at the same
      position
    - k is byte of secret key at given position
    - m1, m2 are true not encrypted bytes from two messages at the same position
    Matching is performed by frequency search with some delta. """
    def __init__(self, lang_stats, delta):
        self._freq_tab = LettersDistributor.distribution(lang_stats)
        self._delta = delta
        # Must be set by set_xors_freqs()
        self._xors_freqs = None

    def set_xors_freqs(self, xors_freqs):
        self._xors_freqs = xors_freqs

    def match(self, xored_value):
        """
        :param xored_value: xor of bytes (at the same position) from two encrypted messages
        """
        freq = self._xors_freqs[xored_value]
        prob_letters = [letters for letters, f in self._freq_tab.items()
                        if (f - self._delta) < freq < (f + self._delta)]
        unique_letters = set([ord(l) for l in itertools.chain(*prob_letters)])
        return unique_letters


class FreqOrderMatcher:
    """
    Match xor-ed value (of two encrypted bytes) with pair of letters.
    xor-ed value should be calculated as: xor_value=e1^e2=(k^m1)^(k^m2)=m1^m2
    - where e1 and e2 are two bytes from two encrypted messages at the same
      position
    - k is byte of secret key at given position
    - m1, m2 are true not encrypted bytes from two messages at the same position
    Both xor-ed values table and letters table, are first sorted by their
    frequencies, and then linked to each other - most common xor-ed value with
    most common pairs, and so on.
    """
    def __init__(self, lang_stats):
        self._freq_tab = LettersDistributor.distribution(lang_stats)
        # Must be set by set_xors_freqs()
        self._orderd_freqs = None

    def set_xors_freqs(self, xors_freqs):
        """ Assign to each xor-ed value (of two encrypted message) corresponding
        letters pair (deducted from letters frequency table for specific language. """
        sorrted_xors_freq = sorted(xors_freqs.items(), key=operator.itemgetter(1), reverse=True)
        sorted_lang_freqs = sorted(self._freq_tab.items(), key=operator.itemgetter(1), reverse=True)

        self._orderd_freqs = {}
        for z in zip(sorrted_xors_freq, sorted_lang_freqs):
            self._orderd_freqs[z[0][0]] = z[1][0]

    def match(self, xored_value):
        """
        :param xored_value: xor of bytes (at the same position) from two encrypted messages
        """
        unique_letters = set([ord(l) for l in self._orderd_freqs[xored_value]])
        return unique_letters


class ResultView:
    def show(self, enc_msgs, keys_candidates, char_base, checks=1):
        self._print_num_of_combinations(keys_candidates)
        for num, key in enumerate(itertools.product(*keys_candidates)):
            if num >= checks:
                break
            self._print_keys_counts(keys_candidates)
            self._print_index(key)
            self._print_secret_msgs(enc_msgs, key)
            self._print_secret_key_str(key, char_base)
            self._print_secret_key_hex(key)
            self._print_separator()

    def _print_num_of_combinations(self, keys_candidates):
        num_of_combinations = 1
        for keys in keys_candidates:
            if not keys:
                continue
            num_of_combinations *= len(keys)
        print('Number of combinations: ' + str(num_of_combinations))

    def _print_keys_counts(self, keys_candidates):
        print('Keys counts: ' + ''.join(['*' if len(keys) >= 10 else str(len(keys)) for keys in keys_candidates]))

    def _print_secret_msgs(self, enc_msgs, key):
        for num, enc_msg in enumerate(enc_msgs):
            output = ''
            for c, k in zip(enc_msg, key):
                if k is not None and chr(c ^ k) in string.digits + string.ascii_letters + string.punctuation + ' ':
                    output += chr(c ^ k)
                else:
                    output += '_'
            space = '.....'
            if num >= 10:
                space = '....'
            print('Plain' + space + str(num) + ': ' + output)

    def _print_index(self, key):
        output = ''
        for i in range(len(key)):
            output += str(i % 10)
        print('Index......: ' + output)

    def _print_secret_key_str(self, key, char_base):
        result = ''
        for k in key:
            if k is None:
                result += '_'
            elif chr(k) not in char_base:
                result += '?'
            else:
                result += chr(k)

        print('Key (str)..: ' + result)

    def _print_secret_key_hex(self, key):
        result = ''
        for k in key:
            if k is None:
                result += '__'
            else:
                result += hex(k)[2:]

        print('Key (hex)..: ' + result)

    def _print_separator(self):
        print('End check')


def crack_stream(enc_msg, method='spaces', key_len_method='high-bits', lang_stats=ENGLISH_LETTERS,
                 char_base=string.ascii_letters+" '", key_len_range=range(2, 100), checks=5):
    """
    Crack byte stream, where key was reused more than one (key length is shorter than stream length)
    :param enc_msg: encoded message. Each character should be encoded as int
    :param method: cracking method: 'best-freq', 'first-order-freq', 'spaces'
    :param key_len_method: method to determine key length: 'hamming', 'high-bits'
    :param lang_stats: character frequencies distribution in specific language: default ENGLISH_LETTERS
    :param char_base: expected characters in output message
    :param key_len_range: key length ranges to check
    :param checks: number of best result to show
    """
    if key_len_method == 'hamming':
        proposed_key_lengths = key_len_hamming_dist(enc_msg, key_len_range)
    elif key_len_method == 'high-bits':
        proposed_key_lengths = key_len_high_bits(enc_msg, key_len_range)
    else:
        raise Exception

    for n in range(min(len(proposed_key_lengths), checks)):
        key_length = proposed_key_lengths[n]
        enc_msg_chunks = [enc_msg[i:key_length+i] for i in range(0, len(enc_msg), key_length)]
        print('\nCheck for key length: ' + str(key_length))
        crack_blocks(enc_msg_chunks, method, lang_stats, char_base)


def key_len_hamming_dist(enc_msg, key_len_range):
    """ Determine key length by counting hamming distance - lower then better """
    keys_hd = {}

    for key_length in key_len_range:
        keys_hd[key_length] = hamming_distance(enc_msg, key_length)

    sorted_tab = sorted(keys_hd.items(), key=operator.itemgetter(1), reverse=True)
    print('Hamming distance from worst to best:')
    result = []
    for k, hd in sorted_tab:
        print('Length [' + str(k) + '] : ' + str(hd))
        result.append(k)

    result.reverse()
    return result


def key_len_high_bits(enc_msg, key_len_range):
    """ Works only when key contain high bits (key is not build from printable characters) """
    HIGH_BIT_MASK = 0x80
    result = []
    for key_length in key_len_range:
        good_key = True
        for ix in range(key_length):
            bytes_per_pos = enc_msg[ix::key_length]

            searched_bit = bytes_per_pos[0] & HIGH_BIT_MASK
            for b in bytes_per_pos:
                if b & HIGH_BIT_MASK != searched_bit:
                    good_key = False
                    break
            if not good_key:
                break

        if good_key:
            result.append(key_length)

    return result


def hamming_distance(enc_msg, key_length):
    """ Normalized Hamming Distance - lower then better """
    bits = 0
    block1 = enc_msg[:key_length]
    block2 = enc_msg[key_length:2*key_length]

    for l in range(key_length):
        bits += bin(block1[l] ^ block2[l]).count('1')

    # normalized Hamming distance
    return bits / key_length


def crack_blocks(enc_msgs, method='spaces', lang_stats=ENGLISH_LETTERS, char_base=string.ascii_letters+" '"):
    """
    Crack blocks of bytes stream, where key was reused for each block.
    :param enc_msgs: list of encoded messages. Each character should be presented as int
    :param method: cracking method: 'best-freq', 'first-order-freq', 'spaces'
    :param lang_stats: letters frequency distribution of specific language. By default ENGLISH_LETTERS
    :param char_base: characters expected in output message
    """
    if method == 'best-freq':
        msg_bytes_matcher = FreqMatcher(lang_stats, delta=0.3)
        cracker = Cracker(char_base, msg_bytes_matcher)
        keys_candidates = cracker.run(enc_msgs)
    elif method == 'first-order-freq':
        msg_bytes_matcher = FreqOrderMatcher(lang_stats)
        cracker = Cracker(char_base, msg_bytes_matcher)
        keys_candidates = cracker.run(enc_msgs)
    elif method == 'spaces':
        keys_candidates = find_key_by_most_common_char(enc_msgs)
    else:
        raise Exception

    v = ResultView()
    v.show(enc_msgs, keys_candidates, char_base)


def find_key_by_most_common_char(enc_msgs, most_common_ch=' '):
    """ Find key by most common character (be default space) """
    counters = []
    for e in enc_msgs:
        for ix in range(len(e)):
            if ix == len(counters):
                counters.append(Counter())
            counters[ix][e[ix]] += 1

    most_common_byte = ord(most_common_ch)
    keys_candidates = []
    for ix in range(len(counters)):
        keys_candidates.append([counters[ix].most_common(1)[0][0] ^ most_common_byte])

    return keys_candidates
