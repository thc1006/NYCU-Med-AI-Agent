"""
Unit tests for metrics collection system.
Tests Prometheus-style metrics, performance tracking, and operational visibility.
"""

import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, List, Any

import pytest
from freezegun import freeze_time

from app.monitoring.metrics import (
    MetricsCollector,
    MetricType,
    Counter,
    Gauge,
    Histogram,
    Summary,
    MetricRegistry,
    PrometheusExporter,
    PerformanceTracker,
    BusinessMetrics,
    SystemMetrics,
    ApiMetrics
)


class TestMetricType:
    """Test metric type enumeration."""

    def test_metric_type_values(self):
        """Test metric type enum values."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.SUMMARY.value == "summary"

    def test_metric_type_validation(self):
        """Test metric type validation."""
        valid_types = ["counter", "gauge", "histogram", "summary"]
        for metric_type in MetricType:
            assert metric_type.value in valid_types


class TestCounter:
    """Test counter metric functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.counter = Counter(
            name="test_counter",
            description="Test counter metric",
            labels=["method", "endpoint"]
        )

    def test_counter_initialization(self):
        """Test counter initialization."""
        assert self.counter.name == "test_counter"
        assert self.counter.description == "Test counter metric"
        assert self.counter.metric_type == MetricType.COUNTER
        assert self.counter._value == 0

    def test_counter_increment_without_labels(self):
        """Test counter increment without labels."""
        self.counter.inc()
        assert self.counter.get_value() == 1

        self.counter.inc(5)
        assert self.counter.get_value() == 6

    def test_counter_increment_with_labels(self):
        """Test counter increment with labels."""
        self.counter.inc(labels={"method": "GET", "endpoint": "/health"})
        self.counter.inc(labels={"method": "GET", "endpoint": "/health"})
        self.counter.inc(labels={"method": "POST", "endpoint": "/triage"})

        assert self.counter.get_value(labels={"method": "GET", "endpoint": "/health"}) == 2
        assert self.counter.get_value(labels={"method": "POST", "endpoint": "/triage"}) == 1

    def test_counter_cannot_decrease(self):
        """Test that counter cannot be decreased."""
        self.counter.inc(10)

        with pytest.raises(ValueError, match="cannot decrease"):
            self.counter.inc(-5)

    def test_counter_get_all_samples(self):
        """Test getting all counter samples."""
        self.counter.inc(labels={"method": "GET", "endpoint": "/health"})
        self.counter.inc(labels={"method": "POST", "endpoint": "/triage"})

        samples = self.counter.get_all_samples()

        assert len(samples) == 2
        assert samples[0]["labels"]["method"] in ["GET", "POST"]
        assert all(sample["value"] == 1 for sample in samples)

    def test_counter_prometheus_format(self):
        """Test counter Prometheus format output."""
        self.counter.inc(3, labels={"method": "GET", "endpoint": "/health"})

        prometheus_output = self.counter.to_prometheus_format()

        assert "# HELP test_counter Test counter metric" in prometheus_output
        assert "# TYPE test_counter counter" in prometheus_output
        assert 'test_counter{method="GET",endpoint="/health"} 3' in prometheus_output


