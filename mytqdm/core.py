"""
mytqdm core - Progress bar implementation
"""

import sys
import time
from typing import Optional, Iterable, Iterator, Any, TextIO, Callable


class tqdm:
    """
    A simple progress bar for iterables.

    Usage:
        for item in tqdm(items):
            process(item)

        # With manual control
        pbar = tqdm(total=100)
        for i in range(100):
            pbar.update(1)
        pbar.close()
    """

    def __init__(
        self,
        iterable: Optional[Iterable] = None,
        desc: Optional[str] = None,
        total: Optional[int] = None,
        leave: bool = True,
        file: Optional[TextIO] = None,
        ncols: Optional[int] = None,
        mininterval: float = 0.1,
        maxinterval: float = 10.0,
        miniters: Optional[int] = None,
        ascii: Optional[bool] = None,
        disable: bool = False,
        unit: str = 'it',
        unit_scale: bool = False,
        dynamic_ncols: bool = False,
        smoothing: float = 0.3,
        bar_format: Optional[str] = None,
        initial: int = 0,
        position: Optional[int] = None,
        postfix: Optional[dict] = None,
        unit_divisor: float = 1000,
        colour: Optional[str] = None,
        delay: float = 0,
    ):
        """
        Initialize the progress bar.

        Parameters:
        -----------
        iterable : Iterable, optional
            Iterable to wrap with progress bar
        desc : str, optional
            Description prefix for the progress bar
        total : int, optional
            Total number of iterations (inferred from iterable if possible)
        leave : bool
            Whether to leave the progress bar on screen after completion
        file : TextIO, optional
            Output file (default: sys.stderr)
        ncols : int, optional
            Width of progress bar (default: auto-detect or 80)
        mininterval : float
            Minimum update interval in seconds
        disable : bool
            Whether to disable the progress bar entirely
        unit : str
            Unit for iteration counting
        unit_scale : bool
            Whether to scale units (K, M, etc.)
        bar_format : str, optional
            Custom format string for the bar
        initial : int
            Initial counter value
        postfix : dict, optional
            Additional stats to display
        colour : str, optional
            Bar colour (not implemented in terminal version)
        """
        self.iterable = iterable
        self.desc = desc or ''
        self.leave = leave
        self.file = file or sys.stderr
        self.ncols = ncols or 80
        self.mininterval = mininterval
        self.maxinterval = maxinterval
        self.miniters = miniters or 1
        self.ascii = ascii if ascii is not None else True
        self.disable = disable
        self.unit = unit
        self.unit_scale = unit_scale
        self.dynamic_ncols = dynamic_ncols
        self.smoothing = smoothing
        self.bar_format = bar_format
        self.position = position
        self.postfix = postfix or {}
        self.unit_divisor = unit_divisor
        self.colour = colour
        self.delay = delay

        # Determine total
        if total is not None:
            self.total = total
        elif iterable is not None:
            try:
                self.total = len(iterable)
            except (TypeError, AttributeError):
                self.total = None
        else:
            self.total = None

        # Internal state
        self.n = initial
        self.start_time = time.time()
        self.last_print_time = self.start_time
        self.last_print_n = initial
        self._closed = False
        self.fp_write = self.file.write

        # Display initial bar
        if not self.disable:
            self._display()

    def __iter__(self) -> Iterator:
        """Iterate over wrapped iterable with progress updates"""
        if self.iterable is None:
            return

        for item in self.iterable:
            yield item
            self.update()

        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __len__(self) -> int:
        if self.total is not None:
            return self.total
        if self.iterable is not None:
            try:
                return len(self.iterable)
            except (TypeError, AttributeError):
                pass
        return 0

    def update(self, n: int = 1) -> None:
        """
        Update the progress bar by n iterations.

        Parameters:
        -----------
        n : int
            Number of iterations to increment
        """
        if self.disable:
            return

        self.n += n

        # Check if we should display
        current_time = time.time()
        delta_time = current_time - self.last_print_time

        if delta_time >= self.mininterval:
            self._display()
            self.last_print_time = current_time
            self.last_print_n = self.n

    def _format_sizeof(self, num: float, suffix: str = '') -> str:
        """Format a number with SI prefixes"""
        if not self.unit_scale:
            return f'{num:.0f}{suffix}'

        for unit in ['', 'K', 'M', 'G', 'T', 'P']:
            if abs(num) < self.unit_divisor:
                return f'{num:.1f}{unit}{suffix}'
            num /= self.unit_divisor
        return f'{num:.1f}E{suffix}'

    def _format_interval(self, seconds: float) -> str:
        """Format time interval as HH:MM:SS or MM:SS"""
        if seconds < 0:
            return '?'

        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)

        if hours:
            return f'{hours:02d}:{mins:02d}:{secs:02d}'
        return f'{mins:02d}:{secs:02d}'

    def _display(self) -> None:
        """Display the progress bar"""
        if self.disable or self._closed:
            return

        elapsed = time.time() - self.start_time

        # Calculate rate
        if elapsed > 0:
            rate = self.n / elapsed
        else:
            rate = 0

        # Format rate
        rate_str = self._format_sizeof(rate, self.unit + '/s')

        # Build progress bar
        if self.total is not None and self.total > 0:
            percentage = min(100, (self.n / self.total) * 100)

            # Calculate remaining time
            if rate > 0:
                remaining = (self.total - self.n) / rate
                remaining_str = self._format_interval(remaining)
            else:
                remaining_str = '?'

            # Build bar
            bar_width = max(10, self.ncols - 50)
            filled = int(bar_width * self.n / self.total)

            if self.ascii:
                bar = '#' * filled + '-' * (bar_width - filled)
            else:
                bar = '\u2588' * filled + '\u2591' * (bar_width - filled)

            # Format: desc: 100%|###---| 10/100 [00:05<00:15, 2.00it/s]
            n_str = self._format_sizeof(self.n) if self.unit_scale else str(self.n)
            total_str = self._format_sizeof(self.total) if self.unit_scale else str(self.total)

            line = f'\r{self.desc}: ' if self.desc else '\r'
            line += f'{percentage:3.0f}%|{bar}| {n_str}/{total_str} '
            line += f'[{self._format_interval(elapsed)}<{remaining_str}, {rate_str}]'
        else:
            # Unknown total - just show count and rate
            n_str = self._format_sizeof(self.n) if self.unit_scale else str(self.n)
            line = f'\r{self.desc}: ' if self.desc else '\r'
            line += f'{n_str}{self.unit} [{self._format_interval(elapsed)}, {rate_str}]'

        # Add postfix
        if self.postfix:
            postfix_str = ', '.join(f'{k}={v}' for k, v in self.postfix.items())
            line += f', {postfix_str}'

        # Write to output
        self.fp_write(line)
        self.file.flush()

    def set_description(self, desc: Optional[str] = None, refresh: bool = True) -> None:
        """Set/modify description prefix"""
        self.desc = desc or ''
        if refresh:
            self._display()

    def set_description_str(self, desc: Optional[str] = None, refresh: bool = True) -> None:
        """Set description without any formatting"""
        self.set_description(desc, refresh)

    def set_postfix(self, ordered_dict: Optional[dict] = None,
                    refresh: bool = True, **kwargs) -> None:
        """Set/modify postfix (additional stats)"""
        if ordered_dict:
            self.postfix.update(ordered_dict)
        self.postfix.update(kwargs)
        if refresh:
            self._display()

    def set_postfix_str(self, s: str = '', refresh: bool = True) -> None:
        """Set postfix as a raw string"""
        self.postfix = {'': s}
        if refresh:
            self._display()

    def clear(self, nolock: bool = False) -> None:
        """Clear the progress bar display"""
        if self.disable:
            return
        self.fp_write('\r' + ' ' * self.ncols + '\r')
        self.file.flush()

    def refresh(self, nolock: bool = False) -> None:
        """Force refresh the display"""
        self._display()

    def reset(self, total: Optional[int] = None) -> None:
        """Reset the progress bar to start"""
        self.n = 0
        if total is not None:
            self.total = total
        self.start_time = time.time()
        self.last_print_time = self.start_time
        self.last_print_n = 0
        self._display()

    def close(self) -> None:
        """Close the progress bar"""
        if self._closed:
            return

        self._closed = True

        if not self.disable:
            self._display()
            if self.leave:
                self.fp_write('\n')
            else:
                self.clear()
            self.file.flush()

    def unpause(self) -> None:
        """Restart timing from current time"""
        cur_time = time.time()
        self.start_time += cur_time - self.last_print_time
        self.last_print_time = cur_time

    @property
    def format_dict(self) -> dict:
        """Return a dict of current progress bar state"""
        elapsed = time.time() - self.start_time
        rate = self.n / elapsed if elapsed > 0 else 0

        return {
            'n': self.n,
            'total': self.total,
            'elapsed': elapsed,
            'rate': rate,
            'prefix': self.desc,
            'unit': self.unit,
            'postfix': self.postfix,
        }

    def display(self, msg: Optional[str] = None, pos: Optional[int] = None) -> None:
        """Display a message or current progress bar"""
        if msg:
            self.fp_write(msg)
            self.file.flush()
        else:
            self._display()

    def write(self, s: str, file: Optional[TextIO] = None,
              end: str = '\n', nolock: bool = False) -> None:
        """Write a message without interfering with progress bar"""
        fp = file or self.file
        self.clear()
        fp.write(s + end)
        fp.flush()
        self._display()

    @classmethod
    def write_stream(cls, s: str, file: Optional[TextIO] = None,
                     end: str = '\n') -> None:
        """Class method to write without active instance"""
        fp = file or sys.stderr
        fp.write(s + end)
        fp.flush()


def trange(*args, **kwargs) -> tqdm:
    """
    Shorthand for tqdm(range(*args), **kwargs)

    Usage:
        for i in trange(100):
            process(i)
    """
    return tqdm(range(*args), **kwargs)


def tqdm_notebook(*args, **kwargs) -> tqdm:
    """Alias for tqdm (notebook version not implemented)"""
    return tqdm(*args, **kwargs)


def tqdm_pandas(tqdm_class=tqdm):
    """Register pandas progress_apply (placeholder)"""
    pass
