#!/usr/bin/python

class StopWords:
    words = None

    def __init__(self, file):
        f = open(file, 'r')
        self.words = {}
        for ln in f:
            ln = ln.strip()
            self.words[ln] = True

        f.close()

    def isstop(self, w):
        return w in self.words
