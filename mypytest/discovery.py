"""
mypytest test discovery

Finds test files, classes, and functions following pytest conventions.
"""

import os
import sys
import importlib.util
import inspect
from typing import List, Callable, Optional, Tuple, Any


class TestItem:
    """Represents a single test to be executed"""

    def __init__(self, name: str, function: Callable, module: Any,
                 cls: Optional[type] = None, params: Optional[Tuple] = None,
                 param_id: Optional[str] = None):
        self.name = name
        self.function = function
        self.module = module
        self.cls = cls
        self.params = params
        self.param_id = param_id
        self.markers = getattr(function, '_pytest_markers', [])

        # Build full node ID
        self.nodeid = self._build_nodeid()

    def _build_nodeid(self) -> str:
        """Build the full test node ID"""
        parts = []

        # Module path
        if hasattr(self.module, '__file__') and self.module.__file__:
            parts.append(os.path.basename(self.module.__file__))
        else:
            parts.append(self.module.__name__)

        # Class name
        if self.cls:
            parts.append(self.cls.__name__)

        # Function name with parameters
        name = self.name
        if self.param_id:
            name = f"{name}[{self.param_id}]"
        parts.append(name)

        return '::'.join(parts)

    def __repr__(self):
        return f"<TestItem {self.nodeid}>"


class TestCollector:
    """Collects tests from files and directories"""

    def __init__(self, patterns: Optional[List[str]] = None):
        self.file_patterns = patterns or ['test_*.py', '*_test.py']
        self.collected: List[TestItem] = []

    def collect_from_path(self, path: str) -> List[TestItem]:
        """Collect tests from a file or directory"""
        self.collected = []

        if os.path.isfile(path):
            self._collect_from_file(path)
        elif os.path.isdir(path):
            self._collect_from_directory(path)
        else:
            raise FileNotFoundError(f"Path not found: {path}")

        return self.collected

    def _collect_from_directory(self, directory: str):
        """Recursively collect tests from a directory"""
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories and common non-test directories
            dirs[:] = [d for d in dirs if not d.startswith('.')
                      and d not in ('__pycache__', 'venv', '.venv', 'node_modules')]

            for filename in files:
                if self._is_test_file(filename):
                    filepath = os.path.join(root, filename)
                    self._collect_from_file(filepath)

    def _is_test_file(self, filename: str) -> bool:
        """Check if a file matches test file patterns"""
        if not filename.endswith('.py'):
            return False

        import fnmatch
        for pattern in self.file_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def _collect_from_file(self, filepath: str):
        """Collect tests from a single file"""
        # Load the module
        module = self._load_module(filepath)
        if module is None:
            return

        # Collect test functions
        for name, obj in inspect.getmembers(module):
            if self._is_test_function(name, obj):
                self._collect_test_function(name, obj, module)
            elif self._is_test_class(name, obj):
                self._collect_test_class(obj, module)

    def _load_module(self, filepath: str):
        """Load a Python module from file path"""
        try:
            # Create a unique module name
            module_name = os.path.splitext(os.path.basename(filepath))[0]

            # Ensure the directory is in sys.path
            directory = os.path.dirname(os.path.abspath(filepath))
            if directory not in sys.path:
                sys.path.insert(0, directory)

            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            return module
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None

    def _is_test_function(self, name: str, obj: Any) -> bool:
        """Check if an object is a test function"""
        if not inspect.isfunction(obj):
            return False
        return name.startswith('test_') or name.startswith('test')

    def _is_test_class(self, name: str, obj: Any) -> bool:
        """Check if an object is a test class"""
        if not inspect.isclass(obj):
            return False
        return name.startswith('Test')

    def _collect_test_function(self, name: str, func: Callable, module: Any,
                               cls: Optional[type] = None):
        """Collect a test function, handling parametrize"""
        # Check for parametrize marker
        params_list = None
        for marker in getattr(func, '_pytest_markers', []):
            if marker.name == 'parametrize':
                params_list = self._expand_parametrize(marker)
                break

        if params_list:
            for params, param_id in params_list:
                item = TestItem(name, func, module, cls=cls,
                              params=params, param_id=param_id)
                self.collected.append(item)
        else:
            item = TestItem(name, func, module, cls=cls)
            self.collected.append(item)

    def _collect_test_class(self, cls: type, module: Any):
        """Collect test methods from a test class"""
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name.startswith('test_') or name.startswith('test'):
                self._collect_test_function(name, method, module, cls=cls)

    def _expand_parametrize(self, marker) -> List[Tuple[Tuple, str]]:
        """Expand parametrize marker into list of (params, id) tuples"""
        argnames = marker.args[0]
        argvalues = marker.args[1]
        ids = marker.kwargs.get('ids')

        if isinstance(argnames, str):
            argnames = [a.strip() for a in argnames.split(',')]

        result = []
        for i, values in enumerate(argvalues):
            if not isinstance(values, (tuple, list)):
                values = (values,)

            # Generate parameter ID
            if ids and i < len(ids):
                param_id = str(ids[i])
            else:
                param_id = '-'.join(str(v) for v in values)

            result.append((tuple(values), param_id))

        return result


def collect_tests(path: str = '.') -> List[TestItem]:
    """Convenience function to collect tests from a path"""
    collector = TestCollector()
    return collector.collect_from_path(path)
