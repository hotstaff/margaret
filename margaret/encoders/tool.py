# Copyright 2017 Hideto Manjo.
#
# Licensed under the MIT License

"""Vector transform function modules."""

# numpy
import numpy as np


class Tool:
    """Tool.

    The numpy array trasform functions class: (Tool)
    int means int scalor value  -> 1
    hot means one hot vector of numpy.float32 -> array([0.0, 1.0, 0.0])
    bin means 0 or 1 vector of numpy.float32 -> array([0.0, 1.0, 1.0])
    arg means float vector of numpy.float32 -> array([0.432223, 0.513513])

    Usage:

    int2hot means that the input is signed int scalor and output is hot vector
        Example: int2hot(0, 4) -> [0, 0, 1, 0]
    """

    @staticmethod
    def int2hot(number, width):
        """Int2hot.

        from int

        returns one hot vector
        The index number of one hot vector corresponds following rules.
        Example:
         [out of range, -1, 0, 1] if width 4.
        index 0 : out of range flag
        index 1 : minimum value < 0
        index end: maximum value > 0
        index (end-2)/2: zero
        """
        num = int(number)
        maxvalue = int(int(width) - 2)/2

        if maxvalue < 0:
            return None

        vec = np.zeros((maxvalue)*2 + 2, dtype=np.float32)

        if abs(num) < maxvalue + 1:
            if num == 0:
                vec[1 + maxvalue] = 1.0
            else:
                vec[1 + num + maxvalue] = 1.0

            return vec

        vec[0] = 1.0
        return vec

    @staticmethod
    def int2bin(number, width):
        """Int2bin.

        from int

        returns binary vector np.float32 array
        """
        return np.array(map(int, list(np.binary_repr(int(number), width))),
                        dtype=np.float32)

    @staticmethod
    def hot2int(vec):
        """Hot2int.

        from hot vector

        returns signed int
        """
        length = len(vec)
        maxvalue = int((length - 2) / 2)
        if length % 2 == 0 and length > 2:
            i = np.argmax(vec)
            if i == 0:
                return None
            return i - maxvalue - 1

        return None

    @staticmethod
    def hot2uint(vec):
        """Hot2uint.

        from hot vector

        returns uint
        """
        return np.argmax(vec)

    @staticmethod
    def bin2uint(uintarray):
        """Bin2int.

        from binary vector

        returns uint32
        """
        square = 2**np.arange(uintarray.shape[0])[::-1]
        return np.dot(uintarray, square).astype(np.uint32)

    @classmethod
    def bin2int(cls, binvec):
        """Bin2int.

        from binary vector

        returns int
        """
        boolarray = binvec.astype(np.bool)
        one = np.array([0]*(len(boolarray) - 1) + [1], dtype=np.bool)
        if boolarray[0] is False:
            return cls.bin2uint(boolarray)
        return -(cls.bin2uint(np.bitwise_and(np.invert(boolarray), one)))

    @staticmethod
    def arg2bin(hotvec, threshold=0.5):
        """Arg2bin.

        from arg(float) vector

        returns binary vector
        """
        binaryvec = np.zeros(hotvec.shape[0], dtype=np.float32)
        binaryvec[np.where(hotvec >= threshold)] = 1
        return binaryvec

    @classmethod
    def arg2binauto(cls, hotvec):
        """Arg2binauto.

        from arg(float) vector

        returns binary vector(auto threshold)
        """
        threshold = hotvec.sum()/hotvec.shape[0]
        return cls.arg2bin(hotvec, threshold)

    @staticmethod
    def arg2hot(vec):
        """Arg2hot.

        from arg(float) vector

        returns one hot vector
        """
        ret = np.zeros(vec.shape[0], dtype=np.float32)
        max_x = np.argmax(vec)
        ret[max_x] = 1.0
        return ret

    @staticmethod
    def arg2digitize(vec, levelarray=np.array([0])):
        """Arg2digitize.

        from arg(float) vector

        returns degitized vector np.float32 array
        """
        return np.array(np.digitize(vec, levelarray), dtype=np.float32)

    @staticmethod
    def uint2hot(number, width):
        """Uint2hot.

        from uint

        returns hot vector
        """
        ret = np.zeros(width, dtype=np.float32)
        ret[int(number)] = 1.0
        return ret

    @classmethod
    def uint2log(cls, number, width):
        """Uint2log.

        from uint

        returns log vector
        """
        if width < 3:
            return None
        if number == 0:
            log2val = 0
        else:
            log2val = np.log2(number)
        degit = int(log2val)
        hotdegit = cls.uint2hot(degit, width-1)
        few = np.array([log2val - degit], dtype=np.float32)
        return np.concatenate((few, hotdegit))

    @classmethod
    def log2uint(cls, logvec):
        """Log2uint.

        from log

        returns uint
        """
        log2val = logvec[0] + cls.hot2uint(logvec[1:])
        return 2**log2val

    @staticmethod
    def rsquare(measured_vec, estimated_vec):
        """Rsquare.
        
        from mesured and estimated vector
        returns R^2
        """
        measured_mean = np.mean(measured_vec)
        top = np.sum((measured_vec - estimated_vec)**2)
        bottom = np.sum((measured_vec - measured_mean)**2)
        if bottom == 0:
            return -float("inf")
        return 1 - (top/bottom)


class Cache:
    """Cache.

    cached return function
    """

    def __init__(self):
        """Init."""
        self.cache = []

    def get(self):
        """Get."""
        if self.cache:
            return self.cache[-1]
        return None

    def set(self, vec):
        """Set."""
        self.cache.append(vec)
        return self.cache[-1]

    def reset(self):
        """Reset cache."""
        self.cache = []

    def before(self, vec, number=1):
        """Before.

        Append cash and return before vector.
        """
        if len(self.cache) < int(number):
            return None
        self.cache.append(vec)
        return self.cache[-int(number)-1]

    def diff(self, vec):
        """Diff.

        Return diff of previous and current vector.
        """
        if self.cache is False:
            self.cache.append(vec)
            return vec
        return vec - self.before(vec)
