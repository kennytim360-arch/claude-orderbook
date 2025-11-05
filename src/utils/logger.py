"""Logging infrastructure for RORO Trading System."""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(
    name: str = "RORO",
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_file_path: str = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up and configure logger for the trading system.

    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file in addition to console
        log_file_path: Path to log file (if None, uses default)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler (INFO and above, simple format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler (all levels, detailed format)
    if log_to_file:
        if log_file_path is None:
            # Get project root
            project_root = Path(__file__).parent.parent.parent
            log_dir = project_root / "data" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file_path = log_dir / "system.log"

        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger


def log_trade(logger: logging.Logger, trade_info: dict):
    """
    Log trade execution with standardized format.

    Args:
        logger: Logger instance
        trade_info: Dictionary with trade details
    """
    msg = (
        f"TRADE | {trade_info.get('action', 'N/A')} | "
        f"{trade_info.get('symbol', 'N/A')} | "
        f"Qty: {trade_info.get('quantity', 0)} | "
        f"Price: ${trade_info.get('price', 0):.2f} | "
        f"Stop: ${trade_info.get('stop_loss', 0):.2f} | "
        f"Target: ${trade_info.get('take_profit', 0):.2f}"
    )
    logger.info(msg)


def log_signal(logger: logging.Logger, signal_info: dict):
    """
    Log signal generation with standardized format.

    Args:
        logger: Logger instance
        signal_info: Dictionary with signal details
    """
    msg = (
        f"SIGNAL | {signal_info.get('type', 'N/A')} | "
        f"Consensus: {signal_info.get('consensus', 'N/A')}/3 | "
        f"Pillars: {signal_info.get('pillars', 'N/A')}"
    )
    logger.info(msg)


def log_performance(logger: logging.Logger, perf_info: dict):
    """
    Log performance metrics with standardized format.

    Args:
        logger: Logger instance
        perf_info: Dictionary with performance metrics
    """
    msg = (
        f"PERFORMANCE | "
        f"Total Return: {perf_info.get('total_return', 0):.2f}% | "
        f"Win Rate: {perf_info.get('win_rate', 0):.1f}% | "
        f"Sharpe: {perf_info.get('sharpe_ratio', 0):.2f} | "
        f"Max DD: {perf_info.get('max_drawdown', 0):.2f}%"
    )
    logger.info(msg)


# Global logger instance
logger = setup_logger()


if __name__ == "__main__":
    # Test logger
    print("Testing Logger...")

    logger.debug("This is a DEBUG message (file only)")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")

    # Test specialized logging functions
    log_signal(logger, {
        'type': 'RISK-ON',
        'consensus': 2,
        'pillars': 'TLT/SPY, GLD/SPY'
    })

    log_trade(logger, {
        'action': 'BUY LONG',
        'symbol': 'SPY',
        'quantity': 10,
        'price': 450.25,
        'stop_loss': 448.00,
        'take_profit': 454.75
    })

    log_performance(logger, {
        'total_return': 15.5,
        'win_rate': 55.2,
        'sharpe_ratio': 1.85,
        'max_drawdown': 8.3
    })

    print("\nLogger configured successfully!")
    print(f"Log file location: {Path(__file__).parent.parent.parent / 'data' / 'logs' / 'system.log'}")
