#! /usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: Mateusz Janda (mateusz.janda [at] gmail [dot] com)
# Ad maiorem Dei gloriam

import itertools as it
from mtpc import crack_stream, crack_blocks


def main():
    print('[+] Testing stream cracking')
    crack_stream(enc_msg=encrypted_stream(), key_len_method='hamming', key_len_range=range(16, 18))

    print('\n[+] Testing block cracking')
    crack_blocks(enc_msgs=encrypted_block(), method='first-order-freq')


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


def encrypted_block():
    # https://en.wikipedia.org/wiki/12_Angry_Men_(1957_film)
    blocks = [
        'In a New York City courthouse a jury commences deliberating the case of an 18-year-old boy from a slum, on trial for allegedly stabbing his father to death.',
        'If there is any reasonable doubt they are to return a verdict of not guilty. If found guilty, the boy will receive a death sentence',
        'In a preliminary vote, all jurors vote "guilty" except Juror 8, who argues that the boy deserves some deliberation.',
        'This irritates some of the other jurors, who are impatient for a quick deliberation, ',
        'especially Juror 7 who has tickets to the evening\'s Yankees game, and 10 who demonstrates blatant prejudice against people from slums',
        'Juror 8 questions the accuracy and reliability of the only two witnesses, and the prosecution\'s claim that the murder weapon, ',
        'a common switchblade (of which he possesses an identical copy), was "rare"',
        'Juror 8 argues that reasonable doubt exists, and that he therefore cannot vote "guilty", but concedes that he has merely hung the jury.',
        'Juror 8 suggests a secret ballot, from which he will abstain, and agrees to change his vote if the others unanimously vote "guilty"',
        'The ballot is held and a new "not guilty" vote appears.',
        'An angry Juror 3 accuses Juror 5, who grew up in a slum, of changing his vote out of sympathy towards slum children.',
        'However, Juror 9 reveals it was he that changed his vote, agreeing there should be some discussion',
        'Juror 8 argues that the noise of a passing train would have obscured the verbal threat that one witness claimed to ',
        'have heard the boy tell his father "I\'m going to kill you"',
        'Juror 5 then changes his vote. Juror 11 also changes his vote, ',
        'believing the boy would not likely have tried to retrieve the murder weapon from the scene if it had been cleaned of fingerprints.'
    ]

    password = 'Never send a human to do a machine\'s job'

    return [[ord(t) ^ ord(p) for t, p in zip(text, it.cycle(password))] for text in blocks]


if __name__ == '__main__':
    main()
