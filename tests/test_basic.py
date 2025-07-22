import pytest


def test_import_main_package():
    try:
        import py_py_kick
    except ImportError:
        pytest.fail("Could not import py_py_kick package")


def test_package_has_version():
    import py_py_kick
    assert hasattr(py_py_kick, "__version__"), "__version__ attribute missing"
    assert hasattr(py_py_kick, "__author__"), "__author__ attribute missing"
    assert hasattr(py_py_kick, "__license__"), "__license__ attribute missing"
