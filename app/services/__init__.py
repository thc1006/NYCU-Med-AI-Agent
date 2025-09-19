"""
服務層套件
包含各種外部 API 整合與業務邏輯服務
"""

from .geocoding import (
    ip_geolocate,
    geocode_address,
    IPLocationResult,
    GeocodeResult,
    GeocodeError
)

__all__ = [
    "ip_geolocate",
    "geocode_address",
    "IPLocationResult",
    "GeocodeResult",
    "GeocodeError"
]