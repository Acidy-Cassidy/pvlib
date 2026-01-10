"""
mypsutil Process information
"""

import os
import signal
import time
from collections import namedtuple

# Named tuples for process info
pmem = namedtuple('pmem', ['rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty'])
pcputimes = namedtuple('pcputimes', ['user', 'system', 'children_user', 'children_system'])
pio = namedtuple('pio', ['read_count', 'write_count', 'read_bytes', 'write_bytes',
                         'read_chars', 'write_chars'])
popenfile = namedtuple('popenfile', ['path', 'fd'])
pthread = namedtuple('pthread', ['id', 'user_time', 'system_time'])
pctxsw = namedtuple('pctxsw', ['voluntary', 'involuntary'])

# Process status constants
STATUS_RUNNING = 'running'
STATUS_SLEEPING = 'sleeping'
STATUS_DISK_SLEEP = 'disk-sleep'
STATUS_STOPPED = 'stopped'
STATUS_TRACING_STOP = 'tracing-stop'
STATUS_ZOMBIE = 'zombie'
STATUS_DEAD = 'dead'
STATUS_WAKE_KILL = 'wake-kill'
STATUS_WAKING = 'waking'
STATUS_IDLE = 'idle'
STATUS_LOCKED = 'locked'
STATUS_WAITING = 'waiting'

_STATUS_MAP = {
    'R': STATUS_RUNNING,
    'S': STATUS_SLEEPING,
    'D': STATUS_DISK_SLEEP,
    'T': STATUS_STOPPED,
    't': STATUS_TRACING_STOP,
    'Z': STATUS_ZOMBIE,
    'X': STATUS_DEAD,
    'x': STATUS_DEAD,
    'K': STATUS_WAKE_KILL,
    'W': STATUS_WAKING,
    'I': STATUS_IDLE,
    'P': STATUS_LOCKED,
}


class NoSuchProcess(Exception):
    """Exception raised when a process doesn't exist"""
    def __init__(self, pid, name=None, msg=None):
        self.pid = pid
        self.name = name
        self.msg = msg or f"process no longer exists (pid={pid})"
        super().__init__(self.msg)


class AccessDenied(Exception):
    """Exception raised when permission is denied"""
    def __init__(self, pid=None, name=None, msg=None):
        self.pid = pid
        self.name = name
        self.msg = msg or f"access denied (pid={pid})"
        super().__init__(self.msg)


