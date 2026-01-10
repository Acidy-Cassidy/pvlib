"""
Input/Output operations
"""

from typing import Optional, List, Iterator, Union
import csv


class DataFrameChunker:
    """Iterator that yields DataFrame chunks"""

    def __init__(self, filepath: str, chunksize: int, **kwargs):
        self.filepath = filepath
        self.chunksize = chunksize
        self.kwargs = kwargs
        self._file = None
        self._reader = None
        self._columns = None
        self._col_indices = None
        self._na_set = None
        self._started = False

    def __iter__(self):
        return self

    def __next__(self):
        from .dataframe import DataFrame

        if not self._started:
            self._start()

        rows = []
        for _ in range(self.chunksize):
            try:
                row = next(self._reader)
                # Skip comment lines
                comment = self.kwargs.get('comment')
                if comment and row and row[0].startswith(comment):
                    continue
                rows.append(row)
            except StopIteration:
                break

        if not rows:
            if self._file:
                self._file.close()
            raise StopIteration

        return self._parse_rows(rows)

    def _start(self):
        sep = self.kwargs.get('sep', ',')
        skiprows = self.kwargs.get('skiprows', 0)
        header = self.kwargs.get('header', 0)
        encoding = self.kwargs.get('encoding', 'utf-8')
        na_values = self.kwargs.get('na_values')

        self._na_set = set(na_values) if na_values else {'', 'NA', 'N/A', 'NaN', 'nan', 'null', 'NULL'}

        self._file = open(self.filepath, 'r', newline='', encoding=encoding, errors='replace')
        self._reader = csv.reader(self._file, delimiter=sep)

        # Skip rows
        for _ in range(skiprows):
            try:
                next(self._reader)
            except StopIteration:
                break

        # Read header
        if header is not None:
            for _ in range(header):
                try:
                    next(self._reader)
                except StopIteration:
                    break
            try:
                header_row = next(self._reader)
                self._columns = [c.strip() for c in header_row]
            except StopIteration:
                self._columns = []
        else:
            self._columns = None

        usecols = self.kwargs.get('usecols')
        if usecols and self._columns:
            if isinstance(usecols[0], int):
                self._col_indices = usecols
                self._columns = [self._columns[i] for i in usecols]
            else:
                self._col_indices = [self._columns.index(c) for c in usecols]
                self._columns = list(usecols)
        else:
            self._col_indices = None

        self._started = True

    def _parse_rows(self, rows):
        from .dataframe import DataFrame

        if not self._columns and rows:
            self._columns = [f'col_{i}' for i in range(len(rows[0]))]

        column_data = {col: [] for col in self._columns}
        col_indices = self._col_indices or list(range(len(self._columns)))

        for row in rows:
            for i, col in zip(col_indices, self._columns):
                val = row[i] if i < len(row) else ''

                if val in self._na_set:
                    val = None
                else:
                    try:
                        if '.' in val or 'e' in val.lower():
                            val = float(val)
                        else:
                            val = int(val)
                    except (ValueError, TypeError):
                        pass

                column_data[col].append(val)

        return DataFrame(column_data, columns=self._columns)


