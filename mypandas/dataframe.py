"""
DataFrame - 2D labeled data structure
"""

from typing import List, Dict, Any, Optional, Union
from .series import Series


class DataFrame:
    """Two-dimensional tabular data structure"""

    def __init__(self, data=None, columns=None, index=None):
        self._columns = []
        self._data = {}  # column_name -> list of values
        self._index = []

        if data is None:
            self._index = list(index) if index else []
            if columns:
                self._columns = list(columns)
                for col in self._columns:
                    self._data[col] = [None] * len(self._index)

        elif isinstance(data, dict):
            # Dict of columns
            self._columns = list(columns) if columns else list(data.keys())
            max_len = max((len(v) for v in data.values()), default=0)
            self._index = list(index) if index else list(range(max_len))

            for col in self._columns:
                if col in data:
                    col_data = list(data[col])
                    # Pad if necessary
                    while len(col_data) < len(self._index):
                        col_data.append(None)
                    self._data[col] = col_data[:len(self._index)]
                else:
                    self._data[col] = [None] * len(self._index)

        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                # List of dicts (records)
                all_keys = set()
                for record in data:
                    all_keys.update(record.keys())
                self._columns = list(columns) if columns else sorted(all_keys)
                self._index = list(index) if index else list(range(len(data)))

                for col in self._columns:
                    self._data[col] = [record.get(col) for record in data]
            else:
                # List of lists (rows)
                if columns:
                    self._columns = list(columns)
                else:
                    num_cols = len(data[0]) if data else 0
                    self._columns = list(range(num_cols))

                self._index = list(index) if index else list(range(len(data)))

                for i, col in enumerate(self._columns):
                    self._data[col] = [row[i] if i < len(row) else None for row in data]

        elif isinstance(data, DataFrame):
            self._columns = list(columns) if columns else data._columns.copy()
            self._index = list(index) if index else data._index.copy()
            self._data = {col: data._data[col].copy() for col in self._columns if col in data._data}

        self._index_map = {idx: i for i, idx in enumerate(self._index)}

    @property
    def columns(self) -> List:
        return self._columns.copy()

    @columns.setter
    def columns(self, new_columns):
        if len(new_columns) != len(self._columns):
            raise ValueError("Length of new column names must match")
        new_data = {}
        for old_col, new_col in zip(self._columns, new_columns):
            new_data[new_col] = self._data[old_col]
        self._data = new_data
        self._columns = list(new_columns)

    @property
    def index(self) -> List:
        return self._index.copy()

    @index.setter
    def index(self, new_index):
        if len(new_index) != len(self._index):
            raise ValueError("Length of new index must match")
        self._index = list(new_index)
        self._index_map = {idx: i for i, idx in enumerate(self._index)}

    @property
    def shape(self) -> tuple:
        return (len(self._index), len(self._columns))

    @property
    def size(self) -> int:
        return len(self._index) * len(self._columns)

    @property
    def values(self) -> List[List]:
        """Return data as list of lists (rows)"""
        return [[self._data[col][i] for col in self._columns] for i in range(len(self._index))]

    @property
    def dtypes(self) -> Series:
        """Return data types of each column"""
        types = {}
        for col in self._columns:
            col_data = [x for x in self._data[col] if x is not None]
            if not col_data:
                types[col] = 'object'
            elif all(isinstance(x, int) for x in col_data):
                types[col] = 'int64'
            elif all(isinstance(x, (int, float)) for x in col_data):
                types[col] = 'float64'
            elif all(isinstance(x, bool) for x in col_data):
                types[col] = 'bool'
            else:
                types[col] = 'object'
        return Series(types)

    @property
    def T(self) -> 'DataFrame':
        """Transpose"""
        new_data = {}
        for i, idx in enumerate(self._index):
            new_data[idx] = [self._data[col][i] for col in self._columns]
        return DataFrame(new_data, columns=self._index, index=self._columns)

    def __len__(self) -> int:
        return len(self._index)

    def __getitem__(self, key):
        if isinstance(key, str):
            # Single column
            if key not in self._data:
                raise KeyError(f"Column '{key}' not found")
            return Series(self._data[key], index=self._index.copy(), name=key)
        elif isinstance(key, list):
            if all(isinstance(k, str) for k in key):
                # Multiple columns
                new_data = {col: self._data[col].copy() for col in key if col in self._data}
                return DataFrame(new_data, columns=key, index=self._index.copy())
            elif all(isinstance(k, bool) for k in key):
                # Boolean indexing
                new_index = [self._index[i] for i, k in enumerate(key) if k]
                new_data = {col: [self._data[col][i] for i, k in enumerate(key) if k]
                           for col in self._columns}
                return DataFrame(new_data, columns=self._columns.copy(), index=new_index)
        elif isinstance(key, Series):
            # Boolean Series indexing
            return self[[bool(v) for v in key._data]]
        raise KeyError(f"Invalid key type: {type(key)}")

    def __setitem__(self, key, value):
        if isinstance(key, str):
            if isinstance(value, Series):
                self._data[key] = value._data.copy()
            elif isinstance(value, list):
                if len(value) != len(self._index):
                    raise ValueError("Length of values must match DataFrame length")
                self._data[key] = value.copy()
            else:
                # Scalar - broadcast to all rows
                self._data[key] = [value] * len(self._index)

            if key not in self._columns:
                self._columns.append(key)

    def __repr__(self) -> str:
        # Build string representation
        lines = []

        # Header
        col_widths = {}
        for col in self._columns:
            col_widths[col] = max(len(str(col)),
                                  max((len(str(v)) for v in self._data[col]), default=0))
        idx_width = max((len(str(idx)) for idx in self._index), default=0)

        header = ' ' * idx_width + '  ' + '  '.join(str(col).rjust(col_widths[col])
                                                     for col in self._columns)
        lines.append(header)

        # Rows (show first and last few if large)
        max_rows = 10
        if len(self._index) <= max_rows:
            row_indices = range(len(self._index))
        else:
            row_indices = list(range(5)) + ['...'] + list(range(len(self._index)-5, len(self._index)))

        for i in row_indices:
            if i == '...':
                lines.append('...')
            else:
                row = str(self._index[i]).rjust(idx_width) + '  '
                row += '  '.join(str(self._data[col][i]).rjust(col_widths[col])
                                for col in self._columns)
                lines.append(row)

        lines.append(f"\n[{len(self._index)} rows x {len(self._columns)} columns]")
        return '\n'.join(lines)

    def __str__(self) -> str:
        return repr(self)

    # Row/column access
    @property
    def loc(self):
        """Label-based indexing"""
        return _LocIndexer(self)

    @property
    def iloc(self):
        """Integer position-based indexing"""
        return _ILocIndexer(self)

    def head(self, n=5) -> 'DataFrame':
        new_index = self._index[:n]
        new_data = {col: self._data[col][:n] for col in self._columns}
        return DataFrame(new_data, columns=self._columns.copy(), index=new_index)

    def tail(self, n=5) -> 'DataFrame':
        new_index = self._index[-n:]
        new_data = {col: self._data[col][-n:] for col in self._columns}
        return DataFrame(new_data, columns=self._columns.copy(), index=new_index)

    def copy(self) -> 'DataFrame':
        new_data = {col: self._data[col].copy() for col in self._columns}
        return DataFrame(new_data, columns=self._columns.copy(), index=self._index.copy())

    # Aggregations
    def sum(self, axis=0) -> Series:
        if axis == 0:
            return Series({col: sum(v for v in self._data[col] if v is not None)
                          for col in self._columns})
        else:
            return Series([sum(self._data[col][i] for col in self._columns
                              if self._data[col][i] is not None)
                          for i in range(len(self._index))], index=self._index.copy())

    def mean(self, axis=0) -> Series:
        if axis == 0:
            result = {}
            for col in self._columns:
                vals = [v for v in self._data[col] if v is not None]
                result[col] = sum(vals) / len(vals) if vals else float('nan')
            return Series(result)
        else:
            result = []
            for i in range(len(self._index)):
                vals = [self._data[col][i] for col in self._columns
                       if self._data[col][i] is not None]
                result.append(sum(vals) / len(vals) if vals else float('nan'))
            return Series(result, index=self._index.copy())

    def min(self, axis=0) -> Series:
        if axis == 0:
            result = {}
            for col in self._columns:
                vals = [v for v in self._data[col] if v is not None]
                result[col] = min(vals) if vals else float('nan')
            return Series(result)
        else:
            result = []
            for i in range(len(self._index)):
                vals = [self._data[col][i] for col in self._columns
                       if self._data[col][i] is not None]
                result.append(min(vals) if vals else float('nan'))
            return Series(result, index=self._index.copy())

    def max(self, axis=0) -> Series:
        if axis == 0:
            result = {}
            for col in self._columns:
                vals = [v for v in self._data[col] if v is not None]
                result[col] = max(vals) if vals else float('nan')
            return Series(result)
        else:
            result = []
            for i in range(len(self._index)):
                vals = [self._data[col][i] for col in self._columns
                       if self._data[col][i] is not None]
                result.append(max(vals) if vals else float('nan'))
            return Series(result, index=self._index.copy())

    def count(self, axis=0) -> Series:
        if axis == 0:
            return Series({col: sum(1 for v in self._data[col] if v is not None)
                          for col in self._columns})
        else:
            return Series([sum(1 for col in self._columns if self._data[col][i] is not None)
                          for i in range(len(self._index))], index=self._index.copy())

    def describe(self) -> 'DataFrame':
        """Generate descriptive statistics"""
        numeric_cols = [col for col in self._columns
                       if all(isinstance(v, (int, float)) or v is None
                             for v in self._data[col])]

        stats = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
        result_data = {col: [] for col in numeric_cols}

        for col in numeric_cols:
            s = Series(self._data[col], name=col)
            result_data[col] = [
                s.count(),
                s.mean(),
                s.std(),
                s.min(),
                s.quantile(0.25),
                s.median(),
                s.quantile(0.75),
                s.max()
            ]

        return DataFrame(result_data, index=stats)

    def info(self) -> None:
        """Print concise summary"""
        print(f"<DataFrame>")
        print(f"Index: {len(self._index)} entries")
        print(f"Columns: {len(self._columns)} entries")
        print(f"dtypes: {self.dtypes.to_dict()}")

    # Data manipulation
    def drop(self, labels=None, axis=0, columns=None) -> 'DataFrame':
        """Drop rows or columns"""
        result = self.copy()

        if columns is not None:
            labels = columns
            axis = 1

        if axis == 0:
            # Drop rows
            if not isinstance(labels, list):
                labels = [labels]
            drop_set = set(labels)
            keep_indices = [i for i, idx in enumerate(result._index) if idx not in drop_set]
            result._index = [result._index[i] for i in keep_indices]
            for col in result._columns:
                result._data[col] = [result._data[col][i] for i in keep_indices]
            result._index_map = {idx: i for i, idx in enumerate(result._index)}
        else:
            # Drop columns
            if not isinstance(labels, list):
                labels = [labels]
            drop_set = set(labels)
            result._columns = [col for col in result._columns if col not in drop_set]
            for col in drop_set:
                if col in result._data:
                    del result._data[col]

        return result

    def dropna(self, axis=0, how='any') -> 'DataFrame':
        """Drop rows with missing values"""
        result = self.copy()

        if axis == 0:
            keep_indices = []
            for i in range(len(result._index)):
                row_vals = [result._data[col][i] for col in result._columns]
                if how == 'any':
                    if all(v is not None and v == v for v in row_vals):
                        keep_indices.append(i)
                elif how == 'all':
                    if any(v is not None and v == v for v in row_vals):
                        keep_indices.append(i)

            result._index = [result._index[i] for i in keep_indices]
            for col in result._columns:
                result._data[col] = [result._data[col][i] for i in keep_indices]
            result._index_map = {idx: i for i, idx in enumerate(result._index)}

        return result

    def fillna(self, value) -> 'DataFrame':
        """Fill missing values"""
        result = self.copy()
        for col in result._columns:
            result._data[col] = [value if (v is None or v != v) else v
                                for v in result._data[col]]
        return result

    def sort_values(self, by, ascending=True) -> 'DataFrame':
        """Sort by values in column(s)"""
        if isinstance(by, str):
            by = [by]

        # Create list of (index_position, row_key) tuples
        def sort_key(i):
            return tuple(self._data[col][i] for col in by)

        sorted_indices = sorted(range(len(self._index)), key=sort_key, reverse=not ascending)

        new_index = [self._index[i] for i in sorted_indices]
        new_data = {col: [self._data[col][i] for i in sorted_indices] for col in self._columns}
        return DataFrame(new_data, columns=self._columns.copy(), index=new_index)

    def sort_index(self, ascending=True) -> 'DataFrame':
        """Sort by index"""
        sorted_pairs = sorted(enumerate(self._index), key=lambda x: x[1], reverse=not ascending)
        sorted_indices = [p[0] for p in sorted_pairs]

        new_index = [self._index[i] for i in sorted_indices]
        new_data = {col: [self._data[col][i] for i in sorted_indices] for col in self._columns}
        return DataFrame(new_data, columns=self._columns.copy(), index=new_index)

    def reset_index(self, drop=False) -> 'DataFrame':
        """Reset index to default integer index"""
        if drop:
            result = self.copy()
            result._index = list(range(len(result._index)))
            result._index_map = {i: i for i in result._index}
            return result
        else:
            new_data = {'index': self._index.copy()}
            new_data.update({col: self._data[col].copy() for col in self._columns})
            return DataFrame(new_data, columns=['index'] + self._columns.copy())

    def set_index(self, keys) -> 'DataFrame':
        """Set column as index"""
        if isinstance(keys, str):
            keys = [keys]

        new_index = [tuple(self._data[k][i] for k in keys) for i in range(len(self._index))]
        if len(keys) == 1:
            new_index = [idx[0] for idx in new_index]

        result = self.drop(columns=keys)
        result._index = new_index
        result._index_map = {idx: i for i, idx in enumerate(result._index)}
        return result

    def rename(self, columns=None, index=None) -> 'DataFrame':
        """Rename columns or index"""
        result = self.copy()
        if columns:
            new_columns = [columns.get(col, col) for col in result._columns]
            new_data = {}
            for old_col, new_col in zip(result._columns, new_columns):
                new_data[new_col] = result._data[old_col]
            result._data = new_data
            result._columns = new_columns
        if index:
            result._index = [index.get(idx, idx) for idx in result._index]
            result._index_map = {idx: i for i, idx in enumerate(result._index)}
        return result

    def apply(self, func, axis=0) -> Union[Series, 'DataFrame']:
        """Apply function along axis"""
        if axis == 0:
            # Apply to each column
            result = {col: func(Series(self._data[col], index=self._index.copy(), name=col))
                     for col in self._columns}
            if all(not isinstance(v, Series) for v in result.values()):
                return Series(result)
            return DataFrame(result)
        else:
            # Apply to each row
            result = []
            for i in range(len(self._index)):
                row = Series({col: self._data[col][i] for col in self._columns})
                result.append(func(row))
            return Series(result, index=self._index.copy())

    def groupby(self, by) -> 'DataFrameGroupBy':
        """Group by column(s)"""
        return DataFrameGroupBy(self, by)

    def merge(self, right, on=None, how='inner', left_on=None, right_on=None,
              suffixes=('_x', '_y')) -> 'DataFrame':
        """Merge with another DataFrame"""
        if on is not None:
            left_on = on
            right_on = on

        if isinstance(left_on, str):
            left_on = [left_on]
        if isinstance(right_on, str):
            right_on = [right_on]

        left_suffix, right_suffix = suffixes

        # Find overlapping columns (excluding join keys)
        left_cols_set = set(self._columns)
        right_cols_set = set(right._columns)
        join_keys = set(left_on) | set(right_on)
        overlapping = (left_cols_set & right_cols_set) - join_keys

        # Build column name mapping
        def get_left_col_name(col):
            if col in overlapping:
                return col + left_suffix
            return col

        def get_right_col_name(col):
            if col in overlapping:
                return col + right_suffix
            return col

        # Build index for right DataFrame
        right_index = {}
        for i in range(len(right._index)):
            key = tuple(right._data[col][i] for col in right_on)
            if key not in right_index:
                right_index[key] = []
            right_index[key].append(i)

        # Build result columns list
        result_columns = []
        for col in self._columns:
            result_columns.append(get_left_col_name(col))
        for col in right._columns:
            if col not in right_on:
                new_col = get_right_col_name(col)
                if new_col not in result_columns:
                    result_columns.append(new_col)

        # Build result data
        result_data = {col: [] for col in result_columns}
        result_index = []

        for i in range(len(self._index)):
            left_key = tuple(self._data[col][i] for col in left_on)

            if left_key in right_index:
                for j in right_index[left_key]:
                    for col in self._columns:
                        new_col = get_left_col_name(col)
                        result_data[new_col].append(self._data[col][i])
                    for col in right._columns:
                        if col not in right_on:
                            new_col = get_right_col_name(col)
                            result_data[new_col].append(right._data[col][j])
                    result_index.append(len(result_index))
            elif how in ('left', 'outer'):
                for col in self._columns:
                    new_col = get_left_col_name(col)
                    result_data[new_col].append(self._data[col][i])
                for col in right._columns:
                    if col not in right_on:
                        new_col = get_right_col_name(col)
                        result_data[new_col].append(None)
                result_index.append(len(result_index))

        return DataFrame(result_data, columns=result_columns, index=result_index)

    def to_sql(self, name: str, con, if_exists='fail', index=True, index_label=None) -> None:
        """
        Write DataFrame to a SQL database table.

        Parameters:
        -----------
        name : str
            Name of SQL table
        con : sqlite3.Connection
            Database connection
        if_exists : str
            How to behave if table exists: 'fail', 'replace', 'append'
        index : bool
            Write index as a column
        index_label : str or None
            Column label for index
        """
        import sqlite3

        cursor = con.cursor()

        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
        table_exists = cursor.fetchone() is not None

        if table_exists:
            if if_exists == 'fail':
                raise ValueError(f"Table '{name}' already exists.")
            elif if_exists == 'replace':
                cursor.execute(f"DROP TABLE IF EXISTS \"{name}\";")
                table_exists = False
            # if 'append', we just insert

        # Build column definitions
        if not table_exists:
            col_defs = []
            if index:
                idx_label = index_label or 'index'
                col_defs.append(f'"{idx_label}" TEXT')
            for col in self._columns:
                # Infer type from data
                col_data = [v for v in self._data[col] if v is not None]
                if col_data:
                    sample = col_data[0]
                    if isinstance(sample, int):
                        sql_type = 'INTEGER'
                    elif isinstance(sample, float):
                        sql_type = 'REAL'
                    else:
                        sql_type = 'TEXT'
                else:
                    sql_type = 'TEXT'
                col_defs.append(f'"{col}" {sql_type}')

            create_sql = f'CREATE TABLE "{name}" ({", ".join(col_defs)});'
            cursor.execute(create_sql)

        # Insert data
        if index:
            idx_label = index_label or 'index'
            columns = [idx_label] + self._columns
        else:
            columns = self._columns

        placeholders = ', '.join(['?'] * len(columns))
        col_names = ', '.join([f'"{c}"' for c in columns])
        insert_sql = f'INSERT INTO "{name}" ({col_names}) VALUES ({placeholders});'

        for i, idx in enumerate(self._index):
            if index:
                row = [idx] + [self._data[col][i] for col in self._columns]
            else:
                row = [self._data[col][i] for col in self._columns]
            cursor.execute(insert_sql, row)

        con.commit()

    def to_dict(self, orient='dict') -> Dict:
        """Convert to dictionary"""
        if orient == 'dict':
            return {col: dict(zip(self._index, self._data[col])) for col in self._columns}
        elif orient == 'list':
            return {col: self._data[col].copy() for col in self._columns}
        elif orient == 'records':
            return [{col: self._data[col][i] for col in self._columns}
                   for i in range(len(self._index))]
        raise ValueError(f"Unknown orient: {orient}")

    def to_csv(self, path, index=True) -> None:
        """Save to CSV file"""
        from .io import to_csv
        to_csv(self, path, index=index)


