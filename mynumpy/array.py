"""
Core ndarray implementation
"""

from typing import Union, List, Tuple, Any
import math


class ndarray:
    """N-dimensional array object"""

    def __init__(self, data: Union[List, 'ndarray'], dtype=None):
        if isinstance(data, ndarray):
            self._data = data._data.copy() if isinstance(data._data, list) else data._data
            self._shape = data._shape
        else:
            self._data, self._shape = self._flatten_and_shape(data)
        self.dtype = dtype or self._infer_dtype()

    def _flatten_and_shape(self, data: Any) -> Tuple[List, Tuple]:
        """Flatten nested list and determine shape"""
        if not isinstance(data, (list, tuple)):
            return [data], (1,)

        shape = []
        current = data
        while isinstance(current, (list, tuple)) and len(current) > 0:
            shape.append(len(current))
            current = current[0]

        flat = self._recursive_flatten(data)
        return flat, tuple(shape)

    def _recursive_flatten(self, data: Any) -> List:
        """Recursively flatten nested structure"""
        if not isinstance(data, (list, tuple)):
            return [data]
        result = []
        for item in data:
            result.extend(self._recursive_flatten(item))
        return result

    def _infer_dtype(self) -> str:
        """Infer data type from values"""
        if not self._data:
            return 'float64'
        sample = self._data[0]
        if isinstance(sample, float):
            return 'float64'
        elif isinstance(sample, int):
            return 'int64'
        elif isinstance(sample, bool):
            return 'bool'
        return 'object'

    @property
    def shape(self) -> Tuple[int, ...]:
        return self._shape

    @property
    def ndim(self) -> int:
        return len(self._shape)

    @property
    def size(self) -> int:
        result = 1
        for dim in self._shape:
            result *= dim
        return result

    @property
    def T(self) -> 'ndarray':
        """Transpose for 2D arrays"""
        if self.ndim != 2:
            return self.copy()
        rows, cols = self._shape
        new_data = []
        for j in range(cols):
            for i in range(rows):
                new_data.append(self._data[i * cols + j])
        result = ndarray.__new__(ndarray)
        result._data = new_data
        result._shape = (cols, rows)
        result.dtype = self.dtype
        return result

    def copy(self) -> 'ndarray':
        result = ndarray.__new__(ndarray)
        result._data = self._data.copy()
        result._shape = self._shape
        result.dtype = self.dtype
        return result

    def reshape(self, *shape) -> 'ndarray':
        """Reshape array to new dimensions"""
        if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
            shape = tuple(shape[0])

        new_size = 1
        for dim in shape:
            new_size *= dim

        if new_size != self.size:
            raise ValueError(f"Cannot reshape array of size {self.size} into shape {shape}")

        result = self.copy()
        result._shape = shape
        return result

    def flatten(self) -> 'ndarray':
        """Return a flattened copy"""
        result = self.copy()
        result._shape = (self.size,)
        return result

    def tolist(self) -> List:
        """Convert to nested Python list"""
        if self.ndim == 1:
            return self._data.copy()
        return self._build_nested(self._data, self._shape)

    def _build_nested(self, flat: List, shape: Tuple) -> List:
        """Build nested list from flat data and shape"""
        if len(shape) == 1:
            return flat[:shape[0]]

        result = []
        stride = 1
        for dim in shape[1:]:
            stride *= dim

        for i in range(shape[0]):
            start = i * stride
            end = start + stride
            result.append(self._build_nested(flat[start:end], shape[1:]))
        return result

    def _get_flat_index(self, indices: Tuple[int, ...]) -> int:
        """Convert multi-dimensional indices to flat index"""
        flat_idx = 0
        multiplier = 1
        for i in range(len(indices) - 1, -1, -1):
            flat_idx += indices[i] * multiplier
            multiplier *= self._shape[i]
        return flat_idx

    def __getitem__(self, key):
        if isinstance(key, int):
            if self.ndim == 1:
                return self._data[key]
            # Return a slice for higher dimensions
            stride = 1
            for dim in self._shape[1:]:
                stride *= dim
            start = key * stride
            end = start + stride
            result = ndarray.__new__(ndarray)
            result._data = self._data[start:end]
            result._shape = self._shape[1:]
            result.dtype = self.dtype
            return result
        elif isinstance(key, tuple):
            if len(key) == self.ndim:
                return self._data[self._get_flat_index(key)]
            # Partial indexing
            result = self
            for idx in key:
                result = result[idx]
            return result
        elif isinstance(key, slice):
            if self.ndim == 1:
                result = ndarray.__new__(ndarray)
                result._data = self._data[key]
                result._shape = (len(result._data),)
                result.dtype = self.dtype
                return result
        raise IndexError(f"Unsupported index type: {type(key)}")

    def __setitem__(self, key, value):
        if isinstance(key, int) and self.ndim == 1:
            self._data[key] = value
        elif isinstance(key, tuple) and len(key) == self.ndim:
            self._data[self._get_flat_index(key)] = value
        else:
            raise IndexError(f"Unsupported index type for assignment")

    def __len__(self) -> int:
        return self._shape[0] if self._shape else 0

    def __repr__(self) -> str:
        return f"array({self.tolist()})"

    def __str__(self) -> str:
        return repr(self)

    # Arithmetic operations
    def _apply_binary_op(self, other, op) -> 'ndarray':
        """Apply binary operation element-wise"""
        result = self.copy()
        if isinstance(other, ndarray):
            if self.shape != other.shape:
                raise ValueError(f"Shape mismatch: {self.shape} vs {other.shape}")
            result._data = [op(a, b) for a, b in zip(self._data, other._data)]
        else:
            result._data = [op(a, other) for a in self._data]
        return result

    def __add__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a + b)

    def __radd__(self, other) -> 'ndarray':
        return self.__add__(other)

    def __sub__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a - b)

    def __rsub__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: b - a)

    def __mul__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a * b)

    def __rmul__(self, other) -> 'ndarray':
        return self.__mul__(other)

    def __truediv__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a / b)

    def __rtruediv__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: b / a)

    def __floordiv__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a // b)

    def __pow__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a ** b)

    def __neg__(self) -> 'ndarray':
        result = self.copy()
        result._data = [-x for x in self._data]
        return result

    def __matmul__(self, other) -> 'ndarray':
        """Matrix multiplication (@ operator)"""
        from .math import dot
        return dot(self, other)

    def __rmatmul__(self, other) -> 'ndarray':
        """Reverse matrix multiplication"""
        from .math import dot
        return dot(other, self)

    # Comparison operations
    def __eq__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a == b)

    def __lt__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a < b)

    def __le__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a <= b)

    def __gt__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a > b)

    def __ge__(self, other) -> 'ndarray':
        return self._apply_binary_op(other, lambda a, b: a >= b)

    # Aggregation methods
    def sum(self, axis=None):
        if axis is None:
            return sum(self._data)
        # TODO: Implement axis-based sum
        raise NotImplementedError("Axis-based sum not yet implemented")

    def mean(self, axis=None):
        if axis is None:
            return sum(self._data) / len(self._data)
        raise NotImplementedError("Axis-based mean not yet implemented")

    def min(self, axis=None):
        if axis is None:
            return min(self._data)
        raise NotImplementedError("Axis-based min not yet implemented")

    def max(self, axis=None):
        if axis is None:
            return max(self._data)
        raise NotImplementedError("Axis-based max not yet implemented")

    def std(self, axis=None):
        if axis is None:
            m = self.mean()
            variance = sum((x - m) ** 2 for x in self._data) / len(self._data)
            return math.sqrt(variance)
        raise NotImplementedError("Axis-based std not yet implemented")

    def var(self, axis=None):
        if axis is None:
            m = self.mean()
            return sum((x - m) ** 2 for x in self._data) / len(self._data)
        raise NotImplementedError("Axis-based var not yet implemented")


def array(data, dtype=None) -> ndarray:
    """Create an ndarray from input data"""
    return ndarray(data, dtype)
