#!/usr/bin/env python3
"""
Test program for custom mynumpy, mypandas, myrequests, and mytqdm libraries.
Simulates usage patterns from m-ndy-main and rag_star projects.
"""

import mynumpy as np
import mypandas as pd
import myrequests as requests
import mytqdm
from mytqdm import tqdm, trange
import mycolorama
from mycolorama import Fore, Back, Style, Cursor, init, deinit
import mypsutil
import mypytest
import mymatplotlib
import mymatplotlib.pyplot as plt
import sqlite3
import tempfile
import os
import time


def test_numpy_basics():
    """Basic numpy operations"""
    print("=" * 50)
    print("NUMPY BASICS")
    print("=" * 50)

    # Array creation
    arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    print(f"Created array:\n{arr}")
    print(f"Shape: {arr.shape}, Size: {arr.size}, Ndim: {arr.ndim}")

    # Math operations
    print(f"\nSum: {np.sum(arr)}")
    print(f"Mean: {np.mean(arr)}")
    print(f"Min: {np.min(arr)}, Max: {np.max(arr)}")

    # Element-wise operations
    arr2 = arr * 2
    print(f"\nArray * 2:\n{arr2}")

    # Matrix multiplication
    a = np.array([[1, 2], [3, 4]])
    b = np.array([[5, 6], [7, 8]])
    print(f"\nMatrix a:\n{a}")
    print(f"Matrix b:\n{b}")
    print(f"a @ b:\n{a @ b}")

    return True


def test_numpy_linalg():
    """Linear algebra - used in face_recognition_module.py"""
    print("\n" + "=" * 50)
    print("NUMPY LINALG (face recognition style)")
    print("=" * 50)

    # Simulate face embeddings
    enrolled_face = np.array([0.12, 0.45, 0.67, 0.23, 0.89, 0.34])
    detected_face = np.array([0.14, 0.43, 0.69, 0.21, 0.87, 0.36])
    stranger_face = np.array([0.85, 0.12, 0.33, 0.76, 0.45, 0.91])

    # Calculate distances
    dist_same = np.linalg.norm(enrolled_face - detected_face)
    dist_stranger = np.linalg.norm(enrolled_face - stranger_face)

    print(f"Enrolled face embedding: {enrolled_face}")
    print(f"Detected face embedding: {detected_face}")
    print(f"Distance (same person): {dist_same:.4f}")
    print(f"Distance (stranger): {dist_stranger:.4f}")

    threshold = 0.6
    print(f"\nThreshold: {threshold}")
    print(f"Same person match: {dist_same <= threshold}")
    print(f"Stranger match: {dist_stranger <= threshold}")

    return True


def test_numpy_embeddings():
    """Embedding operations - used in rag_star embeddings.py"""
    print("\n" + "=" * 50)
    print("NUMPY EMBEDDINGS (RAG style)")
    print("=" * 50)

    # Simulate sentence embeddings
    embeddings = [
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8],
        [0.9, 1.0, 1.1, 1.2],
    ]

    # Convert to array with specific dtype
    X = np.asarray(embeddings, dtype=np.float32)
    print(f"Embeddings array:\n{X}")
    print(f"Shape: {X.shape}, Dtype: {X.dtype}")
    print(f"Dimension (shape[1]): {X.shape[1]}")

    # Simulate query vector
    query = np.array([0.15, 0.25, 0.35, 0.45])

    # Calculate similarities (dot product for normalized vectors)
    similarities = []
    for i in range(X.shape[0]):
        # Get row as 1D array
        row = X[i]
        sim = np.dot(row, query)
        similarities.append(float(sim))

    print(f"\nQuery: {query}")
    print(f"Similarities: {similarities}")

    # Find best match
    sim_arr = np.array(similarities)
    best_idx = np.argmax(sim_arr)
    print(f"Best match: index {best_idx}")

    return True


def test_pandas_basics():
    """Basic pandas operations"""
    print("\n" + "=" * 50)
    print("PANDAS BASICS")
    print("=" * 50)

    # Create DataFrame
    df = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
        'age': [25, 30, 35, 28],
        'salary': [50000, 60000, 70000, 55000],
        'department': ['Engineering', 'Sales', 'Engineering', 'Marketing']
    })

    print("DataFrame:")
    print(df)

    print(f"\nColumns: {df.columns}")
    print(f"Shape: {df.shape}")

    print(f"\nAge statistics:")
    print(f"  Mean: {df['age'].mean()}")
    print(f"  Min: {df['age'].min()}")
    print(f"  Max: {df['age'].max()}")

    # Filtering
    print("\nEngineering department:")
    eng_df = df[df['department'] == 'Engineering']
    print(eng_df)

    # GroupBy
    print("\nSalary by department:")
    grouped = df.groupby('department').mean()
    print(grouped)

    return True


def test_pandas_merge():
    """Merge with suffixes - used in parse_player_stats.py"""
    print("\n" + "=" * 50)
    print("PANDAS MERGE (player stats style)")
    print("=" * 50)

    # Simulate player stats from different years
    stats_2023 = pd.DataFrame({
        'player_id': [101, 102, 103, 104],
        'name': ['Smith', 'Jones', 'Williams', 'Brown'],
        'batting_avg': [0.285, 0.312, 0.267, 0.298],
        'home_runs': [28, 35, 22, 31]
    })

    stats_2024 = pd.DataFrame({
        'player_id': [101, 102, 103, 105],
        'batting_avg': [0.291, 0.305, 0.278, 0.315],
        'home_runs': [32, 38, 25, 29]
    })

    print("2023 Stats:")
    print(stats_2023)
    print("\n2024 Stats:")
    print(stats_2024)

    # Merge with suffixes
    merged = pd.merge(
        stats_2023,
        stats_2024,
        on='player_id',
        suffixes=('_2023', '_2024')
    )

    print("\nMerged (inner join with suffixes):")
    print(merged)

    return True


