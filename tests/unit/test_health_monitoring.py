"""
Unit tests for health monitoring system.
Tests health checks for external services, dependencies, and system resources.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

import pytest
import httpx
from freezegun import freeze_time

from app.monitoring.health import (
    HealthChecker,
    HealthStatus,
    HealthCheckResult,
    ServiceHealthCheck,
    DatabaseHealthCheck,
    GooglePlacesHealthCheck,
    GeocodingHealthCheck,
    SystemResourceHealthCheck,
    CircuitBreakerHealthCheck,
    HealthMonitor
)


class TestHealthStatus:
    """Test health status enumeration and utilities."""

    def test_health_status_values(self):
        """Test health status enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"

    def test_health_status_ordering(self):
        """Test health status severity ordering."""
        statuses = [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
            HealthStatus.UNKNOWN
        ]

        # Test that statuses can be compared by severity
        assert HealthStatus.HEALTHY < HealthStatus.DEGRADED
        assert HealthStatus.DEGRADED < HealthStatus.UNHEALTHY
        assert HealthStatus.UNHEALTHY < HealthStatus.UNKNOWN

    def test_aggregate_health_status(self):
        """Test aggregation of multiple health statuses."""
        # All healthy should return healthy
        assert HealthStatus.aggregate([
            HealthStatus.HEALTHY,
            HealthStatus.HEALTHY
        ]) == HealthStatus.HEALTHY

        # Any degraded should return degraded
        assert HealthStatus.aggregate([
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED
        ]) == HealthStatus.DEGRADED

        # Any unhealthy should return unhealthy
        assert HealthStatus.aggregate([
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY
        ]) == HealthStatus.UNHEALTHY

        # Unknown should be worst status
        assert HealthStatus.aggregate([
            HealthStatus.HEALTHY,
            HealthStatus.UNKNOWN
        ]) == HealthStatus.UNKNOWN


class TestHealthCheckResult:
    """Test health check result data structure."""

    def test_creates_healthy_result(self):
        """Test creation of healthy health check result."""
        result = HealthCheckResult.healthy(
            service="test_service",
            message="Service is operating normally",
            details={"response_time_ms": 50}
        )

        assert result.service == "test_service"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Service is operating normally"
        assert result.details["response_time_ms"] == 50
        assert result.timestamp is not None

    def test_creates_unhealthy_result(self):
        """Test creation of unhealthy health check result."""
        error = Exception("Service connection failed")
        result = HealthCheckResult.unhealthy(
            service="test_service",
            message="Service unavailable",
            error=error,
            details={"last_successful_check": "2024-01-15T10:00:00Z"}
        )

        assert result.service == "test_service"
        assert result.status == HealthStatus.UNHEALTHY
        assert result.message == "Service unavailable"
        assert result.error == error
        assert result.details["last_successful_check"] == "2024-01-15T10:00:00Z"

    def test_creates_degraded_result(self):
        """Test creation of degraded health check result."""
        result = HealthCheckResult.degraded(
            service="test_service",
            message="Service responding slowly",
            details={"response_time_ms": 5000, "threshold_ms": 1000}
        )

        assert result.service == "test_service"
        assert result.status == HealthStatus.DEGRADED
        assert result.message == "Service responding slowly"
        assert result.details["response_time_ms"] == 5000

    @freeze_time("2024-01-15 10:30:00")
    def test_result_timestamp_is_current(self):
        """Test health check result timestamp is current time."""
        result = HealthCheckResult.healthy("test_service", "OK")

        assert result.timestamp == datetime(2024, 1, 15, 10, 30, 0)

    def test_result_serialization(self):
        """Test health check result can be serialized to dict."""
        result = HealthCheckResult.healthy(
            service="test_service",
            message="OK",
            details={"metric": 123}
        )

        serialized = result.to_dict()

        assert serialized["service"] == "test_service"
        assert serialized["status"] == "healthy"
        assert serialized["message"] == "OK"
        assert serialized["details"]["metric"] == 123
        assert "timestamp" in serialized


