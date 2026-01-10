"""
mypsutil Memory information
"""

import os
from collections import namedtuple

# Named tuples for memory info
svmem = namedtuple('svmem', ['total', 'available', 'percent', 'used', 'free',
                             'active', 'inactive', 'buffers', 'cached', 'shared', 'slab'])
sswap = namedtuple('sswap', ['total', 'used', 'free', 'percent', 'sin', 'sout'])


def _read_meminfo():
    """Read /proc/meminfo and return as dict"""
    mem = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    # Value is in kB, convert to bytes
                    value_parts = parts[1].strip().split()
                    value = int(value_parts[0]) * 1024  # kB to bytes
                    mem[key] = value
    except (IOError, OSError, ValueError):
        pass
    return mem


def virtual_memory():
    """
    Return statistics about system memory usage.

    Returns a named tuple with:
    - total: total physical memory
    - available: memory that can be given to processes without swapping
    - percent: percentage of memory used
    - used: memory used
    - free: memory not used at all (zeroed) that is readily available
    - active: memory currently in use or very recently used
    - inactive: memory marked as not used
    - buffers: cache for things like file system metadata
    - cached: cache for various things
    - shared: memory that may be accessed by multiple processes
    - slab: in-kernel data structures cache
    """
    mem = _read_meminfo()

    total = mem.get('MemTotal', 0)
    free = mem.get('MemFree', 0)
    buffers = mem.get('Buffers', 0)
    cached = mem.get('Cached', 0)
    shared = mem.get('Shmem', 0)
    active = mem.get('Active', 0)
    inactive = mem.get('Inactive', 0)
    slab = mem.get('Slab', 0)

    # Available memory (kernel 3.14+)
    available = mem.get('MemAvailable', 0)
    if available == 0:
        # Estimate available memory
        available = free + buffers + cached

    used = total - free - buffers - cached
    if used < 0:
        used = total - free

    percent = round((total - available) / total * 100, 1) if total > 0 else 0.0

    return svmem(
        total=total,
        available=available,
        percent=percent,
        used=used,
        free=free,
        active=active,
        inactive=inactive,
        buffers=buffers,
        cached=cached,
        shared=shared,
        slab=slab
    )


def swap_memory():
    """
    Return statistics about swap memory.

    Returns a named tuple with:
    - total: total swap memory
    - used: used swap memory
    - free: free swap memory
    - percent: percentage of swap used
    - sin: bytes swapped in from disk
    - sout: bytes swapped out to disk
    """
    mem = _read_meminfo()

    total = mem.get('SwapTotal', 0)
    free = mem.get('SwapFree', 0)
    used = total - free

    percent = round(used / total * 100, 1) if total > 0 else 0.0

    # Get swap I/O from /proc/vmstat
    sin = 0
    sout = 0
    try:
        with open('/proc/vmstat', 'r') as f:
            for line in f:
                if line.startswith('pswpin '):
                    sin = int(line.split()[1]) * 4096  # pages to bytes
                elif line.startswith('pswpout '):
                    sout = int(line.split()[1]) * 4096
    except (IOError, OSError, ValueError):
        pass

    return sswap(
        total=total,
        used=used,
        free=free,
        percent=percent,
        sin=sin,
        sout=sout
    )
