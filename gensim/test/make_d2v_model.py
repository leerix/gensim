#!/usr/bin/env python
import numpy as np

import gensim
from gensim import utils
from gensim.models import doc2vec
from gensim.test.utils import common_texts, datapath


class DocsLeeCorpus(object):
    def __init__(self, string_tags=False, unicode_tags=False):
        self.string_tags = string_tags
        self.unicode_tags = unicode_tags

    def _tag(self, i):
        if self.unicode_tags:
            return '_\xa1_%d' % i
        elif self.string_tags:
            return '_*%d' % i
        return i

    def __iter__(self):
        with open(datapath('lee_background.cor')) as f:
            for i, line in enumerate(f):
                yield doc2vec.TaggedDocument(utils.simple_preprocess(line), [self._tag(i)])


def models_equal(model, model2):
    # check words/hidden-weights
    assert len(model.wv.vocab) == len(model2.wv.vocab)
    assert np.allclose(model.wv.vectors, model2.wv.vectors)
    if model.hs:
        assert np.allclose(model.trainables.syn1, model2.trainables.syn1)
    if model.negative:
        assert np.allclose(model.trainables.syn1neg, model2.trainables.syn1neg)
    # check docvecs
    assert len(model.docvecs.doctags) == len(model2.docvecs.doctags)
    assert len(model.docvecs.offset2doctag) == len(model2.docvecs.offset2doctag)
    return True


# makes a bigger model
def make_and_save_model_lee():
    corpus = DocsLeeCorpus()
    model = doc2vec.Doc2Vec(vector_size=100, min_count=2, epochs=20, workers=1)
    model.build_vocab(corpus)
    assert model.docvecs.vectors_docs.shape == (300, 100)
    model.train(corpus, total_examples=model.corpus_count, epochs=model.epochs)

    # save
    path = datapath(f'old_d2v_models/d2v_{gensim.__version__}.mdl')
    model.save(path)

    # load and check
    model2 = doc2vec.Doc2Vec.load(path)
    assert models_equal(model, model2)


def make_and_save_model():
    sentences = [doc2vec.TaggedDocument(words, [i]) for i, words in enumerate(common_texts)]
    vector_size = 5
    model = doc2vec.Doc2Vec(vector_size=vector_size, min_count=2, epochs=20, workers=1)
    model.build_vocab(sentences)
    assert model.docvecs.vectors_docs.shape == (len(sentences), vector_size)
    model.train(sentences, total_examples=model.corpus_count, epochs=model.epochs)

    # save
    path = datapath(f'old_d2v_models/d2v_{gensim.__version__}.mdl')
    model.save(path)

    # load and check
    model2 = doc2vec.Doc2Vec.load(path)
    assert models_equal(model, model2)


if __name__ == '__main__':
    make_and_save_model()
