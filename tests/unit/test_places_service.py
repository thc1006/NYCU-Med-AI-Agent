"""
測試地點搜尋服務
包含醫院搜尋、地點格式化等功能的完整測試
"""

import pytest
import respx
import httpx
from unittest.mock import patch, Mock
from app.services.places import (
    nearby_hospitals,
    format_hospital_results,
    PlaceResult,
    calculate_distance,
    nearby_hospitals_with_fallback,
    PlacesAPIError
)


class TestPlaceResult:
    """測試PlaceResult資料模型"""

    def test_place_result_creation(self):
        """測試：創建PlaceResult物件"""
        # Given
        result = PlaceResult(
            id="test_place_id",
            name="台大醫院",
            address="台北市中正區中山南路7號",
            latitude=25.0408,
            longitude=121.5129,
            distance_meters=500,
            phone="02-23123456",
            rating=4.5,
            is_open_now=True,
            opening_hours=["週一-週五 08:00-17:00"],
            business_status="OPERATIONAL"
        )

        # Then
        assert result.id == "test_place_id"
        assert result.name == "台大醫院"
        assert result.address == "台北市中正區中山南路7號"
        assert result.latitude == 25.0408
        assert result.longitude == 121.5129
        assert result.distance_meters == 500
        assert result.phone == "02-23123456"
        assert result.rating == 4.5
        assert result.is_open_now == True
        assert result.opening_hours == ["週一-週五 08:00-17:00"]
        assert result.business_status == "OPERATIONAL"

    def test_place_result_minimal_data(self):
        """測試：最小資料創建PlaceResult"""
        # Given
        result = PlaceResult(
            id="test_id",
            name="測試醫院",
            address="測試地址",
            latitude=25.0,
            longitude=121.5,
            distance_meters=1000
        )

        # Then
        assert result.id == "test_id"
        assert result.name == "測試醫院"
        assert result.phone is None
        assert result.rating is None
        assert result.is_open_now is None


class TestNearbyHospitals:
    """測試附近醫院搜尋功能"""

    @respx.mock
    def test_nearby_hospitals_success(self):
        """測試：附近醫院搜尋成功"""
        # Given
        lat, lng = 25.0330, 121.5654
        radius = 3000
        max_results = 10

        mock_response = {
            "places": [
                {
                    "id": "place_1",
                    "displayName": {"text": "台大醫院"},
                    "formattedAddress": "台北市中正區中山南路7號",
                    "location": {"latitude": 25.0408, "longitude": 121.5129},
                    "internationalPhoneNumber": "02-23123456",
                    "rating": 4.5,
                    "currentOpeningHours": {
                        "openNow": True,
                        "weekdayText": ["週一: 08:00–17:00"]
                    },
                    "businessStatus": "OPERATIONAL"
                },
                {
                    "id": "place_2",
                    "displayName": {"text": "馬偕醫院"},
                    "formattedAddress": "台北市中山區中山北路二段92號",
                    "location": {"latitude": 25.0630, "longitude": 121.5234}
                }
            ]
        }

        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # When
        results = nearby_hospitals(lat, lng, radius, max_results)

        # Then
        assert len(results) == 2
        assert results[0].name == "台大醫院"
        assert results[0].phone == "02-23123456"
        assert results[0].rating == 4.5
        assert results[0].is_open_now == True
        assert results[1].name == "馬偕醫院"

    @respx.mock
    def test_nearby_hospitals_no_results(self):
        """測試：無搜尋結果"""
        # Given
        lat, lng = 25.0330, 121.5654
        mock_response = {"places": []}

        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # When
        results = nearby_hospitals(lat, lng, 1000, 10)

        # Then
        assert results == []

    @respx.mock
    def test_nearby_hospitals_api_error(self):
        """測試：API錯誤"""
        # Given
        lat, lng = 25.0330, 121.5654

        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(400, json={"error": "Bad Request"})
        )

        # When
        results = nearby_hospitals(lat, lng, 1000, 10)

        # Then
        assert results == []

    @respx.mock
    def test_nearby_hospitals_network_error(self):
        """測試：網路錯誤"""
        # Given
        lat, lng = 25.0330, 121.5654

        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            side_effect=httpx.RequestError("Network error")
        )

        # When
        results = nearby_hospitals(lat, lng, 1000, 10)

        # Then
        assert results == []

    def test_nearby_hospitals_invalid_coordinates(self):
        """測試：無效座標"""
        # When
        results = nearby_hospitals(200, 200, 1000, 10)  # 超出有效範圍

        # Then
        assert results == []

    def test_nearby_hospitals_invalid_radius(self):
        """測試：無效半徑"""
        # When
        results = nearby_hospitals(25.0330, 121.5654, -1000, 10)  # 負數半徑

        # Then
        assert results == []

    def test_nearby_hospitals_invalid_max_results(self):
        """測試：無效最大結果數"""
        # When
        results = nearby_hospitals(25.0330, 121.5654, 1000, 0)  # 零結果

        # Then
        assert results == []


