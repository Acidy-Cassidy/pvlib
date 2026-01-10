"""
Array utility functions
"""

from .array import ndarray
from typing import List, Union, Tuple


def concatenate(arrays: List[ndarray], axis=0) -> ndarray:
    """Join arrays along an axis"""
    if not arrays:
        raise ValueError("Need at least one array to concatenate")

    if axis == 0:
        # Concatenate along first axis
        if arrays[0].ndim == 1:
            new_data = []
            for arr in arrays:
                new_data.extend(arr._data)
            result = ndarray.__new__(ndarray)
            result._data = new_data
            result._shape = (len(new_data),)
            result.dtype = arrays[0].dtype
            return result
        else:
            new_data = []
            total_rows = 0
            cols = arrays[0]._shape[1]
            for arr in arrays:
                if arr._shape[1] != cols:
                    raise ValueError("All arrays must have same number of columns")
                new_data.extend(arr._data)
                total_rows += arr._shape[0]
            result = ndarray.__new__(ndarray)
            result._data = new_data
            result._shape = (total_rows, cols)
            result.dtype = arrays[0].dtype
            return result
    elif axis == 1:
        if arrays[0].ndim != 2:
            raise ValueError("axis=1 requires 2D arrays")
        rows = arrays[0]._shape[0]
        for arr in arrays:
            if arr._shape[0] != rows:
                raise ValueError("All arrays must have same number of rows")

        new_data = []
        new_cols = sum(arr._shape[1] for arr in arrays)
        for i in range(rows):
            for arr in arrays:
                cols = arr._shape[1]
                new_data.extend(arr._data[i * cols:(i + 1) * cols])

        result = ndarray.__new__(ndarray)
        result._data = new_data
        result._shape = (rows, new_cols)
        result.dtype = arrays[0].dtype
        return result

    raise ValueError(f"axis {axis} not supported")


def stack(arrays: List[ndarray], axis=0) -> ndarray:
    """Stack arrays along a new axis"""
    if not arrays:
        raise ValueError("Need at least one array to stack")

    shape = arrays[0]._shape
    for arr in arrays:
        if arr._shape != shape:
            raise ValueError("All arrays must have same shape")

    if axis == 0:
        new_data = []
        for arr in arrays:
            new_data.extend(arr._data)
        result = ndarray.__new__(ndarray)
        result._data = new_data
        result._shape = (len(arrays),) + shape
        result.dtype = arrays[0].dtype
        return result

    raise NotImplementedError(f"stack with axis={axis} not implemented")


def vstack(arrays: List[ndarray]) -> ndarray:
    """Stack arrays vertically (row-wise)"""
    processed = []
    for arr in arrays:
        if arr.ndim == 1:
            # Convert 1D to 2D row
            new_arr = ndarray.__new__(ndarray)
            new_arr._data = arr._data.copy()
            new_arr._shape = (1, len(arr._data))
            new_arr.dtype = arr.dtype
            processed.append(new_arr)
        else:
            processed.append(arr)
    return concatenate(processed, axis=0)


def hstack(arrays: List[ndarray]) -> ndarray:
    """Stack arrays horizontally (column-wise)"""
    if arrays[0].ndim == 1:
        return concatenate(arrays, axis=0)
    return concatenate(arrays, axis=1)


def split(arr: ndarray, indices_or_sections, axis=0) -> List[ndarray]:
    """Split array into multiple sub-arrays"""
    if isinstance(indices_or_sections, int):
        # Split into equal parts
        n = indices_or_sections
        if axis == 0:
            size = arr._shape[0]
            if size % n != 0:
                raise ValueError(f"Array of size {size} cannot be split into {n} equal parts")
            chunk_size = size // n
            indices = [i * chunk_size for i in range(1, n)]
        else:
            raise NotImplementedError("split with axis != 0 not fully implemented")
    else:
        indices = list(indices_or_sections)

    result = []
    prev = 0
    for idx in indices + [arr._shape[0]]:
        if arr.ndim == 1:
            chunk = ndarray.__new__(ndarray)
            chunk._data = arr._data[prev:idx]
            chunk._shape = (idx - prev,)
            chunk.dtype = arr.dtype
        else:
            cols = arr._shape[1]
            chunk = ndarray.__new__(ndarray)
            chunk._data = arr._data[prev * cols:idx * cols]
            chunk._shape = (idx - prev, cols)
            chunk.dtype = arr.dtype
        result.append(chunk)
        prev = idx

    return result