class TestServiceHealthCheck:
    """Test abstract service health check functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create a concrete implementation for testing
        class ConcreteHealthCheck(ServiceHealthCheck):
            async def _perform_check(self):
                return HealthCheckResult.healthy("test_service", "OK")

        self.health_check = ConcreteHealthCheck(
            service_name="test_service",
            timeout_seconds=5.0,
            retry_attempts=3
        )

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test health check timeout handling."""
        async def slow_check():
            await asyncio.sleep(10)  # Longer than timeout
            return HealthCheckResult.healthy("test_service", "OK")

        with patch.object(self.health_check, '_perform_check', side_effect=slow_check):
            result = await self.health_check.check()

            assert result.status == HealthStatus.UNHEALTHY
            assert "timeout" in result.message.lower()

    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test health check retry mechanism."""
        call_count = 0

        async def failing_check():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return HealthCheckResult.healthy("test_service", "OK")

        with patch.object(self.health_check, '_perform_check', side_effect=failing_check):
            result = await self.health_check.check()

            assert call_count == 3
            assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test behavior when all retry attempts fail."""
        async def always_failing_check():
            raise Exception("Persistent failure")

        with patch.object(self.health_check, '_perform_check', side_effect=always_failing_check):
            result = await self.health_check.check()

            assert result.status == HealthStatus.UNHEALTHY
            assert "Persistent failure" in result.message


