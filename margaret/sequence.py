# Copyright 2017 Hideto Manjo.
#
# Licensed under the MIT License

"""IO modules for input data to DNC model."""
import logging
from margaret.core.memory import VirtualMemory
from margaret.core.cell import Cell

LOGGER = logging.getLogger(__name__)


class SequenceHead:
    """SequenceHead.

    Describes the head class for reading sequence data.
    A sequence with any number of slots can be represented.
    """
    def __init__(self, mem, seqlen, slot=2):
        """Init.

        A sequence consists of a bunch of virtual memory for the
        number of slots. Reserved size of virtual memory is the
        length of the sequence multiplied by the number of slots.
        """
        self._seqlen = seqlen
        self._slot = slot

        if not self._type_check(mem):
            raise TypeError("The specified memory cannot be set.")
        self._mem = mem

    @staticmethod
    def alloc(seqlen, slot):
        """Alloc.

        Get the initial memory.
        Can be specified as the reference source of the sequencer head.
        """
        return VirtualMemory(seqlen * slot)

    def _type_check(self, mem):
        if not isinstance(mem, VirtualMemory):
            return False

        shape = mem.shape()
        if len(shape) != self._seqlen * self._slot:
            return False
        return True

    def set(self, n, *xargs):
        """Set the nth sequence memory data.

        Raises the exception ValueError if the number of slots does not match.
        """
        if len(xargs) != self._slot:
            raise ValueError("The number of input slots does not match.")

        for i, x in enumerate(xargs):
            if x is not None:
                self._mem[n + i] = x

    def get(self, n):
        """Return the nth sequence memory data.

        The return value is a list of slot lengths.
        """
        return [self._mem[n + i] for i in range(self._slot)]

    def replace(self, mem):
        """replace.

        Replace referenced memory with external memory.
        """
        if self._mem.is_shape_equal(mem):
            self._mem = mem


class Sequence:
    """Sequence.

    A sequence holds input / output data, operations on the data, and functions
    that are called at the start and end.
    """

    def __init__(self, memory, seqlen, slot=2):
        """Init."""
        self.info = {}
        self.seqlen = seqlen
        self.slot = slot
        self.operands = [None] * seqlen
        self.data = SequenceHead(memory, seqlen, slot)

    def set(self, n, work, *xargs, before=None, after=None):
        """Sets the nth sequence."""
        self.data.set(n, *xargs)
        self.operands[n] = (work, before, after)

    def get(self, n):
        """Return the nth sequence."""
        return {
            "work": self.operands[0],
            "before": self.operands[1],
            "after": self.operands[2],
            "mem": self.data.get(n)
        }

    def iter_get(self, order):
        """Interation get method."""
        if isinstance(order, (list, tuple)):
            for i in order:
                yield self.get(i)
        else:
            for i in range(self.seqlen):
                yield self.get(i)


class SequenceCell(Cell):
    """SequenceCell.

    A sequence cell is a cell of sequencer. When the trigger is entered,
    the sequence specified by self.pos is read and written to self.mem_out.
    self.pos represents the position indicated by the head of the sequence cell.
    """

    def __init__(self, seqlen, slot):
        """Init."""
        super(SequenceCell, self).__init__()
        self.mem_in = SequenceHead.alloc(seqlen, slot)
        self.mem_out = SequenceHead.alloc(1, slot)
        self.pos = 0
        self._seqlen = seqlen
        self._slot = slot
        self._head = SequenceHead(self.mem_in, self._seqlen, self._slot)

    def seek(self, pos):
        """Seek head.

        Change pos to self.pos after reading and writing the sequence of
        the specified pos. If there is no movement to the specified pos-
        ition, False is returned.
        """
        if pos < self._seqlen:
            self.mem_out.write_all(self._head.get(pos))
            self.pos = pos
            return True

        return False

    def run(self):
        """Start."""
        while not self._exit:
            self._trig.wait()
            self.seek(self.pos)
            self._trig.clear()
            self._internal_release()
