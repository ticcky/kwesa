#!/usr/bin/env python
import json
import sys
import sqlite3
from porter import PorterStemmer
import kwutils
import stopwords
import itertools
import re
from collections import defaultdict

RE_TAG = re.compile("<[/]{0,1}[^>]*>")


class Indexer(object):
    DB_ITER_QUERY = "SELECT Id, Body FROM Posts WHERE Id > {id} ORDER BY Id LIMIT {limit}"
    ITER_STEP = 100
    stopword_file = "res/stopwords.en.txt"
    
    
    def __init__(self):
        self.p = PorterStemmer()
        self.sw = stopwords.StopWords(self.stopword_file)
        self.re_tag = RE_TAG
        self.index = None

    def find(self, w):
        if w in self.index:
            return self.index[w].keys()
        else:
            return []

    def load_index(self, indexfile):
        with open(indexfile, 'r') as f:
            self.index = json.loads(f.read())
        

    def build_index(self, db_file, outfile):
        db = sqlite3.connect(db_file)
        
        self.index = index = defaultdict(lambda:defaultdict())

        start_id = 0

        while 1:
            q = self.DB_ITER_QUERY.format(id=start_id, limit=self.ITER_STEP)
            print q
            res = db.execute(q)
            res_rows = res.fetchall()
            if len(res_rows) == 0: break

            for doc_id, doc_body in res_rows:
                start_id = doc_id = int(doc_id)
                doc_body = doc_body.lower()
                words = kwutils.tokenize(doc_body)
                w_stemmed = kwutils.stem(words, self.p)
                w_stopped = w_stemmed
                w_stopped = kwutils.filter_stopwords(w_stemmed, self.sw)

                for w in w_stopped:
                    w = w.strip()
                    if len(w) > 0:
                        index[w][doc_id] = 1
        
        with open(outfile, 'w') as f_out:
            f_out.write(json.dumps(index))
                
        
class Searcher(object):
    DB_WORD_QUERY = "SELECT Id, Body FROM Posts WHERE Body LIKE '%{word}%';"
    DB_DOC_QUERY = "SELECT Id, Title, Body FROM Posts WHERE Id = {id};"
    DB_ALL_DOCS_QUERY = "SELECT Id FROM Posts -- LIMIT 10;"
    stopword_file = "res/stopwords.en.txt"

    def __init__(self, db_file, indexer):
        self.db_file = db_file
        self.indexer = indexer
        
        self.db = sqlite3.connect(db_file)
        self.p = PorterStemmer()
        self.sw = stopwords.StopWords(self.stopword_file)
        
        self.re_tag = RE_TAG

    def cleanup_doc(self, s):
        return self.re_tag.sub("", s)

    def rank_docs(self, rank, kws):
        #total_occ = sum(itertools.chain(*[x.values() for x in rank.values()]))
        total_occ = len(kws)
        res = []

        for doc_id, dd in rank.items():
            score = float(sum(dd.values())) / total_occ
            res += [(-score, doc_id)]

        res.sort()
        return res

    def self_search_all(self):
        results = {}
        q = self.DB_ALL_DOCS_QUERY
        res = self.db.execute(q)
        for (doc_id,) in res.fetchall():
            print >>sys.stderr, 'searching', doc_id
            results[doc_id] = self.self_search(doc_id)
        return results
        

    def self_search(self, doc_id):
        q = self.DB_DOC_QUERY.format(id=doc_id)
        res = self.db.execute(q)
        doc_id, doc_title, doc_body = res.fetchone()
        if doc_title is None: return None
        return self.search(doc_title)

    def search(self, phrase):
        phrase = phrase.lower()
        words = kwutils.tokenize(phrase)
        w_stemmed = kwutils.stem(words, self.p)
        w_stopped = w_stemmed
        w_stopped = kwutils.filter_stopwords(w_stemmed, self.sw)

        rank = defaultdict(lambda: defaultdict(lambda: 0))

        for word in w_stopped:
            if len(word) == 0: continue
            
            #q = self.DB_WORD_QUERY.format(word=word)
            #print >>sys.stderr, q
            #res = self.db.execute(q)
            res = self.indexer.find(word)
            for doc_id in res:
                rank[doc_id][word] = 1

        return self.rank_docs(rank, w_stopped)

        
if __name__ == '__main__':
    doc_db = sys.argv[1]
    index_file = sys.argv[2]
    results_file = sys.argv[3]
    i = Indexer()
    #i.build_index(doc_db, index_file)
    i.load_index(index_file)
    s = Searcher(doc_db, i)
    results = s.self_search_all()

    with open(results_file, 'w') as f_out:
        f_out.write(json.dumps(results))

        
    #print s.self_search(7878)
    exit(0)

    while 1:
        phrase = sys.stdin.readline().strip()
        if len(phrase) > 0:
            s.search(phrase)
        else:
            break