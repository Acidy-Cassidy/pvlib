"""
mypytest fixtures

Provides setup/teardown functionality with dependency injection.
"""

import inspect
import functools
from typing import Callable, Dict, Any, Optional, Generator, List
from contextlib import contextmanager


class FixtureScope:
    """Fixture scope constants"""
    FUNCTION = 'function'
    CLASS = 'class'
    MODULE = 'module'
    SESSION = 'session'


class FixtureDefinition:
    """Represents a fixture definition"""

    def __init__(self, func: Callable, scope: str = FixtureScope.FUNCTION,
                 autouse: bool = False, params: Optional[List] = None,
                 ids: Optional[List[str]] = None, name: Optional[str] = None):
        self.func = func
        self.scope = scope
        self.autouse = autouse
        self.params = params
        self.ids = ids
        self.name = name or func.__name__

        # Check if fixture is a generator (for teardown)
        self.is_generator = inspect.isgeneratorfunction(func)

        # Get fixture dependencies (other fixtures this one needs)
        sig = inspect.signature(func)
        self.dependencies = [p.name for p in sig.parameters.values()
                           if p.name not in ('request',)]

    def __repr__(self):
        return f"<FixtureDefinition {self.name} scope={self.scope}>"


class FixtureRequest:
    """Provides information about the requesting test"""

    def __init__(self, test_item, fixture_manager: 'FixtureManager'):
        self.node = test_item
        self.function = test_item.function if test_item else None
        self.cls = test_item.cls if test_item else None
        self.module = test_item.module if test_item else None
        self.param = None
        self.param_index = None
        self._fixture_manager = fixture_manager
        self._finalizers: List[Callable] = []

    def addfinalizer(self, finalizer: Callable):
        """Add a finalizer to be called after test"""
        self._finalizers.append(finalizer)

    def getfixturevalue(self, name: str) -> Any:
        """Get the value of a fixture by name"""
        return self._fixture_manager.get_fixture_value(name, self)

    @property
    def fixturenames(self) -> List[str]:
        """Return list of fixture names available to this test"""
        return list(self._fixture_manager._fixtures.keys())


class FixtureManager:
    """Manages fixture registration and resolution"""

    def __init__(self):
        self._fixtures: Dict[str, FixtureDefinition] = {}
        self._cache: Dict[str, Dict[str, Any]] = {
            FixtureScope.FUNCTION: {},
            FixtureScope.CLASS: {},
            FixtureScope.MODULE: {},
            FixtureScope.SESSION: {},
        }
        self._active_generators: List[Generator] = []
        self._finalizers: List[Callable] = []

    def register_fixture(self, fixture_def: FixtureDefinition):
        """Register a fixture"""
        self._fixtures[fixture_def.name] = fixture_def

    def get_fixture(self, name: str) -> Optional[FixtureDefinition]:
        """Get a fixture definition by name"""
        return self._fixtures.get(name)

    def get_fixture_value(self, name: str, request: FixtureRequest) -> Any:
        """Get the value of a fixture, computing if necessary"""
        fixture_def = self._fixtures.get(name)
        if fixture_def is None:
            raise ValueError(f"Fixture '{name}' not found")

        # Check cache
        cache = self._cache[fixture_def.scope]
        if name in cache:
            return cache[name]

        # Resolve dependencies first
        kwargs = {}
        for dep_name in fixture_def.dependencies:
            if dep_name == 'request':
                kwargs['request'] = request
            else:
                kwargs[dep_name] = self.get_fixture_value(dep_name, request)

        # Add request if it's a parameter
        sig = inspect.signature(fixture_def.func)
        if 'request' in sig.parameters:
            kwargs['request'] = request

        # Execute fixture
        if fixture_def.is_generator:
            gen = fixture_def.func(**kwargs)
            value = next(gen)
            self._active_generators.append(gen)
        else:
            value = fixture_def.func(**kwargs)

        # Cache the value
        cache[name] = value

        return value

    def get_required_fixtures(self, test_item) -> List[str]:
        """Get list of fixtures required by a test"""
        required = []

        # Get fixtures from function signature
        sig = inspect.signature(test_item.function)
        for param_name in sig.parameters:
            if param_name in self._fixtures:
                required.append(param_name)

        # Add autouse fixtures
        for name, fixture_def in self._fixtures.items():
            if fixture_def.autouse and name not in required:
                required.append(name)

        return required

    def setup_fixtures(self, test_item) -> Dict[str, Any]:
        """Setup fixtures for a test, return dict of fixture values"""
        request = FixtureRequest(test_item, self)
        required = self.get_required_fixtures(test_item)

        values = {}
        for name in required:
            values[name] = self.get_fixture_value(name, request)

        return values

    def teardown_fixtures(self, scope: str = FixtureScope.FUNCTION):
        """Teardown fixtures of given scope"""
        # Run generator teardowns
        for gen in reversed(self._active_generators):
            try:
                next(gen)
            except StopIteration:
                pass
            except Exception as e:
                print(f"Error in fixture teardown: {e}")

        self._active_generators.clear()

        # Clear cache for scope
        self._cache[scope].clear()

        # Run finalizers
        for finalizer in reversed(self._finalizers):
            try:
                finalizer()
            except Exception as e:
                print(f"Error in finalizer: {e}")

        self._finalizers.clear()

    def clear_all(self):
        """Clear all caches and state"""
        for scope in self._cache:
            self._cache[scope].clear()
        self._active_generators.clear()
        self._finalizers.clear()


