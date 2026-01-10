"""
mypsutil CPU information
"""

import os
import time
from collections import namedtuple

# Named tuples for CPU info
scputimes = namedtuple('scputimes', ['user', 'system', 'idle', 'nice', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice'])
scpufreq = namedtuple('scpufreq', ['current', 'min', 'max'])
scpustats = namedtuple('scpustats', ['ctx_switches', 'interrupts', 'soft_interrupts', 'syscalls'])

# Store previous CPU times for percent calculation
_last_cpu_times = None
_last_cpu_times_per_cpu = None
_last_time = None


def _read_proc_stat():
    """Read /proc/stat and return CPU lines"""
    try:
        with open('/proc/stat', 'r') as f:
            return f.readlines()
    except (IOError, OSError):
        return []


def _parse_cpu_line(line):
    """Parse a CPU line from /proc/stat"""
    parts = line.split()
    # cpu user nice system idle iowait irq softirq steal guest guest_nice
    values = [int(x) for x in parts[1:]]
    # Pad with zeros if needed
    while len(values) < 10:
        values.append(0)
    return scputimes(*values[:10])


def cpu_count(logical=True):
    """
    Return the number of CPUs in the system.

    Parameters:
    -----------
    logical : bool
        If True, return logical CPUs (including hyperthreading)
        If False, return physical CPU cores
    """
    if logical:
        # Try os.cpu_count first
        count = os.cpu_count()
        if count:
            return count

        # Fallback to /proc/cpuinfo
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return sum(1 for line in f if line.startswith('processor'))
        except (IOError, OSError):
            return 1
    else:
        # Physical cores
        try:
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
                # Count unique physical id + core id combinations
                physical_ids = set()
                current_physical = None
                for line in content.split('\n'):
                    if line.startswith('physical id'):
                        current_physical = line.split(':')[1].strip()
                    elif line.startswith('core id') and current_physical is not None:
                        core_id = line.split(':')[1].strip()
                        physical_ids.add((current_physical, core_id))

                if physical_ids:
                    return len(physical_ids)

                # Fallback: count 'cpu cores' entries
                cores = [int(line.split(':')[1]) for line in content.split('\n')
                        if line.startswith('cpu cores')]
                if cores:
                    return cores[0]
        except (IOError, OSError, ValueError):
            pass

        # Last fallback
        return cpu_count(logical=True)


def cpu_times(percpu=False):
    """
    Return system CPU times as a named tuple.

    Parameters:
    -----------
    percpu : bool
        If True, return a list of times for each CPU
    """
    lines = _read_proc_stat()

    if percpu:
        result = []
        for line in lines:
            if line.startswith('cpu') and not line.startswith('cpu '):
                result.append(_parse_cpu_line(line))
        return result if result else [_parse_cpu_line('cpu 0 0 0 0 0 0 0 0 0 0')]
    else:
        for line in lines:
            if line.startswith('cpu '):
                return _parse_cpu_line(line)
        return scputimes(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)


def cpu_percent(interval=None, percpu=False):
    """
    Return CPU utilization as a percentage.

    Parameters:
    -----------
    interval : float
        If not None, block for this many seconds and compare CPU times
    percpu : bool
        If True, return a list of percentages for each CPU
    """
    global _last_cpu_times, _last_cpu_times_per_cpu, _last_time

    def calc_percent(t1, t2):
        """Calculate CPU percent between two time snapshots"""
        t1_all = sum(t1)
        t2_all = sum(t2)
        t1_busy = t1_all - t1.idle - t1.iowait
        t2_busy = t2_all - t2.idle - t2.iowait

        if t2_all == t1_all:
            return 0.0

        busy_delta = t2_busy - t1_busy
        all_delta = t2_all - t1_all

        return round((busy_delta / all_delta) * 100, 1)

    if interval is not None and interval > 0:
        t1 = cpu_times(percpu=percpu)
        time.sleep(interval)
        t2 = cpu_times(percpu=percpu)

        if percpu:
            return [calc_percent(t1[i], t2[i]) for i in range(len(t1))]
        else:
            return calc_percent(t1, t2)
    else:
        # Non-blocking mode - compare with last call
        current_times = cpu_times(percpu=percpu)
        current_time = time.time()

        if percpu:
            if _last_cpu_times_per_cpu is None:
                _last_cpu_times_per_cpu = current_times
                _last_time = current_time
                return [0.0] * len(current_times)

            result = [calc_percent(_last_cpu_times_per_cpu[i], current_times[i])
                     for i in range(len(current_times))]
            _last_cpu_times_per_cpu = current_times
            return result
        else:
            if _last_cpu_times is None:
                _last_cpu_times = current_times
                _last_time = current_time
                return 0.0

            result = calc_percent(_last_cpu_times, current_times)
            _last_cpu_times = current_times
            return result


def cpu_times_percent(interval=None, percpu=False):
    """
    Return CPU times as percentages.
    """
    t1 = cpu_times(percpu=percpu)

    if interval is not None and interval > 0:
        time.sleep(interval)

    t2 = cpu_times(percpu=percpu)

    def calc_times_percent(times1, times2):
        total = sum(times2) - sum(times1)
        if total == 0:
            return scputimes(*([0.0] * 10))

        return scputimes(*[
            round(((getattr(times2, f) - getattr(times1, f)) / total) * 100, 1)
            for f in times1._fields
        ])

    if percpu:
        return [calc_times_percent(t1[i], t2[i]) for i in range(len(t1))]
    else:
        return calc_times_percent(t1, t2)


def cpu_freq(percpu=False):
    """
    Return CPU frequency as a named tuple.

    Returns (current, min, max) in MHz.
    """
    def read_freq_file(path):
        try:
            with open(path, 'r') as f:
                return int(f.read().strip()) / 1000  # Convert kHz to MHz
        except (IOError, OSError, ValueError):
            return 0.0

    if percpu:
        result = []
        cpu_id = 0
        while True:
            base = f'/sys/devices/system/cpu/cpu{cpu_id}/cpufreq'
            if not os.path.exists(base):
                break

            current = read_freq_file(f'{base}/scaling_cur_freq')
            min_freq = read_freq_file(f'{base}/scaling_min_freq')
            max_freq = read_freq_file(f'{base}/scaling_max_freq')

            result.append(scpufreq(current, min_freq, max_freq))
            cpu_id += 1

        return result if result else [scpufreq(0.0, 0.0, 0.0)]
    else:
        # Return average/first CPU frequency
        base = '/sys/devices/system/cpu/cpu0/cpufreq'
        current = read_freq_file(f'{base}/scaling_cur_freq')
        min_freq = read_freq_file(f'{base}/scaling_min_freq')
        max_freq = read_freq_file(f'{base}/scaling_max_freq')

        # Try /proc/cpuinfo as fallback
        if current == 0:
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'cpu MHz' in line:
                            current = float(line.split(':')[1].strip())
                            break
            except (IOError, OSError, ValueError):
                pass

        return scpufreq(current, min_freq, max_freq)


def cpu_stats():
    """
    Return CPU statistics.
    """
    ctx_switches = 0
    interrupts = 0
    soft_interrupts = 0

    try:
        with open('/proc/stat', 'r') as f:
            for line in f:
                if line.startswith('ctxt '):
                    ctx_switches = int(line.split()[1])
                elif line.startswith('intr '):
                    interrupts = int(line.split()[1])
                elif line.startswith('softirq '):
                    soft_interrupts = int(line.split()[1])
    except (IOError, OSError, ValueError):
        pass

    return scpustats(ctx_switches, interrupts, soft_interrupts, 0)


def getloadavg():
    """
    Return the system load average over the last 1, 5, and 15 minutes.
    """
    try:
        return os.getloadavg()
    except (OSError, AttributeError):
        try:
            with open('/proc/loadavg', 'r') as f:
                parts = f.read().split()
                return (float(parts[0]), float(parts[1]), float(parts[2]))
        except (IOError, OSError, ValueError):
            return (0.0, 0.0, 0.0)
