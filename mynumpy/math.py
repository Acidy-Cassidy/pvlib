"""
Mathematical operations
"""

import math as pymath
from .array import ndarray
from typing import Union

# Save reference to built-in sum before we shadow it
_builtin_sum = sum


def sum(arr: ndarray, axis=None):
    """Sum of array elements"""
    return arr.sum(axis)


def mean(arr: ndarray, axis=None):
    """Mean of array elements"""
    return arr.mean(axis)


def min(arr: ndarray, axis=None):
    """Minimum of array elements"""
    return arr.min(axis)


def max(arr: ndarray, axis=None):
    """Maximum of array elements"""
    return arr.max(axis)


def std(arr: ndarray, axis=None):
    """Standard deviation of array elements"""
    return arr.std(axis)


def var(arr: ndarray, axis=None):
    """Variance of array elements"""
    return arr.var(axis)


def sqrt(arr: Union[ndarray, int, float]) -> ndarray:
    """Element-wise square root"""
    if isinstance(arr, (int, float)):
        return pymath.sqrt(arr)
    result = arr.copy()
    result._data = [pymath.sqrt(x) for x in result._data]
    return result


def abs(arr: Union[ndarray, int, float]) -> ndarray:
    """Element-wise absolute value"""
    if isinstance(arr, (int, float)):
        return pymath.fabs(arr)
    result = arr.copy()
    result._data = [pymath.fabs(x) for x in result._data]
    return result


def power(arr: ndarray, exponent) -> ndarray:
    """Element-wise power"""
    return arr ** exponent


def exp(arr: Union[ndarray, int, float]) -> ndarray:
    """Element-wise exponential"""
    if isinstance(arr, (int, float)):
        return pymath.exp(arr)
    result = arr.copy()
    result._data = [pymath.exp(x) for x in result._data]
    return result


def log(arr: Union[ndarray, int, float]) -> ndarray:
    """Element-wise natural logarithm"""
    if isinstance(arr, (int, float)):
        return pymath.log(arr)
    result = arr.copy()
    result._data = [pymath.log(x) for x in result._data]
    return result


def log10(arr: Union[ndarray, int, float]) -> ndarray:
    """Element-wise base-10 logarithm"""
    if isinstance(arr, (int, float)):
        return pymath.log10(arr)
    result = arr.copy()
    result._data = [pymath.log10(x) for x in result._data]
    return result


def sin(arr: Union[ndarray, int, float]) -> ndarray:
    """Element-wise sine"""
    if isinstance(arr, (int, float)):
        return pymath.sin(arr)
    result = arr.copy()
    result._data = [pymath.sin(x) for x in result._data]
    return result


def cos(arr: Union[ndarray, int, float]) -> ndarray:
    """Element-wise cosine"""
    if isinstance(arr, (int, float)):
        return pymath.cos(arr)
    result = arr.copy()
    result._data = [pymath.cos(x) for x in result._data]
    return result


def tan(arr: Union[ndarray, int, float]) -> ndarray:
    """Element-wise tangent"""
    if isinstance(arr, (int, float)):
        return pymath.tan(arr)
    result = arr.copy()
    result._data = [pymath.tan(x) for x in result._data]
    return result


def dot(a: ndarray, b: ndarray):
    """Dot product of two arrays"""
    if a.ndim == 1 and b.ndim == 1:
        # Vector dot product
        if len(a._data) != len(b._data):
            raise ValueError("Vectors must have same length")
        return _builtin_sum(x * y for x, y in zip(a._data, b._data))

    if a.ndim == 2 and b.ndim == 2:
        # Matrix multiplication
        if a._shape[1] != b._shape[0]:
            raise ValueError(f"Matrix shapes {a._shape} and {b._shape} not aligned")

        m, k = a._shape
        k2, n = b._shape
        result_data = []

        for i in range(m):
            for j in range(n):
                val = 0
                for p in range(k):
                    val += a._data[i * k + p] * b._data[p * n + j]
                result_data.append(val)

        result = ndarray.__new__(ndarray)
        result._data = result_data
        result._shape = (m, n)
        result.dtype = 'float64'
        return result

    if a.ndim == 2 and b.ndim == 1:
        # Matrix-vector multiplication
        if a._shape[1] != len(b._data):
            raise ValueError("Shapes not aligned")

        m, k = a._shape
        result_data = []
        for i in range(m):
            val = 0
            for j in range(k):
                val += a._data[i * k + j] * b._data[j]
            result_data.append(val)

        result = ndarray.__new__(ndarray)
        result._data = result_data
        result._shape = (m,)
        result.dtype = 'float64'
        return result

    raise NotImplementedError("dot not implemented for these dimensions")


def matmul(a: ndarray, b: ndarray) -> ndarray:
    """Matrix multiplication (@ operator)"""
    return dot(a, b)


def clip(arr: ndarray, a_min, a_max) -> ndarray:
    """Clip values to range"""
    result = arr.copy()
    result._data = [max(a_min, min(a_max, x)) for x in result._data]
    return result


def floor(arr: Union[ndarray, int, float]) -> ndarray:
    """Element-wise floor"""
    if isinstance(arr, (int, float)):
        return pymath.floor(arr)
    result = arr.copy()
    result._data = [pymath.floor(x) for x in result._data]
    return result


def ceil(arr: Union[ndarray, int, float]) -> ndarray:
    """Element-wise ceiling"""
    if isinstance(arr, (int, float)):
        return pymath.ceil(arr)
    result = arr.copy()
    result._data = [pymath.ceil(x) for x in result._data]
    return result


def round(arr: Union[ndarray, int, float], decimals=0) -> ndarray:
    """Element-wise rounding"""
    if isinstance(arr, (int, float)):
        return pymath.floor(arr * 10**decimals + 0.5) / 10**decimals
    result = arr.copy()
    result._data = [pymath.floor(x * 10**decimals + 0.5) / 10**decimals for x in result._data]
    return result