class _LocIndexer:
    """Label-based indexer"""

    def __init__(self, df: DataFrame):
        self._df = df

    def __getitem__(self, key):
        if isinstance(key, tuple):
            row_key, col_key = key
        else:
            row_key = key
            col_key = slice(None)

        # Handle row selection
        if isinstance(row_key, slice):
            start_idx = self._df._index_map.get(row_key.start, 0) if row_key.start else 0
            stop_idx = self._df._index_map.get(row_key.stop, len(self._df._index)) if row_key.stop else len(self._df._index)
            row_indices = range(start_idx, stop_idx + 1 if row_key.stop in self._df._index_map else stop_idx)
        elif isinstance(row_key, list):
            row_indices = [self._df._index_map[k] for k in row_key]
        else:
            row_indices = [self._df._index_map[row_key]]

        # Handle column selection
        if isinstance(col_key, slice):
            cols = self._df._columns
        elif isinstance(col_key, list):
            cols = col_key
        elif isinstance(col_key, str):
            cols = [col_key]
        else:
            cols = self._df._columns

        # Build result
        if len(row_indices) == 1 and len(cols) == 1:
            return self._df._data[cols[0]][row_indices[0]]

        if len(cols) == 1:
            return Series([self._df._data[cols[0]][i] for i in row_indices],
                         index=[self._df._index[i] for i in row_indices],
                         name=cols[0])

        new_data = {col: [self._df._data[col][i] for i in row_indices] for col in cols}
        new_index = [self._df._index[i] for i in row_indices]
        return DataFrame(new_data, columns=cols, index=new_index)


