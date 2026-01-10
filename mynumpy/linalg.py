"""
Linear algebra functions
"""

import math as pymath
from .array import ndarray
from typing import Union


def norm(x: Union[ndarray, list], ord=None, axis=None, keepdims=False):
    """
    Matrix or vector norm.

    For vectors (1D arrays), computes:
    - ord=None or ord=2: Euclidean norm (L2)
    - ord=1: Sum of absolute values (L1)
    - ord=inf: Maximum absolute value

    For matrices (2D arrays), computes Frobenius norm by default.
    """
    if isinstance(x, list):
        from .array import array
        x = array(x)

    if axis is not None:
        raise NotImplementedError("axis parameter not yet implemented for norm")

    data = x._data

    if ord is None or ord == 2:
        # Euclidean norm (L2)
        return pymath.sqrt(sum(val * val for val in data))
    elif ord == 1:
        # L1 norm
        return sum(abs(val) for val in data)
    elif ord == float('inf'):
        # Infinity norm
        return max(abs(val) for val in data)
    elif ord == -float('inf'):
        return min(abs(val) for val in data)
    elif isinstance(ord, (int, float)):
        # General p-norm
        return sum(abs(val) ** ord for val in data) ** (1.0 / ord)
    else:
        raise ValueError(f"Invalid norm order: {ord}")


def dot(a: ndarray, b: ndarray):
    """Dot product of two arrays"""
    from .math import dot as math_dot
    return math_dot(a, b)


def inv(a: ndarray) -> ndarray:
    """
    Compute inverse of a matrix (2x2 only for now).
    """
    if a.ndim != 2 or a._shape[0] != a._shape[1]:
        raise ValueError("Input must be a square matrix")

    n = a._shape[0]
    if n == 2:
        # 2x2 matrix inverse
        a11, a12, a21, a22 = a._data
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-10:
            raise ValueError("Singular matrix")
        result = ndarray.__new__(ndarray)
        result._data = [a22 / det, -a12 / det, -a21 / det, a11 / det]
        result._shape = (2, 2)
        result.dtype = 'float64'
        return result

    raise NotImplementedError("Matrix inverse only implemented for 2x2 matrices")


def det(a: ndarray) -> float:
    """
    Compute determinant of a matrix (up to 3x3).
    """
    if a.ndim != 2 or a._shape[0] != a._shape[1]:
        raise ValueError("Input must be a square matrix")

    n = a._shape[0]
    if n == 1:
        return a._data[0]
    elif n == 2:
        return a._data[0] * a._data[3] - a._data[1] * a._data[2]
    elif n == 3:
        # 3x3 determinant using rule of Sarrus
        m = a._data
        return (m[0] * m[4] * m[8] + m[1] * m[5] * m[6] + m[2] * m[3] * m[7]
                - m[2] * m[4] * m[6] - m[1] * m[3] * m[8] - m[0] * m[5] * m[7])

    raise NotImplementedError("Determinant only implemented for matrices up to 3x3")


def eig(a: ndarray):
    """
    Compute eigenvalues (2x2 only).
    Returns (eigenvalues, eigenvectors) but eigenvectors not fully implemented.
    """
    if a.ndim != 2 or a._shape != (2, 2):
        raise NotImplementedError("Eigenvalue decomposition only implemented for 2x2")

    a11, a12, a21, a22 = a._data
    trace = a11 + a22
    det_val = a11 * a22 - a12 * a21

    discriminant = trace * trace - 4 * det_val
    if discriminant < 0:
        raise ValueError("Complex eigenvalues not supported")

    sqrt_disc = pymath.sqrt(discriminant)
    eig1 = (trace + sqrt_disc) / 2
    eig2 = (trace - sqrt_disc) / 2

    result = ndarray.__new__(ndarray)
    result._data = [eig1, eig2]
    result._shape = (2,)
    result.dtype = 'float64'

    # Placeholder for eigenvectors
    vecs = ndarray.__new__(ndarray)
    vecs._data = [1.0, 0.0, 0.0, 1.0]
    vecs._shape = (2, 2)
    vecs.dtype = 'float64'

    return result, vecs


def solve(a: ndarray, b: ndarray) -> ndarray:
    """
    Solve linear system ax = b for x (2x2 only).
    """
    if a._shape != (2, 2):
        raise NotImplementedError("solve only implemented for 2x2 systems")

    a_inv = inv(a)
    from .math import dot
    return dot(a_inv, b)


def matrix_rank(a: ndarray) -> int:
    """
    Estimate matrix rank (simplified).
    """
    # Simplified: count non-zero rows
    if a.ndim == 1:
        return 1 if any(v != 0 for v in a._data) else 0

    rows = a._shape[0]
    cols = a._shape[1]
    rank = 0
    for i in range(rows):
        row_start = i * cols
        row_end = row_start + cols
        if any(a._data[row_start:row_end]):
            rank += 1
    return min(rank, cols)
