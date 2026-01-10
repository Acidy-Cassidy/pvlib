"""
mypsutil Network information
"""

import os
import socket
from collections import namedtuple

# Named tuples for network info
snetio = namedtuple('snetio', ['bytes_sent', 'bytes_recv', 'packets_sent', 'packets_recv',
                               'errin', 'errout', 'dropin', 'dropout'])
snicaddr = namedtuple('snicaddr', ['family', 'address', 'netmask', 'broadcast', 'ptp'])
snicstats = namedtuple('snicstats', ['isup', 'duplex', 'speed', 'mtu'])
sconn = namedtuple('sconn', ['fd', 'family', 'type', 'laddr', 'raddr', 'status', 'pid'])
addr = namedtuple('addr', ['ip', 'port'])

# Connection statuses
CONN_ESTABLISHED = 'ESTABLISHED'
CONN_SYN_SENT = 'SYN_SENT'
CONN_SYN_RECV = 'SYN_RECV'
CONN_FIN_WAIT1 = 'FIN_WAIT1'
CONN_FIN_WAIT2 = 'FIN_WAIT2'
CONN_TIME_WAIT = 'TIME_WAIT'
CONN_CLOSE = 'CLOSE'
CONN_CLOSE_WAIT = 'CLOSE_WAIT'
CONN_LAST_ACK = 'LAST_ACK'
CONN_LISTEN = 'LISTEN'
CONN_CLOSING = 'CLOSING'
CONN_NONE = 'NONE'

# TCP state mapping from /proc/net/tcp
_TCP_STATES = {
    '01': CONN_ESTABLISHED,
    '02': CONN_SYN_SENT,
    '03': CONN_SYN_RECV,
    '04': CONN_FIN_WAIT1,
    '05': CONN_FIN_WAIT2,
    '06': CONN_TIME_WAIT,
    '07': CONN_CLOSE,
    '08': CONN_CLOSE_WAIT,
    '09': CONN_LAST_ACK,
    '0A': CONN_LISTEN,
    '0B': CONN_CLOSING,
}


def net_io_counters(pernic=False, nowrap=True):
    """
    Return network I/O statistics.

    Parameters:
    -----------
    pernic : bool
        If True, return a dict with stats per network interface
    nowrap : bool
        If True, handle counter wrapping

    Returns named tuple(s) with bytes/packets sent/received and errors.
    """
    nics = {}

    try:
        with open('/proc/net/dev', 'r') as f:
            lines = f.readlines()[2:]  # Skip header lines

            for line in lines:
                if ':' in line:
                    name, data = line.split(':')
                    name = name.strip()
                    fields = data.split()

                    if len(fields) >= 16:
                        nics[name] = snetio(
                            bytes_recv=int(fields[0]),
                            packets_recv=int(fields[1]),
                            errin=int(fields[2]),
                            dropin=int(fields[3]),
                            bytes_sent=int(fields[8]),
                            packets_sent=int(fields[9]),
                            errout=int(fields[10]),
                            dropout=int(fields[11])
                        )
    except (IOError, OSError, ValueError):
        pass

    if pernic:
        return nics
    else:
        # Aggregate all interfaces
        if not nics:
            return None

        totals = {
            'bytes_sent': 0,
            'bytes_recv': 0,
            'packets_sent': 0,
            'packets_recv': 0,
            'errin': 0,
            'errout': 0,
            'dropin': 0,
            'dropout': 0
        }

        for nic in nics.values():
            totals['bytes_sent'] += nic.bytes_sent
            totals['bytes_recv'] += nic.bytes_recv
            totals['packets_sent'] += nic.packets_sent
            totals['packets_recv'] += nic.packets_recv
            totals['errin'] += nic.errin
            totals['errout'] += nic.errout
            totals['dropin'] += nic.dropin
            totals['dropout'] += nic.dropout

        return snetio(**totals)


def net_if_addrs():
    """
    Return network interface addresses.

    Returns a dict mapping interface names to lists of address tuples.
    """
    result = {}

    try:
        # Get list of interfaces
        interfaces = os.listdir('/sys/class/net/')

        for iface in interfaces:
            result[iface] = []

            # Try to get IPv4 address using socket
            try:
                import fcntl
                import struct
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # SIOCGIFADDR
                addr_info = fcntl.ioctl(
                    sock.fileno(),
                    0x8915,
                    struct.pack('256s', iface[:15].encode('utf-8'))
                )
                ip_addr = socket.inet_ntoa(addr_info[20:24])

                # SIOCGIFNETMASK
                netmask_info = fcntl.ioctl(
                    sock.fileno(),
                    0x891b,
                    struct.pack('256s', iface[:15].encode('utf-8'))
                )
                netmask = socket.inet_ntoa(netmask_info[20:24])

                result[iface].append(snicaddr(
                    family=socket.AF_INET,
                    address=ip_addr,
                    netmask=netmask,
                    broadcast=None,
                    ptp=None
                ))
                sock.close()
            except (IOError, OSError, socket.error):
                pass

            # Try to get MAC address
            try:
                with open(f'/sys/class/net/{iface}/address', 'r') as f:
                    mac = f.read().strip()
                    if mac and mac != '00:00:00:00:00:00':
                        result[iface].append(snicaddr(
                            family=socket.AF_PACKET if hasattr(socket, 'AF_PACKET') else -1,
                            address=mac,
                            netmask=None,
                            broadcast=None,
                            ptp=None
                        ))
            except (IOError, OSError):
                pass

    except (IOError, OSError):
        pass

    return result


