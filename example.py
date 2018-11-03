#! /usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: Mateusz Janda (mateusz.janda [at] gmail [dot] com)
# Ad maiorem Dei gloriam

import itertools as it
from mtpc import crack_stream, crack_blocks
import string


def encrypted_stream():
    # https://en.wikipedia.org/wiki/12_Angry_Men_(1957_film)
    text = 'In a New York City courthouse a jury commences deliberating the ' \
        'case of an 18-year-old boy from a slum, on trial for allegedly ' \
        'stabbing his father to death. If there is any reasonable doubt ' \
        'they are to return a verdict of not guilty. If found guilty, ' \
        'the boy will receive a death sentence.' \
        'In a preliminary vote, all jurors vote "guilty" except Juror 8, who ' \
        'argues that the boy deserves some deliberation. This irritates some ' \
        'of the other jurors, who are impatient for a quick deliberation, ' \
        'especially Juror 7 who has tickets to the evening\'s Yankees game, and '\
        '10 who demonstrates blatant prejudice against people from slums. '

    password = 'There is no spoon'

    return [ord(t) ^ ord(p) for t, p in zip(text, it.cycle(password))]


def main():
    crack_stream(enc_msg=encrypted_stream(), key_len_method='hamming', key_len_range=range(16, 18))


if __name__ == '__main__':
    main()