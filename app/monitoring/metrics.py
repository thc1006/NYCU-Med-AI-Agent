"""
Metrics collection system for Taiwan Medical AI Assistant.
Provides Prometheus-style metrics, performance tracking, and operational visibility.
"""

import time
import threading
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable
import psutil
import statistics


class MetricType(Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class Counter:
    """Counter metric that only increases."""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.metric_type = MetricType.COUNTER
        self.labels = labels or []
        self._value = 0
        self._labeled_values: Dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment counter by amount."""
        if amount < 0:
            raise ValueError("Counter cannot decrease")

        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                self._labeled_values[label_key] += amount
            else:
                self._value += amount

    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                return self._labeled_values.get(label_key, 0)
            else:
                return self._value

    def get_all_samples(self) -> List[Dict[str, Any]]:
        """Get all counter samples."""
        with self._lock:
            samples = []

            # Add unlabeled sample if it has a value
            if self._value > 0:
                samples.append({
                    "name": self.name,
                    "labels": {},
                    "value": self._value
                })

            # Add labeled samples
            for label_key, value in self._labeled_values.items():
                if value > 0:
                    labels_dict = dict(label_key)
                    samples.append({
                        "name": self.name,
                        "labels": labels_dict,
                        "value": value
                    })

            return samples

    def to_prometheus_format(self) -> str:
        """Convert to Prometheus format."""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} counter"
        ]

        samples = self.get_all_samples()
        for sample in samples:
            if sample["labels"]:
                label_str = ",".join(f'{k}="{v}"' for k, v in sample["labels"].items())
                lines.append(f'{self.name}{{{label_str}}} {sample["value"]}')
            else:
                lines.append(f'{self.name} {sample["value"]}')

        return "\n".join(lines)


class Gauge:
    """Gauge metric that can increase and decrease."""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.metric_type = MetricType.GAUGE
        self.labels = labels or []
        self._value = 0
        self._labeled_values: Dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge value."""
        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                self._labeled_values[label_key] = value
            else:
                self._value = value

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment gauge by amount."""
        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                self._labeled_values[label_key] += amount
            else:
                self._value += amount

    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge by amount."""
        self.inc(-amount, labels)

    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                return self._labeled_values.get(label_key, 0)
            else:
                return self._value

    def set_to_current_time(self, labels: Optional[Dict[str, str]] = None):
        """Set gauge to current timestamp."""
        self.set(datetime.now().timestamp(), labels)

    def track_inprogress(self, labels: Optional[Dict[str, str]] = None):
        """Decorator to track in-progress operations."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                self.inc(1, labels)
                try:
                    return func(*args, **kwargs)
                finally:
                    self.dec(1, labels)
            return wrapper
        return decorator

    def get_all_samples(self) -> List[Dict[str, Any]]:
        """Get all gauge samples."""
        with self._lock:
            samples = []

            # Add unlabeled sample
            samples.append({
                "name": self.name,
                "labels": {},
                "value": self._value
            })

            # Add labeled samples
            for label_key, value in self._labeled_values.items():
                labels_dict = dict(label_key)
                samples.append({
                    "name": self.name,
                    "labels": labels_dict,
                    "value": value
                })

            return samples

    def to_prometheus_format(self) -> str:
        """Convert to Prometheus format."""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} gauge"
        ]

        samples = self.get_all_samples()
        for sample in samples:
            if sample["labels"]:
                label_str = ",".join(f'{k}="{v}"' for k, v in sample["labels"].items())
                lines.append(f'{self.name}{{{label_str}}} {sample["value"]}')
            else:
                lines.append(f'{self.name} {sample["value"]}')

        return "\n".join(lines)


class Histogram:
    """Histogram metric for observing distributions."""

    def __init__(self, name: str, description: str,
                 buckets: Optional[List[float]] = None,
                 labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.metric_type = MetricType.HISTOGRAM
        self.labels = labels or []

        # Default buckets if none provided
        if buckets is None:
            buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

        # Always include +Inf bucket
        self.buckets = sorted(buckets) + [float('inf')]

        self._buckets: Dict[float, int] = {bucket: 0 for bucket in self.buckets}
        self._labeled_buckets: Dict[tuple, Dict[float, int]] = defaultdict(
            lambda: {bucket: 0 for bucket in self.buckets}
        )

        self._count = 0
        self._sum = 0.0
        self._labeled_count: Dict[tuple, int] = defaultdict(int)
        self._labeled_sum: Dict[tuple, float] = defaultdict(float)

        self._observations: List[float] = []
        self._labeled_observations: Dict[tuple, List[float]] = defaultdict(list)

        self._lock = threading.Lock()

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value."""
        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                self._labeled_count[label_key] += 1
                self._labeled_sum[label_key] += value
                self._labeled_observations[label_key].append(value)

                # Update buckets
                for bucket in self.buckets:
                    if value <= bucket:
                        self._labeled_buckets[label_key][bucket] += 1
            else:
                self._count += 1
                self._sum += value
                self._observations.append(value)

                # Update buckets
                for bucket in self.buckets:
                    if value <= bucket:
                        self._buckets[bucket] += 1

    def get_statistics(self, labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get histogram statistics."""
        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                count = self._labeled_count.get(label_key, 0)
                sum_val = self._labeled_sum.get(label_key, 0.0)
            else:
                count = self._count
                sum_val = self._sum

            avg = sum_val / count if count > 0 else 0

            return {
                "count": count,
                "sum": sum_val,
                "avg": avg
            }

    def get_quantiles(self, quantiles: List[float], labels: Optional[Dict[str, str]] = None) -> Dict[float, float]:
        """Calculate quantiles from observations."""
        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                observations = self._labeled_observations.get(label_key, [])
            else:
                observations = self._observations

            if not observations:
                return {q: 0.0 for q in quantiles}

            sorted_obs = sorted(observations)
            result = {}

            for q in quantiles:
                index = int(q * (len(sorted_obs) - 1))
                result[q] = sorted_obs[index]

            return result

    def time(self, labels: Optional[Dict[str, str]] = None):
        """Decorator/context manager to time operations."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.time() - start_time
                    self.observe(duration, labels)
            return wrapper

        # Can also be used as context manager
        @contextmanager
        def timer():
            start_time = time.time()
            try:
                yield
            finally:
                duration = time.time() - start_time
                self.observe(duration, labels)

        # Return context manager if called without arguments
        if labels is not None or not hasattr(decorator, '__call__'):
            return timer()
        else:
            return decorator

    def to_prometheus_format(self) -> str:
        """Convert to Prometheus format."""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} histogram"
        ]

        with self._lock:
            # Add bucket metrics
            for bucket in self.buckets:
                bucket_str = "+Inf" if bucket == float('inf') else str(bucket)
                lines.append(f'{self.name}_bucket{{le="{bucket_str}"}} {self._buckets[bucket]}')

                # Add labeled bucket metrics
                for label_key, buckets in self._labeled_buckets.items():
                    labels_dict = dict(label_key)
                    labels_dict["le"] = bucket_str
                    label_str = ",".join(f'{k}="{v}"' for k, v in labels_dict.items())
                    lines.append(f'{self.name}_bucket{{{label_str}}} {buckets[bucket]}')

            # Add count and sum
            lines.append(f'{self.name}_count {self._count}')
            lines.append(f'{self.name}_sum {self._sum}')

            # Add labeled count and sum
            for label_key in self._labeled_count.keys():
                labels_dict = dict(label_key)
                label_str = ",".join(f'{k}="{v}"' for k, v in labels_dict.items())
                lines.append(f'{self.name}_count{{{label_str}}} {self._labeled_count[label_key]}')
                lines.append(f'{self.name}_sum{{{label_str}}} {self._labeled_sum[label_key]}')

        return "\n".join(lines)


