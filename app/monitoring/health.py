"""
Health monitoring system for Taiwan Medical AI Assistant.
Provides comprehensive health checks for all services and dependencies.
"""

import asyncio
import time
import os
import socket
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import threading
import psutil

import httpx
import asyncpg


class HealthStatus(Enum):
    """Health status enumeration with severity ordering."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

    def __lt__(self, other):
        """Enable comparison by severity."""
        if not isinstance(other, HealthStatus):
            return NotImplemented

        severity_order = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 1,
            HealthStatus.UNHEALTHY: 2,
            HealthStatus.UNKNOWN: 3
        }
        return severity_order[self] < severity_order[other]

    @classmethod
    def aggregate(cls, statuses: List['HealthStatus']) -> 'HealthStatus':
        """Aggregate multiple health statuses into worst status."""
        if not statuses:
            return cls.UNKNOWN

        return max(statuses)


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    service: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Dict[str, Any]
    error: Optional[Exception] = None

    @classmethod
    def healthy(cls, service: str, message: str, details: Optional[Dict[str, Any]] = None) -> 'HealthCheckResult':
        """Create a healthy health check result."""
        return cls(
            service=service,
            status=HealthStatus.HEALTHY,
            message=message,
            timestamp=datetime.now(),
            details=details or {},
            error=None
        )

    @classmethod
    def unhealthy(cls, service: str, message: str, error: Optional[Exception] = None,
                  details: Optional[Dict[str, Any]] = None) -> 'HealthCheckResult':
        """Create an unhealthy health check result."""
        return cls(
            service=service,
            status=HealthStatus.UNHEALTHY,
            message=message,
            timestamp=datetime.now(),
            details=details or {},
            error=error
        )

    @classmethod
    def degraded(cls, service: str, message: str, details: Optional[Dict[str, Any]] = None) -> 'HealthCheckResult':
        """Create a degraded health check result."""
        return cls(
            service=service,
            status=HealthStatus.DEGRADED,
            message=message,
            timestamp=datetime.now(),
            details=details or {},
            error=None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize health check result to dictionary."""
        return {
            "service": self.service,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "error": str(self.error) if self.error else None
        }


