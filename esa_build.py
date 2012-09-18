#!/usr/bin/env python
import sys
import os
from porter import PorterStemmer
import kwutils
import stopwords
from collections import defaultdict
import json


class ESABuild(object):
    stopword_file = "res/stopwords.basic.txt"

    def __init__(self):
        pass

    def build(self, docpath, outfile):
        p = PorterStemmer()
        sw = stopwords.StopWords(self.stopword_file)

        ndx = defaultdict(list)

        for filename in os.listdir(docpath):
            if not filename.endswith(".txt"): continue

            doc_id = hash(filename.replace(".txt", ""))
            with open(os.path.join(docpath, filename)) as f:
                f_content = kwutils.normalize(f.read().lower())

            words = kwutils.tokenize(f_content)
            w_stemmed = kwutils.stem(words, p)
            w_stopped = kwutils.filter_stopwords(w_stemmed, sw)

            for word in w_stopped:
                if len(word) > 0:
                    if not doc_id in ndx[word]:
                        ndx[word].append(doc_id)

        with open(outfile, 'w') as f:
            f.write(json.dumps(ndx))


if __name__ == '__main__':
    eb = ESABuild()
    eb.build(sys.argv[1], sys.argv[2])
