"""
mypandas - Your custom pandas library
"""

from .dataframe import DataFrame
from .series import Series
from .io import read_csv, to_csv, read_json, to_json


def merge(left, right, on=None, how='inner', left_on=None, right_on=None,
          suffixes=('_x', '_y')) -> DataFrame:
    """Merge two DataFrames"""
    return left.merge(right, on=on, how=how, left_on=left_on, right_on=right_on,
                      suffixes=suffixes)


def concat(objs, axis=0, ignore_index=False):
    """Concatenate DataFrames or Series"""
    if not objs:
        return DataFrame()

    if axis == 0:
        # Vertical concatenation (stack rows)
        all_columns = []
        for obj in objs:
            if isinstance(obj, DataFrame):
                for col in obj._columns:
                    if col not in all_columns:
                        all_columns.append(col)

        result_data = {col: [] for col in all_columns}
        result_index = []

        for obj in objs:
            if isinstance(obj, DataFrame):
                for i in range(len(obj._index)):
                    for col in all_columns:
                        if col in obj._data:
                            result_data[col].append(obj._data[col][i])
                        else:
                            result_data[col].append(None)
                    if ignore_index:
                        result_index.append(len(result_index))
                    else:
                        result_index.append(obj._index[i])
            elif isinstance(obj, Series):
                for i in range(len(obj._index)):
                    for col in all_columns:
                        if col == obj.name:
                            result_data[col].append(obj._data[i])
                        else:
                            result_data[col].append(None)
                    if ignore_index:
                        result_index.append(len(result_index))
                    else:
                        result_index.append(obj._index[i])

        return DataFrame(result_data, columns=all_columns, index=result_index)

    elif axis == 1:
        # Horizontal concatenation (add columns)
        if not all(isinstance(obj, DataFrame) for obj in objs):
            raise ValueError("axis=1 concatenation requires all DataFrames")

        result_data = {}
        result_index = objs[0]._index.copy()

        for obj in objs:
            for col in obj._columns:
                new_col = col
                suffix = 0
                while new_col in result_data:
                    suffix += 1
                    new_col = f"{col}_{suffix}"
                result_data[new_col] = obj._data[col].copy()

        return DataFrame(result_data, index=result_index)

    raise ValueError(f"axis must be 0 or 1, got {axis}")


# NaN constant
NA = float('nan')
NaT = None  # Not a Time placeholder


__version__ = "0.1.0"
__all__ = ["DataFrame", "Series", "read_csv", "to_csv", "read_json", "to_json",
           "merge", "concat", "NA", "NaT"]