class TestNearbyHospitalsWithFallback:
    """測試附近醫院搜尋降級功能"""

    @respx.mock
    def test_nearby_hospitals_with_fallback_success(self):
        """測試：附近醫院搜尋成功"""
        # Given
        lat, lng = 25.0330, 121.5654

        mock_response = {
            "places": [
                {
                    "id": "place_1",
                    "displayName": {"text": "台大醫院"},
                    "formattedAddress": "台北市中正區中山南路7號",
                    "location": {"latitude": 25.0408, "longitude": 121.5129},
                    "internationalPhoneNumber": "02-23123456",
                    "rating": 4.5,
                    "currentOpeningHours": {
                        "openNow": True,
                        "weekdayDescriptions": ["週一: 08:00–17:00"]
                    },
                    "businessStatus": "OPERATIONAL"
                }
            ]
        }

        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # When
        result = nearby_hospitals_with_fallback(lat, lng, 3000, 10)

        # Then
        assert result["status"] == "ok"
        assert len(result["results"]) == 1
        assert result["results"][0].name == "台大醫院"

    def test_nearby_hospitals_with_fallback_static_fallback(self):
        """測試：靜態降級機制"""
        # When - 啟用級聯降級
        result = nearby_hospitals_with_fallback(25.0330, 121.5654, enable_cascade=True)

        # Then
        assert "results" in result
        assert "emergency_numbers" in result


class TestPlacesAPIError:
    """測試Places API錯誤物件"""

    def test_places_api_error_creation(self):
        """測試：創建PlacesAPIError物件"""
        # Given
        error = PlacesAPIError(
            "API key not valid",
            status_code=401,
            error_type="UNAUTHENTICATED"
        )

        # Then
        assert str(error) == "API key not valid"
        assert error.status_code == 401
        assert error.error_type == "UNAUTHENTICATED"

    def test_places_api_error_minimal(self):
        """測試：最小參數創建PlacesAPIError"""
        # Given
        error = PlacesAPIError("General error")

        # Then
        assert str(error) == "General error"
        assert error.status_code is None
        assert error.error_type is None


class TestFormatHospitalResults:
    """測試醫院結果格式化功能"""

    def test_format_hospital_results_success(self):
        """測試：格式化醫院結果成功"""
        # Given
        place_results = [
            PlaceResult(
                id="place_1",
                name="台大醫院",
                address="台北市中正區中山南路7號",
                latitude=25.0408,
                longitude=121.5129,
                distance_meters=500,
                phone="02-23123456",
                rating=4.5,
                is_open_now=True
            ),
            PlaceResult(
                id="place_2",
                name="馬偕醫院",
                address="台北市中山區中山北路二段92號",
                latitude=25.0630,
                longitude=121.5234,
                distance_meters=1200
            )
        ]

        # When
        formatted_result = format_hospital_results(place_results)

        # Then
        assert formatted_result["count"] == 2
        results = formatted_result["results"]
        assert len(results) == 2

        # 檢查第一個結果
        assert results[0]["name"] == "台大醫院"
        assert results[0]["address"] == "台北市中正區中山南路7號"
        assert results[0]["distance_meters"] == 500
        assert results[0]["phone"] == "02-23123456"
        assert results[0]["rating"] == 4.5
        assert results[0]["is_open_now"] == True

        # 檢查第二個結果
        assert results[1]["name"] == "馬偕醫院"
        assert results[1]["distance_meters"] == 1200
        assert "phone" not in results[1]  # 沒有電話號碼
        assert "rating" not in results[1]  # 沒有評分

    def test_format_hospital_results_empty_list(self):
        """測試：格式化空列表"""
        # When
        formatted_result = format_hospital_results([])

        # Then
        assert formatted_result["count"] == 0
        assert formatted_result["results"] == []

    def test_format_hospital_results_with_emergency_info(self):
        """測試：格式化結果含緊急資訊"""
        # Given
        place_results = [
            PlaceResult(
                id="place_1",
                name="台大醫院",
                address="台北市中正區中山南路7號",
                latitude=25.0408,
                longitude=121.5129,
                distance_meters=500
            )
        ]

        # When
        result = format_hospital_results(place_results, include_emergency_info=True)

        # Then
        assert "emergency_numbers" in result
        assert "emergency_reminder" in result
        assert "緊急情況請立即撥打 119" in result["emergency_reminder"]


