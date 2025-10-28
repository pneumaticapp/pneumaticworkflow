import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock

import httpx

from tests.fixtures.e2e import AsyncIteratorMock


class TestLoadTesting:
    """Load testing scenarios"""

    def test_concurrent_uploads__100_requests__complete_within_30_seconds(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        auth_headers,
        mock_upload_use_case_execute,
    ):
        """Test 100 concurrent uploads"""
        # Arrange
        num_requests = 100
        results = []
        errors = []
        start_time = time.time()

        def upload_file(i):
            try:
                mock_upload_use_case_execute.return_value = MagicMock(
                    file_id=f'load-test-file-id-{i}',
                    public_url=f'http://localhost:8000/load-test-file-id-{i}',
                )

                response = e2e_client.post(
                    '/upload',
                    files={
                        'file': (
                            f'load_test_{i}.txt',
                            f'load test content {i}'.encode(),
                            'text/plain',
                        ),
                    },
                    headers=auth_headers,
                )
                results.append(
                    (i, response.status_code, time.time() - start_time),
                )
            except httpx.HTTPError as e:
                errors.append((i, str(e), time.time() - start_time))

        # Act
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(upload_file, i) for i in range(num_requests)
            ]

            for future in as_completed(futures):
                future.result()  # Wait for completion and handle exceptions

        end_time = time.time()
        total_time = end_time - start_time

        # Assert
        assert len(errors) == 0, f'Errors occurred: {errors}'
        assert len(results) == num_requests
        assert total_time < 30, (
            f'Test took {total_time:.2f} seconds, expected < 30'
        )

        # Check all responses are successful
        for i, status_code, response_time in results:
            assert status_code == 200, (
                f'Request {i} failed with status {status_code}'
            )
            assert response_time < 25, (
                f'Request {i} took {response_time:.2f} seconds'
            )

    def test_concurrent_downloads__50_requests__complete_within_15_seconds(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        auth_headers,
        mock_download_use_case_execute,
    ):
        """Test 50 concurrent downloads"""
        # Arrange
        num_requests = 50
        results = []
        errors = []
        start_time = time.time()

        def download_file(i):
            try:
                mock_record = MagicMock()
                mock_record.file_id = f'load-test-download-id-{i}'
                mock_record.filename = f'load_test_{i}.txt'
                mock_record.content_type = 'text/plain'
                mock_record.size = 20
                mock_download_use_case_execute.return_value = (
                    mock_record,
                    AsyncIteratorMock(f'load test content {i}'.encode()),
                )

                response = e2e_client.get(
                    f'/load-test-download-id-{i}',
                    headers=auth_headers,
                )
                results.append(
                    (i, response.status_code, time.time() - start_time),
                )
            except httpx.HTTPError as e:
                errors.append((i, str(e), time.time() - start_time))

        # Act
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(download_file, i) for i in range(num_requests)
            ]

            for future in as_completed(futures):
                future.result()

        end_time = time.time()
        total_time = end_time - start_time

        # Assert
        assert len(errors) == 0, f'Errors occurred: {errors}'
        assert len(results) == num_requests
        assert total_time < 15, (
            f'Test took {total_time:.2f} seconds, expected < 15'
        )

        # Check all responses are successful
        for i, status_code, response_time in results:
            assert status_code == 200, (
                f'Request {i} failed with status {status_code}'
            )
            assert response_time < 12, (
                f'Request {i} took {response_time:.2f} seconds'
            )

    def test_mixed_workload__upload_download_cycle__complete_within_60_seconds(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        auth_headers,
        mock_upload_use_case_execute,
        mock_download_use_case_execute,
    ):
        """Test mixed upload-download load"""
        # Arrange
        num_cycles = 100
        results = []
        errors = []
        start_time = time.time()

        def upload_download_cycle(i):
            try:
                # Upload phase
                mock_upload_use_case_execute.return_value = MagicMock(
                    file_id=f'mixed-workload-id-{i}',
                    public_url=f'http://localhost:8000/mixed-workload-id-{i}',
                )

                upload_response = e2e_client.post(
                    '/upload',
                    files={
                        'file': (
                            f'mixed_test_{i}.txt',
                            f'mixed workload content {i}'.encode(),
                            'text/plain',
                        ),
                    },
                    headers=auth_headers,
                )

                if upload_response.status_code != 200:
                    errors.append(
                        (
                            i,
                            f'Upload failed: {upload_response.status_code}',
                            time.time() - start_time,
                        ),
                    )
                    return

                # Download phase
                mock_record = MagicMock()
                mock_record.file_id = f'mixed-workload-id-{i}'
                mock_record.filename = f'mixed_test_{i}.txt'
                mock_record.content_type = 'text/plain'
                mock_record.size = 25
                mock_download_use_case_execute.return_value = (
                    mock_record,
                    AsyncIteratorMock(f'mixed workload content {i}'.encode()),
                )

                download_response = e2e_client.get(
                    f'/mixed-workload-id-{i}',
                    headers=auth_headers,
                )

                results.append(
                    (
                        i,
                        upload_response.status_code,
                        download_response.status_code,
                        time.time() - start_time,
                    ),
                )
            except httpx.HTTPError as e:
                errors.append((i, str(e), time.time() - start_time))

        # Act
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [
                executor.submit(upload_download_cycle, i)
                for i in range(num_cycles)
            ]

            for future in as_completed(futures):
                future.result()

        end_time = time.time()
        total_time = end_time - start_time

        # Assert
        assert len(errors) == 0, f'Errors occurred: {errors}'
        assert len(results) == num_cycles
        assert total_time < 60, (
            f'Test took {total_time:.2f} seconds, expected < 60'
        )

        # Check all cycles completed successfully
        for i, upload_status, download_status, cycle_time in results:
            assert upload_status == 200, (
                f'Upload {i} failed with status {upload_status}'
            )
            assert download_status == 200, (
                f'Download {i} failed with status {download_status}'
            )
            assert cycle_time < 55, f'Cycle {i} took {cycle_time:.2f} seconds'


