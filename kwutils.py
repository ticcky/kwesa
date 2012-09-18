#!/usr/bin/python

import re


def normalize(txt):
    pattern = re.compile('[\s-]+')
    txt = pattern.sub(' ', txt)
    pattern = re.compile('[0-9]')
    txt = pattern.sub(' ', txt)
    txt = txt.replace('\n', ' ')
    txt = ''.join(ch for ch in txt if ch.isalnum() or ch in ['.', ',', ' '])
    txt = txt.replace('.', ' . ')
    txt = txt.replace(',', ' , ')

    return txt


def tokenize(txt):
    txt = normalize(txt)
    txt = txt.split(' ')
    return txt


def filter_stopwords(lst, sw):
    new_lst = []
    for l in lst:
        if not sw.isstop(l):
            new_lst.append(l)
    return new_lst


def stem(lst, p):
    res = []
    for w in lst:
        res.append(p.stem(w, 0, len(w) - 1))
    return res


def precision(good, bad):
    return good / float(good + bad)

def recall(good, total):
    return good / float(total)