def where(condition, x=None, y=None):
    """Return elements based on condition"""
    if x is None and y is None:
        # Return indices where condition is True
        if isinstance(condition, ndarray):
            indices = [i for i, v in enumerate(condition._data) if v]
            result = ndarray.__new__(ndarray)
            result._data = indices
            result._shape = (len(indices),)
            result.dtype = 'int64'
            return (result,)
        raise TypeError("condition must be ndarray")

    # Return x where condition is True, else y
    if isinstance(condition, ndarray):
        cond_data = condition._data
    else:
        cond_data = [condition]

    if isinstance(x, ndarray):
        x_data = x._data
    else:
        x_data = [x] * len(cond_data)

    if isinstance(y, ndarray):
        y_data = y._data
    else:
        y_data = [y] * len(cond_data)

    result_data = [x_data[i] if cond_data[i] else y_data[i] for i in range(len(cond_data))]

    result = ndarray.__new__(ndarray)
    result._data = result_data
    result._shape = condition._shape if isinstance(condition, ndarray) else (len(result_data),)
    result.dtype = 'float64'
    return result


def argmax(arr: ndarray, axis=None):
    """Return index of maximum value"""
    if axis is None:
        max_val = arr._data[0]
        max_idx = 0
        for i, v in enumerate(arr._data):
            if v > max_val:
                max_val = v
                max_idx = i
        return max_idx
    raise NotImplementedError("argmax with axis not implemented")


def argmin(arr: ndarray, axis=None):
    """Return index of minimum value"""
    if axis is None:
        min_val = arr._data[0]
        min_idx = 0
        for i, v in enumerate(arr._data):
            if v < min_val:
                min_val = v
                min_idx = i
        return min_idx
    raise NotImplementedError("argmin with axis not implemented")


def argsort(arr: ndarray, axis=-1) -> ndarray:
    """Return indices that would sort the array"""
    if arr.ndim == 1 or axis == -1:
        indices = sorted(range(len(arr._data)), key=lambda i: arr._data[i])
        result = ndarray.__new__(ndarray)
        result._data = indices
        result._shape = (len(indices),)
        result.dtype = 'int64'
        return result
    raise NotImplementedError("argsort with axis not implemented")


def sort(arr: ndarray, axis=-1) -> ndarray:
    """Return sorted array"""
    if arr.ndim == 1:
        result = ndarray.__new__(ndarray)
        result._data = sorted(arr._data)
        result._shape = arr._shape
        result.dtype = arr.dtype
        return result
    raise NotImplementedError("sort for multi-dimensional arrays not implemented")


def unique(arr: ndarray, return_counts=False, return_index=False):
    """Return unique elements"""
    seen = {}
    unique_vals = []
    indices = []
    counts = []

    for i, v in enumerate(arr._data):
        if v not in seen:
            seen[v] = len(unique_vals)
            unique_vals.append(v)
            indices.append(i)
            counts.append(1)
        else:
            counts[seen[v]] += 1

    result = ndarray.__new__(ndarray)
    result._data = unique_vals
    result._shape = (len(unique_vals),)
    result.dtype = arr.dtype

    returns = [result]
    if return_index:
        idx_arr = ndarray.__new__(ndarray)
        idx_arr._data = indices
        idx_arr._shape = (len(indices),)
        idx_arr.dtype = 'int64'
        returns.append(idx_arr)
    if return_counts:
        count_arr = ndarray.__new__(ndarray)
        count_arr._data = counts
        count_arr._shape = (len(counts),)
        count_arr.dtype = 'int64'
        returns.append(count_arr)

    if len(returns) == 1:
        return returns[0]
    return tuple(returns)


def flatten(arr: ndarray) -> ndarray:
    """Flatten array to 1D"""
    return arr.flatten()


def copy(arr: ndarray) -> ndarray:
    """Return a copy of the array"""
    return arr.copy()


def transpose(arr: ndarray, axes=None) -> ndarray:
    """Transpose array"""
    if axes is not None:
        raise NotImplementedError("transpose with custom axes not implemented")
    return arr.T


def squeeze(arr: ndarray, axis=None) -> ndarray:
    """Remove single-dimensional entries from shape"""
    new_shape = tuple(d for d in arr._shape if d != 1)
    if not new_shape:
        new_shape = (1,)
    result = arr.copy()
    result._shape = new_shape
    return result


def expand_dims(arr: ndarray, axis) -> ndarray:
    """Expand dimensions of array"""
    new_shape = list(arr._shape)
    if axis < 0:
        axis = len(new_shape) + axis + 1
    new_shape.insert(axis, 1)
    result = arr.copy()
    result._shape = tuple(new_shape)
    return result
