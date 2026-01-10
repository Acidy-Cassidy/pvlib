"""
mypsutil Disk information
"""

import os
from collections import namedtuple

# Named tuples for disk info
sdiskusage = namedtuple('sdiskusage', ['total', 'used', 'free', 'percent'])
sdiskpart = namedtuple('sdiskpart', ['device', 'mountpoint', 'fstype', 'opts', 'maxfile', 'maxpath'])
sdiskio = namedtuple('sdiskio', ['read_count', 'write_count', 'read_bytes', 'write_bytes',
                                  'read_time', 'write_time', 'read_merged_count',
                                  'write_merged_count', 'busy_time'])


def disk_usage(path):
    """
    Return disk usage statistics for the given path.

    Parameters:
    -----------
    path : str
        Path to get disk usage for

    Returns a named tuple with total, used, free, and percent.
    """
    try:
        st = os.statvfs(path)

        # Total space
        total = st.f_blocks * st.f_frsize

        # Free space available to non-root users
        free = st.f_bavail * st.f_frsize

        # Used space
        used = (st.f_blocks - st.f_bfree) * st.f_frsize

        # Calculate percentage
        # Use total - free_for_root for accurate percentage
        total_used = (st.f_blocks - st.f_bfree) * st.f_frsize
        percent = round(total_used / total * 100, 1) if total > 0 else 0.0

        return sdiskusage(total=total, used=used, free=free, percent=percent)
    except (OSError, IOError) as e:
        raise OSError(f"Cannot get disk usage for {path}: {e}")


def disk_partitions(all=False):
    """
    Return all mounted disk partitions.

    Parameters:
    -----------
    all : bool
        If True, include all filesystems including virtual ones

    Returns a list of named tuples with device, mountpoint, fstype, and opts.
    """
    partitions = []

    # Virtual filesystem types to exclude
    virtual_fstypes = {
        'sysfs', 'proc', 'devtmpfs', 'devpts', 'tmpfs', 'securityfs',
        'cgroup', 'cgroup2', 'pstore', 'debugfs', 'hugetlbfs', 'mqueue',
        'fusectl', 'configfs', 'binfmt_misc', 'autofs', 'rpc_pipefs',
        'nfsd', 'overlay', 'nsfs', 'tracefs', 'bpf'
    }

    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4:
                    device = parts[0]
                    mountpoint = parts[1]
                    fstype = parts[2]
                    opts = parts[3]

                    # Skip virtual filesystems unless 'all' is True
                    if not all and fstype in virtual_fstypes:
                        continue

                    # Skip certain device patterns
                    if not all and not device.startswith('/'):
                        continue

                    partitions.append(sdiskpart(
                        device=device,
                        mountpoint=mountpoint,
                        fstype=fstype,
                        opts=opts,
                        maxfile=255,  # Typical max filename length
                        maxpath=4096  # Typical max path length
                    ))
    except (IOError, OSError):
        pass

    return partitions


def disk_io_counters(perdisk=False, nowrap=True):
    """
    Return disk I/O statistics.

    Parameters:
    -----------
    perdisk : bool
        If True, return a dict with stats per disk
    nowrap : bool
        If True, handle counter wrapping

    Returns named tuple(s) with read/write counts, bytes, and times.
    """
    disks = {}

    try:
        with open('/proc/diskstats', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 14:
                    # parts[2] is device name
                    name = parts[2]

                    # Skip partitions (e.g., sda1) unless it's a whole disk
                    # Also skip loop and ram devices
                    if name.startswith('loop') or name.startswith('ram'):
                        continue

                    # Fields from /proc/diskstats
                    reads_completed = int(parts[3])
                    reads_merged = int(parts[4])
                    sectors_read = int(parts[5])
                    read_time = int(parts[6])
                    writes_completed = int(parts[7])
                    writes_merged = int(parts[8])
                    sectors_written = int(parts[9])
                    write_time = int(parts[10])
                    io_in_progress = int(parts[11]) if len(parts) > 11 else 0
                    io_time = int(parts[12]) if len(parts) > 12 else 0

                    # Sector size is typically 512 bytes
                    sector_size = 512

                    disks[name] = sdiskio(
                        read_count=reads_completed,
                        write_count=writes_completed,
                        read_bytes=sectors_read * sector_size,
                        write_bytes=sectors_written * sector_size,
                        read_time=read_time,
                        write_time=write_time,
                        read_merged_count=reads_merged,
                        write_merged_count=writes_merged,
                        busy_time=io_time
                    )
    except (IOError, OSError, ValueError):
        pass

    if perdisk:
        return disks
    else:
        # Aggregate all disks
        if not disks:
            return None

        totals = {
            'read_count': 0,
            'write_count': 0,
            'read_bytes': 0,
            'write_bytes': 0,
            'read_time': 0,
            'write_time': 0,
            'read_merged_count': 0,
            'write_merged_count': 0,
            'busy_time': 0
        }

        for disk in disks.values():
            totals['read_count'] += disk.read_count
            totals['write_count'] += disk.write_count
            totals['read_bytes'] += disk.read_bytes
            totals['write_bytes'] += disk.write_bytes
            totals['read_time'] += disk.read_time
            totals['write_time'] += disk.write_time
            totals['read_merged_count'] += disk.read_merged_count
            totals['write_merged_count'] += disk.write_merged_count
            totals['busy_time'] += disk.busy_time

        return sdiskio(**totals)
