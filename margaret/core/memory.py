# coding: UTF-8
# Copyright 2017 Hideto Manjo.
#
# Licensed under the MIT License

"""Virtual memory module."""

from collections import deque
import numpy as np

from margaret.core.formats import NumpyFormat


class VirtualMemory:
    """Virtual Memory.

    This module provides a virtual memory for connecting neural networks.
    Neural network functions as an asynchronous process by replacing the
     neural network I / O with this memory.
    This memory module can be locked externally. All normal reads and wr-
    ites are blocked and will not be returned unless unlocked. This func-
    tion is used for exclusive reading of memory data.
    """

    def __init__(self, slot=3):
        """Init."""
        self._memory = None
        self._slot = slot
        self.clear()

    @classmethod
    def __typecheck(cls, data, memory):
        if not isinstance(data, np.ndarray):
            return False

        if memory is not None:
            if memory.dtype != data.dtype:
                return False
            if memory.shape != data.shape:
                return False

        return True

    @staticmethod
    def list2axis(np_list):
        """List to numpy new axis 0."""
        return np.stack(np_list)

    @staticmethod
    def axis2list(np_array):
        """First axis to list."""
        return list(np_array)

    def is_shape_equal(self, memory):
        """Test whether the given memory shape fits."""
        own_shape = self.shape()
        other_shape = memory.shape()

        if len(own_shape) != len(other_shape):
            return False
        for own, other in zip(self.shape(), memory.shape()):
            if own != other:
                return False
        return True

    def is_slot_equal(self, memory):
        """Test whether the given memory shape fits."""
        if self._slot != len(memory.shape()):
            return False
        return True

    def clear(self, slot=None):
        """Clear memory and typecheck."""
        if slot is None:
            self._memory = deque([None] * self._slot)
        else:
            self._memory[slot] = None

    def __getitem__(self, slot):
        """Read."""
        return self.read(slot)

    def __setitem__(self, slot, data):
        """Write."""
        self.write(slot, data)

    def read(self, slot):
        """Read."""
        return self._memory[slot]

    def write(self, slot, data, force=False):
        """Write."""
        if force and not self.__typecheck(data, self._memory[slot]):
            raise TypeError("Virtual memory type check error.")
        self._memory[slot] = data

    def read_all(self):
        """Read all."""
        return list(self._memory)

    def write_all(self, memory, force=False):
        """Write all."""
        for i, array in enumerate(memory):
            self.write(i, array, force)

    def read_list(self, slot):
        """Read as first index is mini batch dimension."""
        return self.axis2list(self.read(slot))

    def write_list(self, slot, data):
        """Write as first index is mini batch dimension."""
        self.write(slot, self.list2axis(data))

    def dump(self):
        """Dump memory data."""
        return [NumpyFormat.encode(array) for array in self._memory]

    def load(self, item_list):
        """Load memory data."""
        new_memory = deque([NumpyFormat.decode(item) for item in item_list])
        self._slot = len(new_memory)
        self._memory = new_memory

    def shape(self):
        """Return shape and dtype informations of memory."""
        ret = []
        for mem in self._memory:
            if isinstance(mem, np.ndarray):
                ret.append((mem.shape, mem.dtype))
            else:
                ret.append(None)
        return tuple(ret)

    def info(self):
        """Return info string of the memory."""
        message = []
        for i, item in enumerate(self.shape()):
            if item is not None:
                message.append("slot: {0}, shape: {1}, dtype: {2}"
                               .format(i, item[0], item[1]))
            else:
                message.append("slot: {0}, not set.".format(i))

        return "\n".join(message)

if __name__ == "__main__":
    M = VirtualMemory()
    t = np.ones((1, 1), dtype=np.float32)
    M.write(0, t)
    M.write(1, t)
    print("-TEST-")
    print(M.read(0) is not None)
    print(M.read(2) is None)
    print(M.info())