def test_pandas_sql():
    """SQL operations - used in rag_star ingest.py"""
    print("\n" + "=" * 50)
    print("PANDAS SQL (ingest style)")
    print("=" * 50)

    # Create test data
    stars_df = pd.DataFrame({
        'star_id': [1001, 1002, 1003, 1004, 1005],
        'name': ['Sirius', 'Canopus', 'Arcturus', 'Vega', 'Capella'],
        'ra': [101.28, 95.99, 213.91, 279.23, 79.17],
        'dec': [-16.72, -52.70, 19.18, 38.78, 45.99],
        'magnitude': [-1.46, -0.74, -0.05, 0.03, 0.08]
    })

    print("Stars DataFrame:")
    print(stars_df)

    # Write to SQLite
    db_path = tempfile.mktemp(suffix='.db')
    conn = sqlite3.connect(db_path)

    stars_df.to_sql('stars', conn, if_exists='replace', index=False)
    print(f"\nWritten to SQLite: {db_path}")

    # Query back
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stars WHERE magnitude < 0")
    bright_stars = cursor.fetchall()
    print(f"\nBright stars (mag < 0) from SQL:")
    for star in bright_stars:
        print(f"  {star}")

    # Test append
    more_stars = pd.DataFrame({
        'star_id': [1006, 1007],
        'name': ['Rigel', 'Procyon'],
        'ra': [78.63, 114.83],
        'dec': [-8.20, 5.22],
        'magnitude': [0.13, 0.34]
    })
    more_stars.to_sql('stars', conn, if_exists='append', index=False)

    count = cursor.execute("SELECT COUNT(*) FROM stars").fetchone()[0]
    print(f"\nTotal stars after append: {count}")

    conn.close()
    os.unlink(db_path)

    return True


def test_pandas_csv():
    """CSV operations with various parameters"""
    print("\n" + "=" * 50)
    print("PANDAS CSV (advanced parsing)")
    print("=" * 50)

    # Create a CSV file with comments and various formats
    csv_content = """# This is a comment
# Another comment line
id,name,value,category
1,Alpha,100.5,A
2,Beta,200.75,B
3,Gamma,300.25,A
4,Delta,400.0,C
5,Epsilon,500.5,B
"""

    csv_path = tempfile.mktemp(suffix='.csv')
    with open(csv_path, 'w') as f:
        f.write(csv_content)

    # Read with comment skipping
    df = pd.read_csv(csv_path, comment='#')
    print("CSV with comments skipped:")
    print(df)

    print(f"\nData types inferred:")
    print(df.dtypes)

    os.unlink(csv_path)

    return True


def test_requests_basics():
    """Basic requests operations"""
    print("\n" + "=" * 50)
    print("REQUESTS BASICS")
    print("=" * 50)

    # Test module imports
    print(f"myrequests version: {requests.__version__}")

    # Test Response class
    from myrequests.models import Response, CaseInsensitiveDict

    resp = Response()
    resp.status_code = 200
    resp.reason = "OK"
    resp.url = "https://example.com"
    resp._content = b'{"message": "Hello, World!"}'
    resp.headers = CaseInsensitiveDict({'Content-Type': 'application/json'})

    print(f"\nResponse object: {resp}")
    print(f"Status code: {resp.status_code}")
    print(f"OK: {resp.ok}")
    print(f"Content (bytes): {resp.content}")
    print(f"Text: {resp.text}")
    print(f"JSON: {resp.json()}")

    # Test case insensitive dict
    print(f"\nHeaders (case insensitive):")
    print(f"  content-type: {resp.headers.get('content-type')}")
    print(f"  Content-Type: {resp.headers.get('Content-Type')}")
    print(f"  CONTENT-TYPE: {resp.headers.get('CONTENT-TYPE')}")

    # Test exceptions
    from myrequests.exceptions import RequestException, HTTPError, Timeout

    print(f"\nException classes available:")
    print(f"  RequestException: {RequestException}")
    print(f"  HTTPError: {HTTPError}")
    print(f"  Timeout: {Timeout}")

    return True


def test_requests_session():
    """Session usage - common pattern in API clients"""
    print("\n" + "=" * 50)
    print("REQUESTS SESSION (API client style)")
    print("=" * 50)

    # Test session creation and configuration
    session = requests.Session()
    session.headers['Authorization'] = 'Bearer test-token'
    session.headers['User-Agent'] = 'MyApp/1.0'

    print(f"Session created")
    print(f"Session headers: {session.headers}")
    print(f"Session cookies: {session.cookies}")

    # Test context manager
    with requests.Session() as s:
        s.headers['X-Custom'] = 'value'
        print(f"\nContext manager session headers: {s.headers}")

    print("\nSession tests passed (no actual HTTP calls made)")

    return True


def test_requests_http_codes():
    """Test HTTP status codes mapping"""
    print("\n" + "=" * 50)
    print("REQUESTS HTTP CODES")
    print("=" * 50)

    print(f"Status codes mapping:")
    print(f"  OK: {requests.codes['ok']}")
    print(f"  Created: {requests.codes['created']}")
    print(f"  Not Found: {requests.codes['not_found']}")
    print(f"  Internal Server Error: {requests.codes['internal_server_error']}")

    # Test Response status handling
    from myrequests.models import Response

    # Test successful response
    good_resp = Response()
    good_resp.status_code = 200
    good_resp.reason = "OK"
    good_resp.url = "https://api.example.com"
    print(f"\n200 Response: ok={good_resp.ok}, bool={bool(good_resp)}")

    # Test error response
    error_resp = Response()
    error_resp.status_code = 404
    error_resp.reason = "Not Found"
    error_resp.url = "https://api.example.com/missing"
    print(f"404 Response: ok={error_resp.ok}, bool={bool(error_resp)}")

    # Test raise_for_status
    try:
        error_resp.raise_for_status()
        print("ERROR: Should have raised HTTPError")
        return False
    except requests.HTTPError as e:
        print(f"HTTPError raised correctly: {type(e).__name__}")

    return True