class Summary:
    """Summary metric with quantiles."""

    def __init__(self, name: str, description: str,
                 quantiles: Optional[List[float]] = None,
                 labels: Optional[List[str]] = None,
                 max_age_seconds: int = 600):
        self.name = name
        self.description = description
        self.metric_type = MetricType.SUMMARY
        self.labels = labels or []
        self.quantiles = quantiles or [0.5, 0.9, 0.95, 0.99]
        self.max_age_seconds = max_age_seconds

        self._observations: deque = deque()
        self._labeled_observations: Dict[tuple, deque] = defaultdict(deque)
        self._count = 0
        self._sum = 0.0
        self._labeled_count: Dict[tuple, int] = defaultdict(int)
        self._labeled_sum: Dict[tuple, float] = defaultdict(float)

        self._lock = threading.Lock()

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value."""
        timestamp = time.time()

        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                self._labeled_observations[label_key].append((value, timestamp))
                self._labeled_count[label_key] += 1
                self._labeled_sum[label_key] += value
            else:
                self._observations.append((value, timestamp))
                self._count += 1
                self._sum += value

            # Clean old observations
            self._clean_old_observations()

    def _clean_old_observations(self):
        """Remove observations older than max_age_seconds."""
        cutoff_time = time.time() - self.max_age_seconds

        # Clean unlabeled observations
        while self._observations and self._observations[0][1] < cutoff_time:
            self._observations.popleft()

        # Clean labeled observations
        for label_key in list(self._labeled_observations.keys()):
            observations = self._labeled_observations[label_key]
            while observations and observations[0][1] < cutoff_time:
                observations.popleft()

            # Remove empty deques
            if not observations:
                del self._labeled_observations[label_key]

    def get_quantiles(self, labels: Optional[Dict[str, str]] = None) -> Dict[float, float]:
        """Get quantile values."""
        with self._lock:
            self._clean_old_observations()

            if labels:
                label_key = tuple(sorted(labels.items()))
                observations = [val for val, _ in self._labeled_observations.get(label_key, [])]
            else:
                observations = [val for val, _ in self._observations]

            if not observations:
                return {q: 0.0 for q in self.quantiles}

            observations.sort()
            result = {}

            for q in self.quantiles:
                if q == 0.5:
                    result[q] = statistics.median(observations)
                else:
                    index = int(q * (len(observations) - 1))
                    result[q] = observations[index]

            return result

    def get_count(self, labels: Optional[Dict[str, str]] = None) -> int:
        """Get observation count."""
        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                return self._labeled_count.get(label_key, 0)
            else:
                return self._count

    def get_sum(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get sum of observations."""
        with self._lock:
            if labels:
                label_key = tuple(sorted(labels.items()))
                return self._labeled_sum.get(label_key, 0.0)
            else:
                return self._sum

    def time(self, labels: Optional[Dict[str, str]] = None):
        """Decorator to time operations."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.time() - start_time
                    self.observe(duration, labels)
            return wrapper
        return decorator

    def to_prometheus_format(self) -> str:
        """Convert to Prometheus format."""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} summary"
        ]

        with self._lock:
            # Add quantile metrics
            quantiles = self.get_quantiles()
            for q in self.quantiles:
                lines.append(f'{self.name}{{quantile="{q}"}} {quantiles.get(q, 0)}')

            # Add labeled quantile metrics
            for label_key in self._labeled_observations.keys():
                labels_dict = dict(label_key)
                labeled_quantiles = self.get_quantiles(labels_dict)
                for q in self.quantiles:
                    labels_dict["quantile"] = str(q)
                    label_str = ",".join(f'{k}="{v}"' for k, v in labels_dict.items())
                    lines.append(f'{self.name}{{{label_str}}} {labeled_quantiles.get(q, 0)}')

            # Add count and sum
            lines.append(f'{self.name}_count {self._count}')
            lines.append(f'{self.name}_sum {self._sum}')

            # Add labeled count and sum
            for label_key in self._labeled_count.keys():
                labels_dict = dict(label_key)
                label_str = ",".join(f'{k}="{v}"' for k, v in labels_dict.items())
                lines.append(f'{self.name}_count{{{label_str}}} {self._labeled_count[label_key]}')
                lines.append(f'{self.name}_sum{{{label_str}}} {self._labeled_sum[label_key]}')

        return "\n".join(lines)


class MetricRegistry:
    """Registry for metrics."""

    def __init__(self):
        self._metrics: Dict[str, Union[Counter, Gauge, Histogram, Summary]] = {}
        self._lock = threading.Lock()

    def register(self, metric: Union[Counter, Gauge, Histogram, Summary]):
        """Register a metric."""
        with self._lock:
            if metric.name in self._metrics:
                raise ValueError(f"Metric '{metric.name}' already registered")
            self._metrics[metric.name] = metric

    def unregister(self, name: str):
        """Unregister a metric."""
        with self._lock:
            if name in self._metrics:
                del self._metrics[name]

    def get_metric(self, name: str) -> Optional[Union[Counter, Gauge, Histogram, Summary]]:
        """Get a metric by name."""
        return self._metrics.get(name)

    def get_all_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram, Summary]]:
        """Get all registered metrics."""
        with self._lock:
            return self._metrics.copy()

    def clear(self):
        """Clear all metrics."""
        with self._lock:
            self._metrics.clear()


class PrometheusExporter:
    """Prometheus format exporter."""

    def __init__(self, registry: MetricRegistry):
        self.registry = registry

    def generate_prometheus_output(self, include_timestamp: bool = False,
                                 extra_headers: Optional[Dict[str, str]] = None,
                                 metric_filter: Optional[Callable[[str], bool]] = None) -> str:
        """Generate Prometheus format output."""
        lines = []

        # Add extra headers
        if extra_headers:
            for header, value in extra_headers.items():
                lines.append(f"{header}: {value}")

        metrics = self.registry.get_all_metrics()

        for name, metric in metrics.items():
            if metric_filter and not metric_filter(name):
                continue

            prometheus_text = metric.to_prometheus_format()
            lines.append(prometheus_text)

        return "\n".join(lines)


class PerformanceTracker:
    """Performance tracking utility."""

    def __init__(self):
        self.registry = MetricRegistry()

        # Initialize performance metrics
        self.request_duration_histogram = Histogram(
            "request_duration_seconds",
            "HTTP request duration",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            labels=["endpoint", "method"]
        )
        self.registry.register(self.request_duration_histogram)

        self.external_api_duration_histogram = Histogram(
            "external_api_duration_seconds",
            "External API call duration",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            labels=["service", "operation"]
        )
        self.registry.register(self.external_api_duration_histogram)

        self.database_operation_duration_histogram = Histogram(
            "database_operation_duration_seconds",
            "Database operation duration",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            labels=["operation", "table"]
        )
        self.registry.register(self.database_operation_duration_histogram)

    @contextmanager
    def track_request(self, endpoint: str, method: str):
        """Track HTTP request performance."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.request_duration_histogram.observe(
                duration,
                labels={"endpoint": endpoint, "method": method}
            )

    @contextmanager
    def track_external_call(self, service: str, operation: str):
        """Track external API call performance."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.external_api_duration_histogram.observe(
                duration,
                labels={"service": service, "operation": operation}
            )

    @contextmanager
    def track_database_operation(self, operation: str, table: str):
        """Track database operation performance."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.database_operation_duration_histogram.observe(
                duration,
                labels={"operation": operation, "table": table}
            )

    def get_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram, Summary]]:
        """Get all performance metrics."""
        return self.registry.get_all_metrics()