class TestDatabaseHealthCheck:
    """Test database health check functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "medical_db",
            "user": "test_user"
        }
        self.health_check = DatabaseHealthCheck(
            service_name="postgresql",
            config=self.db_config
        )

    @pytest.mark.asyncio
    async def test_successful_connection_check(self):
        """Test successful database connection check."""
        mock_connection = AsyncMock()
        mock_connection.execute.return_value = [(1,)]

        with patch('asyncpg.connect', return_value=mock_connection):
            result = await self.health_check.check()

            assert result.status == HealthStatus.HEALTHY
            assert result.service == "postgresql"
            assert "response_time_ms" in result.details
            mock_connection.execute.assert_called_with("SELECT 1")

    @pytest.mark.asyncio
    async def test_connection_failure(self):
        """Test database connection failure handling."""
        with patch('asyncpg.connect', side_effect=Exception("Connection refused")):
            result = await self.health_check.check()

            assert result.status == HealthStatus.UNHEALTHY
            assert "Connection refused" in result.message

    @pytest.mark.asyncio
    async def test_slow_response_detection(self):
        """Test detection of slow database responses."""
        mock_connection = AsyncMock()

        async def slow_execute(query):
            await asyncio.sleep(2)  # Simulate slow response
            return [(1,)]

        mock_connection.execute = slow_execute

        with patch('asyncpg.connect', return_value=mock_connection):
            result = await self.health_check.check()

            assert result.details["response_time_ms"] > 1000
            if result.details["response_time_ms"] > self.health_check.degraded_threshold_ms:
                assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_connection_pool_metrics(self):
        """Test connection pool health metrics."""
        mock_pool = Mock()
        mock_pool.get_size.return_value = 10
        mock_pool.get_idle_size.return_value = 7
        mock_pool.get_max_size.return_value = 20

        with patch.object(self.health_check, '_get_connection_pool', return_value=mock_pool):
            with patch('asyncpg.connect') as mock_connect:
                mock_connection = AsyncMock()
                mock_connection.execute.return_value = [(1,)]
                mock_connect.return_value = mock_connection

                result = await self.health_check.check()

                assert "pool_size" in result.details
                assert "pool_idle" in result.details
                assert "pool_max" in result.details
                assert result.details["pool_utilization_percent"] == 30.0  # (10-7)/20 * 100


class TestGooglePlacesHealthCheck:
    """Test Google Places API health check functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.health_check = GooglePlacesHealthCheck(
            service_name="google_places",
            api_key="test_api_key"
        )

    @pytest.mark.asyncio
    async def test_successful_api_check(self):
        """Test successful Places API health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "places": [],
            "status": "OK"
        }

        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await self.health_check.check()

            assert result.status == HealthStatus.HEALTHY
            assert result.service == "google_places"
            assert "response_time_ms" in result.details
            assert "quota_remaining" in result.details

    @pytest.mark.asyncio
    async def test_api_quota_exceeded(self):
        """Test handling of API quota exceeded."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {
                "code": 429,
                "message": "Quota exceeded"
            }
        }

        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await self.health_check.check()

            assert result.status == HealthStatus.UNHEALTHY
            assert "quota" in result.message.lower()

    @pytest.mark.asyncio
    async def test_api_authentication_failure(self):
        """Test handling of API authentication failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "code": 401,
                "message": "Invalid API key"
            }
        }

        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await self.health_check.check()

            assert result.status == HealthStatus.UNHEALTHY
            assert "authentication" in result.message.lower() or "api key" in result.message.lower()

    @pytest.mark.asyncio
    async def test_api_rate_limiting_detection(self):
        """Test detection of API rate limiting."""
        # Simulate slow response indicating rate limiting
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"places": []}

        async def slow_request(*args, **kwargs):
            await asyncio.sleep(3)  # Simulate slow response
            return mock_response

        with patch('httpx.AsyncClient.post', side_effect=slow_request):
            result = await self.health_check.check()

            assert result.details["response_time_ms"] > 2000
            if result.details["response_time_ms"] > 2500:
                assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_network_connectivity_check(self):
        """Test network connectivity check to Google servers."""
        with patch('httpx.AsyncClient.post', side_effect=httpx.ConnectError("Network unreachable")):
            result = await self.health_check.check()

            assert result.status == HealthStatus.UNHEALTHY
            assert "network" in result.message.lower() or "connectivity" in result.message.lower()


class TestGeocodingHealthCheck:
    """Test Geocoding API health check functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.health_check = GeocodingHealthCheck(
            service_name="google_geocoding",
            api_key="test_api_key"
        )

    @pytest.mark.asyncio
    async def test_successful_geocoding_check(self):
        """Test successful Geocoding API health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{
                "formatted_address": "台北市信義區",
                "geometry": {
                    "location": {"lat": 25.0339, "lng": 121.5645}
                }
            }],
            "status": "OK"
        }

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await self.health_check.check()

            assert result.status == HealthStatus.HEALTHY
            assert result.service == "google_geocoding"
            assert "response_time_ms" in result.details

    @pytest.mark.asyncio
    async def test_geocoding_language_support_check(self):
        """Test Geocoding API Chinese language support."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{
                "formatted_address": "台灣台北市信義區",
                "geometry": {
                    "location": {"lat": 25.0339, "lng": 121.5645}
                }
            }],
            "status": "OK"
        }

        with patch('httpx.AsyncClient.get', return_value=mock_response) as mock_get:
            result = await self.health_check.check()

            # Verify that the request includes Chinese language parameter
            call_args = mock_get.call_args
            params = call_args[1]["params"] if call_args and len(call_args) > 1 and "params" in call_args[1] else {}
            assert params.get("language") == "zh-TW"
            assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_geocoding_zero_results_handling(self):
        """Test handling of zero results from Geocoding API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [],
            "status": "ZERO_RESULTS"
        }

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await self.health_check.check()

            # Zero results for test query might indicate service degradation
            assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
            assert "zero_results" in result.details or "ZERO_RESULTS" in str(result.details)


class TestSystemResourceHealthCheck:
    """Test system resource health check functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.health_check = SystemResourceHealthCheck(
            service_name="system_resources"
        )

    @pytest.mark.asyncio
    async def test_cpu_usage_monitoring(self):
        """Test CPU usage monitoring."""
        # Mock all system resources to ensure deterministic results
        mock_memory = Mock()
        mock_memory.percent = 50.0
        mock_memory.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.used = 4 * 1024 * 1024 * 1024  # 4GB

        mock_disk = Mock()
        mock_disk.percent = 50.0
        mock_disk.free = 50 * 1024 * 1024 * 1024  # 50GB

        with patch('psutil.cpu_percent', return_value=45.5):
            with patch('psutil.virtual_memory', return_value=mock_memory):
                with patch('psutil.disk_usage', return_value=mock_disk):
                    result = await self.health_check.check()

                    assert "cpu_usage_percent" in result.details
                    assert result.details["cpu_usage_percent"] == 45.5
                    assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self):
        """Test memory usage monitoring."""
        mock_memory = Mock()
        mock_memory.percent = 72.3
        mock_memory.available = 2 * 1024 * 1024 * 1024  # 2GB
        mock_memory.total = 8 * 1024 * 1024 * 1024  # 8GB

        with patch('psutil.virtual_memory', return_value=mock_memory):
            result = await self.health_check.check()

            assert "memory_usage_percent" in result.details
            assert result.details["memory_usage_percent"] == 72.3
            assert "memory_available_gb" in result.details

    @pytest.mark.asyncio
    async def test_disk_usage_monitoring(self):
        """Test disk usage monitoring."""
        mock_disk = Mock()
        mock_disk.percent = 68.7
        mock_disk.free = 50 * 1024 * 1024 * 1024  # 50GB
        mock_disk.total = 100 * 1024 * 1024 * 1024  # 100GB

        with patch('psutil.disk_usage', return_value=mock_disk):
            result = await self.health_check.check()

            assert "disk_usage_percent" in result.details
            assert result.details["disk_usage_percent"] == 68.7

    @pytest.mark.asyncio
    async def test_high_resource_usage_detection(self):
        """Test detection of high resource usage."""
        # Test high CPU usage
        with patch('psutil.cpu_percent', return_value=95.0):
            with patch('psutil.virtual_memory') as mock_memory:
                mock_memory.return_value.percent = 50.0
                with patch('psutil.disk_usage') as mock_disk:
                    mock_disk.return_value.percent = 50.0

                    result = await self.health_check.check()

                    assert result.status == HealthStatus.DEGRADED
                    assert result.details["cpu_usage_percent"] == 95.0

    @pytest.mark.asyncio
    async def test_critical_resource_usage_detection(self):
        """Test detection of critical resource usage."""
        # Test critical memory usage
        mock_memory = Mock()
        mock_memory.percent = 98.5
        mock_memory.available = 100 * 1024 * 1024  # 100MB
        mock_memory.used = 8 * 1024 * 1024 * 1024  # 8GB

        mock_disk = Mock()
        mock_disk.percent = 50.0
        mock_disk.free = 50 * 1024 * 1024 * 1024  # 50GB

        with patch('psutil.cpu_percent', return_value=50.0):
            with patch('psutil.virtual_memory', return_value=mock_memory):
                with patch('psutil.disk_usage', return_value=mock_disk):
                    result = await self.health_check.check()

                    assert result.status == HealthStatus.UNHEALTHY
                    assert result.details["memory_usage_percent"] == 98.5

    @pytest.mark.asyncio
    async def test_load_average_monitoring(self):
        """Test system load average monitoring."""
        # Skip on Windows since getloadavg is not available
        import os
        if os.name == 'nt':
            pytest.skip("os.getloadavg not available on Windows")

        with patch('os.getloadavg', return_value=(1.5, 1.2, 0.8)):
            result = await self.health_check.check()

            assert "load_average_1m" in result.details
            assert "load_average_5m" in result.details
            assert "load_average_15m" in result.details
            assert result.details["load_average_1m"] == 1.5