class Process:
    """
    Represents an OS process with the given PID.
    """

    def __init__(self, pid=None):
        """
        Initialize a Process object.

        Parameters:
        -----------
        pid : int
            Process ID. If None, use current process.
        """
        if pid is None:
            pid = os.getpid()
        self._pid = pid
        self._name = None
        self._create_time = None

        # Verify process exists
        if not self.is_running():
            raise NoSuchProcess(pid)

    @property
    def pid(self):
        """The process PID"""
        return self._pid

    def _read_proc_file(self, filename):
        """Read a file from /proc/[pid]/"""
        path = f'/proc/{self._pid}/{filename}'
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise NoSuchProcess(self._pid)
        except PermissionError:
            raise AccessDenied(self._pid)

    def _read_stat(self):
        """Parse /proc/[pid]/stat"""
        content = self._read_proc_file('stat')
        # Handle process names with spaces/parentheses
        # Format: pid (name) state ...
        start = content.index('(') + 1
        end = content.rindex(')')
        name = content[start:end]
        parts = content[end + 2:].split()
        return name, parts

    def name(self):
        """Return process name"""
        if self._name is None:
            name, _ = self._read_stat()
            self._name = name
        return self._name

    def exe(self):
        """Return process executable path"""
        try:
            return os.readlink(f'/proc/{self._pid}/exe')
        except FileNotFoundError:
            raise NoSuchProcess(self._pid)
        except PermissionError:
            raise AccessDenied(self._pid)

    def cmdline(self):
        """Return process command line arguments"""
        content = self._read_proc_file('cmdline')
        return content.split('\x00')[:-1] if content else []

    def cwd(self):
        """Return process current working directory"""
        try:
            return os.readlink(f'/proc/{self._pid}/cwd')
        except FileNotFoundError:
            raise NoSuchProcess(self._pid)
        except PermissionError:
            raise AccessDenied(self._pid)

    def status(self):
        """Return process status"""
        _, parts = self._read_stat()
        state = parts[0]
        return _STATUS_MAP.get(state, state)

    def ppid(self):
        """Return parent process ID"""
        _, parts = self._read_stat()
        return int(parts[1])

    def parent(self):
        """Return parent process as Process object"""
        ppid = self.ppid()
        if ppid:
            return Process(ppid)
        return None

    def uids(self):
        """Return process UIDs (real, effective, saved)"""
        content = self._read_proc_file('status')
        for line in content.split('\n'):
            if line.startswith('Uid:'):
                parts = line.split()[1:4]
                return tuple(int(x) for x in parts)
        return (0, 0, 0)

    def gids(self):
        """Return process GIDs (real, effective, saved)"""
        content = self._read_proc_file('status')
        for line in content.split('\n'):
            if line.startswith('Gid:'):
                parts = line.split()[1:4]
                return tuple(int(x) for x in parts)
        return (0, 0, 0)

    def username(self):
        """Return process username"""
        import pwd
        try:
            return pwd.getpwuid(self.uids()[0]).pw_name
        except (KeyError, ImportError):
            return str(self.uids()[0])

    def create_time(self):
        """Return process creation time as timestamp"""
        if self._create_time is None:
            _, parts = self._read_stat()
            # parts[19] is starttime in clock ticks
            starttime = int(parts[19])

            # Get system boot time
            boot_time = 0
            try:
                with open('/proc/stat', 'r') as f:
                    for line in f:
                        if line.startswith('btime '):
                            boot_time = int(line.split()[1])
                            break
            except (IOError, OSError, ValueError):
                pass

            # Convert clock ticks to seconds
            try:
                hz = os.sysconf('SC_CLK_TCK')
            except (ValueError, OSError):
                hz = 100

            self._create_time = boot_time + (starttime / hz)

        return self._create_time

    def memory_info(self):
        """Return process memory information"""
        content = self._read_proc_file('statm')
        parts = content.split()
        page_size = os.sysconf('SC_PAGE_SIZE')

        # statm: size resident shared text lib data dirty
        vms = int(parts[0]) * page_size
        rss = int(parts[1]) * page_size
        shared = int(parts[2]) * page_size
        text = int(parts[3]) * page_size
        lib = int(parts[4]) * page_size
        data = int(parts[5]) * page_size
        dirty = int(parts[6]) * page_size if len(parts) > 6 else 0

        return pmem(rss=rss, vms=vms, shared=shared, text=text,
                   lib=lib, data=data, dirty=dirty)

    def memory_percent(self, memtype='rss'):
        """Return process memory as a percentage"""
        from .memory import virtual_memory
        mem = self.memory_info()
        total = virtual_memory().total
        value = getattr(mem, memtype, mem.rss)
        return round(value / total * 100, 2)

    def cpu_times(self):
        """Return process CPU times"""
        _, parts = self._read_stat()

        try:
            hz = os.sysconf('SC_CLK_TCK')
        except (ValueError, OSError):
            hz = 100

        user = int(parts[11]) / hz
        system = int(parts[12]) / hz
        children_user = int(parts[13]) / hz
        children_system = int(parts[14]) / hz

        return pcputimes(user=user, system=system,
                        children_user=children_user, children_system=children_system)

    def cpu_percent(self, interval=None):
        """Return process CPU utilization as a percentage"""
        if interval is not None and interval > 0:
            t1 = self.cpu_times()
            time.sleep(interval)
            t2 = self.cpu_times()

            delta_user = t2.user - t1.user
            delta_system = t2.system - t1.system
            delta_time = delta_user + delta_system

            return round(delta_time / interval * 100, 1)
        else:
            return 0.0

    def num_threads(self):
        """Return number of threads"""
        _, parts = self._read_stat()
        return int(parts[17])

    def threads(self):
        """Return process threads"""
        result = []
        try:
            task_dir = f'/proc/{self._pid}/task'
            for tid in os.listdir(task_dir):
                try:
                    with open(f'{task_dir}/{tid}/stat', 'r') as f:
                        content = f.read()
                        end = content.rindex(')')
                        parts = content[end + 2:].split()

                        try:
                            hz = os.sysconf('SC_CLK_TCK')
                        except (ValueError, OSError):
                            hz = 100

                        user_time = int(parts[11]) / hz
                        system_time = int(parts[12]) / hz

                        result.append(pthread(id=int(tid), user_time=user_time,
                                            system_time=system_time))
                except (IOError, OSError, ValueError):
                    pass
        except (IOError, OSError):
            pass
        return result

    def nice(self):
        """Return process nice value"""
        _, parts = self._read_stat()
        return int(parts[16])

    def is_running(self):
        """Check if process is running"""
        try:
            os.kill(self._pid, 0)
            return True
        except OSError:
            return False

    def suspend(self):
        """Suspend the process"""
        os.kill(self._pid, signal.SIGSTOP)

    def resume(self):
        """Resume the process"""
        os.kill(self._pid, signal.SIGCONT)

    def terminate(self):
        """Terminate the process (SIGTERM)"""
        os.kill(self._pid, signal.SIGTERM)

    def kill(self):
        """Kill the process (SIGKILL)"""
        os.kill(self._pid, signal.SIGKILL)

    def wait(self, timeout=None):
        """Wait for process to terminate"""
        return os.waitpid(self._pid, 0)

    def open_files(self):
        """Return files opened by process"""
        result = []
        try:
            fd_dir = f'/proc/{self._pid}/fd'
            for fd in os.listdir(fd_dir):
                try:
                    path = os.readlink(f'{fd_dir}/{fd}')
                    if path.startswith('/') and not path.startswith('/proc'):
                        result.append(popenfile(path=path, fd=int(fd)))
                except (OSError, ValueError):
                    pass
        except (IOError, OSError):
            pass
        return result

    def num_fds(self):
        """Return number of file descriptors"""
        try:
            return len(os.listdir(f'/proc/{self._pid}/fd'))
        except (IOError, OSError):
            return 0

    def environ(self):
        """Return process environment variables"""
        content = self._read_proc_file('environ')
        env = {}
        for item in content.split('\x00'):
            if '=' in item:
                key, _, value = item.partition('=')
                env[key] = value
        return env

    def __repr__(self):
        return f"psutil.Process(pid={self._pid}, name='{self.name()}', status='{self.status()}')"

    def __eq__(self, other):
        if isinstance(other, Process):
            return self._pid == other._pid and self.create_time() == other.create_time()
        return False

    def __hash__(self):
        return hash(self._pid)