class BusinessMetrics:
    """Business-specific metrics tracking."""

    def __init__(self):
        self.registry = MetricRegistry()

        # Triage metrics
        self.triage_requests_counter = Counter(
            "triage_requests_total",
            "Total triage requests",
            labels=["level"]
        )
        self.registry.register(self.triage_requests_counter)

        self.triage_duration_histogram = Histogram(
            "triage_duration_seconds",
            "Triage processing duration",
            labels=["level"]
        )
        self.registry.register(self.triage_duration_histogram)

        # Hospital search metrics
        self.hospital_searches_counter = Counter(
            "hospital_searches_total",
            "Total hospital searches",
            labels=["type"]
        )
        self.registry.register(self.hospital_searches_counter)

        self.hospital_search_results_histogram = Histogram(
            "hospital_search_results_count",
            "Number of hospital search results",
            buckets=[0, 1, 2, 5, 10, 20, 50],
            labels=["type"]
        )
        self.registry.register(self.hospital_search_results_histogram)

        # Emergency escalation metrics
        self.emergency_escalations_counter = Counter(
            "emergency_escalations_total",
            "Total emergency escalations",
            labels=["type"]
        )
        self.registry.register(self.emergency_escalations_counter)

        # User satisfaction metrics
        self.user_satisfaction_histogram = Histogram(
            "user_satisfaction_score",
            "User satisfaction scores",
            buckets=[1, 2, 3, 4, 5]
        )
        self.registry.register(self.user_satisfaction_histogram)

        # Task 21: Emergency search counter
        self.emergency_searches_total = Counter(
            "emergency_searches_total",
            "Total emergency searches triggered by red-flag symptoms",
            labels=["symptom_type"]
        )
        self.registry.register(self.emergency_searches_total)

        # Task 22: Red-flag detection timing histogram
        self.red_flag_detection_duration_seconds = Histogram(
            "red_flag_detection_duration_seconds",
            "Time taken to detect red-flag symptoms in seconds",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
        )
        self.registry.register(self.red_flag_detection_duration_seconds)

    def track_triage_request(self, level: str, symptom_category: str, duration_seconds: float):
        """Track triage request metrics."""
        self.triage_requests_counter.inc(labels={"level": level})
        self.triage_duration_histogram.observe(duration_seconds, labels={"level": level})

    def track_hospital_search(self, search_type: str, radius_meters: int,
                            results_count: int, duration_seconds: float):
        """Track hospital search metrics."""
        self.hospital_searches_counter.inc(labels={"type": search_type})
        self.hospital_search_results_histogram.observe(results_count, labels={"type": search_type})

    def track_emergency_escalation(self, symptom_category: str, escalation_type: str):
        """Track emergency escalation metrics."""
        self.emergency_escalations_counter.inc(labels={"type": escalation_type})

    def track_user_satisfaction(self, score: int):
        """Track user satisfaction metrics."""
        self.user_satisfaction_histogram.observe(score)

    def track_emergency_search(self, symptoms: List[str]):
        """Track emergency search triggered by symptoms."""
        symptom_type = ",".join(sorted(symptoms[:3]))  # Track first 3 symptoms
        self.emergency_searches_total.inc(labels={"symptom_type": symptom_type})

    def track_red_flag_detection(self, duration_seconds: float):
        """Track time taken to detect red-flag symptoms."""
        self.red_flag_detection_duration_seconds.observe(duration_seconds)

    def get_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram, Summary]]:
        """Get all business metrics."""
        return self.registry.get_all_metrics()


