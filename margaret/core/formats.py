# Copyright 2019 Hideto Manjo.
#
# Licensed under the MIT License

"""Core formats module.

This module defines the formats for serializing to communicate between modules.
"""

import numpy as np

class ListNumpyFormat:
    """Numpy ndarray list exchange dict.

    This class encode or decode list(numpy.ndarray) for speedup.
    Since ndarray is sent after stacking, the element shape and dtype
    must be the same.
    """

    @staticmethod
    def _typecheck(item):
        if not isinstance(item, list):
            raise TypeError("Type check error.")

    @staticmethod
    def encode(array_list):
        """Encode."""
        ListNumpyFormat._typecheck(array_list)
        array = np.concatenate(array_list)
        ret = {
            "array": array.tobytes(),
            "dtype": str(array.dtype),
            "shape": array.shape,
            "length": len(array_list),
        }
        return ret

    @staticmethod
    def decode(item):
        """Decode."""
        array = np.frombuffer(item["array"], item["dtype"])
        return np.array_split(array.reshape(item["shape"]), item["length"], 0)

class NumpyFormat:
    """Numpy ndarray exchange dict."""

    @staticmethod
    def _typecheck(item):
        if not isinstance(item, np.ndarray):
            raise TypeError("Type check error.")

    @staticmethod
    def encode(array):
        """Encode."""
        NumpyFormat._typecheck(array)
        ret = {
            "array": array.tobytes(),
            "dtype": str(array.dtype),
            "shape": array.shape,
        }
        return ret

    @staticmethod
    def decode(item):
        """Decode."""
        array = np.frombuffer(item["array"], item["dtype"])
        return array.reshape(item["shape"])