def test_tqdm_basic():
    """Basic tqdm progress bar operations"""
    print("\n" + "=" * 50)
    print("TQDM BASICS")
    print("=" * 50)

    print(f"mytqdm version: {mytqdm.__version__}")

    # Test basic iteration
    print("\nBasic progress bar:")
    items = list(range(20))
    result = []
    for item in tqdm(items, desc="Processing"):
        result.append(item * 2)
        time.sleep(0.02)

    print(f"Processed {len(result)} items")

    # Test trange
    print("\nUsing trange:")
    total = 0
    for i in trange(15, desc="Counting"):
        total += i
        time.sleep(0.02)
    print(f"Sum: {total}")

    return True


def test_tqdm_manual():
    """Manual tqdm update - used for custom progress tracking"""
    print("\n" + "=" * 50)
    print("TQDM MANUAL UPDATE")
    print("=" * 50)

    # Test manual progress bar
    print("\nManual update mode:")
    pbar = tqdm(total=50, desc="Manual progress")
    for i in range(5):
        time.sleep(0.05)
        pbar.update(10)
    pbar.close()

    # Test with context manager
    print("\nContext manager mode:")
    with tqdm(total=30, desc="Context mgr") as pbar:
        for i in range(3):
            time.sleep(0.05)
            pbar.update(10)

    return True


def test_tqdm_features():
    """Test additional tqdm features"""
    print("\n" + "=" * 50)
    print("TQDM FEATURES")
    print("=" * 50)

    # Test set_description
    print("\nDynamic description:")
    pbar = tqdm(range(10), desc="Starting")
    for i, _ in enumerate(pbar):
        if i == 5:
            pbar.set_description("Halfway")
        time.sleep(0.02)

    # Test set_postfix
    print("\nWith postfix stats:")
    with tqdm(range(10), desc="Training") as pbar:
        for i in pbar:
            pbar.set_postfix(loss=1.0/(i+1), acc=i*10)
            time.sleep(0.02)

    # Test disable
    print("\nDisabled progress bar (no output expected):")
    for _ in tqdm(range(5), disable=True):
        time.sleep(0.01)
    print("Disabled test passed")

    # Test unknown total
    print("\nUnknown total (no percentage):")

    def gen():
        for i in range(8):
            yield i

    for _ in tqdm(gen(), desc="Generator"):
        time.sleep(0.02)

    return True


def test_colorama_basics():
    """Basic colorama operations"""
    print("\n" + "=" * 50)
    print("COLORAMA BASICS")
    print("=" * 50)

    print(f"mycolorama version: {mycolorama.__version__}")

    # Test Fore colors
    print("\nForeground colors:")
    print(f"  {Fore.RED}RED{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}GREEN{Style.RESET_ALL}")
    print(f"  {Fore.BLUE}BLUE{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}YELLOW{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}CYAN{Style.RESET_ALL}")
    print(f"  {Fore.MAGENTA}MAGENTA{Style.RESET_ALL}")

    # Test Back colors
    print("\nBackground colors:")
    print(f"  {Back.RED}RED BG{Style.RESET_ALL}")
    print(f"  {Back.GREEN}GREEN BG{Style.RESET_ALL}")
    print(f"  {Back.BLUE}BLUE BG{Style.RESET_ALL}")

    # Test styles
    print("\nStyles:")
    print(f"  {Style.BRIGHT}BRIGHT{Style.RESET_ALL}")
    print(f"  {Style.DIM}DIM{Style.RESET_ALL}")

    return True


def test_colorama_combinations():
    """Test color combinations"""
    print("\n" + "=" * 50)
    print("COLORAMA COMBINATIONS")
    print("=" * 50)

    # Combined foreground + background
    print("\nCombinations:")
    print(f"  {Fore.WHITE}{Back.RED}White on Red{Style.RESET_ALL}")
    print(f"  {Fore.BLACK}{Back.YELLOW}Black on Yellow{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}{Back.BLUE}White on Blue{Style.RESET_ALL}")

    # With style
    print(f"  {Style.BRIGHT}{Fore.GREEN}Bright Green{Style.RESET_ALL}")
    print(f"  {Style.BRIGHT}{Fore.RED}{Back.WHITE}Bright Red on White{Style.RESET_ALL}")

    # Light/extended colors
    print("\nExtended colors:")
    print(f"  {Fore.LIGHTRED_EX}Light Red{Style.RESET_ALL}")
    print(f"  {Fore.LIGHTGREEN_EX}Light Green{Style.RESET_ALL}")
    print(f"  {Fore.LIGHTBLUE_EX}Light Blue{Style.RESET_ALL}")

    return True


def test_colorama_codes():
    """Test ANSI code generation"""
    print("\n" + "=" * 50)
    print("COLORAMA ANSI CODES")
    print("=" * 50)

    from mycolorama.ansi import code_to_chars, CSI

    # Verify escape sequences
    print(f"CSI prefix: {repr(CSI)}")
    print(f"Fore.RED raw: {repr(Fore.RED)}")
    print(f"Back.GREEN raw: {repr(Back.GREEN)}")
    print(f"Style.BRIGHT raw: {repr(Style.BRIGHT)}")
    print(f"Style.RESET_ALL raw: {repr(Style.RESET_ALL)}")

    # Test code_to_chars function
    red_code = code_to_chars(31)
    print(f"\ncode_to_chars(31) = {repr(red_code)}")
    assert red_code == '\033[31m', f"Expected '\\033[31m', got {repr(red_code)}"
    print("Code generation verified!")

    return True


