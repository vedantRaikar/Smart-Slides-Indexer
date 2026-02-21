"""Observability utilities: logging, metrics, and tracing."""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict

from core.config import get_config


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_logging():
    """Setup structured logging based on config."""
    config = get_config()

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.logging.level))

    # Remove existing handlers
    logger.handlers = []

    # Create handler
    if config.logging.output == "file" and config.logging.file_path:
        handler = logging.FileHandler(config.logging.file_path)
    else:
        handler = logging.StreamHandler(sys.stdout)

    # Set formatter
    if config.logging.format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

    logger.addHandler(handler)

    return logger


class MetricsCollector:
    """Simple metrics collector for Prometheus."""

    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}

    def increment(self, name: str, labels: Dict[str, str] = None):
        """Increment a counter."""
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + 1

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge value."""
        key = self._make_key(name, labels)
        self._gauges[key] = value

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def generate_metrics(self) -> str:
        """Generate Prometheus metrics text."""
        lines = []

        for name, value in self._counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        for name, value in self._gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        return "\n".join(lines)


# Global metrics collector
metrics = MetricsCollector()


def trace_function(func):
    """Decorator for tracing function calls."""
    def wrapper(*args, **kwargs):
        config = get_config()
        
        if not config.metrics.enable_tracing:
            return func(*args, **kwargs)
        
        # Simple tracing - in production use OpenTelemetry
        logger = logging.getLogger(func.__module__)
        logger.info(f"Entering {func.__name__}")
        
        start_time = datetime.utcnow()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Exiting {func.__name__} in {duration:.3f}s")
            return result
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error in {func.__name__} after {duration:.3f}s: {e}")
            raise
    
    return wrapper
