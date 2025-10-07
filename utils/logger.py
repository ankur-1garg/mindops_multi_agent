# utils/logger.py
import logging
import os
import sys
import codecs

# Ensure stdout can handle UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def setup_logger(name: str, level=logging.INFO):
    """Sets up a centralized logger with UTF-8 encoding support."""
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger  # Avoid adding multiple handlers

    logger.setLevel(level)

    # Create logs directory
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File Handler with UTF-8 encoding
    fh = logging.FileHandler(f'{log_dir}/workflow.log', encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console Handler with UTF-8 encoding
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
