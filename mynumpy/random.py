"""
Random number generation
"""

import random as pyrandom
from .array import ndarray
from typing import Union, Tuple


class RandomGenerator:
    """Random number generator with numpy-like interface"""

    def __init__(self, seed=None):
        self._rng = pyrandom.Random(seed)

    def seed(self, seed):
        """Set random seed"""
        self._rng.seed(seed)

    def random(self, size=None) -> Union[float, ndarray]:
        """Random floats in [0.0, 1.0)"""
        if size is None:
            return self._rng.random()

        if isinstance(size, int):
            size = (size,)

        total = 1
        for dim in size:
            total *= dim

        result = ndarray.__new__(ndarray)
        result._data = [self._rng.random() for _ in range(total)]
        result._shape = size
        result.dtype = 'float64'
        return result

    def rand(self, *shape) -> Union[float, ndarray]:
        """Random floats in [0.0, 1.0) with shape as positional args"""
        if not shape:
            return self._rng.random()
        return self.random(shape)

    def randn(self, *shape) -> Union[float, ndarray]:
        """Standard normal distribution"""
        if not shape:
            return self._rng.gauss(0, 1)

        total = 1
        for dim in shape:
            total *= dim

        result = ndarray.__new__(ndarray)
        result._data = [self._rng.gauss(0, 1) for _ in range(total)]
        result._shape = shape
        result.dtype = 'float64'
        return result

    def randint(self, low, high=None, size=None) -> Union[int, ndarray]:
        """Random integers from low (inclusive) to high (exclusive)"""
        if high is None:
            high = low
            low = 0

        if size is None:
            return self._rng.randint(low, high - 1)

        if isinstance(size, int):
            size = (size,)

        total = 1
        for dim in size:
            total *= dim

        result = ndarray.__new__(ndarray)
        result._data = [self._rng.randint(low, high - 1) for _ in range(total)]
        result._shape = size
        result.dtype = 'int64'
        return result

    def uniform(self, low=0.0, high=1.0, size=None) -> Union[float, ndarray]:
        """Uniform distribution over [low, high)"""
        if size is None:
            return self._rng.uniform(low, high)

        if isinstance(size, int):
            size = (size,)

        total = 1
        for dim in size:
            total *= dim

        result = ndarray.__new__(ndarray)
        result._data = [self._rng.uniform(low, high) for _ in range(total)]
        result._shape = size
        result.dtype = 'float64'
        return result

    def normal(self, loc=0.0, scale=1.0, size=None) -> Union[float, ndarray]:
        """Normal (Gaussian) distribution"""
        if size is None:
            return self._rng.gauss(loc, scale)

        if isinstance(size, int):
            size = (size,)

        total = 1
        for dim in size:
            total *= dim

        result = ndarray.__new__(ndarray)
        result._data = [self._rng.gauss(loc, scale) for _ in range(total)]
        result._shape = size
        result.dtype = 'float64'
        return result

    def choice(self, a, size=None, replace=True) -> Union[any, ndarray]:
        """Random sample from array"""
        if isinstance(a, ndarray):
            population = a._data
        elif isinstance(a, int):
            population = list(range(a))
        else:
            population = list(a)

        if size is None:
            return self._rng.choice(population)

        if isinstance(size, int):
            size = (size,)

        total = 1
        for dim in size:
            total *= dim

        if replace:
            data = [self._rng.choice(population) for _ in range(total)]
        else:
            if total > len(population):
                raise ValueError("Cannot take a larger sample than population without replacement")
            data = self._rng.sample(population, total)

        result = ndarray.__new__(ndarray)
        result._data = data
        result._shape = size
        result.dtype = 'float64' if isinstance(data[0], float) else 'int64'
        return result

    def shuffle(self, arr: ndarray) -> None:
        """Shuffle array in place (first axis only)"""
        if arr.ndim == 1:
            self._rng.shuffle(arr._data)
        else:
            # Shuffle along first axis
            stride = arr.size // arr._shape[0]
            chunks = [arr._data[i*stride:(i+1)*stride] for i in range(arr._shape[0])]
            self._rng.shuffle(chunks)
            arr._data = [val for chunk in chunks for val in chunk]

    def permutation(self, x) -> ndarray:
        """Random permutation"""
        if isinstance(x, int):
            data = list(range(x))
            self._rng.shuffle(data)
            result = ndarray.__new__(ndarray)
            result._data = data
            result._shape = (x,)
            result.dtype = 'int64'
            return result
        else:
            result = x.copy()
            self.shuffle(result)
            return result


# Default generator instance
_default_rng = RandomGenerator()


def seed(s):
    """Set random seed"""
    _default_rng.seed(s)


def random(size=None):
    """Random floats in [0.0, 1.0)"""
    return _default_rng.random(size)


def rand(*shape):
    """Random floats in [0.0, 1.0)"""
    return _default_rng.rand(*shape)


def randn(*shape):
    """Standard normal distribution"""
    return _default_rng.randn(*shape)


def randint(low, high=None, size=None):
    """Random integers"""
    return _default_rng.randint(low, high, size)


def uniform(low=0.0, high=1.0, size=None):
    """Uniform distribution"""
    return _default_rng.uniform(low, high, size)


def normal(loc=0.0, scale=1.0, size=None):
    """Normal distribution"""
    return _default_rng.normal(loc, scale, size)


def choice(a, size=None, replace=True):
    """Random choice"""
    return _default_rng.choice(a, size, replace)


def shuffle(arr):
    """Shuffle in place"""
    return _default_rng.shuffle(arr)


def permutation(x):
    """Random permutation"""
    return _default_rng.permutation(x)
