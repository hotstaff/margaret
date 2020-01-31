# coding: UTF-8
# Copyright 2017 Hideto Manjo.
#
# Licensed under the MIT License

"""Word2vec encoder modules."""

import logging
from threading import Lock
import numpy as np
import MeCab
from gensim.models import Word2Vec
from gensim.models import KeyedVectors

# LOGGER
LOGGER = logging.getLogger(__name__)

class Word2vecEncoderBase:
    """Word2vecEncoderBase."""

    def __init__(self, model_file, keyed_format, mecab_option):
        """Init."""
        LOGGER.info("Loading mecab")
        self.mecab = MeCab.Tagger(" {}".format(mecab_option))
        LOGGER.info("Loading word2vector or fasttext model.")
        if keyed_format:
            self.model = KeyedVectors\
                        .load_word2vec_format(model_file, binary=False)
        else:
            # word2vec binary format
            self.model = Word2Vec.load(model_file)
        LOGGER.info("vocab : %d words.", len(self.model.wv.vocab))

    def wakati(self, text):
        """Return wakati list."""
        return self.mecab.parse(text).split(" ")[0:-1]

    def unload_model(self):
        """Unload gensim model."""
        self.model = None

class Word2vecEncoder(Word2vecEncoderBase):
    """Text to Wordvector module."""

    def __init__(self, model_file, keyed_format=True, mecab_option="-Owakati"):
        """Init."""
        super(Word2vecEncoder, self).__init__(model_file, keyed_format,
                                              mecab_option)

    def similar_word_by_vector(self, vector, topn=10):
        """Return similar word."""
        return self.model.similar_by_vector(vector=vector,
                                            topn=topn)

    def check_dict(self, word, index=False):
        """Check transformable of the word."""
        try:
            if index:
                return self.model.wv.vocab[word].index
            return self.model[word]
        except KeyError:
            LOGGER.warning("Not found: %s", word)
            return None

    def vectorize(self, wakati_list):
        """Return vector list created from word list."""
        vectorized = []
        try:
            vectorized = self.model[wakati_list]
        except KeyError:
            LOGGER.warning("Vectorize vocab error: %s", wakati_list)
            return None
        return vectorized

    def encode(self, text, fix_length=False, maxlen=10, blankchar="空白"):
        """Encode text to vector."""
        wakati_list = self.wakati(text)

        if wakati_list is False or len(wakati_list) > maxlen:
            return None

        if fix_length:
            if len(wakati_list) != maxlen:
                wakati_list += [blankchar]*(maxlen-len(wakati_list))

        return self.vectorize(wakati_list)

    def decode(self, vector_list, sepalator="", blankchar="空白"):
        """Decode vector to text."""
        vector_array = np.array(vector_list, dtype=np.float32)
        answer_texts = []

        for vec in vector_array:
            similar_word = self.similar_word_by_vector(vec)[0][0]
            if similar_word != blankchar and similar_word is not None:
                answer_texts.append(similar_word)

        return sepalator.join(answer_texts)

class Word2vecLink(Word2vecEncoderBase):
    """Text to Wordvector embeded layer."""

    def __init__(self, model_file, keyed_format=True, mecab_option="-Owakati",
                 memory_clear=True):
        """Init."""
        super(Word2vecLink, self).__init__(model_file, keyed_format,
                                           mecab_option)

        self.index2word = self.model.wv.index2word
        self.word2index = {w: i for i, w in enumerate(self.index2word)}
        self.n_vocab = len(self.index2word)

        # memory clear
        if memory_clear:
            self.unload_model()

    def get_initialW(self):
        """Get_initialW."""
        if self.model is None:
            assert "Gensim model is unloaded."
            return None
        return self.model.wv.vectors

    def get_index_from_word(self, word):
        """Get index."""
        return self.word2index.get(word, None)

    def get_word_from_index(self, index):
        """Get word."""
        index = int(index)
        if index > self.n_vocab - 1 or index < 0:
            LOGGER.warning("Index is out of bound: %d", index)
            return None

        return self.index2word[index]

    def encode(self, text, fix_length=False, minlen=1, maxlen=10):
        """Encode."""
        wakati_list = self.wakati(text)
        if len(wakati_list) > maxlen:
            return None
        if len(wakati_list) < minlen:
            return None

        vector_list = []
        for word in wakati_list:
            index = self.get_index_from_word(word)
            if index is None:
                return None
            vector_list.append([index])

        black_index = self.n_vocab - 1
        if fix_length and len(vector_list) != maxlen:
            vector_list += [[black_index]]*(maxlen-len(wakati_list))

        return vector_list

    def decode(self, vector_list, sepalator=""):
        """Decode."""
        length = len(vector_list)
        black_index = self.n_vocab-1
        word_list = [None] * len(vector_list)
        for i in range(length):
            index = vector_list[i][0]
            if int(index) == black_index:
                word_list[i] = ""
                continue
            word_list[i] = self.get_word_from_index(index)

        return sepalator.join(word_list)



class LockedWord2vecEncoder(Word2vecEncoder):
    """Locked encoder."""

    def __init__(self, *args, **kwargs):
        """Init."""
        super(LockedWord2vecEncoder, self).__init__(*args, **kwargs)
        self.lock = Lock()

    def encode(self, *args, **kwargs):
        """Locked encode."""
        with self.lock:
            ret = super(LockedWord2vecEncoder, self).encode(*args, **kwargs)
        return ret

    def decode(self, *args, **kwargs):
        """Locked decode."""
        with self.lock:
            ret = super(LockedWord2vecEncoder, self).decode(*args, **kwargs)
        return ret