def test_colorama_cursor():
    """Test cursor control"""
    print("\n" + "=" * 50)
    print("COLORAMA CURSOR CONTROL")
    print("=" * 50)

    # Test cursor movement codes
    print(f"Cursor.UP(1) raw: {repr(Cursor.UP(1))}")
    print(f"Cursor.DOWN(2) raw: {repr(Cursor.DOWN(2))}")
    print(f"Cursor.FORWARD(3) raw: {repr(Cursor.FORWARD(3))}")
    print(f"Cursor.BACK(4) raw: {repr(Cursor.BACK(4))}")
    print(f"Cursor.POS(10, 5) raw: {repr(Cursor.POS(10, 5))}")

    # Verify format
    assert Cursor.UP(1) == '\033[1A'
    assert Cursor.DOWN(2) == '\033[2B'
    assert Cursor.FORWARD(3) == '\033[3C'
    assert Cursor.BACK(4) == '\033[4D'
    print("\nCursor codes verified!")

    return True


def test_colorama_init():
    """Test initialization functions"""
    print("\n" + "=" * 50)
    print("COLORAMA INITIALIZATION")
    print("=" * 50)

    from mycolorama import init, deinit, reinit, just_fix_windows_console

    # Test init/deinit cycle
    print("Testing init/deinit cycle...")
    init()
    print(f"  After init: stdout wrapped")
    deinit()
    print(f"  After deinit: stdout restored")

    # Test with autoreset
    print("\nTesting with autoreset=True...")
    init(autoreset=True)
    print(f"  {Fore.RED}This should auto-reset")
    print("  Back to normal")
    deinit()

    # Test just_fix_windows_console
    print("\nTesting just_fix_windows_console...")
    just_fix_windows_console()
    print("  Windows console fix applied (no-op on non-Windows)")

    print("\nInitialization tests passed!")

    return True


def test_psutil_cpu():
    """Test CPU information"""
    print("\n" + "=" * 50)
    print("PSUTIL CPU")
    print("=" * 50)

    print(f"mypsutil version: {mypsutil.__version__}")

    # CPU count
    logical_cpus = mypsutil.cpu_count(logical=True)
    physical_cpus = mypsutil.cpu_count(logical=False)
    print(f"\nCPU Count:")
    print(f"  Logical CPUs: {logical_cpus}")
    print(f"  Physical CPUs: {physical_cpus}")

    # CPU times
    cpu_times = mypsutil.cpu_times()
    print(f"\nCPU Times:")
    print(f"  User: {cpu_times.user:.1f}s")
    print(f"  System: {cpu_times.system:.1f}s")
    print(f"  Idle: {cpu_times.idle:.1f}s")

    # CPU percent (brief interval)
    cpu_pct = mypsutil.cpu_percent(interval=0.1)
    print(f"\nCPU Percent: {cpu_pct}%")

    # CPU frequency
    cpu_freq = mypsutil.cpu_freq()
    print(f"\nCPU Frequency:")
    print(f"  Current: {cpu_freq.current:.0f} MHz")
    print(f"  Min: {cpu_freq.min:.0f} MHz")
    print(f"  Max: {cpu_freq.max:.0f} MHz")

    # Load average
    load = mypsutil.getloadavg()
    print(f"\nLoad Average: {load[0]:.2f}, {load[1]:.2f}, {load[2]:.2f}")

    return True


def test_psutil_memory():
    """Test memory information"""
    print("\n" + "=" * 50)
    print("PSUTIL MEMORY")
    print("=" * 50)

    # Virtual memory
    vmem = mypsutil.virtual_memory()
    print(f"\nVirtual Memory:")
    print(f"  Total: {vmem.total / (1024**3):.2f} GB")
    print(f"  Available: {vmem.available / (1024**3):.2f} GB")
    print(f"  Used: {vmem.used / (1024**3):.2f} GB")
    print(f"  Free: {vmem.free / (1024**3):.2f} GB")
    print(f"  Percent: {vmem.percent}%")

    # Swap memory
    swap = mypsutil.swap_memory()
    print(f"\nSwap Memory:")
    print(f"  Total: {swap.total / (1024**3):.2f} GB")
    print(f"  Used: {swap.used / (1024**3):.2f} GB")
    print(f"  Free: {swap.free / (1024**3):.2f} GB")
    print(f"  Percent: {swap.percent}%")

    return True


def test_psutil_disk():
    """Test disk information"""
    print("\n" + "=" * 50)
    print("PSUTIL DISK")
    print("=" * 50)

    # Disk usage for root
    usage = mypsutil.disk_usage('/')
    print(f"\nDisk Usage (/):")
    print(f"  Total: {usage.total / (1024**3):.2f} GB")
    print(f"  Used: {usage.used / (1024**3):.2f} GB")
    print(f"  Free: {usage.free / (1024**3):.2f} GB")
    print(f"  Percent: {usage.percent}%")

    # Disk partitions
    partitions = mypsutil.disk_partitions(all=False)
    print(f"\nDisk Partitions ({len(partitions)} found):")
    for p in partitions[:3]:  # Show first 3
        print(f"  {p.device} -> {p.mountpoint} ({p.fstype})")

    # Disk I/O
    disk_io = mypsutil.disk_io_counters()
    if disk_io:
        print(f"\nDisk I/O:")
        print(f"  Read: {disk_io.read_bytes / (1024**3):.2f} GB")
        print(f"  Written: {disk_io.write_bytes / (1024**3):.2f} GB")

    return True