def pids():
    """Return a list of all running PIDs"""
    result = []
    try:
        for entry in os.listdir('/proc'):
            if entry.isdigit():
                result.append(int(entry))
    except (IOError, OSError):
        pass
    return sorted(result)


def pid_exists(pid):
    """Check if a PID exists"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def process_iter(attrs=None, ad_value=None):
    """
    Return an iterator over all running processes.

    Parameters:
    -----------
    attrs : list
        List of process attributes to retrieve
    ad_value : any
        Default value for attributes that couldn't be retrieved
    """
    for pid in pids():
        try:
            proc = Process(pid)
            if attrs:
                info = {'pid': pid}
                for attr in attrs:
                    try:
                        value = getattr(proc, attr)
                        info[attr] = value() if callable(value) else value
                    except (AccessDenied, NoSuchProcess):
                        info[attr] = ad_value
                proc.info = info
            yield proc
        except (NoSuchProcess, AccessDenied):
            pass


def wait_procs(procs, timeout=None, callback=None):
    """
    Wait for multiple processes to terminate.
    """
    gone = []
    alive = []

    for proc in procs:
        if not proc.is_running():
            gone.append(proc)
        else:
            alive.append(proc)

    if callback:
        for proc in gone:
            callback(proc)

    return (gone, alive)