class TestCalculateDistance:
    """測試距離計算功能"""

    def test_calculate_distance_same_point(self):
        """測試：相同點距離"""
        # Given
        lat1, lng1 = 25.0330, 121.5654
        lat2, lng2 = 25.0330, 121.5654

        # When
        distance = calculate_distance(lat1, lng1, lat2, lng2)

        # Then
        assert distance == 0.0

    def test_calculate_distance_known_points(self):
        """測試：已知點間距離"""
        # Given - 台北101到台北車站的大約距離
        taipei_101_lat, taipei_101_lng = 25.0340, 121.5645
        taipei_station_lat, taipei_station_lng = 25.0478, 121.5170

        # When
        distance = calculate_distance(
            taipei_101_lat, taipei_101_lng,
            taipei_station_lat, taipei_station_lng
        )

        # Then
        # 大約2-3公里的距離
        assert 2000 <= distance <= 4000

    def test_calculate_distance_invalid_coordinates(self):
        """測試：無效座標"""
        # When
        distance = calculate_distance(200, 200, 25.0330, 121.5654)

        # Then
        # 應該能處理但返回大距離值或錯誤
        assert distance >= 0

    def test_calculate_distance_negative_coordinates(self):
        """測試：負座標"""
        # Given - 南半球座標
        lat1, lng1 = -25.0330, -121.5654
        lat2, lng2 = -25.0340, -121.5645

        # When
        distance = calculate_distance(lat1, lng1, lat2, lng2)

        # Then
        assert distance >= 0


class TestPlacesErrorHandling:
    """測試地點服務錯誤處理"""

    @patch('app.services.places.httpx.post')
    def test_timeout_handling(self, mock_post):
        """測試：超時處理"""
        # Given
        mock_post.side_effect = httpx.TimeoutException("Request timeout")

        # When
        results = nearby_hospitals(25.0330, 121.5654, 1000, 10)

        # Then
        assert results == []

    @patch('app.services.places.httpx.post')
    def test_json_decode_error_handling(self, mock_post):
        """測試：JSON解析錯誤處理"""
        # Given
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        # When
        results = nearby_hospitals(25.0330, 121.5654, 1000, 10)

        # Then
        assert results == []

    @patch('app.services.places.httpx.post')
    def test_rate_limit_handling(self, mock_post):
        """測試：速率限制處理"""
        # Given
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        mock_post.return_value = mock_response

        # When
        results = nearby_hospitals(25.0330, 121.5654, 1000, 10)

        # Then
        assert results == []


class TestPlacesConfigurationHandling:
    """測試地點服務配置處理"""

    @patch('app.services.places.get_settings')
    def test_missing_api_key_handling(self, mock_get_settings):
        """測試：缺少API金鑰處理"""
        # Given
        mock_settings = Mock()
        mock_settings.google_places_api_key = None
        mock_get_settings.return_value = mock_settings

        # When
        results = nearby_hospitals(25.0330, 121.5654, 1000, 10)

        # Then
        assert results == []

    @patch('app.services.places.get_settings')
    def test_empty_api_key_handling(self, mock_get_settings):
        """測試：空API金鑰處理"""
        # Given
        mock_settings = Mock()
        mock_settings.google_places_api_key = ""
        mock_get_settings.return_value = mock_settings

        # When
        results = nearby_hospitals(25.0330, 121.5654, 1000, 10)

        # Then
        assert results == []