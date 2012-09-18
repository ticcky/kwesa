#!/usr/bin/env python
import json
import sys
from porter import PorterStemmer
import kwutils
import stopwords
import itertools
from operator import mul
from collections import defaultdict
import math
import time
import Pycluster


class ESAAnalyze(object):
    # stopword_file = "res/stopwords.basic.txt"
    stopword_file = "res/stopwords.en.txt"
    dims = None
    dim_map = {}

    def __init__(self):
        self.dims = set()

    def load(self, ndxfile):
        with open(ndxfile, "r") as f:
            self.ndx = json.loads(f.read())
        self.p = PorterStemmer()
        self.sw = stopwords.StopWords(self.stopword_file)

        for w, val in self.ndx.items():
            for d in val:
                self.dim_map[d] = len(self.dims) - 1
                self.dims.add(d)
        

    def analyze(self, sentence):
        words = kwutils.tokenize(sentence)
        w_stemmed = kwutils.stem(words, self.p)
        w_stopped = kwutils.filter_stopwords(w_stemmed, self.sw)

        vector = set()
        for word in w_stopped:
            for doc_id in self.ndx.get(word, []):
                vector.add(doc_id)
        return vector

    def build_cross_similarity_index(self, index_file):
        cindex = {}
        cntr = 0
        onetime = 0.0
        for word, wv in self.ndx.items():
            res = []
            t_beg = time.time()
            for nword, nv in self.ndx.items():
                wsim = self.compute_similarity([wv, nv])
                res.append((wsim, nword))
                cntr += 1
                #if cntr % 100 == 0:
                #    print float(cntr) / len(self.ndx)**2
            onetime += time.time() - t_beg
            print (onetime/cntr)*(len(self.ndx)**2 - cntr)
            cindex[word] = res

        import pdb; pdb.set_trace()

        with open(index_file, 'w') as f:
            f.write(json.dumps(cindex))

    def as_vector(self, v):
        res = [0 for i in range(len(self.dims))]
        for vv in v:
            res[self.dim_map[vv]] = 1
        return tuple(res)

    def suggest(self, word):
        v = self.analyze(word)

        # pick first x
        res = []
        for nword, nv in self.ndx.items():
            wsim = self.compute_similarity([v, nv])
            res.append((wsim, nword, self.as_vector(nv)))
        res.sort()
        res = res[::-1]

        # from first y pick the most distant ones
        res2 = [v for (sim, word, v) in res]
        resw = [word for (sim, word, v) in res]
        lab, err, nfound = Pycluster.kcluster(res2, 40)

        resg = defaultdict(lambda: [])
        for i, l in enumerate(lab):
            resg[l] += [res[i]]

        res_sug = []
        used_groups = set()
        for l, w in zip(lab, resw):
            if not l in used_groups:
                res_sug += [w]
                used_groups.add(l)
                
        return res_sug
        #for sim, word in reversed(sorted(res)):
        #    print sim, word

    def compute_similarity(self, vectors):
        subspace = set(itertools.chain(*vectors))
        commonspace = set()
        commonspace = reduce(lambda a, b: a.intersection(b), map(set, vectors))
        #    set(vectors[0]).intersection(set(vectors[1]))
        
        #for dim in subspace:
        #    if all(map(lambda x: dim in x, vectors)):
        #        commonspace.add(dim)

        val = float(len(commonspace))
        val /= (reduce(mul, [math.sqrt(len(x)) for x in vectors]))
        #val /= (reduce(mul, [math.sqrt(len(x)) for x in vectors]))
        val = 0.0
        return val


if __name__ == '__main__':
    ea = ESAAnalyze()
    ea.load(sys.argv[1])
    #v1 = ea.analyze(sys.argv[2])
    #v2 = ea.analyze(sys.argv[3])
    #print ea.compute_similarity([v1, v2])
    for i, sug in enumerate(ea.suggest(sys.argv[2])):
        print i, ":", sug
    #ea.build_cross_similarity_index(sys.argv[2])
