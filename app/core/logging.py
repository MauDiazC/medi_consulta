import logging
import json
import os
import sys
from datetime import datetime, timezone
from opentelemetry import trace

class JsonFormatter(logging.Formatter):
    """
    Institutional JSON Formatter for Mediconsulta.
    Enriches logs with Trace/Span IDs for total observability.
    """
    def format(self, record):
        # 1. Get Telemetry Context
        current_span = trace.get_current_span()
        context = current_span.get_span_context()
        
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "trace_id": format(context.trace_id, '032x') if context.is_valid else None,
            "span_id": format(context.span_id, '016x') if context.is_valid else None,
        }
        
        # 2. Capture approved contextual fields from 'extra'
        for field in ["event_type", "correlation_id", "organization_id", "note_id", "status"]:
            if hasattr(record, field):
                log_record[field] = getattr(record, field)
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def configure_logging():
    """
    Configures the global logging system to use enriched JSON stdout output.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Reset existing handlers to ensure single JSON output stream
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    root_logger.addHandler(handler)
    
    # Silence verbose infrastructure loggers
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
