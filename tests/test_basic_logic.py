import logging

import pytest
from py_py_kick import KickClient


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


def test_kick_client_initialization_logs_info(caplog):
    with caplog.at_level(logging.INFO):
        client = KickClient(channel_id="12345")
        assert "client has info" in client
        assert "KickClient initialized for channel ID: 12345" in caplog.text
        assert "INFO" in caplog.text


def test_create_clip_logs_error_on_missing_channel_id(caplog):
    with caplog.at_level(logging.ERROR):
        client = KickClient()
        with pytest.raises(ValueError, match="Channel ID is required to create a clip."):
            client.create_clip(title="Test Clip")
        assert "Channel ID is required to create a clip. Aborting clip creation." in caplog.text
        assert "ERROR" in caplog.text
