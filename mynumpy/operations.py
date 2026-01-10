"""
Array creation and manipulation operations
"""

from .array import ndarray
from typing import Union, Tuple


def zeros(shape: Union[int, Tuple[int, ...]], dtype='float64') -> ndarray:
    """Create array filled with zeros"""
    if isinstance(shape, int):
        shape = (shape,)

    size = 1
    for dim in shape:
        size *= dim

    result = ndarray.__new__(ndarray)
    result._data = [0.0 if 'float' in dtype else 0] * size
    result._shape = shape
    result.dtype = dtype
    return result


def ones(shape: Union[int, Tuple[int, ...]], dtype='float64') -> ndarray:
    """Create array filled with ones"""
    if isinstance(shape, int):
        shape = (shape,)

    size = 1
    for dim in shape:
        size *= dim

    result = ndarray.__new__(ndarray)
    result._data = [1.0 if 'float' in dtype else 1] * size
    result._shape = shape
    result.dtype = dtype
    return result


def full(shape: Union[int, Tuple[int, ...]], fill_value, dtype=None) -> ndarray:
    """Create array filled with specified value"""
    if isinstance(shape, int):
        shape = (shape,)

    size = 1
    for dim in shape:
        size *= dim

    result = ndarray.__new__(ndarray)
    result._data = [fill_value] * size
    result._shape = shape
    result.dtype = dtype or ('float64' if isinstance(fill_value, float) else 'int64')
    return result


def arange(start, stop=None, step=1, dtype=None) -> ndarray:
    """Create array with evenly spaced values"""
    if stop is None:
        stop = start
        start = 0

    data = []
    current = start
    while (step > 0 and current < stop) or (step < 0 and current > stop):
        data.append(current)
        current += step

    result = ndarray.__new__(ndarray)
    result._data = data
    result._shape = (len(data),)
    result.dtype = dtype or ('float64' if isinstance(step, float) else 'int64')
    return result


def linspace(start, stop, num=50, dtype='float64') -> ndarray:
    """Create array with evenly spaced values over interval"""
    if num < 0:
        raise ValueError("Number of samples must be non-negative")
    if num == 0:
        return zeros(0)
    if num == 1:
        result = ndarray.__new__(ndarray)
        result._data = [float(start)]
        result._shape = (1,)
        result.dtype = dtype
        return result

    step = (stop - start) / (num - 1)
    data = [start + i * step for i in range(num)]
    data[-1] = stop  # Ensure exact endpoint

    result = ndarray.__new__(ndarray)
    result._data = data
    result._shape = (num,)
    result.dtype = dtype
    return result


def reshape(arr: ndarray, shape: Tuple[int, ...]) -> ndarray:
    """Reshape array to new dimensions"""
    return arr.reshape(shape)


def empty(shape: Union[int, Tuple[int, ...]], dtype='float64') -> ndarray:
    """Create uninitialized array (filled with zeros in this implementation)"""
    return zeros(shape, dtype)


def eye(n: int, m=None, k=0, dtype='float64') -> ndarray:
    """Create identity matrix"""
    if m is None:
        m = n

    result = zeros((n, m), dtype)
    for i in range(min(n, m)):
        if 0 <= i + k < m:
            result._data[i * m + i + k] = 1.0 if 'float' in dtype else 1
    return result


def identity(n: int, dtype='float64') -> ndarray:
    """Create square identity matrix"""
    return eye(n, dtype=dtype)


def diag(v: ndarray, k=0) -> ndarray:
    """Extract diagonal or create diagonal matrix"""
    if v.ndim == 1:
        # Create diagonal matrix from 1D array
        n = len(v._data) + abs(k)
        result = zeros((n, n), v.dtype)
        for i, val in enumerate(v._data):
            if k >= 0:
                result._data[i * n + i + k] = val
            else:
                result._data[(i - k) * n + i] = val
        return result
    elif v.ndim == 2:
        # Extract diagonal from 2D array
        rows, cols = v._shape
        diag_len = min(rows, cols - k) if k >= 0 else min(rows + k, cols)
        diag_len = max(0, diag_len)
        data = []
        for i in range(diag_len):
            if k >= 0:
                data.append(v._data[i * cols + i + k])
            else:
                data.append(v._data[(i - k) * cols + i])
        result = ndarray.__new__(ndarray)
        result._data = data
        result._shape = (len(data),)
        result.dtype = v.dtype
        return result
    raise ValueError("Input must be 1D or 2D array")
