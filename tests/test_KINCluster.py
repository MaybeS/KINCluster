# -*- coding: utf-8 -*-
"""
    tests.KINCluster
    ---------------
    Test KINCluster
    :author: MaybeS(maytryark@gmail.com)
"""

import pytest

from KINCluster.core.cluster import Cluster 
from KINCluster.core.pipeline import Pipeline 
from KINCluster.core.extractor import Extractor 
from KINCluster.core.item import Item
from KINCluster.lib.tokenizer import tokenize, stemize

import codecs

test_text = ['2016헌나1.txt', '2014헌나1.txt']
test_keyword = ['헌법판결문', '헌법판결문']
# test_text = ['small.txt', 'small.txt']
# test_keyword = ['언어', '언어']

# Test1
class PipelineFile(Pipeline):
    def capture_item(self):
        for text, keyword in zip(test_text, test_keyword):
            with codecs.open('tests/data/' + text, 'r', 'utf-8') as f:
                content = f.read()
            yield Item(title=text,content=content,keyword=keyword,date='')

def test_app1():
    """ Testing for cluster, using test data
    """
    cluster = Cluster(epoch=32, tokenizer="stemize")
    pipeline = PipelineFile()

    for item in pipeline.capture_item():
        cluster.put_item(item)
    cluster.cluster()

    extractor = Extractor(cluster)
    for idx, dump in enumerate(cluster.dumps):
        items, vectors = map(list, zip(*dump))

        extracted = extractor.dump(idx)

        assert isinstance(extracted.keywords, list)
        assert isinstance(extracted.topic, Item)
        pipeline.dress_item(extracted, items)

# Test2
import pymysql
SERVER_RDB = '175.207.13.225'
class PipelineServer(Pipeline):
    def __init__(self, keyword):
        self.keyword = keyword
    def capture_item(self):
        conn = pymysql.connect(host=SERVER_RDB,
                           user='memento',
                           password='memento@0x100_',
                           db='memento',
                           charset='utf8')
        cur = conn.cursor()

        columns = ['keyword', 'title', 'content', 'published_time']

        sql = "SELECT " + ",".join(columns) + " FROM articles where keyword like \'" + self.keyword  +"\' limit 1000"

        result = cur.execute(sql)

        for keyword, title, content, ptime in cur:
            yield Item(title=title,content=content,keyword=keyword,date=ptime)

        cur.close()
        conn.close()

def test_app2():
    """ Testing for cluster, using test data
    """
    cluster = Cluster(epoch=32, tokenizer="tokenize")
    pipe = PipelineServer('김태희')

    for item in pipe.capture_item():
        cluster.put_item(item)
    cluster.cluster()

    extractor = Extractor(cluster)
    for idx, dump in enumerate(cluster.dumps):
        items, vectors = map(list, zip(*dump))

        extracted = extractor.dump(idx)

        # assert isinstance(extracted, Item)

        pipe.dress_item(extracted, items)
    print (cluster.distribution)

# Test3
import pandas as pd
from nltk import ngrams
test_csv = 'tests/data/test.csv'
class Item(Item):
    def __str__(self):
        return " ".join(map(str, self.items))
    def __repr__(self):
        return " ".join(map(str, self.items))


class PipelineCsv(Pipeline):
    def __init__(self, csv):
        self.frame = pd.read_csv(csv)
    def capture_item(self):
        for idx, row in self.frame.iterrows():
            yield Item(title=row.title,content=row.content,keyword=row.actor,date=row.date)
    def dress_item(self, extracted, items):
        if len(items) < 3: return
        print (len(items), extracted.topic.title)

def test_app3():
    """ Testing for cluster, using test data
    """
    cluster = Cluster(tokenizer="tokenize")
    pipe = PipelineCsv(test_csv)

    for item in pipe.capture_item():
        cluster.put_item(item)
    cluster.cluster()

    extractor = Extractor(cluster)
    for idx, dump in enumerate(cluster.dumps):
        items, vectors = map(list, zip(*dump))
        extracted = extractor.dump(idx)

        pipe.dress_item(extracted, items)
    print (cluster.distribution)

if __name__ == '__main__':
    test_app2()