class ServiceHealthCheck(ABC):
    """Abstract base class for service health checks."""

    def __init__(self, service_name: str, timeout_seconds: float = 30.0, retry_attempts: int = 3):
        self.service_name = service_name
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = retry_attempts

    async def check(self) -> HealthCheckResult:
        """Perform health check with timeout and retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                # Apply timeout to the health check
                result = await asyncio.wait_for(
                    self._perform_check(),
                    timeout=self.timeout_seconds
                )
                return result

            except asyncio.TimeoutError:
                if attempt == self.retry_attempts - 1:
                    return HealthCheckResult.unhealthy(
                        service=self.service_name,
                        message=f"Health check timeout after {self.timeout_seconds}s",
                        details={"timeout_seconds": self.timeout_seconds}
                    )
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    return HealthCheckResult.unhealthy(
                        service=self.service_name,
                        message=str(e),
                        error=e,
                        details={"retry_attempts": self.retry_attempts}
                    )
                await asyncio.sleep(0.5 * (attempt + 1))

        return HealthCheckResult.unhealthy(
            service=self.service_name,
            message="Unknown failure after retries"
        )

    @abstractmethod
    async def _perform_check(self) -> HealthCheckResult:
        """Perform the actual health check. To be implemented by subclasses."""
        pass


class DatabaseHealthCheck(ServiceHealthCheck):
    """Health check for PostgreSQL database."""

    def __init__(self, service_name: str = "postgresql", config: Optional[Dict[str, Any]] = None,
                 degraded_threshold_ms: float = 1000.0):
        super().__init__(service_name)
        self.config = config or {}
        self.degraded_threshold_ms = degraded_threshold_ms

    async def _perform_check(self) -> HealthCheckResult:
        """Perform database health check."""
        start_time = time.time()

        try:
            # Connect to database
            connection = await asyncpg.connect(**self.config)

            # Execute simple query
            result = await connection.execute("SELECT 1")

            # Close connection
            await connection.close()

            response_time_ms = (time.time() - start_time) * 1000

            details = {
                "response_time_ms": response_time_ms,
                "query": "SELECT 1"
            }

            # Add connection pool metrics if available
            pool_metrics = self._get_connection_pool()
            if pool_metrics:
                details.update({
                    "pool_size": pool_metrics.get_size(),
                    "pool_idle": pool_metrics.get_idle_size(),
                    "pool_max": pool_metrics.get_max_size(),
                    "pool_utilization_percent": ((pool_metrics.get_size() - pool_metrics.get_idle_size()) / pool_metrics.get_size()) * 100
                })

            if response_time_ms > self.degraded_threshold_ms:
                return HealthCheckResult.degraded(
                    service=self.service_name,
                    message=f"Database responding slowly ({response_time_ms:.2f}ms)",
                    details=details
                )

            return HealthCheckResult.healthy(
                service=self.service_name,
                message="Database connection successful",
                details=details
            )

        except Exception as e:
            return HealthCheckResult.unhealthy(
                service=self.service_name,
                message=f"Database connection failed: {str(e)}",
                error=e,
                details={"response_time_ms": (time.time() - start_time) * 1000}
            )

    def _get_connection_pool(self):
        """Get connection pool for metrics. Override in subclass if needed."""
        return None


class GooglePlacesHealthCheck(ServiceHealthCheck):
    """Health check for Google Places API."""

    def __init__(self, service_name: str = "google_places", api_key: str = None,
                 degraded_threshold_ms: float = 2000.0):
        super().__init__(service_name)
        self.api_key = api_key
        self.degraded_threshold_ms = degraded_threshold_ms

    async def _perform_check(self) -> HealthCheckResult:
        """Perform Google Places API health check."""
        start_time = time.time()

        try:
            async with httpx.AsyncClient() as client:
                # Test with a simple nearby search
                test_payload = {
                    "includedTypes": ["hospital"],
                    "locationRestriction": {
                        "circle": {
                            "center": {"latitude": 25.0339, "longitude": 121.5645},
                            "radius": 1000.0
                        }
                    },
                    "languageCode": "zh-TW",
                    "regionCode": "TW",
                    "maxResultCount": 1
                }

                headers = {
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": self.api_key,
                    "X-Goog-FieldMask": "places.displayName,places.formattedAddress"
                }

                response = await client.post(
                    "https://places.googleapis.com/v1/places:searchNearby",
                    json=test_payload,
                    headers=headers,
                    timeout=self.timeout_seconds
                )

                response_time_ms = (time.time() - start_time) * 1000

                details = {
                    "response_time_ms": response_time_ms,
                    "status_code": response.status_code,
                    "quota_remaining": response.headers.get("X-Quota-Remaining", "unknown")
                }

                if response.status_code == 200:
                    data = response.json()
                    details["places_count"] = len(data.get("places", []))

                    if response_time_ms > self.degraded_threshold_ms:
                        return HealthCheckResult.degraded(
                            service=self.service_name,
                            message=f"Google Places API responding slowly ({response_time_ms:.2f}ms)",
                            details=details
                        )

                    return HealthCheckResult.healthy(
                        service=self.service_name,
                        message="Google Places API accessible",
                        details=details
                    )

                elif response.status_code == 401:
                    return HealthCheckResult.unhealthy(
                        service=self.service_name,
                        message="Google Places API authentication failed",
                        details=details
                    )

                elif response.status_code == 429:
                    return HealthCheckResult.unhealthy(
                        service=self.service_name,
                        message="Google Places API quota exceeded",
                        details=details
                    )

                else:
                    return HealthCheckResult.unhealthy(
                        service=self.service_name,
                        message=f"Google Places API error: {response.status_code}",
                        details=details
                    )

        except httpx.ConnectError as e:
            return HealthCheckResult.unhealthy(
                service=self.service_name,
                message="Google Places API network connectivity issue",
                error=e,
                details={"response_time_ms": (time.time() - start_time) * 1000}
            )

        except Exception as e:
            return HealthCheckResult.unhealthy(
                service=self.service_name,
                message=f"Google Places API check failed: {str(e)}",
                error=e,
                details={"response_time_ms": (time.time() - start_time) * 1000}
            )


class GeocodingHealthCheck(ServiceHealthCheck):
    """Health check for Google Geocoding API."""

    def __init__(self, service_name: str = "google_geocoding", api_key: str = None):
        super().__init__(service_name)
        self.api_key = api_key

    async def _perform_check(self) -> HealthCheckResult:
        """Perform Geocoding API health check."""
        start_time = time.time()

        try:
            async with httpx.AsyncClient() as client:
                # Test with a known address in Taiwan
                params = {
                    "address": "台北市信義區",
                    "language": "zh-TW",
                    "region": "TW",
                    "key": self.api_key
                }

                response = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params=params,
                    timeout=self.timeout_seconds
                )

                response_time_ms = (time.time() - start_time) * 1000

                details = {
                    "response_time_ms": response_time_ms,
                    "status_code": response.status_code
                }

                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "UNKNOWN")

                    details["api_status"] = status
                    details["results_count"] = len(data.get("results", []))

                    if status == "OK":
                        return HealthCheckResult.healthy(
                            service=self.service_name,
                            message="Geocoding API accessible with zh-TW support",
                            details=details
                        )
                    elif status == "ZERO_RESULTS":
                        details["zero_results"] = True
                        return HealthCheckResult.degraded(
                            service=self.service_name,
                            message="Geocoding API accessible but returned zero results",
                            details=details
                        )
                    else:
                        return HealthCheckResult.unhealthy(
                            service=self.service_name,
                            message=f"Geocoding API error status: {status}",
                            details=details
                        )

                else:
                    return HealthCheckResult.unhealthy(
                        service=self.service_name,
                        message=f"Geocoding API HTTP error: {response.status_code}",
                        details=details
                    )

        except Exception as e:
            return HealthCheckResult.unhealthy(
                service=self.service_name,
                message=f"Geocoding API check failed: {str(e)}",
                error=e,
                details={"response_time_ms": (time.time() - start_time) * 1000}
            )


class SystemResourceHealthCheck(ServiceHealthCheck):
    """Health check for system resources (CPU, memory, disk)."""

    def __init__(self, service_name: str = "system_resources",
                 cpu_threshold: float = 80.0, memory_threshold: float = 85.0,
                 disk_threshold: float = 90.0):
        super().__init__(service_name)
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold

    async def _perform_check(self) -> HealthCheckResult:
        """Perform system resource health check."""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Get memory usage
            memory = psutil.virtual_memory()

            # Get disk usage
            disk = psutil.disk_usage('/')

            # Get load average (Unix-like systems only)
            load_avg = None
            try:
                load_avg = os.getloadavg()
            except (AttributeError, OSError):
                # Windows or other systems that don't support getloadavg
                pass

            details = {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "memory_used_bytes": memory.used,
                "disk_usage_percent": disk.percent,
                "disk_free_bytes": disk.free
            }

            if load_avg:
                details.update({
                    "load_average_1m": load_avg[0],
                    "load_average_5m": load_avg[1],
                    "load_average_15m": load_avg[2]
                })

            # Determine health status based on thresholds
            if (cpu_percent > 95 or memory.percent > 95 or disk.percent > 95):
                return HealthCheckResult.unhealthy(
                    service=self.service_name,
                    message="Critical resource usage detected",
                    details=details
                )

            elif (cpu_percent > self.cpu_threshold or
                  memory.percent > self.memory_threshold or
                  disk.percent > self.disk_threshold):
                return HealthCheckResult.degraded(
                    service=self.service_name,
                    message="High resource usage detected",
                    details=details
                )

            else:
                return HealthCheckResult.healthy(
                    service=self.service_name,
                    message="System resources within normal limits",
                    details=details
                )

        except Exception as e:
            return HealthCheckResult.unhealthy(
                service=self.service_name,
                message=f"System resource check failed: {str(e)}",
                error=e
            )


class CircuitBreakerHealthCheck(ServiceHealthCheck):
    """Health check for circuit breaker status."""

    def __init__(self, service_name: str = "circuit_breakers"):
        super().__init__(service_name)

    async def _perform_check(self) -> HealthCheckResult:
        """Perform circuit breaker health check."""
        try:
            breaker_states = self._get_circuit_breaker_states()

            total_breakers = len(breaker_states)
            open_breakers = sum(1 for state in breaker_states.values() if state["state"] == "open")
            half_open_breakers = sum(1 for state in breaker_states.values() if state["state"] == "half_open")
            closed_breakers = sum(1 for state in breaker_states.values() if state["state"] == "closed")

            open_breaker_services = [service for service, state in breaker_states.items()
                                   if state["state"] == "open"]

            details = {
                "total_breakers": total_breakers,
                "open_breakers": open_breakers,
                "half_open_breakers": half_open_breakers,
                "closed_breakers": closed_breakers,
                "open_breaker_services": open_breaker_services
            }

            if open_breakers >= 2:
                return HealthCheckResult.unhealthy(
                    service=self.service_name,
                    message=f"Multiple circuit breakers open ({open_breakers})",
                    details=details
                )
            elif open_breakers > 0:
                return HealthCheckResult.degraded(
                    service=self.service_name,
                    message=f"Circuit breaker open for: {', '.join(open_breaker_services)}",
                    details=details
                )
            else:
                return HealthCheckResult.healthy(
                    service=self.service_name,
                    message="All circuit breakers operational",
                    details=details
                )

        except Exception as e:
            return HealthCheckResult.unhealthy(
                service=self.service_name,
                message=f"Circuit breaker check failed: {str(e)}",
                error=e
            )

    def _get_circuit_breaker_states(self) -> Dict[str, Dict[str, Any]]:
        """Get circuit breaker states. Override in implementation."""
        # Mock implementation for testing
        return {
            "google_places": {"state": "closed", "failure_count": 0, "last_failure": None},
            "geocoding": {"state": "closed", "failure_count": 0, "last_failure": None},
            "database": {"state": "closed", "failure_count": 0, "last_failure": None}
        }


class HealthMonitor:
    """Health monitor orchestration."""

    def __init__(self, global_timeout_seconds: float = 30.0):
        self.health_checks: Dict[str, ServiceHealthCheck] = {}
        self.global_timeout_seconds = global_timeout_seconds
        self._history: Dict[str, List[HealthCheckResult]] = {}
        self._history_enabled = False
        self._max_history_entries = 10

    def register_health_check(self, health_check: ServiceHealthCheck):
        """Register a health check."""
        self.health_checks[health_check.service_name] = health_check

    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks in parallel."""
        if not self.health_checks:
            return {}

        # Run all health checks in parallel with global timeout
        try:
            tasks = [
                asyncio.create_task(health_check.check())
                for health_check in self.health_checks.values()
            ]

            results = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=self.global_timeout_seconds
            )

            result_dict = {}
            for i, (service_name, health_check) in enumerate(self.health_checks.items()):
                result = results[i]
                result_dict[service_name] = result

                # Add to history if enabled
                if self._history_enabled:
                    if service_name not in self._history:
                        self._history[service_name] = []

                    self._history[service_name].append(result)

                    # Trim history to max entries
                    if len(self._history[service_name]) > self._max_history_entries:
                        self._history[service_name] = self._history[service_name][-self._max_history_entries:]

            return result_dict

        except asyncio.TimeoutError:
            # Return timeout results for all services
            return {
                service_name: HealthCheckResult.unhealthy(
                    service=service_name,
                    message=f"Global health check timeout ({self.global_timeout_seconds}s)"
                )
                for service_name in self.health_checks.keys()
            }

    def calculate_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """Calculate overall health status from individual results."""
        if not results:
            return HealthStatus.UNKNOWN

        statuses = [result.status for result in results.values()]
        return HealthStatus.aggregate(statuses)

    def enable_history_tracking(self, max_entries: int = 10):
        """Enable health check history tracking."""
        self._history_enabled = True
        self._max_history_entries = max_entries

    def get_health_history(self, service_name: str) -> List[HealthCheckResult]:
        """Get health check history for a service."""
        return self._history.get(service_name, [])


