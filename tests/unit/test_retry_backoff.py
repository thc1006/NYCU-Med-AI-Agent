"""
測試指數退避重試機制
測試重點：
- 429/503 錯誤自動重試
- 指數退避計算正確
- 最大重試次數限制
- 成功後停止重試
"""

import pytest
import time
from unittest.mock import Mock, patch, call
import httpx
from app.utils.resilience import exponential_backoff_retry


class TestExponentialBackoff:
    """指數退避重試測試"""

    def test_successful_first_attempt(self):
        """測試第一次就成功不需重試"""
        mock_func = Mock(return_value={"status": "ok"})

        result = exponential_backoff_retry(
            mock_func,
            max_retries=3,
            base_delay=0.1
        )

        assert result == {"status": "ok"}
        assert mock_func.call_count == 1

    def test_retry_on_429_rate_limit(self):
        """測試 429 錯誤觸發重試"""
        mock_func = Mock(side_effect=[
            httpx.HTTPStatusError("Rate limited", request=Mock(), response=Mock(status_code=429)),
            httpx.HTTPStatusError("Rate limited", request=Mock(), response=Mock(status_code=429)),
            {"status": "ok"}
        ])

        with patch('time.sleep') as mock_sleep:
            result = exponential_backoff_retry(
                mock_func,
                max_retries=3,
                base_delay=0.1
            )

        assert result == {"status": "ok"}
        assert mock_func.call_count == 3
        # 驗證退避延遲：0.1秒, 0.2秒
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.1)
        mock_sleep.assert_any_call(0.2)

    def test_retry_on_503_service_unavailable(self):
        """測試 503 服務不可用觸發重試"""
        mock_func = Mock(side_effect=[
            httpx.HTTPStatusError("Service unavailable", request=Mock(), response=Mock(status_code=503)),
            {"status": "ok"}
        ])

        with patch('time.sleep') as mock_sleep:
            result = exponential_backoff_retry(
                mock_func,
                max_retries=3,
                base_delay=0.1
            )

        assert result == {"status": "ok"}
        assert mock_func.call_count == 2

    def test_max_retries_exceeded(self):
        """測試超過最大重試次數"""
        mock_func = Mock(side_effect=httpx.HTTPStatusError(
            "Rate limited",
            request=Mock(),
            response=Mock(status_code=429)
        ))

        with patch('time.sleep'):
            with pytest.raises(httpx.HTTPStatusError):
                exponential_backoff_retry(
                    mock_func,
                    max_retries=3,
                    base_delay=0.1
                )

        assert mock_func.call_count == 4  # 初始 + 3次重試

    def test_exponential_delay_calculation(self):
        """測試指數延遲計算"""
        mock_func = Mock(side_effect=[
            httpx.HTTPStatusError("Error", request=Mock(), response=Mock(status_code=429)),
            httpx.HTTPStatusError("Error", request=Mock(), response=Mock(status_code=429)),
            httpx.HTTPStatusError("Error", request=Mock(), response=Mock(status_code=429)),
            {"status": "ok"}
        ])

        with patch('time.sleep') as mock_sleep:
            result = exponential_backoff_retry(
                mock_func,
                max_retries=3,
                base_delay=1.0
            )

        # 驗證指數增長：1秒, 2秒, 4秒
        expected_delays = [1.0, 2.0, 4.0]
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays

    def test_max_delay_cap(self):
        """測試最大延遲上限"""
        mock_func = Mock(side_effect=[
            httpx.HTTPStatusError("Error", request=Mock(), response=Mock(status_code=429))
            for _ in range(10)
        ] + [{"status": "ok"}])

        with patch('time.sleep') as mock_sleep:
            result = exponential_backoff_retry(
                mock_func,
                max_retries=10,
                base_delay=1.0,
                max_delay=10.0
            )

        # 驗證沒有超過最大延遲
        for call in mock_sleep.call_args_list:
            assert call[0][0] <= 10.0

    def test_jitter_randomization(self):
        """測試抖動隨機化"""
        mock_func = Mock(side_effect=[
            httpx.HTTPStatusError("Error", request=Mock(), response=Mock(status_code=429)),
            httpx.HTTPStatusError("Error", request=Mock(), response=Mock(status_code=429)),
            {"status": "ok"}
        ])

        with patch('time.sleep') as mock_sleep:
            result = exponential_backoff_retry(
                mock_func,
                max_retries=3,
                base_delay=1.0,
                jitter=True
            )

        # 驗證延遲有隨機變化（不完全等於基礎值）
        delays = [call[0][0] for call in mock_sleep.call_args_list]
        # 帶抖動的延遲應該在 [0.5*base, 1.5*base] 範圍內
        assert 0.5 <= delays[0] <= 1.5  # 第一次重試
        assert 1.0 <= delays[1] <= 3.0  # 第二次重試

    def test_non_retryable_errors(self):
        """測試不可重試的錯誤"""
        mock_func = Mock(side_effect=httpx.HTTPStatusError(
            "Bad request",
            request=Mock(),
            response=Mock(status_code=400)
        ))

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            exponential_backoff_retry(
                mock_func,
                max_retries=3,
                base_delay=0.1
            )

        # 400 錯誤不應該重試
        assert mock_func.call_count == 1
        assert exc_info.value.response.status_code == 400

    def test_custom_retry_conditions(self):
        """測試自定義重試條件"""
        mock_func = Mock(side_effect=[
            httpx.ConnectTimeout("Timeout"),
            httpx.ReadTimeout("Timeout"),
            {"status": "ok"}
        ])

        def should_retry(exception):
            return isinstance(exception, (httpx.ConnectTimeout, httpx.ReadTimeout))

        with patch('time.sleep'):
            result = exponential_backoff_retry(
                mock_func,
                max_retries=3,
                base_delay=0.1,
                retry_condition=should_retry
            )

        assert result == {"status": "ok"}
        assert mock_func.call_count == 3

    def test_retry_with_callback(self):
        """測試重試回調函數"""
        retry_attempts = []

        def on_retry(attempt, delay, exception):
            retry_attempts.append({
                "attempt": attempt,
                "delay": delay,
                "error": str(exception)
            })

        mock_func = Mock(side_effect=[
            httpx.HTTPStatusError("Error", request=Mock(), response=Mock(status_code=429)),
            {"status": "ok"}
        ])

        with patch('time.sleep'):
            result = exponential_backoff_retry(
                mock_func,
                max_retries=3,
                base_delay=0.1,
                on_retry=on_retry
            )

        assert len(retry_attempts) == 1
        assert retry_attempts[0]["attempt"] == 1
        assert retry_attempts[0]["delay"] == 0.1

    def test_preserve_function_arguments(self):
        """測試保留函數參數"""
        mock_func = Mock(side_effect=[
            httpx.HTTPStatusError("Error", request=Mock(), response=Mock(status_code=429)),
            {"result": "success"}
        ])

        with patch('time.sleep'):
            result = exponential_backoff_retry(
                lambda: mock_func(arg1="test", arg2=123),
                max_retries=3,
                base_delay=0.1
            )

        assert result == {"result": "success"}
        # 驗證函數被調用時帶有正確參數
        mock_func.assert_called_with(arg1="test", arg2=123)