class TestStressTesting:
    """Stress testing scenarios"""

    def test_extreme_concurrency__500_requests__system_remains_stable(
        self,
        e2e_client,
        mock_auth_middleware,
        mock_http_client,
        mock_storage_service,
        auth_headers,
        mock_upload_use_case_execute,
    ):
        """Test extreme concurrency"""
        # Arrange
        num_requests = 500
        results = []
        errors = []
        start_time = time.time()

        def extreme_upload(i):
            try:
                mock_upload_use_case_execute.return_value = MagicMock(
                    file_id=f'extreme-id-{i}',
                    public_url=f'http://localhost:8000/extreme-id-{i}',
                )

                response = e2e_client.post(
                    '/upload',
                    files={
                        'file': (
                            f'extreme_test_{i}.txt',
                            f'extreme content {i}'.encode(),
                            'text/plain',
                        ),
                    },
                    headers=auth_headers,
                )
                results.append(
                    (i, response.status_code, time.time() - start_time),
                )
            except httpx.HTTPError as e:
                errors.append((i, str(e), time.time() - start_time))

        # Act
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [
                executor.submit(extreme_upload, i) for i in range(num_requests)
            ]

            for future in as_completed(futures):
                future.result()

        end_time = time.time()
        total_time = end_time - start_time

        # Assert
        assert total_time < 120, (
            f'Test took {total_time:.2f} seconds, expected < 120'
        )

        # System should handle most requests successfully
        success_rate = len([r for r in results if r[1] == 200]) / num_requests
        assert success_rate > 0.8, f'Success rate {success_rate:.2%} too low'

        # Error rate should be reasonable
        error_rate = len(errors) / num_requests
        assert error_rate < 0.2, f'Error rate {error_rate:.2%} too high'