class SystemMetrics:
    """System resource metrics tracking."""

    def __init__(self):
        self.registry = MetricRegistry()

        # CPU metrics
        self.cpu_usage_gauge = Gauge(
            "cpu_usage_percent",
            "CPU usage percentage"
        )
        self.registry.register(self.cpu_usage_gauge)

        # Memory metrics
        self.memory_usage_gauge = Gauge(
            "memory_usage_percent",
            "Memory usage percentage"
        )
        self.registry.register(self.memory_usage_gauge)

        self.memory_available_gauge = Gauge(
            "memory_available_bytes",
            "Available memory in bytes"
        )
        self.registry.register(self.memory_available_gauge)

        self.memory_used_gauge = Gauge(
            "memory_used_bytes",
            "Used memory in bytes"
        )
        self.registry.register(self.memory_used_gauge)

        # Disk metrics
        self.disk_usage_gauge = Gauge(
            "disk_usage_percent",
            "Disk usage percentage"
        )
        self.registry.register(self.disk_usage_gauge)

        self.disk_free_gauge = Gauge(
            "disk_free_bytes",
            "Free disk space in bytes"
        )
        self.registry.register(self.disk_free_gauge)

        # Network metrics
        self.network_bytes_sent_counter = Counter(
            "network_bytes_sent_total",
            "Total bytes sent over network"
        )
        self.registry.register(self.network_bytes_sent_counter)

        self.network_bytes_received_counter = Counter(
            "network_bytes_received_total",
            "Total bytes received over network"
        )
        self.registry.register(self.network_bytes_received_counter)

    def collect_cpu_metrics(self):
        """Collect CPU metrics."""
        cpu_percent = psutil.cpu_percent()
        self.cpu_usage_gauge.set(cpu_percent)

    def collect_memory_metrics(self):
        """Collect memory metrics."""
        memory = psutil.virtual_memory()
        self.memory_usage_gauge.set(memory.percent)
        self.memory_available_gauge.set(memory.available)
        self.memory_used_gauge.set(memory.used)

    def collect_disk_metrics(self, path: str = "/"):
        """Collect disk metrics."""
        disk = psutil.disk_usage(path)
        self.disk_usage_gauge.set(disk.percent)
        self.disk_free_gauge.set(disk.free)

    def collect_network_metrics(self):
        """Collect network metrics."""
        network = psutil.net_io_counters()
        # These are cumulative, so we set the counter to the current value
        # In a real implementation, you'd want to track deltas
        self.network_bytes_sent_counter._value = network.bytes_sent
        self.network_bytes_received_counter._value = network.bytes_recv

    def collect_all_metrics(self):
        """Collect all system metrics."""
        self.collect_cpu_metrics()
        self.collect_memory_metrics()
        self.collect_disk_metrics()
        self.collect_network_metrics()

    def get_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram, Summary]]:
        """Get all system metrics."""
        return self.registry.get_all_metrics()