def read_csv(filepath: str, sep=',', header=0, index_col=None,
             usecols=None, dtype=None, na_values=None,
             skiprows=0, engine='python', on_bad_lines='skip',
             low_memory=True, chunksize=None, comment=None,
             encoding='utf-8') -> Union['DataFrame', DataFrameChunker]:
    """
    Read CSV file into DataFrame.

    Parameters:
    -----------
    filepath : str
        Path to CSV file
    sep : str
        Delimiter to use (default ',')
    header : int or None
        Row number to use as column names (default 0)
    index_col : int or str or None
        Column to use as index
    usecols : list or None
        Columns to read
    dtype : dict or None
        Column data types (not fully implemented)
    na_values : list or None
        Additional values to treat as NA
    skiprows : int
        Number of rows to skip at start
    engine : str
        Parser engine ('python' or 'c') - ignored, always uses Python
    on_bad_lines : str
        How to handle bad lines ('skip', 'warn', 'error')
    low_memory : bool
        Ignored in this implementation
    chunksize : int or None
        Return iterator yielding chunks of this size
    comment : str or None
        Character indicating comment lines to skip
    encoding : str
        File encoding (default 'utf-8')
    """
    from .dataframe import DataFrame

    if chunksize is not None:
        return DataFrameChunker(filepath, chunksize, sep=sep, header=header,
                                usecols=usecols, na_values=na_values,
                                skiprows=skiprows, comment=comment,
                                encoding=encoding)

    try:
        with open(filepath, 'r', newline='', encoding=encoding, errors='replace') as f:
            reader = csv.reader(f, delimiter=sep)
            rows = []
            for row in reader:
                # Skip comment lines
                if comment and row and row[0].startswith(comment):
                    continue
                rows.append(row)
    except Exception as e:
        if on_bad_lines == 'error':
            raise
        rows = []

    if not rows:
        return DataFrame()

    # Skip rows
    if skiprows:
        rows = rows[skiprows:]

    if not rows:
        return DataFrame()

    # Handle header
    if header is not None:
        if header < len(rows):
            columns = [c.strip() for c in rows[header]]
            data_rows = rows[header + 1:]
        else:
            columns = []
            data_rows = []
    else:
        columns = [f'col_{i}' for i in range(len(rows[0]))]
        data_rows = rows

    # Filter columns if usecols specified
    if usecols is not None:
        if isinstance(usecols[0], int):
            col_indices = usecols
            columns = [columns[i] for i in col_indices]
        else:
            col_indices = [columns.index(c) for c in usecols]
            columns = list(usecols)
    else:
        col_indices = list(range(len(columns)))

    # Build column data
    column_data = {col: [] for col in columns}
    na_set = set(na_values) if na_values else {'', 'NA', 'N/A', 'NaN', 'nan', 'null', 'NULL'}

    for row in data_rows:
        for i, col in zip(col_indices, columns):
            val = row[i] if i < len(row) else ''

            if val in na_set:
                val = None
            else:
                # Try to convert to number
                try:
                    if '.' in val or 'e' in val.lower():
                        val = float(val)
                    else:
                        val = int(val)
                except (ValueError, TypeError):
                    pass

            column_data[col].append(val)

    df = DataFrame(column_data, columns=columns)

    # Set index if specified
    if index_col is not None:
        if isinstance(index_col, int):
            index_col = columns[index_col]
        df = df.set_index(index_col)

    return df


def to_csv(df: 'DataFrame', filepath: str, sep=',', index=True, header=True) -> None:
    """Write DataFrame to CSV file"""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=sep)

        # Write header
        if header:
            row = []
            if index:
                row.append('')
            row.extend(df._columns)
            writer.writerow(row)

        # Write data rows
        for i, idx in enumerate(df._index):
            row = []
            if index:
                row.append(idx)
            row.extend(df._data[col][i] for col in df._columns)
            writer.writerow(row)


def read_json(filepath: str, orient='records') -> 'DataFrame':
    """Read JSON file into DataFrame"""
    import json
    from .dataframe import DataFrame

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if orient == 'records':
        return DataFrame(data)
    elif orient == 'columns':
        return DataFrame(data)
    elif orient == 'index':
        records = []
        index = []
        for idx, row in data.items():
            index.append(idx)
            records.append(row)
        df = DataFrame(records)
        df._index = index
        df._index_map = {idx: i for i, idx in enumerate(df._index)}
        return df
    raise ValueError(f"Unknown orient: {orient}")


def to_json(df: 'DataFrame', filepath: str, orient='records', indent=2) -> None:
    """Write DataFrame to JSON file"""
    import json

    if orient == 'records':
        data = df.to_dict(orient='records')
    elif orient == 'columns':
        data = df.to_dict(orient='list')
    elif orient == 'index':
        data = {}
        for i, idx in enumerate(df._index):
            data[str(idx)] = {col: df._data[col][i] for col in df._columns}
    else:
        raise ValueError(f"Unknown orient: {orient}")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)
