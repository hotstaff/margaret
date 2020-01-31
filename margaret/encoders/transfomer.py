# Copyright 2017 Hideto Manjo.
#
# Licensed under the MIT License

"""Transformer module."""

import logging
import numpy as np

LOGGER = logging.getLogger(__name__)


class Transformer:
    """Class Transformer.

    Vector transform module(pack/unpack).
    The name of Transfomer class means vector transformer.
    The instance convert vector to any vector using defined
     pack/unpack methods.

    Required:
        pack and unpack field is required

    Option format:
        option ={
            'pack':[
                [1, callback, 1, 0],
                [FIELD LENGTH, CALLBACK, ARGUMENT1, ARGUMENT2],  # hint
                ]
            'unpack':[
                [1, callback, 1],
                ]
            }
    """

    def __init__(self, option=None, reset_callback=None):
        """Init."""
        self.option = option
        self.reset_callback = reset_callback

        self.dim = {}

        # option check
        if self.option is None:
            raise Exception("transformer requires option.")
        if 'pack' not in self.option or 'unpack' not in self.option:
            LOGGER.error("the pack or unpack field is required.")
            raise Exception("the pack and unpack field is required.")
        for field in ['pack', 'unpack']:
            self.dim[field] = 0
            # check pass
            if self.option[field] is None:
                continue

            for trans in self.option[field]:
                if len(trans) < 2:
                    LOGGER.error("transformer field syntax error.")
                    raise SyntaxError("transformer field syntax error.")
                if trans[1] is not None and not callable(trans[1]):
                    LOGGER.error("the second field is not callable.")
                    raise SyntaxError("the second field is not callable.")
                if trans[0] is not None:
                    self.dim[field] += trans[0]

        # callback check
        if self.reset_callback is not None and not callable(reset_callback):
            LOGGER.error("init is not callable.")
            raise SyntaxError("init is not callable.")

    @staticmethod
    def _handler(func, *args):
        return func(*args)

    def _trans(self, vector, name):
        # check
        if vector is None:
            return None
        if name not in self.option:
            return None

        # pass through
        if self.option[name] is None:
            ret = np.array(vector, dtype=np.float32)
            return ret

        ret = np.array([], dtype=np.float32)
        i = 0
        for trans in self.option[name]:

            length = trans[0]
            callback = trans[1]
            if callback is None:
                i = i + length
                continue  # if callback is None skip for length
            args = trans[2:]

            if length == 1:
                add = self._handler(callback, vector[i], *args)
            elif length is None:
                add = self._handler(callback, *args)
                length = 0
            else:
                add = self._handler(callback, vector[i:i+length], *args)
            if add.shape == ():
                add = add.reshape((1))

            ret = np.concatenate((ret, add))
            i = i + length

        return ret

    def pack(self, vector):
        """Pack."""
        return self._trans(vector, 'pack')

    def unpack(self, vector):
        """Unpack."""
        return self._trans(vector, 'unpack')

    def reset(self):
        """Reset callback for stateful packing."""
        if self.reset_callback is not None:
            self._handler(self.reset_callback)