# Global fixture manager
_fixture_manager = FixtureManager()


def fixture(func=None, *, scope: str = FixtureScope.FUNCTION,
            autouse: bool = False, params: Optional[List] = None,
            ids: Optional[List[str]] = None, name: Optional[str] = None):
    """
    Decorator to mark a function as a fixture.

    Usage:
        @fixture
        def my_fixture():
            return some_value

        @fixture(scope='module')
        def module_fixture():
            # setup
            yield value
            # teardown

        @fixture(params=[1, 2, 3])
        def param_fixture(request):
            return request.param
    """
    def decorator(fn):
        fixture_def = FixtureDefinition(
            fn, scope=scope, autouse=autouse,
            params=params, ids=ids, name=name
        )
        _fixture_manager.register_fixture(fixture_def)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper._is_fixture = True
        wrapper._fixture_def = fixture_def
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def get_fixture_manager() -> FixtureManager:
    """Get the global fixture manager"""
    return _fixture_manager


# Built-in fixtures
@fixture
def tmp_path():
    """Provide a temporary directory unique to the test invocation"""
    import tempfile
    import shutil

    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path, ignore_errors=True)


@fixture
def tmp_path_factory():
    """Factory for creating temporary directories"""
    import tempfile
    import shutil

    created = []

    class TmpPathFactory:
        def mktemp(self, basename: str = 'test') -> str:
            path = tempfile.mkdtemp(prefix=basename)
            created.append(path)
            return path

    yield TmpPathFactory()

    for path in created:
        shutil.rmtree(path, ignore_errors=True)


@fixture
def capsys():
    """Capture stdout and stderr"""
    import sys
    from io import StringIO

    class CaptureResult:
        def __init__(self, out: str, err: str):
            self.out = out
            self.err = err

    class Capsys:
        def __init__(self):
            self._capture_out = StringIO()
            self._capture_err = StringIO()
            self._old_stdout = sys.stdout
            self._old_stderr = sys.stderr
            sys.stdout = self._capture_out
            sys.stderr = self._capture_err

        def readouterr(self) -> CaptureResult:
            out = self._capture_out.getvalue()
            err = self._capture_err.getvalue()
            self._capture_out.truncate(0)
            self._capture_out.seek(0)
            self._capture_err.truncate(0)
            self._capture_err.seek(0)
            return CaptureResult(out, err)

        def _restore(self):
            sys.stdout = self._old_stdout
            sys.stderr = self._old_stderr

    capsys = Capsys()
    yield capsys
    capsys._restore()


@fixture
def monkeypatch():
    """Monkeypatching for tests"""

    class MonkeyPatch:
        def __init__(self):
            self._patches = []

        def setattr(self, target, name, value):
            """Set an attribute on an object"""
            if isinstance(target, str):
                # target is a dotted path
                parts = target.rsplit('.', 1)
                if len(parts) == 2:
                    import importlib
                    module = importlib.import_module(parts[0])
                    target = module
                    name = parts[1]

            old_value = getattr(target, name, None)
            self._patches.append((target, name, old_value, hasattr(target, name)))
            setattr(target, name, value)

        def delattr(self, target, name):
            """Delete an attribute"""
            if hasattr(target, name):
                old_value = getattr(target, name)
                self._patches.append((target, name, old_value, True))
                delattr(target, name)

        def setenv(self, name, value):
            """Set an environment variable"""
            import os
            old_value = os.environ.get(name)
            self._patches.append(('env', name, old_value, name in os.environ))
            os.environ[name] = value

        def delenv(self, name, raising=True):
            """Delete an environment variable"""
            import os
            if name in os.environ:
                old_value = os.environ[name]
                self._patches.append(('env', name, old_value, True))
                del os.environ[name]
            elif raising:
                raise KeyError(name)

        def undo(self):
            """Undo all patches"""
            import os
            for patch in reversed(self._patches):
                target, name, old_value, existed = patch
                if target == 'env':
                    if existed:
                        os.environ[name] = old_value
                    elif name in os.environ:
                        del os.environ[name]
                else:
                    if existed:
                        setattr(target, name, old_value)
                    elif hasattr(target, name):
                        delattr(target, name)
            self._patches.clear()

    mp = MonkeyPatch()
    yield mp
    mp.undo()
