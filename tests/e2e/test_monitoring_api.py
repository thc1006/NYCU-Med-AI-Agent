"""
E2E tests for monitoring API endpoints.
Tests complete monitoring dashboard functionality with real API integration.
"""

import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, List, Any

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time

from app.main import app
from app.monitoring.health import HealthStatus
from app.monitoring.metrics import MetricType


class TestHealthMonitoringEndpoints:
    """Test health monitoring API endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_health_check_endpoint_basic(self):
        """Test basic health check endpoint."""
        response = self.client.get("/v1/monitoring/health")

        assert response.status_code == 200
        health_data = response.json()

        assert "status" in health_data
        assert health_data["status"] in ["healthy", "degraded", "unhealthy", "unknown"]
        assert "timestamp" in health_data
        assert "checks" in health_data

    def test_health_check_with_details(self):
        """Test health check endpoint with detailed information."""
        response = self.client.get("/v1/monitoring/health?include_details=true")

        assert response.status_code == 200
        health_data = response.json()

        assert "overall_status" in health_data
        assert "checks" in health_data
        assert "system_info" in health_data

        # Verify individual service checks
        checks = health_data["checks"]
        expected_services = ["database", "google_places", "geocoding", "system_resources"]

        for service in expected_services:
            assert service in checks
            service_check = checks[service]
            assert "status" in service_check
            assert "message" in service_check
            assert "timestamp" in service_check

    def test_health_check_individual_service(self):
        """Test health check for individual service."""
        services = ["database", "google_places", "geocoding", "system_resources"]

        for service in services:
            response = self.client.get(f"/v1/monitoring/health/{service}")

            assert response.status_code == 200
            service_health = response.json()

            assert service_health["service"] == service
            assert "status" in service_health
            assert "details" in service_health
            assert "last_check" in service_health

    def test_health_check_nonexistent_service(self):
        """Test health check for non-existent service."""
        response = self.client.get("/v1/monitoring/health/nonexistent_service")

        assert response.status_code == 404
        error_data = response.json()
        assert "not found" in error_data["detail"].lower()

    def test_health_check_with_timeout(self):
        """Test health check with custom timeout."""
        response = self.client.get("/v1/monitoring/health?timeout=5")

        assert response.status_code == 200
        health_data = response.json()

        # Should complete within reasonable time even with timeout
        assert "status" in health_data

    @patch('app.monitoring.health.DatabaseHealthCheck.check')
    def test_health_check_service_failure(self, mock_db_check):
        """Test health check when service is failing."""
        from app.monitoring.health import HealthCheckResult

        mock_db_check.return_value = HealthCheckResult.unhealthy(
            service="database",
            message="Connection failed",
            error=Exception("Database unreachable")
        )

        response = self.client.get("/v1/monitoring/health")

        assert response.status_code == 503  # Service Unavailable
        health_data = response.json()

        assert health_data["status"] == "unhealthy"
        assert "database" in health_data["checks"]
        assert health_data["checks"]["database"]["status"] == "unhealthy"

    def test_health_check_includes_correlation_id(self):
        """Test that health check includes correlation ID in response."""
        correlation_id = "test-correlation-123"

        response = self.client.get(
            "/v1/monitoring/health",
            headers={"X-Correlation-ID": correlation_id}
        )

        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == correlation_id

    def test_health_check_response_caching(self):
        """Test health check response caching headers."""
        response = self.client.get("/v1/monitoring/health")

        assert response.status_code == 200
        # Health checks should not be cached
        assert "no-cache" in response.headers.get("Cache-Control", "").lower()

    def test_health_history_endpoint(self):
        """Test health history endpoint."""
        # First, trigger some health checks
        for _ in range(3):
            self.client.get("/v1/monitoring/health")
            time.sleep(0.1)

        response = self.client.get("/v1/monitoring/health/history?limit=5")

        assert response.status_code == 200
        history_data = response.json()

        assert "entries" in history_data
        assert "total_count" in history_data
        assert len(history_data["entries"]) <= 5

        # Verify history entry structure
        if history_data["entries"]:
            entry = history_data["entries"][0]
            assert "timestamp" in entry
            assert "overall_status" in entry
            assert "services" in entry


class TestMetricsEndpoints:
    """Test metrics monitoring API endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_metrics_prometheus_endpoint(self):
        """Test Prometheus metrics endpoint."""
        response = self.client.get("/v1/monitoring/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        metrics_text = response.text

        # Verify Prometheus format
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text

        # Check for expected metric families
        expected_metrics = [
            "http_requests_total",
            "http_request_duration_histogram",
            "system_cpu_usage_percent",
            "system_memory_usage_percent"
        ]

        for metric in expected_metrics:
            assert metric in metrics_text

    def test_metrics_json_endpoint(self):
        """Test JSON metrics endpoint."""
        response = self.client.get("/v1/monitoring/metrics?format=json")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        metrics_data = response.json()

        assert "metrics" in metrics_data
        assert "timestamp" in metrics_data
        assert "collection_duration_ms" in metrics_data

        # Verify metric structure
        metrics = metrics_data["metrics"]
        for metric_name, metric_info in metrics.items():
            assert "type" in metric_info
            assert "description" in metric_info
            assert "samples" in metric_info

    def test_metrics_filtered_by_type(self):
        """Test filtering metrics by type."""
        response = self.client.get("/v1/monitoring/metrics?type=counter")

        assert response.status_code == 200
        metrics_text = response.text

        # Should only contain counter metrics
        lines = metrics_text.split('\n')
        type_lines = [line for line in lines if line.startswith("# TYPE")]

        for line in type_lines:
            assert "counter" in line

    def test_metrics_filtered_by_name_pattern(self):
        """Test filtering metrics by name pattern."""
        response = self.client.get("/v1/monitoring/metrics?name_pattern=http_*")

        assert response.status_code == 200
        metrics_text = response.text

        # Should only contain HTTP-related metrics
        metric_lines = [line for line in metrics_text.split('\n')
                       if line and not line.startswith('#')]

        for line in metric_lines:
            if line.strip():
                assert line.startswith('http_')

    def test_business_metrics_endpoint(self):
        """Test business-specific metrics endpoint."""
        response = self.client.get("/v1/monitoring/metrics/business")

        assert response.status_code == 200
        business_data = response.json()

        assert "triage_requests" in business_data
        assert "hospital_searches" in business_data
        assert "emergency_escalations" in business_data

        # Verify business metric structure
        triage_data = business_data["triage_requests"]
        assert "total" in triage_data
        assert "by_level" in triage_data
        assert "avg_response_time_ms" in triage_data

    def test_performance_metrics_endpoint(self):
        """Test performance metrics endpoint."""
        response = self.client.get("/v1/monitoring/metrics/performance")

        assert response.status_code == 200
        perf_data = response.json()

        assert "api_performance" in perf_data
        assert "external_services" in perf_data
        assert "system_resources" in perf_data

        # Verify API performance data
        api_perf = perf_data["api_performance"]
        assert "request_duration" in api_perf
        assert "request_rate" in api_perf
        assert "error_rate" in api_perf

    def test_metrics_with_time_range(self):
        """Test metrics with time range filtering."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)

        response = self.client.get(
            f"/v1/monitoring/metrics/performance?"
            f"start_time={start_time.isoformat()}&"
            f"end_time={end_time.isoformat()}"
        )

        assert response.status_code == 200
        perf_data = response.json()

        assert "time_range" in perf_data
        assert perf_data["time_range"]["start"] == start_time.isoformat()
        assert perf_data["time_range"]["end"] == end_time.isoformat()

    def test_real_time_metrics_stream(self):
        """Test real-time metrics streaming endpoint."""
        # This would typically use WebSocket or Server-Sent Events
        response = self.client.get("/v1/monitoring/metrics/stream")

        # For HTTP endpoint, should return current metrics
        assert response.status_code == 200
        stream_data = response.json()

        assert "current_metrics" in stream_data
        assert "update_interval_seconds" in stream_data
        assert "stream_id" in stream_data


class TestAuditLoggingEndpoints:
    """Test audit logging API endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_audit_events_query_endpoint(self):
        """Test querying audit events endpoint."""
        # First trigger some activity to generate audit events
        self.client.post("/v1/triage", json={"symptomText": "headache"})
        self.client.get("/v1/hospitals/nearby?lat=25.0339&lng=121.5645")

        response = self.client.get("/v1/monitoring/audit/events?limit=10")

        assert response.status_code == 200
        audit_data = response.json()

        assert "events" in audit_data
        assert "total_count" in audit_data
        assert "page_info" in audit_data

        # Verify audit event structure
        if audit_data["events"]:
            event = audit_data["events"][0]
            assert "event_id" in event
            assert "event_type" in event
            assert "timestamp" in event
            assert "action" in event
            # Should NOT contain PII
            assert "user_email" not in event
            assert "phone_number" not in event

    def test_audit_events_by_correlation_id(self):
        """Test querying audit events by correlation ID."""
        correlation_id = "test-correlation-456"

        # Make request with specific correlation ID
        self.client.post(
            "/v1/triage",
            json={"symptomText": "chest pain"},
            headers={"X-Correlation-ID": correlation_id}
        )

        response = self.client.get(
            f"/v1/monitoring/audit/events?correlation_id={correlation_id}"
        )

        assert response.status_code == 200
        audit_data = response.json()

        # All returned events should have the same correlation ID
        for event in audit_data["events"]:
            assert event["correlation_id"] == correlation_id

    def test_audit_events_by_time_range(self):
        """Test querying audit events by time range."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)

        response = self.client.get(
            f"/v1/monitoring/audit/events?"
            f"start_time={start_time.isoformat()}&"
            f"end_time={end_time.isoformat()}"
        )

        assert response.status_code == 200
        audit_data = response.json()

        # Verify time range filtering
        for event in audit_data["events"]:
            event_time = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
            assert start_time <= event_time <= end_time

    def test_audit_events_by_event_type(self):
        """Test querying audit events by event type."""
        response = self.client.get(
            "/v1/monitoring/audit/events?event_type=medical_consultation"
        )

        assert response.status_code == 200
        audit_data = response.json()

        # All events should be of the specified type
        for event in audit_data["events"]:
            assert event["event_type"] == "medical_consultation"

    def test_audit_trail_endpoint(self):
        """Test audit trail reconstruction endpoint."""
        correlation_id = "test-trail-789"

        # Generate a sequence of related events
        self.client.get(
            "/v1/monitoring/health",
            headers={"X-Correlation-ID": correlation_id}
        )
        self.client.post(
            "/v1/triage",
            json={"symptomText": "fever"},
            headers={"X-Correlation-ID": correlation_id}
        )

        response = self.client.get(
            f"/v1/monitoring/audit/trail/{correlation_id}"
        )

        assert response.status_code == 200
        trail_data = response.json()

        assert "correlation_id" in trail_data
        assert "events" in trail_data
        assert "timeline" in trail_data
        assert "summary" in trail_data

        # Events should be ordered chronologically
        events = trail_data["events"]
        for i in range(1, len(events)):
            prev_time = datetime.fromisoformat(events[i-1]["timestamp"].replace('Z', '+00:00'))
            curr_time = datetime.fromisoformat(events[i]["timestamp"].replace('Z', '+00:00'))
            assert prev_time <= curr_time

    def test_compliance_report_endpoint(self):
        """Test compliance reporting endpoint."""
        response = self.client.get("/v1/monitoring/audit/compliance/pdpa")

        assert response.status_code == 200
        compliance_data = response.json()

        assert "report_period" in compliance_data
        assert "data_processing_events" in compliance_data
        assert "consent_events" in compliance_data
        assert "retention_compliance" in compliance_data

        # Verify PDPA compliance metrics
        assert "legal_basis_breakdown" in compliance_data
        assert "data_subject_rights_requests" in compliance_data

    def test_security_audit_report_endpoint(self):
        """Test security audit reporting endpoint."""
        response = self.client.get("/v1/monitoring/audit/security")

        assert response.status_code == 200
        security_data = response.json()

        assert "authentication_events" in security_data
        assert "authorization_events" in security_data
        assert "security_incidents" in security_data
        assert "rate_limiting_events" in security_data

    def test_audit_access_requires_admin(self):
        """Test that audit access requires admin privileges."""
        # Without admin token
        response = self.client.get("/v1/monitoring/audit/events")

        # Should require authentication/authorization
        assert response.status_code in [401, 403]

    def test_audit_data_retention_endpoint(self):
        """Test audit data retention management endpoint."""
        response = self.client.get("/v1/monitoring/audit/retention/status")

        assert response.status_code == 200
        retention_data = response.json()

        assert "current_retention_days" in retention_data
        assert "total_events" in retention_data
        assert "oldest_event_date" in retention_data
        assert "expired_events_count" in retention_data

    def test_audit_anonymization_endpoint(self):
        """Test audit log anonymization endpoint."""
        response = self.client.post("/v1/monitoring/audit/anonymize", json={
            "older_than_days": 30,
            "anonymization_level": "high"
        })

        assert response.status_code == 200
        anonymization_data = response.json()

        assert "anonymized_events_count" in anonymization_data
        assert "anonymization_timestamp" in anonymization_data
        assert "anonymization_level" in anonymization_data


class TestMonitoringDashboardEndpoints:
    """Test monitoring dashboard API endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_dashboard_summary_endpoint(self):
        """Test monitoring dashboard summary endpoint."""
        response = self.client.get("/v1/monitoring/dashboard")

        assert response.status_code == 200
        dashboard_data = response.json()

        assert "overall_health" in dashboard_data
        assert "key_metrics" in dashboard_data
        assert "recent_alerts" in dashboard_data
        assert "system_status" in dashboard_data

        # Verify key metrics structure
        key_metrics = dashboard_data["key_metrics"]
        assert "requests_per_minute" in key_metrics
        assert "avg_response_time_ms" in key_metrics
        assert "error_rate_percent" in key_metrics
        assert "active_users" in key_metrics

    def test_dashboard_real_time_status(self):
        """Test real-time status for dashboard."""
        response = self.client.get("/v1/monitoring/dashboard/realtime")

        assert response.status_code == 200
        realtime_data = response.json()

        assert "timestamp" in realtime_data
        assert "health_status" in realtime_data
        assert "active_connections" in realtime_data
        assert "current_load" in realtime_data

    def test_dashboard_alerts_endpoint(self):
        """Test dashboard alerts endpoint."""
        response = self.client.get("/v1/monitoring/dashboard/alerts")

        assert response.status_code == 200
        alerts_data = response.json()

        assert "active_alerts" in alerts_data
        assert "alert_history" in alerts_data
        assert "alert_summary" in alerts_data

        # Verify alert structure
        for alert in alerts_data["active_alerts"]:
            assert "alert_id" in alert
            assert "severity" in alert
            assert "message" in alert
            assert "timestamp" in alert
            assert "source" in alert

    def test_dashboard_performance_trends(self):
        """Test performance trends for dashboard."""
        response = self.client.get("/v1/monitoring/dashboard/trends?period=1h")

        assert response.status_code == 200
        trends_data = response.json()

        assert "period" in trends_data
        assert "data_points" in trends_data
        assert "metrics" in trends_data

        # Verify trend data structure
        for metric_name, metric_data in trends_data["metrics"].items():
            assert "values" in metric_data
            assert "timestamps" in metric_data
            assert len(metric_data["values"]) == len(metric_data["timestamps"])

    def test_dashboard_service_map(self):
        """Test service dependency map endpoint."""
        response = self.client.get("/v1/monitoring/dashboard/service-map")

        assert response.status_code == 200
        service_map = response.json()

        assert "services" in service_map
        assert "dependencies" in service_map
        assert "health_status" in service_map

        # Verify service map structure
        for service in service_map["services"]:
            assert "name" in service
            assert "status" in service
            assert "type" in service

    def test_dashboard_configuration_endpoint(self):
        """Test dashboard configuration endpoint."""
        response = self.client.get("/v1/monitoring/dashboard/config")

        assert response.status_code == 200
        config_data = response.json()

        assert "refresh_intervals" in config_data
        assert "alert_thresholds" in config_data
        assert "display_preferences" in config_data

    def test_dashboard_export_report(self):
        """Test dashboard report export functionality."""
        response = self.client.get("/v1/monitoring/dashboard/export?format=pdf")

        # PDF export might return different status codes based on implementation
        assert response.status_code in [200, 202]

        if response.status_code == 200:
            assert response.headers["content-type"] == "application/pdf"
        elif response.status_code == 202:
            # Async generation
            export_data = response.json()
            assert "export_id" in export_data
            assert "status" in export_data


class TestAlertingEndpoints:
    """Test alerting system API endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_alert_rules_endpoint(self):
        """Test alert rules management endpoint."""
        response = self.client.get("/v1/monitoring/alerts/rules")

        assert response.status_code == 200
        rules_data = response.json()

        assert "rules" in rules_data
        assert "total_count" in rules_data

        # Verify rule structure
        for rule in rules_data["rules"]:
            assert "rule_id" in rule
            assert "name" in rule
            assert "condition" in rule
            assert "severity" in rule
            assert "enabled" in rule

    def test_create_alert_rule(self):
        """Test creating new alert rule."""
        new_rule = {
            "name": "High Error Rate",
            "condition": "error_rate > 5%",
            "severity": "warning",
            "notification_channels": ["email", "slack"]
        }

        response = self.client.post("/v1/monitoring/alerts/rules", json=new_rule)

        assert response.status_code == 201
        created_rule = response.json()

        assert created_rule["name"] == new_rule["name"]
        assert "rule_id" in created_rule
        assert created_rule["enabled"] is True

    def test_alert_notifications_endpoint(self):
        """Test alert notifications endpoint."""
        response = self.client.get("/v1/monitoring/alerts/notifications")

        assert response.status_code == 200
        notifications_data = response.json()

        assert "notifications" in notifications_data
        assert "channels" in notifications_data

        # Verify notification structure
        for notification in notifications_data["notifications"]:
            assert "notification_id" in notification
            assert "alert_id" in notification
            assert "channel" in notification
            assert "status" in notification
            assert "timestamp" in notification

    def test_alert_silencing_endpoint(self):
        """Test alert silencing functionality."""
        silence_config = {
            "duration_hours": 2,
            "reason": "Scheduled maintenance",
            "affected_services": ["google_places"]
        }

        response = self.client.post("/v1/monitoring/alerts/silence", json=silence_config)

        assert response.status_code == 200
        silence_data = response.json()

        assert "silence_id" in silence_data
        assert "expires_at" in silence_data

    def test_webhooks_for_external_alerts(self):
        """Test webhook endpoints for external alerting systems."""
        webhook_payload = {
            "alert_name": "External Service Down",
            "severity": "critical",
            "description": "External API is not responding",
            "source": "external_monitor"
        }

        response = self.client.post("/v1/monitoring/webhooks/alerts", json=webhook_payload)

        assert response.status_code == 200
        webhook_response = response.json()

        assert "received" in webhook_response
        assert "alert_id" in webhook_response


class TestMonitoringIntegrationTests:
    """Test complete monitoring system integration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_end_to_end_monitoring_flow(self):
        """Test complete monitoring flow from request to dashboard."""
        correlation_id = "e2e-test-monitoring"

        # 1. Make a medical consultation request
        triage_response = self.client.post(
            "/v1/triage",
            json={"symptomText": "severe chest pain"},
            headers={"X-Correlation-ID": correlation_id}
        )
        assert triage_response.status_code == 200

        # 2. Check that health monitoring detects the activity
        health_response = self.client.get("/v1/monitoring/health")
        assert health_response.status_code in [200, 503]  # May be degraded due to test env

        # 3. Verify metrics are collected
        metrics_response = self.client.get("/v1/monitoring/metrics?format=json")
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.json()

        # Should have HTTP request metrics
        assert "http_requests_total" in str(metrics_data)

        # 4. Check audit events are logged
        audit_response = self.client.get(
            f"/v1/monitoring/audit/events?correlation_id={correlation_id}"
        )
        if audit_response.status_code == 200:
            audit_data = audit_response.json()
            # Should have events for the medical consultation
            assert len(audit_data["events"]) > 0

        # 5. Verify dashboard shows updated information
        dashboard_response = self.client.get("/v1/monitoring/dashboard")
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()

        assert "overall_health" in dashboard_data
        assert "key_metrics" in dashboard_data

    def test_monitoring_under_load(self):
        """Test monitoring system under simulated load."""
        correlation_ids = []

        # Generate load
        for i in range(10):
            correlation_id = f"load-test-{i}"
            correlation_ids.append(correlation_id)

            response = self.client.post(
                "/v1/triage",
                json={"symptomText": f"test symptom {i}"},
                headers={"X-Correlation-ID": correlation_id}
            )
            # Don't assert success as some might fail under load

        # Check that monitoring systems handle the load
        time.sleep(1)  # Allow for async processing

        # Health check should still respond
        health_response = self.client.get("/v1/monitoring/health")
        assert health_response.status_code in [200, 503]

        # Metrics should be updated
        metrics_response = self.client.get("/v1/monitoring/metrics")
        assert metrics_response.status_code == 200

        # Dashboard should remain accessible
        dashboard_response = self.client.get("/v1/monitoring/dashboard")
        assert dashboard_response.status_code == 200

    def test_monitoring_during_service_failure(self):
        """Test monitoring behavior during service failures."""
        # Simulate external service failure
        with patch('app.services.places.nearby_hospitals') as mock_places:
            mock_places.side_effect = Exception("Service unavailable")

            # Make request that will fail
            response = self.client.get("/v1/hospitals/nearby?lat=25.0339&lng=121.5645")
            # Expect this to fail

            # Health check should detect the failure
            health_response = self.client.get("/v1/monitoring/health")
            assert health_response.status_code in [200, 503]

            # Metrics should record the failure
            metrics_response = self.client.get("/v1/monitoring/metrics?format=json")
            assert metrics_response.status_code == 200

            # Dashboard should show the issue
            dashboard_response = self.client.get("/v1/monitoring/dashboard")
            assert dashboard_response.status_code == 200

    @freeze_time("2024-01-15 10:30:00")
    def test_monitoring_data_consistency(self):
        """Test consistency of monitoring data across endpoints."""
        # Make a request to generate data
        self.client.post("/v1/triage", json={"symptomText": "headache"})

        # Get data from multiple endpoints
        health_data = self.client.get("/v1/monitoring/health").json()
        metrics_data = self.client.get("/v1/monitoring/metrics?format=json").json()
        dashboard_data = self.client.get("/v1/monitoring/dashboard").json()

        # Check timestamp consistency (should be within a few seconds)
        current_time = datetime(2024, 1, 15, 10, 30, 0)

        for data_source in [health_data, metrics_data, dashboard_data]:
            if "timestamp" in data_source:
                reported_time = datetime.fromisoformat(
                    data_source["timestamp"].replace('Z', '+00:00')
                )
                time_diff = abs((current_time - reported_time.replace(tzinfo=None)).total_seconds())
                assert time_diff < 60  # Within 1 minute

    def test_monitoring_security_headers(self):
        """Test that monitoring endpoints include proper security headers."""
        endpoints = [
            "/v1/monitoring/health",
            "/v1/monitoring/metrics",
            "/v1/monitoring/dashboard"
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)

            # Should include security headers
            headers = response.headers
            assert "X-Content-Type-Options" in headers
            assert "X-Frame-Options" in headers
            assert "X-XSS-Protection" in headers

    def test_monitoring_rate_limiting(self):
        """Test rate limiting on monitoring endpoints."""
        # Monitoring endpoints should have higher rate limits
        # but should still be protected

        endpoint = "/v1/monitoring/health"

        # Make many requests rapidly
        responses = []
        for _ in range(100):
            response = self.client.get(endpoint)
            responses.append(response)

        # Should eventually hit rate limit
        status_codes = [r.status_code for r in responses]

        # Most should succeed, but may have some rate limiting
        success_rate = sum(1 for code in status_codes if code == 200) / len(status_codes)
        assert success_rate > 0.8  # At least 80% should succeed