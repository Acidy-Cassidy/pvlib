"""
mypsutil System information
"""

import os
import time
import socket
from collections import namedtuple

# Named tuples for system info
suser = namedtuple('suser', ['name', 'terminal', 'host', 'started', 'pid'])


def boot_time():
    """
    Return system boot time as a Unix timestamp.
    """
    try:
        with open('/proc/stat', 'r') as f:
            for line in f:
                if line.startswith('btime '):
                    return float(line.split()[1])
    except (IOError, OSError, ValueError):
        pass

    # Fallback: use uptime
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
            return time.time() - uptime_seconds
    except (IOError, OSError, ValueError):
        return 0.0


def users():
    """
    Return users currently connected to the system.
    """
    result = []

    try:
        import struct

        # Read from utmp file
        utmp_paths = ['/var/run/utmp', '/run/utmp', '/var/adm/utmp']

        for utmp_path in utmp_paths:
            if os.path.exists(utmp_path):
                with open(utmp_path, 'rb') as f:
                    # utmp record structure varies by system
                    # Simplified parsing for Linux
                    while True:
                        data = f.read(384)  # Typical utmp record size on Linux
                        if not data or len(data) < 384:
                            break

                        # Type is first 4 bytes (little endian)
                        record_type = struct.unpack('<I', data[0:4])[0]

                        # Type 7 is USER_PROCESS
                        if record_type == 7:
                            # User name at offset 4, 32 bytes
                            user = data[4:36].rstrip(b'\x00').decode('utf-8', errors='replace')
                            # Terminal at offset 8, 32 bytes (after ut_id)
                            terminal = data[40:72].rstrip(b'\x00').decode('utf-8', errors='replace')
                            # Host at offset 76, 256 bytes
                            host = data[76:332].rstrip(b'\x00').decode('utf-8', errors='replace')
                            # Time at offset 340, 4 bytes
                            started = struct.unpack('<I', data[340:344])[0]
                            # PID at offset 36, 4 bytes
                            pid = struct.unpack('<I', data[36:40])[0]

                            if user:
                                result.append(suser(
                                    name=user,
                                    terminal=terminal,
                                    host=host,
                                    started=float(started),
                                    pid=pid
                                ))
                break
    except (IOError, OSError, struct.error):
        pass

    # Fallback: try 'who' command parsing
    if not result:
        try:
            import subprocess
            output = subprocess.check_output(['who'], universal_newlines=True)
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        result.append(suser(
                            name=parts[0],
                            terminal=parts[1] if len(parts) > 1 else '',
                            host=parts[4].strip('()') if len(parts) > 4 else '',
                            started=0.0,
                            pid=0
                        ))
        except (subprocess.SubprocessError, OSError):
            pass

    return result


# Platform constants
LINUX = os.name == 'posix' and os.path.exists('/proc')
WINDOWS = os.name == 'nt'
MACOS = os.name == 'posix' and os.uname().sysname == 'Darwin'
BSD = os.name == 'posix' and 'bsd' in os.uname().sysname.lower()
POSIX = os.name == 'posix'


def version_info():
    """Return mypsutil version as tuple"""
    return (1, 0, 0)


# Architecture info
def _get_arch():
    """Get system architecture"""
    import platform
    return platform.machine()


ARCH = _get_arch()


# Sensors (temperature, fans, battery)
shwtemp = namedtuple('shwtemp', ['label', 'current', 'high', 'critical'])
sfan = namedtuple('sfan', ['label', 'current'])
sbattery = namedtuple('sbattery', ['percent', 'secsleft', 'power_plugged'])

POWER_TIME_UNKNOWN = -1
POWER_TIME_UNLIMITED = -2