def net_if_stats():
    """
    Return network interface statistics.

    Returns a dict mapping interface names to stats tuples.
    """
    result = {}

    try:
        interfaces = os.listdir('/sys/class/net/')

        for iface in interfaces:
            base = f'/sys/class/net/{iface}'

            # Check if interface is up
            isup = False
            try:
                with open(f'{base}/operstate', 'r') as f:
                    isup = f.read().strip().lower() == 'up'
            except (IOError, OSError):
                pass

            # Get MTU
            mtu = 0
            try:
                with open(f'{base}/mtu', 'r') as f:
                    mtu = int(f.read().strip())
            except (IOError, OSError, ValueError):
                pass

            # Get speed (in Mbps)
            speed = 0
            try:
                with open(f'{base}/speed', 'r') as f:
                    speed = int(f.read().strip())
            except (IOError, OSError, ValueError):
                pass

            # Duplex (0=half, 1=full, 2=unknown)
            duplex = 2
            try:
                with open(f'{base}/duplex', 'r') as f:
                    duplex_str = f.read().strip().lower()
                    if duplex_str == 'full':
                        duplex = 1
                    elif duplex_str == 'half':
                        duplex = 0
            except (IOError, OSError):
                pass

            result[iface] = snicstats(isup=isup, duplex=duplex, speed=speed, mtu=mtu)

    except (IOError, OSError):
        pass

    return result


def net_connections(kind='inet'):
    """
    Return system-wide socket connections.

    Parameters:
    -----------
    kind : str
        Filter connections by type:
        'inet' - IPv4 and IPv6
        'inet4' - IPv4 only
        'inet6' - IPv6 only
        'tcp' - TCP (IPv4)
        'tcp4' - TCP (IPv4)
        'tcp6' - TCP (IPv6)
        'udp' - UDP (IPv4)
        'udp4' - UDP (IPv4)
        'udp6' - UDP (IPv6)
        'all' - All connections

    Returns a list of connection named tuples.
    """
    connections = []

    def parse_addr(addr_str):
        """Parse address:port from hex format"""
        if addr_str == '00000000:0000':
            return addr('0.0.0.0', 0)
        try:
            ip_hex, port_hex = addr_str.split(':')
            # Convert hex IP to dotted decimal (little endian)
            ip_int = int(ip_hex, 16)
            ip = socket.inet_ntoa(ip_int.to_bytes(4, 'little'))
            port = int(port_hex, 16)
            return addr(ip, port)
        except (ValueError, socket.error):
            return addr('', 0)

    def read_proc_net(filename, family, sock_type):
        """Read connections from /proc/net/tcp or /proc/net/udp"""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()[1:]  # Skip header

                for line in lines:
                    parts = line.split()
                    if len(parts) >= 10:
                        local_addr = parse_addr(parts[1])
                        remote_addr = parse_addr(parts[2])
                        state = _TCP_STATES.get(parts[3], CONN_NONE)

                        # Get inode to find PID
                        inode = parts[9]

                        connections.append(sconn(
                            fd=-1,
                            family=family,
                            type=sock_type,
                            laddr=local_addr,
                            raddr=remote_addr,
                            status=state if sock_type == socket.SOCK_STREAM else CONN_NONE,
                            pid=None
                        ))
        except (IOError, OSError):
            pass

    # Determine which files to read
    if kind in ('inet', 'inet4', 'tcp', 'tcp4', 'all'):
        read_proc_net('/proc/net/tcp', socket.AF_INET, socket.SOCK_STREAM)
    if kind in ('inet', 'inet4', 'udp', 'udp4', 'all'):
        read_proc_net('/proc/net/udp', socket.AF_INET, socket.SOCK_DGRAM)
    if kind in ('inet', 'inet6', 'tcp6', 'all'):
        read_proc_net('/proc/net/tcp6', socket.AF_INET6, socket.SOCK_STREAM)
    if kind in ('inet', 'inet6', 'udp6', 'all'):
        read_proc_net('/proc/net/udp6', socket.AF_INET6, socket.SOCK_DGRAM)

    return connections
