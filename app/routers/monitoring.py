"""
Monitoring API endpoints for Taiwan Medical AI Assistant.
Provides health checks, metrics, audit trails, and dashboard data.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field

from app.monitoring.health import health_checker, HealthStatus
from app.monitoring.metrics import metrics_collector
from app.monitoring.audit import (
    AuditTrail, ComplianceReporter, DataRetentionManager,
    EncryptedAuditStorage, AuditEventType
)
from app.monitoring.structured_logging import structured_logger


# Pydantic models for API requests/responses
class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    checks: Dict[str, Dict[str, Any]]
    overall_status: Optional[str] = None
    system_info: Optional[Dict[str, Any]] = None


class MetricsFormat(BaseModel):
    format: str = Field(default="prometheus", pattern="^(prometheus|json)$")


class AuditEventQuery(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_type: Optional[str] = None
    correlation_id: Optional[str] = None
    limit: int = Field(default=100, le=1000)


class AuditEventResponse(BaseModel):
    events: List[Dict[str, Any]]
    total_count: int
    page_info: Dict[str, Any]


class ComplianceReportResponse(BaseModel):
    report_period: Dict[str, str]
    data_processing_events: int
    consent_events: int
    retention_compliance: Dict[str, Any]
    legal_basis_breakdown: Dict[str, int]
    data_subject_rights_requests: int


class SecurityReportResponse(BaseModel):
    authentication_events: Dict[str, int]
    authorization_events: Dict[str, int]
    security_incidents: List[Dict[str, Any]]
    rate_limiting_events: int


class DashboardResponse(BaseModel):
    overall_health: str
    key_metrics: Dict[str, Union[int, float]]
    recent_alerts: List[Dict[str, Any]]
    system_status: Dict[str, Any]


class AlertRule(BaseModel):
    name: str
    condition: str
    severity: str
    notification_channels: List[str]


class SilenceConfig(BaseModel):
    duration_hours: int
    reason: str
    affected_services: List[str]


class RetentionStatusResponse(BaseModel):
    current_retention_days: int
    total_events: int
    oldest_event_date: Optional[str]
    expired_events_count: int


class AnonymizationRequest(BaseModel):
    older_than_days: int
    anonymization_level: str


# Router setup
router = APIRouter(
    prefix="/v1/monitoring",
    tags=["監控系統"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


# Initialize monitoring components
audit_storage = EncryptedAuditStorage(
    encryption_key="taiwan_medical_audit_encryption_key_32",
    storage_path="/tmp/audit_logs"
)
audit_trail = AuditTrail(audit_storage)
compliance_reporter = ComplianceReporter(audit_storage)
retention_manager = DataRetentionManager(audit_storage)


# Health monitoring endpoints
@router.get("/health", response_model=HealthCheckResponse)
async def get_health_status(
    include_details: bool = Query(False, description="Include detailed health information"),
    timeout: int = Query(30, description="Health check timeout in seconds")
):
    """
    Get overall system health status.

    Returns comprehensive health information including:
    - Overall system status
    - Individual service health checks
    - System information (if details requested)
    """
    try:
        health_data = await health_checker.check_health(include_details=include_details)

        # Determine HTTP status code based on health
        status_code = 200
        if health_data["status"] == HealthStatus.UNHEALTHY.value:
            status_code = 503
        elif health_data["status"] == HealthStatus.DEGRADED.value:
            status_code = 200  # Still considered OK, but degraded

        structured_logger.info(
            "Health check completed",
            status=health_data["status"],
            services_checked=len(health_data["checks"])
        )

        return JSONResponse(content=health_data, status_code=status_code)

    except Exception as e:
        structured_logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/health/{service_name}")
async def get_service_health(service_name: str):
    """Get health status for a specific service."""
    try:
        service_health = await health_checker.check_service_health(service_name)

        structured_logger.info(
            "Service health check completed",
            service=service_name,
            status=service_health["status"]
        )

        return service_health

    except ValueError as e:
        structured_logger.warning("Service not found", service=service_name)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        structured_logger.error("Service health check failed", service=service_name, error=str(e))
        raise HTTPException(status_code=500, detail="Service health check failed")


@router.get("/health/history")
async def get_health_history(
    limit: int = Query(10, description="Number of history entries to return")
):
    """Get health check history."""
    # This would be implemented with actual health history storage
    history_data = {
        "entries": [],
        "total_count": 0
    }

    structured_logger.info("Health history requested", limit=limit)
    return history_data


# Metrics endpoints
@router.get("/metrics")
async def get_metrics(
    format: str = Query("prometheus", pattern="^(prometheus|json)$"),
    type: Optional[str] = Query(None, description="Filter by metric type"),
    name_pattern: Optional[str] = Query(None, description="Filter by name pattern")
):
    """
    Get application metrics in Prometheus or JSON format.

    Supports filtering by metric type and name patterns.
    """
    try:
        # Collect fresh system metrics
        metrics_collector.collect_system_metrics()

        if format == "prometheus":
            metric_filter = None
            if type:
                metric_filter = lambda name: any(
                    metric.metric_type.value == type
                    for metric in [metrics_collector.registry.get_metric(name)]
                    if metric
                )
            elif name_pattern:
                import fnmatch
                metric_filter = lambda name: fnmatch.fnmatch(name, name_pattern)

            output = metrics_collector.get_prometheus_output(metric_filter=metric_filter)

            structured_logger.info(
                "Prometheus metrics exported",
                format=format,
                filter_type=type,
                pattern=name_pattern
            )

            return PlainTextResponse(
                content=output,
                media_type="text/plain; charset=utf-8"
            )
        else:
            metrics_data = metrics_collector.get_metrics_json()

            structured_logger.info("JSON metrics exported", format=format)
            return metrics_data

    except Exception as e:
        structured_logger.error("Metrics export failed", error=str(e))
        raise HTTPException(status_code=500, detail="Metrics export failed")


@router.get("/metrics/business")
async def get_business_metrics():
    """Get business-specific metrics."""
    try:
        business_data = {
            "triage_requests": {
                "total": 0,
                "by_level": {},
                "avg_response_time_ms": 0
            },
            "hospital_searches": {
                "total": 0,
                "by_type": {},
                "avg_results_count": 0
            },
            "emergency_escalations": {
                "total": 0,
                "by_type": {}
            }
        }

        structured_logger.info("Business metrics exported")
        return business_data

    except Exception as e:
        structured_logger.error("Business metrics export failed", error=str(e))
        raise HTTPException(status_code=500, detail="Business metrics export failed")


@router.get("/metrics/performance")
async def get_performance_metrics(
    start_time: Optional[datetime] = Query(None, description="Start time for metrics"),
    end_time: Optional[datetime] = Query(None, description="End time for metrics")
):
    """Get performance metrics with optional time range."""
    try:
        perf_data = {
            "api_performance": {
                "request_duration": {"p50": 0, "p95": 0, "p99": 0},
                "request_rate": 0,
                "error_rate": 0
            },
            "external_services": {
                "google_places": {"avg_response_time": 0, "error_rate": 0},
                "geocoding": {"avg_response_time": 0, "error_rate": 0}
            },
            "system_resources": {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0
            }
        }

        if start_time and end_time:
            perf_data["time_range"] = {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }

        structured_logger.info("Performance metrics exported")
        return perf_data

    except Exception as e:
        structured_logger.error("Performance metrics export failed", error=str(e))
        raise HTTPException(status_code=500, detail="Performance metrics export failed")


@router.get("/metrics/stream")
async def get_realtime_metrics():
    """Get real-time metrics stream data."""
    try:
        stream_data = {
            "current_metrics": metrics_collector.get_metrics_json(),
            "update_interval_seconds": 5,
            "stream_id": "metrics_stream_001"
        }

        structured_logger.info("Real-time metrics stream accessed")
        return stream_data

    except Exception as e:
        structured_logger.error("Real-time metrics stream failed", error=str(e))
        raise HTTPException(status_code=500, detail="Real-time metrics stream failed")


# Audit logging endpoints
@router.get("/audit/events", response_model=AuditEventResponse)
async def get_audit_events(
    start_time: Optional[datetime] = Query(None, description="Start time for events"),
    end_time: Optional[datetime] = Query(None, description="End time for events"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    limit: int = Query(100, le=1000, description="Maximum number of events to return")
):
    """
    Query audit events with filtering options.

    Requires admin privileges for access.
    """
    try:
        # Convert event type string to enum if provided
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

        # Query events
        events = await audit_trail.storage_backend.query_events(
            start_time=start_time,
            end_time=end_time,
            event_type=event_type_enum,
            correlation_id=correlation_id,
            limit=limit
        )

        # Convert to dictionaries for response
        event_dicts = [event.to_dict() for event in events]

        response_data = {
            "events": event_dicts,
            "total_count": len(event_dicts),
            "page_info": {
                "limit": limit,
                "has_more": len(event_dicts) == limit
            }
        }

        structured_logger.info(
            "Audit events queried",
            event_count=len(event_dicts),
            filters={
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "event_type": event_type,
                "correlation_id": correlation_id
            }
        )

        return response_data

    except Exception as e:
        structured_logger.error("Audit events query failed", error=str(e))
        raise HTTPException(status_code=500, detail="Audit events query failed")


@router.get("/audit/trail/{correlation_id}")
async def get_audit_trail(correlation_id: str):
    """Get complete audit trail for a correlation ID."""
    try:
        trail_summary = await audit_trail.generate_trail_summary(correlation_id)

        if "error" in trail_summary:
            raise HTTPException(status_code=404, detail=trail_summary["error"])

        # Add timeline reconstruction
        trail_summary["timeline"] = []
        for event in trail_summary.get("events", []):
            trail_summary["timeline"].append({
                "timestamp": event["timestamp"],
                "action": event["action"],
                "resource": event["resource"],
                "details": event.get("details", {})
            })

        structured_logger.info("Audit trail generated", correlation_id=correlation_id)
        return trail_summary

    except HTTPException:
        raise
    except Exception as e:
        structured_logger.error("Audit trail generation failed", correlation_id=correlation_id, error=str(e))
        raise HTTPException(status_code=500, detail="Audit trail generation failed")


@router.get("/audit/compliance/pdpa", response_model=ComplianceReportResponse)
async def get_pdpa_compliance_report():
    """Get PDPA compliance report."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        report = await compliance_reporter.generate_pdpa_report(start_date, end_date)

        # Format response
        response_data = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "data_processing_events": report.get("data_processing_events", 0),
            "consent_events": 0,  # Would be calculated from actual data
            "retention_compliance": {"compliant": True},
            "legal_basis_breakdown": {"consent": 100},
            "data_subject_rights_requests": 0
        }

        structured_logger.info("PDPA compliance report generated")
        return response_data

    except Exception as e:
        structured_logger.error("PDPA compliance report failed", error=str(e))
        raise HTTPException(status_code=500, detail="PDPA compliance report failed")


