"""
Google Places Nearby Search 整合測試
測試重點：
- 使用 Places API (New) Nearby Search 查詢醫院
- 強制 languageCode=zh-TW, regionCode=TW
- includedTypes 包含 hospital
- 回傳格式化結果：名稱、地址、電話、評分、營業時間
- 錯誤處理：API KEY 無效、配額用盡、網路錯誤
- 距離排序與評分排序
"""

import pytest
import httpx
import respx
from app.services.places import nearby_hospitals, PlaceResult
from app.config import get_settings


class TestPlacesNearbySearch:
    """Google Places Nearby Search 測試類別"""

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """設定測試環境"""
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_places_api_key_12345")

    def test_nearby_hospitals_basic_search(self):
        """測試基本醫院搜尋功能"""
        with respx.mock:
            # 模擬 Google Places Nearby Search API 回應
            mock_response = {
                "places": [
                    {
                        "id": "ChIJK_1234567890",
                        "displayName": {"text": "台大醫院"},
                        "formattedAddress": "台北市中正區中山南路7號",
                        "internationalPhoneNumber": "+886 2 2312 3456",
                        "rating": 4.2,
                        "location": {
                            "latitude": 25.0408,
                            "longitude": 121.5149
                        },
                        "currentOpeningHours": {
                            "openNow": True,
                            "weekdayDescriptions": ["24 小時營業"]
                        },
                        "businessStatus": "OPERATIONAL"
                    },
                    {
                        "id": "ChIJL_0987654321",
                        "displayName": {"text": "榮民總醫院"},
                        "formattedAddress": "台北市北投區石牌路二段201號",
                        "internationalPhoneNumber": "+886 2 2875 7808",
                        "rating": 4.0,
                        "location": {
                            "latitude": 25.1172,
                            "longitude": 121.5240
                        },
                        "currentOpeningHours": {
                            "openNow": True,
                            "weekdayDescriptions": ["24 小時營業"]
                        },
                        "businessStatus": "OPERATIONAL"
                    }
                ]
            }

            # 模擬 Places API 請求
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            # 執行搜尋
            results = nearby_hospitals(
                lat=25.0339,
                lng=121.5645,
                radius=3000
            )

            # 驗證結果
            assert len(results) == 2
            assert results[0].name == "台大醫院"
            assert results[0].address == "台北市中正區中山南路7號"
            assert results[0].phone == "+886 2 2312 3456"
            assert results[0].rating == 4.2
            assert results[0].is_open_now is True
            assert results[0].latitude == 25.0408
            assert results[0].longitude == 121.5149

    def test_nearby_hospitals_taiwan_localization(self):
        """測試台灣在地化參數"""
        with respx.mock:
            # 捕獲實際請求以驗證參數
            request_captured = None

            def capture_request(request):
                nonlocal request_captured
                request_captured = request
                return httpx.Response(200, json={"places": []})

            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                side_effect=capture_request
            )

            # 執行搜尋
            nearby_hospitals(lat=25.0339, lng=121.5645, radius=5000)

            # 驗證請求參數
            assert request_captured is not None
            request_body = request_captured.content.decode('utf-8')

            # 驗證台灣在地化參數
            assert '"languageCode": "zh-TW"' in request_body
            assert '"regionCode": "TW"' in request_body
            assert '"includedTypes": ["hospital"]' in request_body

            # 驗證位置限制
            assert '"circle"' in request_body
            assert '"center"' in request_body
            assert '"latitude": 25.0339' in request_body
            assert '"longitude": 121.5645' in request_body
            assert '"radius": 5000' in request_body

    def test_nearby_hospitals_missing_fields_handling(self):
        """測試缺少欄位的處理"""
        with respx.mock:
            # 模擬部分資料缺失的回應
            mock_response = {
                "places": [
                    {
                        "id": "ChIJK_minimal",
                        "displayName": {"text": "小型診所"},
                        "formattedAddress": "台北市信義區信義路五段150號",
                        "location": {
                            "latitude": 25.0350,
                            "longitude": 121.5650
                        },
                        "businessStatus": "OPERATIONAL"
                        # 故意缺少 phone, rating, openingHours
                    }
                ]
            }

            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            results = nearby_hospitals(lat=25.0339, lng=121.5645, radius=3000)

            # 驗證缺少欄位的預設值
            assert len(results) == 1
            result = results[0]
            assert result.name == "小型診所"
            assert result.address == "台北市信義區信義路五段150號"
            assert result.phone is None  # 缺少電話
            assert result.rating is None  # 缺少評分
            assert result.is_open_now is None  # 缺少營業時間
            assert result.opening_hours == []  # 空的營業時間列表

    def test_nearby_hospitals_distance_calculation(self):
        """測試距離計算"""
        with respx.mock:
            mock_response = {
                "places": [
                    {
                        "id": "ChIJK_near",
                        "displayName": {"text": "近距離醫院"},
                        "formattedAddress": "台北市中正區重慶南路一段122號",
                        "location": {
                            "latitude": 25.0440,
                            "longitude": 121.5150
                        },
                        "businessStatus": "OPERATIONAL"
                    },
                    {
                        "id": "ChIJK_far",
                        "displayName": {"text": "遠距離醫院"},
                        "formattedAddress": "台北市士林區中山北路六段405號",
                        "location": {
                            "latitude": 25.1200,
                            "longitude": 121.5300
                        },
                        "businessStatus": "OPERATIONAL"
                    }
                ]
            }

            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            # 從台北車站座標搜尋
            results = nearby_hospitals(lat=25.0478, lng=121.5170, radius=10000)

            # 驗證距離計算 (近的醫院距離應該較短)
            assert len(results) == 2
            near_hospital = next(r for r in results if r.name == "近距離醫院")
            far_hospital = next(r for r in results if r.name == "遠距離醫院")

            assert near_hospital.distance_meters < far_hospital.distance_meters
            assert near_hospital.distance_meters > 0
            assert far_hospital.distance_meters > 0

    def test_nearby_hospitals_api_key_invalid(self):
        """測試 API KEY 無效錯誤"""
        with respx.mock:
            # 模擬 401 未授權錯誤
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(401, json={
                    "error": {
                        "code": 401,
                        "message": "API key not valid. Please pass a valid API key.",
                        "status": "UNAUTHENTICATED"
                    }
                })
            )

            # 驗證應該拋出適當的例外
            with pytest.raises(Exception) as exc_info:
                nearby_hospitals(lat=25.0339, lng=121.5645, radius=3000)

            assert "API key not valid" in str(exc_info.value)

    def test_nearby_hospitals_quota_exceeded(self):
        """測試配額超過錯誤"""
        with respx.mock:
            # 模擬 429 配額超過錯誤
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(429, json={
                    "error": {
                        "code": 429,
                        "message": "Quota exceeded.",
                        "status": "RESOURCE_EXHAUSTED"
                    }
                })
            )

            # 驗證應該拋出適當的例外
            with pytest.raises(Exception) as exc_info:
                nearby_hospitals(lat=25.0339, lng=121.5645, radius=3000)

            assert "Quota exceeded" in str(exc_info.value)

    def test_nearby_hospitals_network_timeout(self):
        """測試網路逾時錯誤"""
        with respx.mock:
            # 模擬網路逾時
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            # 驗證應該拋出適當的例外
            with pytest.raises(Exception) as exc_info:
                nearby_hospitals(lat=25.0339, lng=121.5645, radius=3000)

            assert "timeout" in str(exc_info.value).lower()

    def test_nearby_hospitals_empty_results(self):
        """測試空結果處理"""
        with respx.mock:
            # 模擬無結果回應
            mock_response = {"places": []}

            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            results = nearby_hospitals(lat=25.0339, lng=121.5645, radius=1000)

            # 驗證空結果
            assert isinstance(results, list)
            assert len(results) == 0

    def test_nearby_hospitals_radius_validation(self):
        """測試半徑參數驗證"""
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json={"places": []})
            )

            # 測試最小半徑
            results = nearby_hospitals(lat=25.0339, lng=121.5645, radius=100)
            assert isinstance(results, list)

            # 測試最大半徑
            results = nearby_hospitals(lat=25.0339, lng=121.5645, radius=50000)
            assert isinstance(results, list)

    def test_nearby_hospitals_coordinate_validation(self):
        """測試座標參數驗證"""
        with pytest.raises(ValueError):
            # 無效緯度 (超出範圍)
            nearby_hospitals(lat=95.0, lng=121.5645, radius=3000)

        with pytest.raises(ValueError):
            # 無效經度 (超出範圍)
            nearby_hospitals(lat=25.0339, lng=185.0, radius=3000)

    def test_nearby_hospitals_max_results_limit(self):
        """測試結果數量限制"""
        with respx.mock:
            # 模擬大量結果
            mock_places = []
            for i in range(25):  # 超過預期的 20 個限制
                mock_places.append({
                    "id": f"ChIJK_hospital_{i}",
                    "displayName": {"text": f"醫院 {i+1}"},
                    "formattedAddress": f"台北市信義區信義路五段{100+i}號",
                    "location": {
                        "latitude": 25.0339 + (i * 0.001),
                        "longitude": 121.5645 + (i * 0.001)
                    },
                    "businessStatus": "OPERATIONAL"
                })

            mock_response = {"places": mock_places}

            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            results = nearby_hospitals(lat=25.0339, lng=121.5645, radius=5000)

            # 驗證結果數量限制 (應該不超過合理數量，如 20)
            assert len(results) <= 20