class TestCircuitBreakerHealthCheck:
    """Test circuit breaker health check functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.health_check = CircuitBreakerHealthCheck(
            service_name="circuit_breakers"
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_status_monitoring(self):
        """Test monitoring of circuit breaker statuses."""
        mock_circuit_breakers = {
            "google_places": {"state": "closed", "failure_count": 0, "last_failure": None},
            "geocoding": {"state": "closed", "failure_count": 0, "last_failure": None},
            "database": {"state": "half_open", "failure_count": 3, "last_failure": "2024-01-15T10:00:00Z"}
        }

        with patch.object(self.health_check, '_get_circuit_breaker_states', return_value=mock_circuit_breakers):
            result = await self.health_check.check()

            assert result.details["total_breakers"] == 3
            assert result.details["open_breakers"] == 0
            assert result.details["half_open_breakers"] == 1
            assert result.details["closed_breakers"] == 2

    @pytest.mark.asyncio
    async def test_open_circuit_breaker_detection(self):
        """Test detection of open circuit breakers."""
        mock_circuit_breakers = {
            "google_places": {"state": "open", "failure_count": 5, "last_failure": "2024-01-15T10:25:00Z"},
            "geocoding": {"state": "closed", "failure_count": 0, "last_failure": None}
        }

        with patch.object(self.health_check, '_get_circuit_breaker_states', return_value=mock_circuit_breakers):
            result = await self.health_check.check()

            assert result.status == HealthStatus.DEGRADED
            assert result.details["open_breakers"] == 1
            assert "google_places" in result.details["open_breaker_services"]

    @pytest.mark.asyncio
    async def test_multiple_open_breakers_critical_status(self):
        """Test critical status when multiple circuit breakers are open."""
        mock_circuit_breakers = {
            "google_places": {"state": "open", "failure_count": 5, "last_failure": "2024-01-15T10:25:00Z"},
            "geocoding": {"state": "open", "failure_count": 3, "last_failure": "2024-01-15T10:20:00Z"},
            "database": {"state": "closed", "failure_count": 0, "last_failure": None}
        }

        with patch.object(self.health_check, '_get_circuit_breaker_states', return_value=mock_circuit_breakers):
            result = await self.health_check.check()

            assert result.status == HealthStatus.UNHEALTHY
            assert result.details["open_breakers"] == 2


class TestHealthMonitor:
    """Test health monitor orchestration functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.health_monitor = HealthMonitor()

    @pytest.mark.asyncio
    async def test_registers_health_checks(self):
        """Test registration of health checks."""
        mock_health_check = Mock(spec=ServiceHealthCheck)
        mock_health_check.service_name = "test_service"

        self.health_monitor.register_health_check(mock_health_check)

        assert "test_service" in self.health_monitor.health_checks
        assert self.health_monitor.health_checks["test_service"] == mock_health_check

    @pytest.mark.asyncio
    async def test_runs_all_health_checks(self):
        """Test running all registered health checks."""
        mock_check_1 = Mock(spec=ServiceHealthCheck)
        mock_check_1.service_name = "service_1"
        mock_check_1.check = AsyncMock(return_value=HealthCheckResult.healthy("service_1", "OK"))

        mock_check_2 = Mock(spec=ServiceHealthCheck)
        mock_check_2.service_name = "service_2"
        mock_check_2.check = AsyncMock(return_value=HealthCheckResult.degraded("service_2", "Slow"))

        self.health_monitor.register_health_check(mock_check_1)
        self.health_monitor.register_health_check(mock_check_2)

        results = await self.health_monitor.check_all()

        assert len(results) == 2
        assert results["service_1"].status == HealthStatus.HEALTHY
        assert results["service_2"].status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_parallel_health_check_execution(self):
        """Test that health checks are executed in parallel."""
        execution_times = []

        async def slow_check():
            start_time = datetime.now()
            await asyncio.sleep(0.1)
            execution_times.append(start_time)
            return HealthCheckResult.healthy("test", "OK")

        mock_check_1 = Mock(spec=ServiceHealthCheck)
        mock_check_1.service_name = "service_1"
        mock_check_1.check = slow_check

        mock_check_2 = Mock(spec=ServiceHealthCheck)
        mock_check_2.service_name = "service_2"
        mock_check_2.check = slow_check

        self.health_monitor.register_health_check(mock_check_1)
        self.health_monitor.register_health_check(mock_check_2)

        start_time = datetime.now()
        await self.health_monitor.check_all()
        total_time = (datetime.now() - start_time).total_seconds()

        # Should complete in roughly 0.1 seconds (parallel) not 0.2 seconds (sequential)
        assert total_time < 0.15
        assert len(execution_times) == 2

    @pytest.mark.asyncio
    async def test_overall_health_status_calculation(self):
        """Test calculation of overall health status."""
        results = {
            "service_1": HealthCheckResult.healthy("service_1", "OK"),
            "service_2": HealthCheckResult.degraded("service_2", "Slow"),
            "service_3": HealthCheckResult.healthy("service_3", "OK")
        }

        overall_status = self.health_monitor.calculate_overall_status(results)

        assert overall_status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_health_check_timeout_handling(self):
        """Test handling of health check timeouts."""
        async def timeout_check():
            await asyncio.sleep(10)  # Very long operation
            return HealthCheckResult.healthy("test", "OK")

        mock_check = Mock(spec=ServiceHealthCheck)
        mock_check.service_name = "timeout_service"
        mock_check.check = timeout_check

        self.health_monitor.register_health_check(mock_check)

        # Set a short timeout for the monitor
        self.health_monitor.global_timeout_seconds = 0.1

        results = await self.health_monitor.check_all()

        assert results["timeout_service"].status == HealthStatus.UNHEALTHY
        assert "timeout" in results["timeout_service"].message.lower()

    @pytest.mark.asyncio
    async def test_health_history_tracking(self):
        """Test tracking of health check history."""
        mock_check = Mock(spec=ServiceHealthCheck)
        mock_check.service_name = "test_service"
        mock_check.check = AsyncMock(return_value=HealthCheckResult.healthy("test_service", "OK"))

        self.health_monitor.register_health_check(mock_check)
        self.health_monitor.enable_history_tracking(max_entries=5)

        # Run health checks multiple times
        for _ in range(3):
            await self.health_monitor.check_all()

        history = self.health_monitor.get_health_history("test_service")

        assert len(history) == 3
        assert all(result.status == HealthStatus.HEALTHY for result in history)