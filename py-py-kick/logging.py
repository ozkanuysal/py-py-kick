import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve or create a logger configured for the py_py_kick package.

    This function obtains a logger instance with the specified name. If the logger
    does not have any handlers attached, it adds a StreamHandler that outputs to
    sys.stdout with a defined log format and date format. The logger level is then
    set to INFO. This ensures a consistent logging setup across the py_py_kick package.

    Parameters:
        name (str): The name of the logger to retrieve or create.

    Returns:
        logging.Logger: A logger instance configured with a StreamHandler, formatter,
                        and log level set to INFO.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