class ApiMetrics:
    """API-specific metrics tracking."""

    def __init__(self):
        self.registry = MetricRegistry()

        # HTTP request metrics
        self.http_requests_counter = Counter(
            "http_requests_total",
            "Total HTTP requests",
            labels=["endpoint", "method", "status_code"]
        )
        self.registry.register(self.http_requests_counter)

        self.http_request_duration_histogram = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration",
            labels=["endpoint", "method"]
        )
        self.registry.register(self.http_request_duration_histogram)

        self.http_response_size_histogram = Histogram(
            "http_response_size_bytes",
            "HTTP response size in bytes",
            buckets=[100, 1000, 10000, 100000, 1000000],
            labels=["endpoint"]
        )
        self.registry.register(self.http_response_size_histogram)

    def track_request(self, endpoint: str, method: str, status_code: int, duration_seconds: float):
        """Track HTTP request metrics."""
        self.http_requests_counter.inc(labels={
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code)
        })
        self.http_request_duration_histogram.observe(
            duration_seconds,
            labels={"endpoint": endpoint, "method": method}
        )

    def track_response_size(self, endpoint: str, size_bytes: int):
        """Track HTTP response size metrics."""
        self.http_response_size_histogram.observe(size_bytes, labels={"endpoint": endpoint})

    def get_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram, Summary]]:
        """Get all API metrics."""
        return self.registry.get_all_metrics()