def test_psutil_network():
    """Test network information"""
    print("\n" + "=" * 50)
    print("PSUTIL NETWORK")
    print("=" * 50)

    # Network I/O
    net_io = mypsutil.net_io_counters()
    if net_io:
        print(f"\nNetwork I/O:")
        print(f"  Bytes Sent: {net_io.bytes_sent / (1024**2):.2f} MB")
        print(f"  Bytes Recv: {net_io.bytes_recv / (1024**2):.2f} MB")
        print(f"  Packets Sent: {net_io.packets_sent}")
        print(f"  Packets Recv: {net_io.packets_recv}")

    # Network interfaces
    if_addrs = mypsutil.net_if_addrs()
    print(f"\nNetwork Interfaces ({len(if_addrs)} found):")
    for name, addrs in list(if_addrs.items())[:3]:
        print(f"  {name}:")
        for addr in addrs[:2]:
            print(f"    {addr.address}")

    # Interface stats
    if_stats = mypsutil.net_if_stats()
    print(f"\nInterface Stats:")
    for name, stats in list(if_stats.items())[:3]:
        print(f"  {name}: up={stats.isup}, mtu={stats.mtu}")

    return True


def test_psutil_process():
    """Test process information"""
    print("\n" + "=" * 50)
    print("PSUTIL PROCESS")
    print("=" * 50)

    # Get current process
    proc = mypsutil.Process()
    print(f"\nCurrent Process:")
    print(f"  PID: {proc.pid}")
    print(f"  Name: {proc.name()}")
    print(f"  Status: {proc.status()}")
    print(f"  PPID: {proc.ppid()}")

    # Memory info
    mem = proc.memory_info()
    print(f"\nProcess Memory:")
    print(f"  RSS: {mem.rss / (1024**2):.2f} MB")
    print(f"  VMS: {mem.vms / (1024**2):.2f} MB")

    # CPU times
    cpu_t = proc.cpu_times()
    print(f"\nProcess CPU Times:")
    print(f"  User: {cpu_t.user:.2f}s")
    print(f"  System: {cpu_t.system:.2f}s")

    # Other info
    print(f"\nOther Info:")
    print(f"  Threads: {proc.num_threads()}")
    print(f"  Nice: {proc.nice()}")
    print(f"  CWD: {proc.cwd()}")

    # List PIDs
    all_pids = mypsutil.pids()
    print(f"\nTotal processes: {len(all_pids)}")

    # Check pid_exists
    print(f"PID {proc.pid} exists: {mypsutil.pid_exists(proc.pid)}")
    print(f"PID 999999 exists: {mypsutil.pid_exists(999999)}")

    return True


def test_psutil_system():
    """Test system information"""
    print("\n" + "=" * 50)
    print("PSUTIL SYSTEM")
    print("=" * 50)

    # Boot time
    boot = mypsutil.boot_time()
    import datetime
    boot_dt = datetime.datetime.fromtimestamp(boot)
    print(f"\nBoot Time: {boot_dt}")

    # Platform info
    print(f"\nPlatform:")
    print(f"  LINUX: {mypsutil.LINUX}")
    print(f"  WINDOWS: {mypsutil.WINDOWS}")
    print(f"  POSIX: {mypsutil.POSIX}")
    print(f"  ARCH: {mypsutil.ARCH}")

    # Users
    users_list = mypsutil.users()
    print(f"\nLogged in users: {len(users_list)}")
    for user in users_list[:3]:
        print(f"  {user.name} on {user.terminal}")

    # Sensors (may not be available in all environments)
    print(f"\nSensors:")
    temps = mypsutil.sensors_temperatures()
    if temps:
        for name, entries in list(temps.items())[:2]:
            print(f"  {name}:")
            for entry in entries[:2]:
                print(f"    {entry.label}: {entry.current}C")
    else:
        print("  No temperature sensors found")

    battery = mypsutil.sensors_battery()
    if battery:
        print(f"\nBattery: {battery.percent}% (plugged: {battery.power_plugged})")
    else:
        print("\nNo battery found")

    return True


def test_pytest_markers():
    """Test pytest markers"""
    print("\n" + "=" * 50)
    print("PYTEST MARKERS")
    print("=" * 50)

    print(f"mypytest version: {mypytest.__version__}")

    # Test mark decorator
    @mypytest.mark.skip(reason="demonstration")
    def skipped_test():
        pass

    @mypytest.mark.xfail(reason="expected failure")
    def expected_fail_test():
        assert False

    @mypytest.mark.parametrize("x,y", [(1, 2), (3, 4)])
    def param_test(x, y):
        assert x < y

    # Check markers were applied
    print(f"\nMarkers applied:")
    print(f"  skipped_test markers: {mypytest.get_markers(skipped_test)}")
    print(f"  expected_fail_test markers: {mypytest.get_markers(expected_fail_test)}")
    print(f"  param_test markers: {mypytest.get_markers(param_test)}")

    # Test has_marker
    print(f"\nhas_marker checks:")
    print(f"  skipped_test has 'skip': {mypytest.has_marker(skipped_test, 'skip')}")
    print(f"  expected_fail_test has 'xfail': {mypytest.has_marker(expected_fail_test, 'xfail')}")
    print(f"  param_test has 'parametrize': {mypytest.has_marker(param_test, 'parametrize')}")

    return True