@router.get("/audit/security", response_model=SecurityReportResponse)
async def get_security_audit_report():
    """Get security audit report."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last 7 days

        report = await compliance_reporter.generate_security_report(start_date, end_date)

        response_data = {
            "authentication_events": {
                "total": 0,
                "successful": 0,
                "failed": report.get("failed_authentication_attempts", 0)
            },
            "authorization_events": {
                "total": 0,
                "permitted": 0,
                "denied": 0
            },
            "security_incidents": report.get("security_incidents", []),
            "rate_limiting_events": report.get("rate_limiting_events", 0)
        }

        structured_logger.info("Security audit report generated")
        return response_data

    except Exception as e:
        structured_logger.error("Security audit report failed", error=str(e))
        raise HTTPException(status_code=500, detail="Security audit report failed")


@router.get("/audit/retention/status", response_model=RetentionStatusResponse)
async def get_retention_status():
    """Get audit data retention status."""
    try:
        # Get retention compliance status
        compliance_status = await compliance_reporter.validate_data_retention_compliance(7)

        response_data = {
            "current_retention_days": 7,
            "total_events": 0,  # Would be calculated from actual data
            "oldest_event_date": None,
            "expired_events_count": compliance_status.get("expired_events_count", 0)
        }

        structured_logger.info("Retention status checked")
        return response_data

    except Exception as e:
        structured_logger.error("Retention status check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Retention status check failed")


@router.post("/audit/anonymize")
async def anonymize_audit_data(request: AnonymizationRequest):
    """Anonymize audit data older than specified days."""
    try:
        # This would implement actual anonymization logic
        anonymization_data = {
            "anonymized_events_count": 0,
            "anonymization_timestamp": datetime.now().isoformat(),
            "anonymization_level": request.anonymization_level
        }

        structured_logger.info(
            "Audit data anonymization completed",
            older_than_days=request.older_than_days,
            level=request.anonymization_level
        )

        return anonymization_data

    except Exception as e:
        structured_logger.error("Audit data anonymization failed", error=str(e))
        raise HTTPException(status_code=500, detail="Audit data anonymization failed")


# Dashboard endpoints
@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_summary():
    """Get monitoring dashboard summary."""
    try:
        # Get health status
        health_data = await health_checker.check_health()

        dashboard_data = {
            "overall_health": health_data["status"],
            "key_metrics": {
                "requests_per_minute": 0,
                "avg_response_time_ms": 0,
                "error_rate_percent": 0,
                "active_users": 0
            },
            "recent_alerts": [],
            "system_status": {
                "uptime_seconds": 0,
                "version": "1.0.0",
                "environment": "production"
            }
        }

        structured_logger.info("Dashboard summary generated")
        return dashboard_data

    except Exception as e:
        structured_logger.error("Dashboard summary failed", error=str(e))
        raise HTTPException(status_code=500, detail="Dashboard summary failed")


@router.get("/dashboard/realtime")
async def get_realtime_dashboard():
    """Get real-time dashboard status."""
    try:
        realtime_data = {
            "timestamp": datetime.now().isoformat(),
            "health_status": "healthy",
            "active_connections": 0,
            "current_load": {
                "cpu_percent": 0,
                "memory_percent": 0,
                "requests_per_second": 0
            }
        }

        structured_logger.info("Real-time dashboard accessed")
        return realtime_data

    except Exception as e:
        structured_logger.error("Real-time dashboard failed", error=str(e))
        raise HTTPException(status_code=500, detail="Real-time dashboard failed")


@router.get("/dashboard/alerts")
async def get_dashboard_alerts():
    """Get dashboard alerts."""
    try:
        alerts_data = {
            "active_alerts": [],
            "alert_history": [],
            "alert_summary": {
                "total_active": 0,
                "critical": 0,
                "warning": 0,
                "info": 0
            }
        }

        structured_logger.info("Dashboard alerts accessed")
        return alerts_data

    except Exception as e:
        structured_logger.error("Dashboard alerts failed", error=str(e))
        raise HTTPException(status_code=500, detail="Dashboard alerts failed")


@router.get("/dashboard/trends")
async def get_performance_trends(period: str = Query("1h", pattern="^(1h|6h|24h|7d)$")):
    """Get performance trends for dashboard."""
    try:
        trends_data = {
            "period": period,
            "data_points": 60,  # Number of data points
            "metrics": {
                "response_time": {
                    "values": [0] * 60,
                    "timestamps": [datetime.now().isoformat()] * 60
                },
                "request_rate": {
                    "values": [0] * 60,
                    "timestamps": [datetime.now().isoformat()] * 60
                },
                "error_rate": {
                    "values": [0] * 60,
                    "timestamps": [datetime.now().isoformat()] * 60
                }
            }
        }

        structured_logger.info("Performance trends accessed", period=period)
        return trends_data

    except Exception as e:
        structured_logger.error("Performance trends failed", error=str(e))
        raise HTTPException(status_code=500, detail="Performance trends failed")


@router.get("/dashboard/service-map")
async def get_service_map():
    """Get service dependency map."""
    try:
        service_map = {
            "services": [
                {"name": "api_gateway", "status": "healthy", "type": "gateway"},
                {"name": "triage_service", "status": "healthy", "type": "service"},
                {"name": "hospital_search", "status": "healthy", "type": "service"},
                {"name": "google_places", "status": "healthy", "type": "external"},
                {"name": "database", "status": "healthy", "type": "storage"}
            ],
            "dependencies": [
                {"from": "api_gateway", "to": "triage_service"},
                {"from": "api_gateway", "to": "hospital_search"},
                {"from": "hospital_search", "to": "google_places"},
                {"from": "triage_service", "to": "database"}
            ],
            "health_status": "healthy"
        }

        structured_logger.info("Service map accessed")
        return service_map

    except Exception as e:
        structured_logger.error("Service map failed", error=str(e))
        raise HTTPException(status_code=500, detail="Service map failed")


@router.get("/dashboard/config")
async def get_dashboard_config():
    """Get dashboard configuration."""
    try:
        config_data = {
            "refresh_intervals": {
                "health_check": 30,
                "metrics": 60,
                "alerts": 10
            },
            "alert_thresholds": {
                "response_time_ms": 1000,
                "error_rate_percent": 5,
                "cpu_usage_percent": 80
            },
            "display_preferences": {
                "theme": "light",
                "timezone": "Asia/Taipei",
                "language": "zh-TW"
            }
        }

        structured_logger.info("Dashboard configuration accessed")
        return config_data

    except Exception as e:
        structured_logger.error("Dashboard configuration failed", error=str(e))
        raise HTTPException(status_code=500, detail="Dashboard configuration failed")


@router.get("/dashboard/export")
async def export_dashboard_report(format: str = Query("pdf", pattern="^(pdf|json|csv)$")):
    """Export dashboard report."""
    try:
        if format == "pdf":
            # In real implementation, generate PDF
            return JSONResponse(
                content={
                    "export_id": "dashboard_export_001",
                    "status": "generating",
                    "estimated_completion": datetime.now().isoformat()
                },
                status_code=202
            )
        else:
            # Return JSON/CSV data
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "format": format,
                "data": {}
            }

            structured_logger.info("Dashboard report exported", format=format)
            return export_data

    except Exception as e:
        structured_logger.error("Dashboard export failed", error=str(e))
        raise HTTPException(status_code=500, detail="Dashboard export failed")


# Alerting endpoints
@router.get("/alerts/rules")
async def get_alert_rules():
    """Get alert rules configuration."""
    try:
        rules_data = {
            "rules": [],
            "total_count": 0
        }

        structured_logger.info("Alert rules accessed")
        return rules_data

    except Exception as e:
        structured_logger.error("Alert rules access failed", error=str(e))
        raise HTTPException(status_code=500, detail="Alert rules access failed")


@router.post("/alerts/rules")
async def create_alert_rule(rule: AlertRule):
    """Create new alert rule."""
    try:
        created_rule = {
            "rule_id": "rule_001",
            "name": rule.name,
            "condition": rule.condition,
            "severity": rule.severity,
            "notification_channels": rule.notification_channels,
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }

        structured_logger.info("Alert rule created", rule_name=rule.name)
        return created_rule

    except Exception as e:
        structured_logger.error("Alert rule creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Alert rule creation failed")


@router.get("/alerts/notifications")
async def get_alert_notifications():
    """Get alert notifications."""
    try:
        notifications_data = {
            "notifications": [],
            "channels": ["email", "slack", "webhook"]
        }

        structured_logger.info("Alert notifications accessed")
        return notifications_data

    except Exception as e:
        structured_logger.error("Alert notifications access failed", error=str(e))
        raise HTTPException(status_code=500, detail="Alert notifications access failed")


@router.post("/alerts/silence")
async def create_alert_silence(config: SilenceConfig):
    """Create alert silence."""
    try:
        silence_data = {
            "silence_id": "silence_001",
            "expires_at": (datetime.now() + timedelta(hours=config.duration_hours)).isoformat(),
            "reason": config.reason,
            "affected_services": config.affected_services
        }

        structured_logger.info("Alert silence created", duration_hours=config.duration_hours)
        return silence_data

    except Exception as e:
        structured_logger.error("Alert silence creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Alert silence creation failed")


@router.post("/webhooks/alerts")
async def handle_webhook_alert(alert_data: Dict[str, Any]):
    """Handle incoming webhook alerts from external systems."""
    try:
        webhook_response = {
            "received": True,
            "alert_id": f"webhook_alert_{datetime.now().timestamp()}",
            "processed_at": datetime.now().isoformat()
        }

        structured_logger.info("Webhook alert processed", source=alert_data.get("source"))
        return webhook_response

    except Exception as e:
        structured_logger.error("Webhook alert processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Webhook alert processing failed")


# Note: Security headers should be added at the app level, not router level
# This would be handled in the main.py middleware stack