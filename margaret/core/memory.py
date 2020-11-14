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
    neural network I/O with this memory.
    """

    def __init__(self, slot=3):
        """Init."""
        # zero array
        self.__zero = np.zeros((1, ), np.float32)

        self._memory = None
        self._slot = slot
        self.clear()

    @classmethod
    def __typecheck(cls, data, memory):
        if not isinstance(data, np.ndarray):
            return False

        if memory.dtype != data.dtype:
            return False
        if memory.shape != data.shape:
            return False

        return True

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
            self._memory = deque([self.__zero] * self._slot)
        else:
            self._memory[slot] = self.__zero

    def set(self, slot, shape, dtype):
        """Set shape and dtype"""
        if self._slot >= slot:
            self._memory[slot] = np.zeros(shape, dtype=dtype)

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
        if not force and not self.__typecheck(data, self._memory[slot]):
            mem = self._memory[slot]
            raise TypeError("Virtual memory type check error.\n"
                            f"input: {data.shape}, {data.dtype}\n"
                            f"mem  : {mem.shape}, {mem.dtype}")
        self._memory[slot] = data

    def read_all(self):
        """Read all."""
        return list(self._memory)

    def write_all(self, memory, force=False):
        """Write all."""
        for i, array in enumerate(memory):
            self.write(i, array, force)

    def shape(self, slot=None):
        """Return shape and dtype informations of memory."""

        if (slot is not None) and (self._slot >= slot):
            mem = self._memory[slot]
            return (mem.shape, mem.dtype)

        return tuple([(mem.shape, mem.dtype) for mem in self._memory])

    def info(self):
        """Return info string of the memory."""
        message = []
        for i, item in enumerate(self.shape()):
            message.append("slot: {0}, shape: {1}, dtype: {2}"
                           .format(i, item[0], item[1]))

        return "\n".join(message)

if __name__ == "__main__":
    # Module test
    # Please run below command for module testing.
    # python -m margaret.core.memory
    #

    M = VirtualMemory()
    t = np.ones((1, 1), dtype=np.float32)
    zero = np.zeros((1,), dtype=np.float32)
    M.set(0, t.shape, t.dtype)
    M.set(1, t.shape, t.dtype)
    M.write(0, t)
    M.write(1, t)
    print("-TEST-")
    print(np.allclose(M.read(0), M.read(1)))
    print(np.allclose(M.read(2), zero))
    print(M.info())