# Default health checker instance
class HealthChecker:
    """Main health checker class for the application."""

    def __init__(self):
        self.monitor = HealthMonitor()
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize health checks with configuration."""
        if self._initialized:
            return

        config = config or {}

        # Register system resource check
        self.monitor.register_health_check(SystemResourceHealthCheck())

        # Register database check if configured
        db_config = config.get("database")
        if db_config:
            self.monitor.register_health_check(DatabaseHealthCheck(config=db_config))

        # Register Google Places check if configured
        places_api_key = config.get("google_places_api_key")
        if places_api_key:
            self.monitor.register_health_check(GooglePlacesHealthCheck(api_key=places_api_key))

        # Register Geocoding check if configured
        geocoding_api_key = config.get("google_geocoding_api_key")
        if geocoding_api_key:
            self.monitor.register_health_check(GeocodingHealthCheck(api_key=geocoding_api_key))

        # Register circuit breaker check
        self.monitor.register_health_check(CircuitBreakerHealthCheck())

        self._initialized = True

    async def check_health(self, include_details: bool = False) -> Dict[str, Any]:
        """Perform health check and return formatted results."""
        if not self._initialized:
            self.initialize()

        results = await self.monitor.check_all()
        overall_status = self.monitor.calculate_overall_status(results)

        response = {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                service: result.to_dict() if include_details else {
                    "status": result.status.value,
                    "message": result.message,
                    "timestamp": result.timestamp.isoformat()
                }
                for service, result in results.items()
            }
        }

        if include_details:
            response["overall_status"] = overall_status.value
            response["system_info"] = {
                "hostname": socket.gethostname(),
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "platform": os.name
            }

        return response

    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        if not self._initialized:
            self.initialize()

        if service_name not in self.monitor.health_checks:
            raise ValueError(f"Service '{service_name}' not found")

        health_check = self.monitor.health_checks[service_name]
        result = await health_check.check()

        return {
            "service": service_name,
            "status": result.status.value,
            "message": result.message,
            "details": result.details,
            "last_check": result.timestamp.isoformat(),
            "error": str(result.error) if result.error else None
        }


# Global health checker instance
health_checker = HealthChecker()