class _ILocIndexer:
    """Integer position-based indexer"""

    def __init__(self, df: DataFrame):
        self._df = df

    def __getitem__(self, key):
        if isinstance(key, tuple):
            row_key, col_key = key
        else:
            row_key = key
            col_key = slice(None)

        # Handle row selection
        if isinstance(row_key, slice):
            row_indices = range(*row_key.indices(len(self._df._index)))
        elif isinstance(row_key, list):
            row_indices = row_key
        elif isinstance(row_key, int):
            row_indices = [row_key]
        else:
            row_indices = list(range(len(self._df._index)))

        # Handle column selection
        if isinstance(col_key, slice):
            col_indices = range(*col_key.indices(len(self._df._columns)))
            cols = [self._df._columns[i] for i in col_indices]
        elif isinstance(col_key, list):
            cols = [self._df._columns[i] for i in col_key]
        elif isinstance(col_key, int):
            cols = [self._df._columns[col_key]]
        else:
            cols = self._df._columns

        # Build result
        if len(row_indices) == 1 and len(cols) == 1:
            return self._df._data[cols[0]][row_indices[0]]

        if len(cols) == 1:
            return Series([self._df._data[cols[0]][i] for i in row_indices],
                         index=[self._df._index[i] for i in row_indices],
                         name=cols[0])

        new_data = {col: [self._df._data[col][i] for i in row_indices] for col in cols}
        new_index = [self._df._index[i] for i in row_indices]
        return DataFrame(new_data, columns=cols, index=new_index)