# Global metrics collectors
class MetricsCollector:
    """Main metrics collector for the application."""

    def __init__(self):
        self.registry = MetricRegistry()
        self.performance_tracker = PerformanceTracker()
        self.business_metrics = BusinessMetrics()
        self.system_metrics = SystemMetrics()
        self.api_metrics = ApiMetrics()
        self.prometheus_exporter = PrometheusExporter(self.registry)

        # Merge all metric registries
        self._merge_registries()

    def _merge_registries(self):
        """Merge all metric registries into the main registry."""
        for tracker in [self.performance_tracker, self.business_metrics,
                       self.system_metrics, self.api_metrics]:
            for name, metric in tracker.get_metrics().items():
                try:
                    self.registry.register(metric)
                except ValueError:
                    # Metric already registered, skip
                    pass

    def collect_system_metrics(self):
        """Collect system metrics."""
        self.system_metrics.collect_all_metrics()

    def get_prometheus_output(self, **kwargs) -> str:
        """Get Prometheus format output."""
        return self.prometheus_exporter.generate_prometheus_output(**kwargs)

    def get_metrics_json(self) -> Dict[str, Any]:
        """Get metrics in JSON format."""
        metrics = self.registry.get_all_metrics()
        result = {
            "metrics": {},
            "timestamp": datetime.now().isoformat(),
            "collection_duration_ms": 0  # Would be calculated in real implementation
        }

        for name, metric in metrics.items():
            if hasattr(metric, 'get_all_samples'):
                samples = metric.get_all_samples()
            else:
                samples = []

            result["metrics"][name] = {
                "type": metric.metric_type.value,
                "description": metric.description,
                "samples": samples
            }

        return result


# Global metrics collector instance
metrics_collector = MetricsCollector()