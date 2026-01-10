"""
mytqdm - Your custom tqdm library

A simple progress bar library for Python iterables.
"""

from .core import tqdm, trange, tqdm_notebook, tqdm_pandas

# Version
__version__ = '1.0.0'
__author__ = 'Custom Implementation'

# Aliases for compatibility
auto = tqdm
autonotebook = tqdm
std_tqdm = tqdm

__all__ = [
    'tqdm',
    'trange',
    'tqdm_notebook',
    'tqdm_pandas',
    'auto',
    'autonotebook',
    'std_tqdm',
]