def test_pytest_assertions():
    """Test pytest assertions"""
    print("\n" + "=" * 50)
    print("PYTEST ASSERTIONS")
    print("=" * 50)

    # Test raises context manager
    print("\nTesting raises():")
    with mypytest.raises(ValueError):
        raise ValueError("test error")
    print("  raises(ValueError) - OK")

    with mypytest.raises(ZeroDivisionError):
        1 / 0
    print("  raises(ZeroDivisionError) - OK")

    # Test approx
    print("\nTesting approx():")
    assert 0.1 + 0.2 == mypytest.approx(0.3)
    print("  0.1 + 0.2 == approx(0.3) - OK")

    assert 3.14159 == mypytest.approx(3.14159, rel=1e-5)
    print("  3.14159 == approx(3.14159) - OK")

    # Test assert functions
    print("\nTesting assert functions:")
    mypytest.assert_equal(1, 1)
    print("  assert_equal(1, 1) - OK")

    mypytest.assert_not_equal(1, 2)
    print("  assert_not_equal(1, 2) - OK")

    mypytest.assert_true(True)
    print("  assert_true(True) - OK")

    mypytest.assert_false(False)
    print("  assert_false(False) - OK")

    mypytest.assert_in(1, [1, 2, 3])
    print("  assert_in(1, [1, 2, 3]) - OK")

    mypytest.assert_is_none(None)
    print("  assert_is_none(None) - OK")

    mypytest.assert_is_instance("hello", str)
    print("  assert_is_instance('hello', str) - OK")

    mypytest.assert_greater(5, 3)
    print("  assert_greater(5, 3) - OK")

    return True


def test_pytest_fixtures():
    """Test pytest fixtures"""
    print("\n" + "=" * 50)
    print("PYTEST FIXTURES")
    print("=" * 50)

    # Create a simple fixture
    @mypytest.fixture
    def sample_data():
        return [1, 2, 3, 4, 5]

    @mypytest.fixture
    def sample_dict():
        return {'a': 1, 'b': 2}

    # Test fixture registration
    fm = mypytest.get_fixture_manager()

    print(f"\nRegistered fixtures:")
    # Built-in fixtures
    print(f"  tmp_path: {fm.get_fixture('tmp_path') is not None}")
    print(f"  capsys: {fm.get_fixture('capsys') is not None}")
    print(f"  monkeypatch: {fm.get_fixture('monkeypatch') is not None}")

    # Test fixture with yield (teardown)
    @mypytest.fixture
    def resource():
        print("  Setup resource")
        yield "resource_value"
        print("  Teardown resource")

    print(f"\nFixture with yield registered: {fm.get_fixture('resource') is not None}")

    # Test fixture scope
    @mypytest.fixture(scope='module')
    def module_fixture():
        return "module scoped"

    fixture_def = fm.get_fixture('module_fixture')
    print(f"\nModule fixture scope: {fixture_def.scope if fixture_def else 'N/A'}")

    return True


def test_pytest_test_discovery():
    """Test pytest test discovery"""
    print("\n" + "=" * 50)
    print("PYTEST TEST DISCOVERY")
    print("=" * 50)

    from mypytest.discovery import TestCollector, TestItem

    # Test TestItem
    def sample_test():
        pass

    class SampleModule:
        __file__ = 'test_sample.py'
        __name__ = 'test_sample'

    item = TestItem('test_sample', sample_test, SampleModule)
    print(f"\nTestItem created:")
    print(f"  Name: {item.name}")
    print(f"  Node ID: {item.nodeid}")

    # Test collector patterns
    collector = TestCollector()
    print(f"\nCollector patterns: {collector.file_patterns}")

    # Test is_test_file
    test_files = ['test_foo.py', 'foo_test.py', 'foo.py', 'test.py']
    print(f"\nFile pattern matching:")
    for f in test_files:
        matches = collector._is_test_file(f)
        print(f"  {f}: {matches}")

    return True


def test_pytest_runner():
    """Test pytest runner"""
    print("\n" + "=" * 50)
    print("PYTEST RUNNER")
    print("=" * 50)

    from mypytest.runner import TestSession, TestOutcome

    # Create a test session
    session = TestSession()
    print(f"\nTestSession created:")
    print(f"  Paths: {session.paths}")
    print(f"  Verbose: {session.verbose}")
    print(f"  Failfast: {session.failfast}")

    # Test outcome enum
    print(f"\nTestOutcome values:")
    for outcome in TestOutcome:
        print(f"  {outcome.name}: {outcome.value}")

    # Create a mini test and run it
    from mypytest.discovery import TestItem
    from mypytest.runner import TestRunner, TestResult

    def passing_test():
        assert 1 + 1 == 2

    def failing_test():
        assert 1 + 1 == 3

    class MockModule:
        __file__ = 'test_mock.py'
        __name__ = 'test_mock'

    # Test passing
    item = TestItem('test_passing', passing_test, MockModule)
    session.collected = [item]

    runner = TestRunner(session)
    result = runner.run_test(item)

    print(f"\nRan passing test:")
    print(f"  Outcome: {result.outcome.value}")
    print(f"  Duration: {result.duration:.4f}s")

    # Test failing
    item2 = TestItem('test_failing', failing_test, MockModule)
    result2 = runner.run_test(item2)

    print(f"\nRan failing test:")
    print(f"  Outcome: {result2.outcome.value}")
    print(f"  Message: {result2.message[:50]}..." if result2.message else "  No message")

    return True