class TestGauge:
    """Test gauge metric functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.gauge = Gauge(
            name="test_gauge",
            description="Test gauge metric",
            labels=["instance"]
        )

    def test_gauge_initialization(self):
        """Test gauge initialization."""
        assert self.gauge.name == "test_gauge"
        assert self.gauge.metric_type == MetricType.GAUGE
        assert self.gauge._value == 0

    def test_gauge_set_value(self):
        """Test setting gauge value."""
        self.gauge.set(42.5)
        assert self.gauge.get_value() == 42.5

        self.gauge.set(10, labels={"instance": "server1"})
        assert self.gauge.get_value(labels={"instance": "server1"}) == 10

    def test_gauge_increment_decrement(self):
        """Test gauge increment and decrement operations."""
        self.gauge.set(10)

        self.gauge.inc(5)
        assert self.gauge.get_value() == 15

        self.gauge.dec(3)
        assert self.gauge.get_value() == 12

    def test_gauge_track_in_progress(self):
        """Test gauge tracking in-progress operations."""
        @self.gauge.track_inprogress()
        def some_operation():
            assert self.gauge.get_value() == 1
            return "result"

        assert self.gauge.get_value() == 0
        result = some_operation()
        assert result == "result"
        assert self.gauge.get_value() == 0

    def test_gauge_set_to_current_time(self):
        """Test setting gauge to current timestamp."""
        with freeze_time("2024-01-15 10:30:00"):
            self.gauge.set_to_current_time()

            expected_timestamp = datetime(2024, 1, 15, 10, 30, 0).timestamp()
            assert self.gauge.get_value() == expected_timestamp


class TestHistogram:
    """Test histogram metric functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.histogram = Histogram(
            name="test_histogram",
            description="Test histogram metric",
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            labels=["operation"]
        )

    def test_histogram_initialization(self):
        """Test histogram initialization."""
        assert self.histogram.name == "test_histogram"
        assert self.histogram.metric_type == MetricType.HISTOGRAM
        assert self.histogram.buckets == [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')]

    def test_histogram_observe_values(self):
        """Test observing values in histogram."""
        values = [0.05, 0.3, 0.8, 1.5, 3.2, 7.1, 15.0]

        for value in values:
            self.histogram.observe(value)

        # Check bucket counts
        assert self.histogram._buckets[0.1] == 1  # 0.05
        assert self.histogram._buckets[0.5] == 2  # 0.05, 0.3
        assert self.histogram._buckets[1.0] == 3  # 0.05, 0.3, 0.8
        assert self.histogram._buckets[2.5] == 4  # + 1.5
        assert self.histogram._buckets[5.0] == 5  # + 3.2
        assert self.histogram._buckets[10.0] == 6  # + 7.1
        assert self.histogram._buckets[float('inf')] == 7  # + 15.0

    def test_histogram_statistics(self):
        """Test histogram statistics calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]

        for value in values:
            self.histogram.observe(value)

        stats = self.histogram.get_statistics()

        assert stats["count"] == 5
        assert stats["sum"] == 15.0
        assert stats["avg"] == 3.0

    def test_histogram_quantiles(self):
        """Test histogram quantile calculation."""
        # Add 100 observations with known distribution
        for i in range(100):
            self.histogram.observe(i / 10.0)  # 0.0 to 9.9

        quantiles = self.histogram.get_quantiles([0.5, 0.95, 0.99])

        assert quantiles[0.5] > 4.0  # Median around 5.0
        assert quantiles[0.95] > 9.0  # 95th percentile around 9.5
        assert quantiles[0.99] > 9.5  # 99th percentile around 9.9

    def test_histogram_timer_decorator(self):
        """Test histogram timer decorator."""
        @self.histogram.time()
        def timed_operation():
            time.sleep(0.01)  # Sleep for 10ms
            return "completed"

        result = timed_operation()

        assert result == "completed"
        stats = self.histogram.get_statistics()
        assert stats["count"] == 1
        assert stats["sum"] > 0.008  # At least 8ms (accounting for precision)

    def test_histogram_context_manager(self):
        """Test histogram context manager for timing."""
        with self.histogram.time():
            time.sleep(0.01)

        stats = self.histogram.get_statistics()
        assert stats["count"] == 1
        assert stats["sum"] > 0.008

    def test_histogram_prometheus_format(self):
        """Test histogram Prometheus format output."""
        self.histogram.observe(0.5, labels={"operation": "triage"})
        self.histogram.observe(1.5, labels={"operation": "triage"})

        prometheus_output = self.histogram.to_prometheus_format()

        assert "# TYPE test_histogram histogram" in prometheus_output
        assert 'test_histogram_bucket{operation="triage",le="0.5"}' in prometheus_output
        assert 'test_histogram_bucket{operation="triage",le="1.0"}' in prometheus_output
        assert 'test_histogram_count{operation="triage"} 2' in prometheus_output
        assert 'test_histogram_sum{operation="triage"} 2' in prometheus_output


class TestSummary:
    """Test summary metric functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.summary = Summary(
            name="test_summary",
            description="Test summary metric",
            quantiles=[0.5, 0.9, 0.95, 0.99],
            labels=["service"]
        )

    def test_summary_initialization(self):
        """Test summary initialization."""
        assert self.summary.name == "test_summary"
        assert self.summary.metric_type == MetricType.SUMMARY
        assert self.summary.quantiles == [0.5, 0.9, 0.95, 0.99]

    def test_summary_observe_values(self):
        """Test observing values in summary."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        for value in values:
            self.summary.observe(value)

        quantiles = self.summary.get_quantiles()

        assert quantiles[0.5] == 5.5  # Median
        assert quantiles[0.9] == 9.1  # 90th percentile
        assert quantiles[0.95] == 9.55  # 95th percentile

    def test_summary_count_and_sum(self):
        """Test summary count and sum tracking."""
        values = [2.5, 3.7, 1.2, 4.8, 2.1]

        for value in values:
            self.summary.observe(value)

        assert self.summary.get_count() == 5
        assert abs(self.summary.get_sum() - 14.3) < 0.001

    def test_summary_timer_functionality(self):
        """Test summary timer functionality."""
        @self.summary.time()
        def operation():
            time.sleep(0.01)
            return "done"

        result = operation()

        assert result == "done"
        assert self.summary.get_count() == 1
        assert self.summary.get_sum() > 0.008

    def test_summary_prometheus_format(self):
        """Test summary Prometheus format output."""
        for i in range(10):
            self.summary.observe(i, labels={"service": "medical"})

        prometheus_output = self.summary.to_prometheus_format()

        assert "# TYPE test_summary summary" in prometheus_output
        assert 'test_summary{service="medical",quantile="0.5"}' in prometheus_output
        assert 'test_summary_count{service="medical"} 10' in prometheus_output
        assert 'test_summary_sum{service="medical"}' in prometheus_output


class TestMetricRegistry:
    """Test metric registry functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.registry = MetricRegistry()

    def test_register_metrics(self):
        """Test registering metrics in registry."""
        counter = Counter("requests_total", "Total HTTP requests")
        gauge = Gauge("memory_usage", "Memory usage in bytes")

        self.registry.register(counter)
        self.registry.register(gauge)

        assert "requests_total" in self.registry._metrics
        assert "memory_usage" in self.registry._metrics

    def test_prevent_duplicate_registration(self):
        """Test prevention of duplicate metric registration."""
        counter1 = Counter("requests_total", "Description 1")
        counter2 = Counter("requests_total", "Description 2")

        self.registry.register(counter1)

        with pytest.raises(ValueError, match="already registered"):
            self.registry.register(counter2)

    def test_get_metric_by_name(self):
        """Test getting metric by name."""
        counter = Counter("requests_total", "Total HTTP requests")
        self.registry.register(counter)

        retrieved = self.registry.get_metric("requests_total")
        assert retrieved is counter

    def test_get_nonexistent_metric(self):
        """Test getting non-existent metric."""
        retrieved = self.registry.get_metric("nonexistent")
        assert retrieved is None

    def test_list_all_metrics(self):
        """Test listing all registered metrics."""
        counter = Counter("requests_total", "Total HTTP requests")
        gauge = Gauge("memory_usage", "Memory usage")

        self.registry.register(counter)
        self.registry.register(gauge)

        metrics = self.registry.get_all_metrics()

        assert len(metrics) == 2
        assert "requests_total" in metrics
        assert "memory_usage" in metrics

    def test_unregister_metric(self):
        """Test unregistering metrics."""
        counter = Counter("requests_total", "Total HTTP requests")
        self.registry.register(counter)

        assert "requests_total" in self.registry._metrics

        self.registry.unregister("requests_total")

        assert "requests_total" not in self.registry._metrics

    def test_clear_all_metrics(self):
        """Test clearing all metrics."""
        counter = Counter("requests_total", "Total HTTP requests")
        gauge = Gauge("memory_usage", "Memory usage")

        self.registry.register(counter)
        self.registry.register(gauge)

        assert len(self.registry._metrics) == 2

        self.registry.clear()

        assert len(self.registry._metrics) == 0


class TestPrometheusExporter:
    """Test Prometheus format exporter."""

    def setup_method(self):
        """Setup test fixtures."""
        self.registry = MetricRegistry()
        self.exporter = PrometheusExporter(self.registry)

    def test_export_single_metric(self):
        """Test exporting single metric to Prometheus format."""
        counter = Counter("http_requests_total", "Total HTTP requests", labels=["method"])
        counter.inc(10, labels={"method": "GET"})
        counter.inc(5, labels={"method": "POST"})

        self.registry.register(counter)

        output = self.exporter.generate_prometheus_output()

        assert "# HELP http_requests_total Total HTTP requests" in output
        assert "# TYPE http_requests_total counter" in output
        assert 'http_requests_total{method="GET"} 10' in output
        assert 'http_requests_total{method="POST"} 5' in output

    def test_export_multiple_metrics(self):
        """Test exporting multiple metrics to Prometheus format."""
        counter = Counter("requests_total", "Total requests")
        gauge = Gauge("memory_bytes", "Memory usage")

        counter.inc(100)
        gauge.set(1024 * 1024 * 512)  # 512MB

        self.registry.register(counter)
        self.registry.register(gauge)

        output = self.exporter.generate_prometheus_output()

        assert "requests_total 100" in output
        assert "memory_bytes 536870912" in output
        assert output.count("# HELP") == 2
        assert output.count("# TYPE") == 2

    def test_export_histogram_format(self):
        """Test exporting histogram in Prometheus format."""
        histogram = Histogram("request_duration", "Request duration", buckets=[0.1, 0.5, 1.0])

        histogram.observe(0.05)
        histogram.observe(0.3)
        histogram.observe(0.8)
        histogram.observe(1.5)

        self.registry.register(histogram)

        output = self.exporter.generate_prometheus_output()

        assert "# TYPE request_duration histogram" in output
        assert 'request_duration_bucket{le="0.1"} 1' in output
        assert 'request_duration_bucket{le="0.5"} 2' in output
        assert 'request_duration_bucket{le="1.0"} 3' in output
        assert 'request_duration_bucket{le="+Inf"} 4' in output
        assert "request_duration_count 4" in output
        assert "request_duration_sum" in output

    def test_export_with_custom_headers(self):
        """Test exporting with custom headers."""
        counter = Counter("test_metric", "Test metric")
        counter.inc(1)

        self.registry.register(counter)

        output = self.exporter.generate_prometheus_output(
            include_timestamp=True,
            extra_headers={"# Custom header": "value"}
        )

        assert "# Custom header: value" in output
        assert "test_metric 1" in output

    def test_export_filtering(self):
        """Test exporting with metric filtering."""
        counter1 = Counter("app_requests_total", "App requests")
        counter2 = Counter("system_cpu_usage", "CPU usage")
        counter1.inc(10)
        counter2.inc(50)

        self.registry.register(counter1)
        self.registry.register(counter2)

        # Export only app metrics
        output = self.exporter.generate_prometheus_output(
            metric_filter=lambda name: name.startswith("app_")
        )

        assert "app_requests_total 10" in output
        assert "system_cpu_usage" not in output


class TestPerformanceTracker:
    """Test performance tracking functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.tracker = PerformanceTracker()

    def test_track_request_duration(self):
        """Test tracking request duration."""
        with self.tracker.track_request("/v1/triage", "POST"):
            time.sleep(0.01)

        metrics = self.tracker.get_metrics()
        request_duration = metrics["request_duration_histogram"]

        stats = request_duration.get_statistics(labels={"endpoint": "/v1/triage", "method": "POST"})
        assert stats["count"] == 1
        assert stats["sum"] > 0.008  # At least 8ms

    def test_track_external_api_calls(self):
        """Test tracking external API call performance."""
        with self.tracker.track_external_call("google_places", "nearby_search"):
            time.sleep(0.005)

        metrics = self.tracker.get_metrics()
        api_duration = metrics["external_api_duration_histogram"]

        stats = api_duration.get_statistics(labels={"service": "google_places", "operation": "nearby_search"})
        assert stats["count"] == 1
        assert stats["sum"] > 0.003

    def test_track_database_operations(self):
        """Test tracking database operation performance."""
        with self.tracker.track_database_operation("SELECT", "hospitals"):
            time.sleep(0.002)

        metrics = self.tracker.get_metrics()
        db_duration = metrics["database_operation_duration_histogram"]

        stats = db_duration.get_statistics(labels={"operation": "SELECT", "table": "hospitals"})
        assert stats["count"] == 1

    def test_concurrent_tracking(self):
        """Test concurrent performance tracking."""
        import threading
        import time

        def worker(worker_id):
            with self.tracker.track_request(f"/worker/{worker_id}", "GET"):
                time.sleep(0.01)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        metrics = self.tracker.get_metrics()
        request_duration = metrics["request_duration_histogram"]

        # Should have tracked 5 different endpoints
        total_count = 0
        for i in range(5):
            stats = request_duration.get_statistics(labels={"endpoint": f"/worker/{i}", "method": "GET"})
            total_count += stats["count"]

        assert total_count == 5

    def test_performance_percentiles(self):
        """Test performance percentile calculation."""
        # Generate known distribution
        durations = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

        for duration in durations:
            with patch('time.time', side_effect=[0, duration]):
                with self.tracker.track_request("/test", "GET"):
                    pass

        metrics = self.tracker.get_metrics()
        request_duration = metrics["request_duration_histogram"]

        quantiles = request_duration.get_quantiles([0.5, 0.9, 0.95])
        assert quantiles[0.5] == 0.55  # Median
        assert quantiles[0.9] == 0.91  # 90th percentile


class TestBusinessMetrics:
    """Test business-specific metrics tracking."""

    def setup_method(self):
        """Setup test fixtures."""
        self.business_metrics = BusinessMetrics()

    def test_track_triage_requests(self):
        """Test tracking triage request metrics."""
        self.business_metrics.track_triage_request("emergency", "chest_pain", 0.25)
        self.business_metrics.track_triage_request("outpatient", "headache", 0.15)
        self.business_metrics.track_triage_request("emergency", "difficulty_breathing", 0.30)

        metrics = self.business_metrics.get_metrics()

        # Check counter metrics
        triage_counter = metrics["triage_requests_total"]
        assert triage_counter.get_value(labels={"level": "emergency"}) == 2
        assert triage_counter.get_value(labels={"level": "outpatient"}) == 1

        # Check duration histogram
        duration_histogram = metrics["triage_duration_histogram"]
        emergency_stats = duration_histogram.get_statistics(labels={"level": "emergency"})
        assert emergency_stats["count"] == 2

    def test_track_hospital_searches(self):
        """Test tracking hospital search metrics."""
        self.business_metrics.track_hospital_search("hospital", 3000, 5, 0.18)
        self.business_metrics.track_hospital_search("pharmacy", 1000, 3, 0.12)

        metrics = self.business_metrics.get_metrics()

        search_counter = metrics["hospital_searches_total"]
        assert search_counter.get_value(labels={"type": "hospital"}) == 1
        assert search_counter.get_value(labels={"type": "pharmacy"}) == 1

        results_histogram = metrics["hospital_search_results_histogram"]
        hospital_stats = results_histogram.get_statistics(labels={"type": "hospital"})
        assert hospital_stats["count"] == 1

    def test_track_emergency_escalations(self):
        """Test tracking emergency escalation metrics."""
        self.business_metrics.track_emergency_escalation("chest_pain", "119_recommended")
        self.business_metrics.track_emergency_escalation("severe_headache", "emergency_room")

        metrics = self.business_metrics.get_metrics()

        escalation_counter = metrics["emergency_escalations_total"]
        assert escalation_counter.get_value(labels={"type": "119_recommended"}) == 1
        assert escalation_counter.get_value(labels={"type": "emergency_room"}) == 1

    def test_track_user_satisfaction_metrics(self):
        """Test tracking user satisfaction metrics."""
        # Simulate user feedback
        satisfaction_scores = [4, 5, 3, 5, 4, 5, 2, 4, 5, 3]

        for score in satisfaction_scores:
            self.business_metrics.track_user_satisfaction(score)

        metrics = self.business_metrics.get_metrics()

        satisfaction_histogram = metrics["user_satisfaction_histogram"]
        stats = satisfaction_histogram.get_statistics()

        assert stats["count"] == 10
        assert 3.0 <= stats["avg"] <= 4.5  # Average should be in reasonable range


class TestSystemMetrics:
    """Test system resource metrics tracking."""

    def setup_method(self):
        """Setup test fixtures."""
        self.system_metrics = SystemMetrics()

    def test_collect_cpu_metrics(self):
        """Test CPU metrics collection."""
        with patch('psutil.cpu_percent', return_value=45.2):
            self.system_metrics.collect_cpu_metrics()

        metrics = self.system_metrics.get_metrics()
        cpu_gauge = metrics["cpu_usage_percent"]

        assert cpu_gauge.get_value() == 45.2

    def test_collect_memory_metrics(self):
        """Test memory metrics collection."""
        mock_memory = Mock()
        mock_memory.percent = 72.5
        mock_memory.available = 2 * 1024 * 1024 * 1024  # 2GB
        mock_memory.used = 6 * 1024 * 1024 * 1024  # 6GB

        with patch('psutil.virtual_memory', return_value=mock_memory):
            self.system_metrics.collect_memory_metrics()

        metrics = self.system_metrics.get_metrics()

        assert metrics["memory_usage_percent"].get_value() == 72.5
        assert metrics["memory_available_bytes"].get_value() == 2 * 1024 * 1024 * 1024
        assert metrics["memory_used_bytes"].get_value() == 6 * 1024 * 1024 * 1024

    def test_collect_disk_metrics(self):
        """Test disk metrics collection."""
        mock_disk = Mock()
        mock_disk.percent = 68.3
        mock_disk.free = 50 * 1024 * 1024 * 1024  # 50GB
        mock_disk.used = 100 * 1024 * 1024 * 1024  # 100GB

        with patch('psutil.disk_usage', return_value=mock_disk):
            self.system_metrics.collect_disk_metrics()

        metrics = self.system_metrics.get_metrics()

        assert metrics["disk_usage_percent"].get_value() == 68.3
        assert metrics["disk_free_bytes"].get_value() == 50 * 1024 * 1024 * 1024

    def test_collect_network_metrics(self):
        """Test network metrics collection."""
        mock_network = Mock()
        mock_network.bytes_sent = 1024 * 1024 * 100  # 100MB
        mock_network.bytes_recv = 1024 * 1024 * 200  # 200MB
        mock_network.packets_sent = 50000
        mock_network.packets_recv = 75000

        with patch('psutil.net_io_counters', return_value=mock_network):
            self.system_metrics.collect_network_metrics()

        metrics = self.system_metrics.get_metrics()

        assert metrics["network_bytes_sent_total"].get_value() == 1024 * 1024 * 100
        assert metrics["network_bytes_received_total"].get_value() == 1024 * 1024 * 200


class TestApiMetrics:
    """Test API-specific metrics tracking."""

    def setup_method(self):
        """Setup test fixtures."""
        self.api_metrics = ApiMetrics()

    def test_track_request_metrics(self):
        """Test tracking HTTP request metrics."""
        self.api_metrics.track_request("/v1/triage", "POST", 200, 0.25)
        self.api_metrics.track_request("/v1/hospitals/nearby", "GET", 200, 0.18)
        self.api_metrics.track_request("/v1/triage", "POST", 400, 0.05)

        metrics = self.api_metrics.get_metrics()

        # Check request counter
        request_counter = metrics["http_requests_total"]
        assert request_counter.get_value(labels={"endpoint": "/v1/triage", "method": "POST", "status_code": "200"}) == 1
        assert request_counter.get_value(labels={"endpoint": "/v1/triage", "method": "POST", "status_code": "400"}) == 1

        # Check duration histogram
        duration_histogram = metrics["http_request_duration_histogram"]
        triage_stats = duration_histogram.get_statistics(labels={"endpoint": "/v1/triage", "method": "POST"})
        assert triage_stats["count"] == 2

    def test_track_error_rates(self):
        """Test tracking API error rates."""
        # Generate mix of successful and failed requests
        for _ in range(80):
            self.api_metrics.track_request("/v1/triage", "POST", 200, 0.2)

        for _ in range(15):
            self.api_metrics.track_request("/v1/triage", "POST", 500, 0.1)

        for _ in range(5):
            self.api_metrics.track_request("/v1/triage", "POST", 400, 0.05)

        metrics = self.api_metrics.get_metrics()
        request_counter = metrics["http_requests_total"]

        total_requests = (
            request_counter.get_value(labels={"endpoint": "/v1/triage", "method": "POST", "status_code": "200"}) +
            request_counter.get_value(labels={"endpoint": "/v1/triage", "method": "POST", "status_code": "500"}) +
            request_counter.get_value(labels={"endpoint": "/v1/triage", "method": "POST", "status_code": "400"})
        )

        error_requests = (
            request_counter.get_value(labels={"endpoint": "/v1/triage", "method": "POST", "status_code": "500"}) +
            request_counter.get_value(labels={"endpoint": "/v1/triage", "method": "POST", "status_code": "400"})
        )

        error_rate = error_requests / total_requests
        assert 0.18 <= error_rate <= 0.22  # Should be around 20%

    def test_track_response_size_metrics(self):
        """Test tracking response size metrics."""
        self.api_metrics.track_response_size("/v1/hospitals/nearby", 1024)
        self.api_metrics.track_response_size("/v1/hospitals/nearby", 2048)
        self.api_metrics.track_response_size("/v1/triage", 512)

        metrics = self.api_metrics.get_metrics()
        size_histogram = metrics["http_response_size_histogram"]

        hospital_stats = size_histogram.get_statistics(labels={"endpoint": "/v1/hospitals/nearby"})
        assert hospital_stats["count"] == 2
        assert hospital_stats["sum"] == 3072

        triage_stats = size_histogram.get_statistics(labels={"endpoint": "/v1/triage"})
        assert triage_stats["count"] == 1
        assert triage_stats["sum"] == 512