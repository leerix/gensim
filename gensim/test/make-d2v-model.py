#!/usr/bin/env python
import argparse
import logging
import logging.config
import pathlib
import sys
import warnings

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


def save_and_load_model(options, basename, model):
    # save
    path = datapath(f'old_d2v_models/{basename}_{gensim.__version__}.mdl')
    p = pathlib.Path(path)
    save_model = True
    if p.exists() and not options.overwrite:
        save_model = False
        options.logger.warning(f'Model already exists at {path}. Use --overwrite to overwrite it.')
    if save_model:
        model.save(path)

    # load and check
    model2 = doc2vec.Doc2Vec.load(path)
    assert models_equal(model, model2)


# makes a bigger model
def make_and_save_model_lee(options):
    corpus = DocsLeeCorpus()
    model = doc2vec.Doc2Vec(vector_size=100, min_count=2, epochs=20, workers=1)
    model.build_vocab(corpus)
    assert model.docvecs.vectors_docs.shape == (300, 100)
    model.train(corpus, total_examples=model.corpus_count, epochs=model.epochs)
    save_and_load_model(options, 'd2v_lee', model)


def make_and_save_model(options):
    sentences = [doc2vec.TaggedDocument(words, [i]) for i, words in enumerate(common_texts)]
    vector_size = 5
    model = doc2vec.Doc2Vec(vector_size=vector_size, min_count=2, epochs=20, workers=1)
    model.build_vocab(sentences)
    assert model.docvecs.vectors_docs.shape == (len(sentences), vector_size)
    model.train(sentences, total_examples=model.corpus_count, epochs=model.epochs)
    save_and_load_model(options, 'd2v_common_texts', model)


def make_d2v_model(options):
    if options.large:
        make_and_save_model_lee(options)
    else:
        make_and_save_model(options)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog='make-d2v-model',
        description='Makes a d2v model with the current version of gensim and saves it to the test data directory',
    )
    parser.add_argument(
        '--large',
        default=False,
        action='store_true',
        help='Create a large model',
    )
    parser.add_argument(
        '--overwrite',
        default=False,
        action='store_true',
        help='Overwrite existing model',
    )

    return parser.parse_args(argv)


def make_logger(name):
    logging_format = '%(asctime)s %(levelname)-8s %(name)s %(filename)s/%(funcName)s/%(lineno)d: %(message)s'
    logging_datefmt = '%Y-%m-%d %H:%M:%S'

    config = {
        'version': 1,
        'formatters': {
            'default': {'format': logging_format, 'datefmt': logging_datefmt},
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
        },
        'root': {
            'handlers': [
                'console',
            ],
            'level': 'DEBUG',
        },
    }
    logging.config.dictConfig(config)
    logging.captureWarnings(True)
    warnings.resetwarnings()
    return logging.getLogger(name)


def main(argv):
    options = parse_args(argv)
    options.logger = make_logger('make-d2v-model')

    m = 0
    try:
        make_d2v_model(options)
    except Exception as e:
        m = 'Exception: %s' % e
        options.logger.exception(m)
    sys.exit(m)


if __name__ == '__main__':
    main(sys.argv[1:])