class DataFrameGroupBy:
    """GroupBy object for DataFrame"""

    def __init__(self, df: DataFrame, by):
        self._df = df
        self._by = by if isinstance(by, list) else [by]
        self._groups = self._compute_groups()

    def _compute_groups(self) -> Dict:
        groups = {}
        for i in range(len(self._df._index)):
            key = tuple(self._df._data[col][i] for col in self._by)
            if len(key) == 1:
                key = key[0]
            if key not in groups:
                groups[key] = []
            groups[key].append(i)
        return groups

    def _is_numeric_column(self, col: str) -> bool:
        """Check if column contains numeric data"""
        vals = [v for v in self._df._data[col] if v is not None]
        if not vals:
            return False
        return all(isinstance(v, (int, float)) for v in vals)

    def _aggregate(self, func, numeric_only=False) -> DataFrame:
        result_data = {col: [] for col in self._by}

        # Determine which columns to aggregate
        agg_cols = []
        for col in self._df._columns:
            if col not in self._by:
                if numeric_only and not self._is_numeric_column(col):
                    continue
                agg_cols.append(col)
                result_data[col] = []

        result_index = []
        for key, indices in self._groups.items():
            if not isinstance(key, tuple):
                key = (key,)

            for i, col in enumerate(self._by):
                result_data[col].append(key[i])

            for col in agg_cols:
                vals = [self._df._data[col][i] for i in indices]
                result_data[col].append(func(vals))

            result_index.append(len(result_index))

        # Determine result columns order
        result_columns = list(self._by) + agg_cols
        return DataFrame(result_data, columns=result_columns, index=result_index)

    def sum(self, numeric_only=True) -> DataFrame:
        def sum_func(vals):
            valid = [v for v in vals if v is not None and isinstance(v, (int, float))]
            return sum(valid) if valid else 0
        return self._aggregate(sum_func, numeric_only=numeric_only)

    def mean(self, numeric_only=True) -> DataFrame:
        def mean_func(vals):
            valid = [v for v in vals if v is not None and isinstance(v, (int, float))]
            return sum(valid) / len(valid) if valid else float('nan')
        return self._aggregate(mean_func, numeric_only=numeric_only)

    def count(self) -> DataFrame:
        return self._aggregate(lambda vals: sum(1 for v in vals if v is not None))

    def min(self) -> DataFrame:
        def min_func(vals):
            valid = [v for v in vals if v is not None]
            return min(valid) if valid else float('nan')
        return self._aggregate(min_func)

    def max(self) -> DataFrame:
        def max_func(vals):
            valid = [v for v in vals if v is not None]
            return max(valid) if valid else float('nan')
        return self._aggregate(max_func)

    def first(self) -> DataFrame:
        return self._aggregate(lambda vals: vals[0] if vals else None)

    def last(self) -> DataFrame:
        return self._aggregate(lambda vals: vals[-1] if vals else None)

    def agg(self, func) -> DataFrame:
        """Apply aggregation function(s)"""
        if callable(func):
            return self._aggregate(func)
        raise NotImplementedError("Only callable aggregation supported")