def sensors_temperatures(fahrenheit=False):
    """
    Return hardware temperatures.

    Returns a dict mapping hardware name to list of temperature readings.
    """
    result = {}

    def to_temp(celsius):
        if fahrenheit:
            return celsius * 9 / 5 + 32
        return celsius

    # Read from /sys/class/hwmon
    hwmon_base = '/sys/class/hwmon'
    try:
        for hwmon in os.listdir(hwmon_base):
            hwmon_path = f'{hwmon_base}/{hwmon}'

            # Get sensor name
            name = 'unknown'
            try:
                with open(f'{hwmon_path}/name', 'r') as f:
                    name = f.read().strip()
            except (IOError, OSError):
                pass

            if name not in result:
                result[name] = []

            # Find temperature inputs
            for entry in os.listdir(hwmon_path):
                if entry.startswith('temp') and entry.endswith('_input'):
                    prefix = entry[:-6]  # Remove '_input'

                    try:
                        with open(f'{hwmon_path}/{entry}', 'r') as f:
                            current = to_temp(int(f.read().strip()) / 1000)
                    except (IOError, OSError, ValueError):
                        continue

                    # Get label
                    label = prefix
                    try:
                        with open(f'{hwmon_path}/{prefix}_label', 'r') as f:
                            label = f.read().strip()
                    except (IOError, OSError):
                        pass

                    # Get high/critical thresholds
                    high = None
                    critical = None
                    try:
                        with open(f'{hwmon_path}/{prefix}_max', 'r') as f:
                            high = to_temp(int(f.read().strip()) / 1000)
                    except (IOError, OSError, ValueError):
                        pass
                    try:
                        with open(f'{hwmon_path}/{prefix}_crit', 'r') as f:
                            critical = to_temp(int(f.read().strip()) / 1000)
                    except (IOError, OSError, ValueError):
                        pass

                    result[name].append(shwtemp(
                        label=label,
                        current=current,
                        high=high,
                        critical=critical
                    ))

    except (IOError, OSError):
        pass

    # Also check /sys/class/thermal
    thermal_base = '/sys/class/thermal'
    try:
        for zone in os.listdir(thermal_base):
            if zone.startswith('thermal_zone'):
                zone_path = f'{thermal_base}/{zone}'

                name = 'thermal'
                try:
                    with open(f'{zone_path}/type', 'r') as f:
                        name = f.read().strip()
                except (IOError, OSError):
                    pass

                try:
                    with open(f'{zone_path}/temp', 'r') as f:
                        current = to_temp(int(f.read().strip()) / 1000)

                    if name not in result:
                        result[name] = []

                    result[name].append(shwtemp(
                        label=zone,
                        current=current,
                        high=None,
                        critical=None
                    ))
                except (IOError, OSError, ValueError):
                    pass
    except (IOError, OSError):
        pass

    return result


def sensors_fans():
    """
    Return hardware fan speeds.

    Returns a dict mapping hardware name to list of fan readings.
    """
    result = {}

    hwmon_base = '/sys/class/hwmon'
    try:
        for hwmon in os.listdir(hwmon_base):
            hwmon_path = f'{hwmon_base}/{hwmon}'

            name = 'unknown'
            try:
                with open(f'{hwmon_path}/name', 'r') as f:
                    name = f.read().strip()
            except (IOError, OSError):
                pass

            for entry in os.listdir(hwmon_path):
                if entry.startswith('fan') and entry.endswith('_input'):
                    prefix = entry[:-6]

                    try:
                        with open(f'{hwmon_path}/{entry}', 'r') as f:
                            current = int(f.read().strip())
                    except (IOError, OSError, ValueError):
                        continue

                    label = prefix
                    try:
                        with open(f'{hwmon_path}/{prefix}_label', 'r') as f:
                            label = f.read().strip()
                    except (IOError, OSError):
                        pass

                    if name not in result:
                        result[name] = []

                    result[name].append(sfan(label=label, current=current))

    except (IOError, OSError):
        pass

    return result


def sensors_battery():
    """
    Return battery status.
    """
    power_base = '/sys/class/power_supply'

    try:
        for supply in os.listdir(power_base):
            supply_path = f'{power_base}/{supply}'

            # Check if it's a battery
            try:
                with open(f'{supply_path}/type', 'r') as f:
                    if f.read().strip().lower() != 'battery':
                        continue
            except (IOError, OSError):
                continue

            # Get capacity
            percent = 0
            try:
                with open(f'{supply_path}/capacity', 'r') as f:
                    percent = int(f.read().strip())
            except (IOError, OSError, ValueError):
                pass

            # Get status
            power_plugged = None
            try:
                with open(f'{supply_path}/status', 'r') as f:
                    status = f.read().strip().lower()
                    if status == 'charging':
                        power_plugged = True
                    elif status == 'discharging':
                        power_plugged = False
                    elif status == 'full':
                        power_plugged = True
            except (IOError, OSError):
                pass

            # Estimate time remaining (simplified)
            secsleft = POWER_TIME_UNKNOWN

            return sbattery(
                percent=percent,
                secsleft=secsleft,
                power_plugged=power_plugged
            )

    except (IOError, OSError):
        pass

    return None
