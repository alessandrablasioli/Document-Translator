"""
Observability module for agent execution tracing and metrics.
Provides structured logging, tracing, and metrics collection.
"""
import logging
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps
from pathlib import Path

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TranslationTracer:
    """
    Tracer for agent execution and translation operations.
    Provides detailed tracing of agent behavior.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        self.traces: List[Dict[str, Any]] = []
        self.log_file = log_file or "translation_traces.json"
        self.trace_file = Path(self.log_file)
    
    def start_trace(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new trace.
        
        Args:
            operation: Name of the operation
            metadata: Optional metadata
            
        Returns:
            Trace ID
        """
        trace_id = f"trace_{int(time.time() * 1000)}"
        trace = {
            "trace_id": trace_id,
            "operation": operation,
            "start_time": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "events": [],
            "status": "running"
        }
        self.traces.append(trace)
        logger.info(f"[TRACE_START] {trace_id} - {operation}")
        return trace_id
    
    def add_event(self, trace_id: str, event_type: str, data: Dict[str, Any]):
        """
        Add an event to a trace.
        
        Args:
            trace_id: Trace ID
            event_type: Type of event (e.g., "chunk_translation", "retry", "error")
            data: Event data
        """
        trace = self._find_trace(trace_id)
        if trace:
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": event_type,
                "data": data
            }
            trace["events"].append(event)
            logger.info(f"[TRACE_EVENT] {trace_id} - {event_type}: {json.dumps(data)}")
    
    def end_trace(self, trace_id: str, status: str = "completed", result: Optional[Dict[str, Any]] = None):
        """
        End a trace.
        
        Args:
            trace_id: Trace ID
            status: Final status ("completed", "failed", "cancelled")
            result: Optional result data
        """
        trace = self._find_trace(trace_id)
        if trace:
            trace["end_time"] = datetime.utcnow().isoformat()
            trace["status"] = status
            if result:
                trace["result"] = result
            
            # Calculate duration
            start = datetime.fromisoformat(trace["start_time"])
            end = datetime.fromisoformat(trace["end_time"])
            trace["duration_seconds"] = (end - start).total_seconds()
            
            logger.info(f"[TRACE_END] {trace_id} - {status} - Duration: {trace['duration_seconds']:.2f}s")
            
            # Save trace to file
            self._save_trace(trace)
    
    def _find_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Find a trace by ID"""
        for trace in self.traces:
            if trace["trace_id"] == trace_id:
                return trace
        return None
    
    def _save_trace(self, trace: Dict[str, Any]):
        """Save trace to file"""
        try:
            # Load existing traces
            if self.trace_file.exists():
                with open(self.trace_file, 'r') as f:
                    all_traces = json.load(f)
            else:
                all_traces = []
            
            # Append new trace
            all_traces.append(trace)
            
            # Keep only last 100 traces
            all_traces = all_traces[-100:]
            
            # Save
            with open(self.trace_file, 'w') as f:
                json.dump(all_traces, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving trace: {e}")
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get a trace by ID"""
        return self._find_trace(trace_id)
    
    def get_recent_traces(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent traces"""
        return self.traces[-limit:]


class MetricsCollector:
    """
    Metrics collector for translation operations.
    Tracks performance, errors, and usage statistics.
    """
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "total_translations": 0,
            "total_chunks": 0,
            "total_retries": 0,
            "total_errors": 0,
            "total_tokens": 0,
            "total_duration": 0.0,
            "average_duration": 0.0,
            "error_rate": 0.0,
            "chunking_rate": 0.0,
            "by_language": {},
            "by_file_type": {},
            "recent_operations": []
        }
    
    def record_translation(
        self,
        language: str,
        file_type: str,
        duration: float,
        chunked: bool = False,
        chunks: int = 1,
        retries: int = 0,
        error: bool = False,
        tokens: Optional[int] = None
    ):
        """
        Record a translation operation.
        
        Args:
            language: Target language
            file_type: File type
            duration: Duration in seconds
            chunked: Whether chunking was used
            chunks: Number of chunks
            retries: Number of retries
            error: Whether an error occurred
            tokens: Optional token count
        """
        self.metrics["total_translations"] += 1
        self.metrics["total_chunks"] += chunks
        self.metrics["total_retries"] += retries
        self.metrics["total_duration"] += duration
        
        if error:
            self.metrics["total_errors"] += 1
        
        if tokens:
            self.metrics["total_tokens"] += tokens
        
        # Add to recent operations first (so chunking_rate can include current op)
        operation = {
            "timestamp": datetime.utcnow().isoformat(),
            "language": language,
            "file_type": file_type,
            "duration": duration,
            "chunked": chunked,
            "chunks": chunks,
            "retries": retries,
            "error": error
        }
        self.metrics["recent_operations"].append(operation)
        self.metrics["recent_operations"] = self.metrics["recent_operations"][-100:]
        
        # Update averages
        if self.metrics["total_translations"] > 0:
            self.metrics["average_duration"] = (
                self.metrics["total_duration"] / self.metrics["total_translations"]
            )
            self.metrics["error_rate"] = (
                self.metrics["total_errors"] / self.metrics["total_translations"]
            )
            if self.metrics["recent_operations"]:
                self.metrics["chunking_rate"] = (
                    sum(1 for op in self.metrics["recent_operations"] if op.get("chunked", False)) /
                    len(self.metrics["recent_operations"])
                )
        
        # Update by language
        if language not in self.metrics["by_language"]:
            self.metrics["by_language"][language] = {
                "count": 0,
                "total_duration": 0.0,
                "errors": 0
            }
        self.metrics["by_language"][language]["count"] += 1
        self.metrics["by_language"][language]["total_duration"] += duration
        if error:
            self.metrics["by_language"][language]["errors"] += 1
        
        # Update by file type
        if file_type not in self.metrics["by_file_type"]:
            self.metrics["by_file_type"][file_type] = {
                "count": 0,
                "total_duration": 0.0,
                "errors": 0
            }
        self.metrics["by_file_type"][file_type]["count"] += 1
        self.metrics["by_file_type"][file_type]["total_duration"] += duration
        if error:
            self.metrics["by_file_type"][file_type]["errors"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            "total_translations": 0,
            "total_chunks": 0,
            "total_retries": 0,
            "total_errors": 0,
            "total_tokens": 0,
            "total_duration": 0.0,
            "average_duration": 0.0,
            "error_rate": 0.0,
            "chunking_rate": 0.0,
            "by_language": {},
            "by_file_type": {},
            "recent_operations": []
        }


# Global instances
tracer = TranslationTracer()
metrics_collector = MetricsCollector()


def trace_operation(operation_name: str):
    """
    Decorator for tracing operations.
    
    Usage:
        @trace_operation("translate_document")
        def translate(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            trace_id = tracer.start_trace(
                operation_name,
                {"function": func.__name__, "args": str(args), "kwargs": str(kwargs)}
            )
            try:
                result = func(*args, **kwargs)
                tracer.end_trace(trace_id, "completed", {"result": "success"})
                return result
            except Exception as e:
                tracer.add_event(trace_id, "error", {"error": str(e)})
                tracer.end_trace(trace_id, "failed", {"error": str(e)})
                raise
        return wrapper
    return decorator

