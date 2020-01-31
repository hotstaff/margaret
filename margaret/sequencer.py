# Copyright 2017 Hideto Manjo.
#
# Licensed under the MIT License

"""IO modules for input data to DNC model."""
import logging
import numpy as np
from margaret.sequence import Sequence, SequenceHead

LOGGER = logging.getLogger(__name__)

# experimental.

class Sequencer:
    """Class Sequencer.

    Data input module
    RAW data <-> sequencer <-> computer
    """

    def __init__(self, x_shape, y_shape, t_shape,
                 x_dtype=np.float32, y_dtype=np.float32, t_dtype=np.float32):
        """Init.

        Input_form and output_form are Transformer option.
        """

        # sequence configure
        self.x_shape = x_shape
        self.y_shape = y_shape
        self.t_shape = t_shape

        self.x_dtype = x_dtype
        self.y_dtype = y_dtype
        self.t_dtype = t_dtype


    @staticmethod
    def _list2array(_list, dtype):
        """Convert list using transfomer."""
        return np.array(_list, dtype=dtype)

    @staticmethod
    def _array2list(array):
        """Convert sequence using transformer."""
        return array.tolist()

    def list2sequence(self, inputlist, answerlist):
        """List2sequence.

        inputlist = [batch, inputlen, any]
        answerlist = [batch, outputlen, any]
        """

        try:
            input_x = self._list2array(inputlist, self.x_dtype)
            output_t = self._list2array(answerlist, self.t_dtype)

        except Exception as err:
            return None

        # batch length check
        if input_x.shape[0] != output_t.shape[0]:
            return None

        inputlen = input_x.shape[1]
        outputlen = output_t.shape[1]
        seqlen = inputlen + outputlen

        # sequence object init
        sequence = Sequence(SequenceHead.alloc(seqlen, 3), seqlen, 3)

        for i in range(seqlen):
            if i < inputlen:
                sequence.set(i, "input", input_x[:, i, :], None, None)
            else:
                sequence.set(i, "output", None, output_t[:, i, :], None)

        return sequence


    def sequence2list(self, sequence):
        """Sequence2list.

        sequence2list genarates list from output sequece of computer
        """
        lists = [[]] * 3
        ret = []

        for i in range(sequence.seqlen):
            seq = sequence.get(i)
            if seq["work"] == "input":
                lists[0].append(seq["mem"][0])
            elif seq["work"] == "output":
                lists[1].append(seq["mem"][1])
                lists[2].append(seq["mem"][2])

        for i in range(3):
            ret.append(self._array2list(np.concatenate(lists[i], axis=1)))

        return ret