def test_pytest_reporting():
    """Test pytest reporting"""
    print("\n" + "=" * 50)
    print("PYTEST REPORTING")
    print("=" * 50)

    from mypytest.reporting import TestReporter, Colors
    from mypytest.runner import TestSession, TestOutcome, TestResult
    from mypytest.discovery import TestItem
    from io import StringIO

    # Create mock results
    class MockModule:
        __file__ = 'test_report.py'
        __name__ = 'test_report'

    def mock_test():
        pass

    item = TestItem('test_mock', mock_test, MockModule)

    # Create results with different outcomes
    results = [
        TestResult(item, TestOutcome.PASSED, duration=0.01),
        TestResult(item, TestOutcome.FAILED, duration=0.02, message="assertion failed"),
        TestResult(item, TestOutcome.SKIPPED, duration=0, message="skipped"),
    ]

    # Test reporter (without color for consistent output)
    output = StringIO()
    reporter = TestReporter(output=output, color=False, verbose=True)

    print(f"\nReporter output (verbose, no color):")
    for result in results:
        reporter.report_test_result(result)

    output_str = output.getvalue()
    print(output_str)

    # Verify output contains expected text
    assert 'PASSED' in output_str
    assert 'FAILED' in output_str
    assert 'SKIPPED' in output_str
    print("Reporter output verified!")

    return True


def test_matplotlib_figure():
    """Test matplotlib figure and axes"""
    print("\n" + "=" * 50)
    print("MATPLOTLIB FIGURE")
    print("=" * 50)

    print(f"mymatplotlib version: {mymatplotlib.__version__}")

    # Create figure
    fig = mymatplotlib.Figure(figsize=(8, 6), dpi=100)
    print(f"\nFigure created:")
    print(f"  Size: {fig.figsize}")
    print(f"  DPI: {fig.dpi}")
    print(f"  Facecolor: {fig.facecolor}")

    # Add subplot
    ax = fig.add_subplot(1, 1, 1)
    print(f"\nAxes added:")
    print(f"  Rect: {ax.rect}")

    # Test subplots function
    fig2, axes = mymatplotlib.subplots(2, 2, figsize=(10, 8))
    print(f"\nSubplots (2x2) created:")
    print(f"  Figure axes count: {len(fig2.axes)}")
    print(f"  Axes type: {type(axes)}")

    return True


def test_matplotlib_plotting():
    """Test matplotlib plotting functions"""
    print("\n" + "=" * 50)
    print("MATPLOTLIB PLOTTING")
    print("=" * 50)

    # Test plot()
    fig, ax = mymatplotlib.subplots()

    x = [0, 1, 2, 3, 4]
    y = [0, 1, 4, 9, 16]

    lines = ax.plot(x, y, 'b-', label='y = x^2')
    print(f"\nplot() test:")
    print(f"  Lines created: {len(lines)}")
    print(f"  Line data points: {len(lines[0].xdata)}")
    print(f"  Line color: {lines[0].color}")

    # Test scatter()
    scatter = ax.scatter([1, 2, 3], [1, 4, 9], c='red', marker='o')
    print(f"\nscatter() test:")
    print(f"  Scatter object: {scatter}")

    # Test bar()
    fig2, ax2 = mymatplotlib.subplots()
    bars = ax2.bar([1, 2, 3, 4], [10, 20, 15, 25], width=0.6)
    print(f"\nbar() test:")
    print(f"  Bars created: {len(bars)}")

    # Test hist()
    import random
    random.seed(42)
    data = [random.gauss(0, 1) for _ in range(100)]
    fig3, ax3 = mymatplotlib.subplots()
    counts, edges, patches = ax3.hist(data, bins=10)
    print(f"\nhist() test:")
    print(f"  Bins: {len(counts)}")
    print(f"  Total count: {sum(counts)}")

    return True


def test_matplotlib_styling():
    """Test matplotlib styling options"""
    print("\n" + "=" * 50)
    print("MATPLOTLIB STYLING")
    print("=" * 50)

    fig, ax = mymatplotlib.subplots()

    # Plot with various styles
    x = list(range(10))
    ax.plot(x, [i**2 for i in x], 'r--', label='dashed')
    ax.plot(x, [i**1.5 for i in x], 'g:', label='dotted')
    ax.plot(x, [i for i in x], 'b-', label='solid')

    # Set labels and title
    ax.set_xlabel('X Axis')
    ax.set_ylabel('Y Axis')
    ax.set_title('Test Plot')

    print(f"\nStyling applied:")
    print(f"  X label: {ax._xlabel}")
    print(f"  Y label: {ax._ylabel}")
    print(f"  Title: {ax._title}")
    print(f"  Lines: {len(ax.lines)}")

    # Test grid
    ax.grid(True)
    print(f"  Grid on: {ax._grid_on}")

    # Test legend
    legend = ax.legend()
    print(f"  Legend labels: {legend.labels}")

    # Test limits
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 100)
    print(f"  X limits: {ax.get_xlim()}")
    print(f"  Y limits: {ax.get_ylim()}")

    return True


def test_matplotlib_colors():
    """Test matplotlib colors module"""
    print("\n" + "=" * 50)
    print("MATPLOTLIB COLORS")
    print("=" * 50)

    from mymatplotlib.colors import (
        to_hex, to_rgba, parse_fmt, get_cmap,
        NAMED_COLORS, DEFAULT_COLORS
    )

    # Test to_hex
    print(f"\nto_hex() conversions:")
    print(f"  'red' -> {to_hex('red')}")
    print(f"  'b' -> {to_hex('b')}")
    print(f"  (1, 0, 0) -> {to_hex((1, 0, 0))}")
    print(f"  '#ff0000' -> {to_hex('#ff0000')}")

    # Test to_rgba
    rgba = to_rgba('blue', alpha=0.5)
    print(f"\nto_rgba('blue', alpha=0.5): {rgba}")

    # Test parse_fmt
    print(f"\nparse_fmt() results:")
    print(f"  'ro-' -> {parse_fmt('ro-')}")
    print(f"  'b--' -> {parse_fmt('b--')}")
    print(f"  'g:' -> {parse_fmt('g:')}")

    # Test colormap
    cmap = get_cmap('viridis')
    print(f"\nColormap 'viridis':")
    print(f"  cmap(0.0) = {cmap(0.0)}")
    print(f"  cmap(0.5) = {cmap(0.5)}")
    print(f"  cmap(1.0) = {cmap(1.0)}")

    # Test color constants
    print(f"\nColor constants:")
    print(f"  Named colors: {len(NAMED_COLORS)} defined")
    print(f"  Default cycle: {len(DEFAULT_COLORS)} colors")

    return True


