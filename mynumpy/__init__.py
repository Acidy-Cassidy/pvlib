"""
mynumpy - Your custom numpy library
"""

import math as _math

from .array import array, ndarray
from .operations import zeros, ones, arange, linspace, reshape, eye, identity, diag, full, empty
from .math import (sum, mean, min, max, dot, sqrt, abs, power, exp, log, log10,
                   sin, cos, tan, clip, matmul, floor, ceil, round, std, var)
from .utils import concatenate, stack, vstack, hstack, split, where, argmax, argmin, argsort, sort, unique, flatten
from . import random
from . import linalg


def asarray(a, dtype=None):
    """Convert input to ndarray"""
    if isinstance(a, ndarray):
        if dtype is None or dtype == a.dtype:
            return a
        # Convert dtype
        result = a.copy()
        result.dtype = dtype
        return result
    return array(a, dtype=dtype)


def astype(arr, dtype):
    """Cast array to specified type"""
    result = arr.copy()
    type_map = {
        'float32': float, 'float64': float, float: float,
        'int32': int, 'int64': int, int: int,
    }
    converter = type_map.get(dtype, lambda x: x)
    result._data = [converter(x) for x in result._data]
    result.dtype = dtype if isinstance(dtype, str) else 'float64'
    return result


# Constants
pi = _math.pi
e = _math.e
inf = float('inf')
nan = float('nan')
newaxis = None

# Data types (simplified)
float64 = 'float64'
float32 = 'float32'
int64 = 'int64'
int32 = 'int32'
bool_ = 'bool'

__version__ = "0.1.0"
__all__ = [
    "array", "ndarray", "asarray", "astype",
    "zeros", "ones", "arange", "linspace", "reshape", "eye", "identity", "diag", "full", "empty",
    "sum", "mean", "min", "max", "dot", "sqrt", "abs", "power", "exp", "log", "log10",
    "sin", "cos", "tan", "clip", "matmul", "floor", "ceil", "round", "std", "var",
    "concatenate", "stack", "vstack", "hstack", "split", "where", "argmax", "argmin", "argsort", "sort", "unique", "flatten",
    "random", "linalg",
    "pi", "e", "inf", "nan", "newaxis",
    "float64", "float32", "int64", "int32", "bool_",
]
