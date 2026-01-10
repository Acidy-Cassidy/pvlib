"""
Series - 1D labeled array
"""

from typing import List, Dict, Any, Optional, Union
import math


class Series:
    """One-dimensional labeled array"""

    def __init__(self, data=None, index=None, name=None, dtype=None):
        if data is None:
            data = []

        if isinstance(data, Series):
            self._data = data._data.copy()
            self._index = index if index is not None else data._index.copy()
            self.name = name if name is not None else data.name
        elif isinstance(data, dict):
            self._index = list(data.keys())
            self._data = list(data.values())
            self.name = name
        elif isinstance(data, (list, tuple)):
            self._data = list(data)
            self._index = list(index) if index is not None else list(range(len(data)))
            self.name = name
        else:
            self._data = [data]
            self._index = [0] if index is None else list(index)
            self.name = name

        if len(self._index) != len(self._data):
            raise ValueError("Index length must match data length")

        self.dtype = dtype or self._infer_dtype()
        self._index_map = {idx: i for i, idx in enumerate(self._index)}

    def _infer_dtype(self) -> str:
        """Infer data type from values"""
        if not self._data:
            return 'object'
        sample = self._data[0]
        if isinstance(sample, float):
            return 'float64'
        elif isinstance(sample, int):
            return 'int64'
        elif isinstance(sample, bool):
            return 'bool'
        elif isinstance(sample, str):
            return 'object'
        return 'object'

    @property
    def index(self) -> List:
        return self._index.copy()

    @property
    def values(self) -> List:
        return self._data.copy()

    @property
    def shape(self) -> tuple:
        return (len(self._data),)

    @property
    def size(self) -> int:
        return len(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[key]
        elif isinstance(key, slice):
            new_data = self._data[key]
            new_index = self._index[key]
            return Series(new_data, index=new_index, name=self.name)
        elif isinstance(key, list):
            if all(isinstance(k, bool) for k in key):
                # Boolean indexing
                new_data = [self._data[i] for i, k in enumerate(key) if k]
                new_index = [self._index[i] for i, k in enumerate(key) if k]
                return Series(new_data, index=new_index, name=self.name)
            else:
                # Label indexing
                new_data = [self._data[self._index_map[k]] for k in key]
                return Series(new_data, index=key, name=self.name)
        elif isinstance(key, Series):
            # Boolean Series indexing
            return self[[bool(v) for v in key._data]]
        elif key in self._index_map:
            return self._data[self._index_map[key]]
        raise KeyError(f"Key not found: {key}")

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self._data[key] = value
        elif key in self._index_map:
            self._data[self._index_map[key]] = value
        else:
            # Add new key
            self._index.append(key)
            self._data.append(value)
            self._index_map[key] = len(self._data) - 1

    def __repr__(self) -> str:
        lines = []
        for idx, val in zip(self._index, self._data):
            lines.append(f"{idx}    {val}")
        if self.name:
            lines.append(f"Name: {self.name}, dtype: {self.dtype}")
        else:
            lines.append(f"dtype: {self.dtype}")
        return '\n'.join(lines)

    def __str__(self) -> str:
        return repr(self)

    # Arithmetic operations
    def _apply_binary_op(self, other, op) -> 'Series':
        if isinstance(other, Series):
            if self._index != other._index:
                # Align by index
                result_data = []
                result_index = []
                for idx in self._index:
                    if idx in other._index_map:
                        result_data.append(op(self._data[self._index_map[idx]],
                                             other._data[other._index_map[idx]]))
                        result_index.append(idx)
                return Series(result_data, index=result_index, name=self.name)
            result_data = [op(a, b) for a, b in zip(self._data, other._data)]
        else:
            result_data = [op(a, other) for a in self._data]
        return Series(result_data, index=self._index.copy(), name=self.name)

    def __add__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a + b)

    def __radd__(self, other) -> 'Series':
        return self.__add__(other)

    def __sub__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a - b)

    def __rsub__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: b - a)

    def __mul__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a * b)

    def __rmul__(self, other) -> 'Series':
        return self.__mul__(other)

    def __truediv__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a / b)

    def __floordiv__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a // b)

    def __pow__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a ** b)

    def __neg__(self) -> 'Series':
        return Series([-x for x in self._data], index=self._index.copy(), name=self.name)

    # Comparison operations
    def __eq__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a == b)

    def __ne__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a != b)

    def __lt__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a < b)

    def __le__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a <= b)

    def __gt__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a > b)

    def __ge__(self, other) -> 'Series':
        return self._apply_binary_op(other, lambda a, b: a >= b)

    # Aggregation methods
    def sum(self):
        return sum(self._data)

    def mean(self):
        return sum(self._data) / len(self._data) if self._data else float('nan')

    def min(self):
        return min(self._data) if self._data else float('nan')

    def max(self):
        return max(self._data) if self._data else float('nan')

    def std(self, ddof=1):
        if len(self._data) <= ddof:
            return float('nan')
        m = self.mean()
        variance = sum((x - m) ** 2 for x in self._data) / (len(self._data) - ddof)
        return math.sqrt(variance)

    def var(self, ddof=1):
        if len(self._data) <= ddof:
            return float('nan')
        m = self.mean()
        return sum((x - m) ** 2 for x in self._data) / (len(self._data) - ddof)

    def median(self):
        if not self._data:
            return float('nan')
        sorted_data = sorted(self._data)
        n = len(sorted_data)
        if n % 2 == 0:
            return (sorted_data[n//2 - 1] + sorted_data[n//2]) / 2
        return sorted_data[n // 2]

    def count(self) -> int:
        return sum(1 for x in self._data if x is not None and x == x)  # Excludes NaN

    def describe(self) -> 'Series':
        """Generate descriptive statistics"""
        stats = {
            'count': self.count(),
            'mean': self.mean(),
            'std': self.std(),
            'min': self.min(),
            '25%': self.quantile(0.25),
            '50%': self.median(),
            '75%': self.quantile(0.75),
            'max': self.max()
        }
        return Series(stats, name=self.name)

    def quantile(self, q: float):
        """Return value at quantile q"""
        if not self._data:
            return float('nan')
        sorted_data = sorted(self._data)
        idx = (len(sorted_data) - 1) * q
        lower = int(idx)
        upper = lower + 1
        if upper >= len(sorted_data):
            return sorted_data[-1]
        weight = idx - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight

    # Utility methods
    def copy(self) -> 'Series':
        return Series(self._data.copy(), index=self._index.copy(), name=self.name)

    def head(self, n=5) -> 'Series':
        return Series(self._data[:n], index=self._index[:n], name=self.name)

    def tail(self, n=5) -> 'Series':
        return Series(self._data[-n:], index=self._index[-n:], name=self.name)

    def unique(self) -> List:
        seen = set()
        result = []
        for item in self._data:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def nunique(self) -> int:
        return len(set(self._data))

    def value_counts(self) -> 'Series':
        counts = {}
        for item in self._data:
            counts[item] = counts.get(item, 0) + 1
        sorted_items = sorted(counts.items(), key=lambda x: -x[1])
        return Series(dict(sorted_items))

    def apply(self, func) -> 'Series':
        return Series([func(x) for x in self._data], index=self._index.copy(), name=self.name)

    def map(self, mapping) -> 'Series':
        if callable(mapping):
            return self.apply(mapping)
        elif isinstance(mapping, dict):
            return Series([mapping.get(x, x) for x in self._data],
                         index=self._index.copy(), name=self.name)
        raise TypeError("mapping must be callable or dict")

    def fillna(self, value) -> 'Series':
        return Series([value if (x is None or x != x) else x for x in self._data],
                     index=self._index.copy(), name=self.name)

    def dropna(self) -> 'Series':
        pairs = [(idx, val) for idx, val in zip(self._index, self._data)
                 if val is not None and val == val]
        if not pairs:
            return Series([], index=[], name=self.name)
        new_index, new_data = zip(*pairs)
        return Series(list(new_data), index=list(new_index), name=self.name)

    def isna(self) -> 'Series':
        return Series([x is None or x != x for x in self._data],
                     index=self._index.copy(), name=self.name)

    def notna(self) -> 'Series':
        return Series([x is not None and x == x for x in self._data],
                     index=self._index.copy(), name=self.name)

    def sort_values(self, ascending=True) -> 'Series':
        pairs = list(zip(self._index, self._data))
        pairs.sort(key=lambda x: x[1], reverse=not ascending)
        new_index, new_data = zip(*pairs) if pairs else ([], [])
        return Series(list(new_data), index=list(new_index), name=self.name)

    def sort_index(self, ascending=True) -> 'Series':
        pairs = list(zip(self._index, self._data))
        pairs.sort(key=lambda x: x[0], reverse=not ascending)
        new_index, new_data = zip(*pairs) if pairs else ([], [])
        return Series(list(new_data), index=list(new_index), name=self.name)

    def reset_index(self, drop=False) -> 'Series':
        if drop:
            return Series(self._data.copy(), name=self.name)
        # Returns DataFrame normally, but for simplicity return Series
        return Series(self._data.copy(), name=self.name)

    def tolist(self) -> List:
        return self._data.copy()

    def to_dict(self) -> Dict:
        return dict(zip(self._index, self._data))

    def astype(self, dtype) -> 'Series':
        """Cast to a different data type"""
        type_map = {
            'int': int, 'int64': int, 'int32': int,
            'float': float, 'float64': float, 'float32': float,
            'str': str, 'object': str,
            'bool': bool
        }
        converter = type_map.get(dtype, dtype)
        return Series([converter(x) for x in self._data],
                     index=self._index.copy(), name=self.name, dtype=dtype)
