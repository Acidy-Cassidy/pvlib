"""
mypsutil - Your custom psutil library

Cross-platform library for system and process utilities.
"""

# CPU functions
from .cpu import (
    cpu_count,
    cpu_times,
    cpu_percent,
    cpu_times_percent,
    cpu_freq,
    cpu_stats,
    getloadavg,
)

# Memory functions
from .memory import (
    virtual_memory,
    swap_memory,
)

# Disk functions
from .disk import (
    disk_usage,
    disk_partitions,
    disk_io_counters,
)

# Network functions
from .network import (
    net_io_counters,
    net_if_addrs,
    net_if_stats,
    net_connections,
    CONN_ESTABLISHED,
    CONN_SYN_SENT,
    CONN_SYN_RECV,
    CONN_FIN_WAIT1,
    CONN_FIN_WAIT2,
    CONN_TIME_WAIT,
    CONN_CLOSE,
    CONN_CLOSE_WAIT,
    CONN_LAST_ACK,
    CONN_LISTEN,
    CONN_CLOSING,
    CONN_NONE,
)

# Process functions and class
from .process import (
    Process,
    pids,
    pid_exists,
    process_iter,
    wait_procs,
    NoSuchProcess,
    AccessDenied,
    STATUS_RUNNING,
    STATUS_SLEEPING,
    STATUS_DISK_SLEEP,
    STATUS_STOPPED,
    STATUS_TRACING_STOP,
    STATUS_ZOMBIE,
    STATUS_DEAD,
    STATUS_WAKE_KILL,
    STATUS_WAKING,
    STATUS_IDLE,
    STATUS_LOCKED,
    STATUS_WAITING,
)

# System functions
from .system import (
    boot_time,
    users,
    LINUX,
    WINDOWS,
    MACOS,
    BSD,
    POSIX,
    ARCH,
    version_info,
    sensors_temperatures,
    sensors_fans,
    sensors_battery,
    POWER_TIME_UNKNOWN,
    POWER_TIME_UNLIMITED,
)

# Named tuples (re-export for convenience)
from .cpu import scputimes, scpufreq, scpustats
from .memory import svmem, sswap
from .disk import sdiskusage, sdiskpart, sdiskio
from .network import snetio, snicaddr, snicstats, sconn
from .process import pmem, pcputimes, pio, popenfile, pthread, pctxsw
from .system import suser, shwtemp, sfan, sbattery

# Version
__version__ = '1.0.0'
__author__ = 'Custom Implementation'

__all__ = [
    # CPU
    'cpu_count', 'cpu_times', 'cpu_percent', 'cpu_times_percent',
    'cpu_freq', 'cpu_stats', 'getloadavg',
    'scputimes', 'scpufreq', 'scpustats',

    # Memory
    'virtual_memory', 'swap_memory',
    'svmem', 'sswap',

    # Disk
    'disk_usage', 'disk_partitions', 'disk_io_counters',
    'sdiskusage', 'sdiskpart', 'sdiskio',

    # Network
    'net_io_counters', 'net_if_addrs', 'net_if_stats', 'net_connections',
    'snetio', 'snicaddr', 'snicstats', 'sconn',
    'CONN_ESTABLISHED', 'CONN_SYN_SENT', 'CONN_SYN_RECV',
    'CONN_FIN_WAIT1', 'CONN_FIN_WAIT2', 'CONN_TIME_WAIT',
    'CONN_CLOSE', 'CONN_CLOSE_WAIT', 'CONN_LAST_ACK',
    'CONN_LISTEN', 'CONN_CLOSING', 'CONN_NONE',

    # Process
    'Process', 'pids', 'pid_exists', 'process_iter', 'wait_procs',
    'NoSuchProcess', 'AccessDenied',
    'pmem', 'pcputimes', 'pio', 'popenfile', 'pthread', 'pctxsw',
    'STATUS_RUNNING', 'STATUS_SLEEPING', 'STATUS_DISK_SLEEP',
    'STATUS_STOPPED', 'STATUS_TRACING_STOP', 'STATUS_ZOMBIE',
    'STATUS_DEAD', 'STATUS_WAKE_KILL', 'STATUS_WAKING',
    'STATUS_IDLE', 'STATUS_LOCKED', 'STATUS_WAITING',

    # System
    'boot_time', 'users',
    'LINUX', 'WINDOWS', 'MACOS', 'BSD', 'POSIX', 'ARCH',
    'version_info',
    'sensors_temperatures', 'sensors_fans', 'sensors_battery',
    'suser', 'shwtemp', 'sfan', 'sbattery',
    'POWER_TIME_UNKNOWN', 'POWER_TIME_UNLIMITED',
]