def test_matplotlib_pyplot():
    """Test matplotlib pyplot interface"""
    print("\n" + "=" * 50)
    print("MATPLOTLIB PYPLOT")
    print("=" * 50)

    # Test state-based interface
    plt.figure(figsize=(8, 6))

    x = plt.linspace(0, 2 * plt.pi, 50)
    y = plt.sin(x)

    plt.plot(x, y, 'b-', label='sin(x)')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Sine Wave')
    plt.grid(True)
    plt.legend()

    print(f"\nPyplot state-based interface:")
    print(f"  Current figure: {plt.gcf()}")
    print(f"  Current axes: {plt.gca()}")
    print(f"  X limits: {plt.xlim()}")
    print(f"  Y limits: {plt.ylim()}")

    # Test math functions
    print(f"\nPyplot math functions:")
    print(f"  linspace(0, 10, 5): {plt.linspace(0, 10, 5)}")
    print(f"  arange(0, 5, 1): {plt.arange(0, 5, 1)}")
    print(f"  sin(0): {plt.sin(0)}")
    print(f"  cos(0): {plt.cos(0)}")
    print(f"  pi: {plt.pi}")

    plt.close()

    return True


def test_matplotlib_savefig():
    """Test matplotlib save functionality"""
    print("\n" + "=" * 50)
    print("MATPLOTLIB SAVEFIG")
    print("=" * 50)

    # Create a simple plot
    fig, ax = mymatplotlib.subplots(figsize=(6, 4))
    ax.plot([0, 1, 2, 3], [0, 1, 4, 9], 'b-o', label='Data')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Test Save')
    ax.legend()
    ax.grid(True)

    # Save to SVG
    svg_path = tempfile.mktemp(suffix='.svg')
    fig.savefig(svg_path)

    # Check file was created
    file_exists = os.path.exists(svg_path)
    file_size = os.path.getsize(svg_path) if file_exists else 0

    print(f"\nSVG save test:")
    print(f"  File created: {file_exists}")
    print(f"  File size: {file_size} bytes")

    # Read and check content
    if file_exists:
        with open(svg_path, 'r') as f:
            content = f.read()
        print(f"  Contains SVG tag: {'<svg' in content}")
        print(f"  Contains polyline: {'<polyline' in content}")
        os.unlink(svg_path)

    # Test text rendering
    from mymatplotlib.backend import render_text
    text_output = render_text(fig)
    print(f"\nText render output:")
    print(f"  Contains 'Figure': {'Figure' in text_output}")
    print(f"  Contains 'Axes': {'Axes' in text_output}")

    return True


def run_all_tests():
    """Run all tests"""
    tests = [
        ("NumPy Basics", test_numpy_basics),
        ("NumPy LinAlg", test_numpy_linalg),
        ("NumPy Embeddings", test_numpy_embeddings),
        ("Pandas Basics", test_pandas_basics),
        ("Pandas Merge", test_pandas_merge),
        ("Pandas SQL", test_pandas_sql),
        ("Pandas CSV", test_pandas_csv),
        ("Requests Basics", test_requests_basics),
        ("Requests Session", test_requests_session),
        ("Requests HTTP Codes", test_requests_http_codes),
        ("TQDM Basic", test_tqdm_basic),
        ("TQDM Manual", test_tqdm_manual),
        ("TQDM Features", test_tqdm_features),
        ("Colorama Basics", test_colorama_basics),
        ("Colorama Combinations", test_colorama_combinations),
        ("Colorama Codes", test_colorama_codes),
        ("Colorama Cursor", test_colorama_cursor),
        ("Colorama Init", test_colorama_init),
        ("Psutil CPU", test_psutil_cpu),
        ("Psutil Memory", test_psutil_memory),
        ("Psutil Disk", test_psutil_disk),
        ("Psutil Network", test_psutil_network),
        ("Psutil Process", test_psutil_process),
        ("Psutil System", test_psutil_system),
        ("Pytest Markers", test_pytest_markers),
        ("Pytest Assertions", test_pytest_assertions),
        ("Pytest Fixtures", test_pytest_fixtures),
        ("Pytest Discovery", test_pytest_test_discovery),
        ("Pytest Runner", test_pytest_runner),
        ("Pytest Reporting", test_pytest_reporting),
        ("Matplotlib Figure", test_matplotlib_figure),
        ("Matplotlib Plotting", test_matplotlib_plotting),
        ("Matplotlib Styling", test_matplotlib_styling),
        ("Matplotlib Colors", test_matplotlib_colors),
        ("Matplotlib Pyplot", test_matplotlib_pyplot),
        ("Matplotlib Savefig", test_matplotlib_savefig),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "PASS" if success else "FAIL"))
        except Exception as e:
            print(f"\nERROR in {name}: {e}")
            results.append((name, f"ERROR: {e}"))

    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    for name, status in results:
        symbol = "✓" if status == "PASS" else "✗"
        print(f"  {symbol} {name}: {status}")

    all_passed = all(s == "PASS" for _, s in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))
    return all_passed


if __name__ == "__main__":
    run_all_tests()
