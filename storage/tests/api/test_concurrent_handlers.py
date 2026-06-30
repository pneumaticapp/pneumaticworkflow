"""Tests for concurrent request handling (mocked I/O)."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock

import httpx
import pytest

from tests.fixtures.e2e import AsyncIteratorMock


def _make_upload_side_effect(prefix):
    """Thread-safe side_effect for upload mock.

    Each call gets a unique file_id based on thread-local index,
    avoiding race conditions from shared return_value mutation.
    """
    _counter = {'value': 0}
    _lock = threading.Lock()

    def _side_effect(*args, **kwargs):
        with _lock:
            idx = _counter['value']
            _counter['value'] += 1
        return MagicMock(
            file_id=f'{prefix}-1234-5678-1234-{idx:012d}',
            public_url=(
                f'http://localhost:8000/{prefix}-1234-5678-1234-{idx:012d}'
            ),
        )

    return _side_effect


@pytest.mark.slow
def test_concurrent_uploads__100_reqs__under_30s(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_upload_use_case_execute,
):
    # arrange
    num_requests = 100
    results = []
    errors = []
    start_time = time.time()

    mock_upload_use_case_execute.side_effect = _make_upload_side_effect(
        '12345678',
    )

    def upload_file(i):
        try:
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
                (
                    i,
                    response.status_code,
                    time.time() - start_time,
                )
            )
        except httpx.HTTPError as e:
            errors.append(
                (
                    i,
                    str(e),
                    time.time() - start_time,
                )
            )

    # act
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(upload_file, i) for i in range(num_requests)
        ]
        for future in as_completed(futures):
            future.result()

    total_time = time.time() - start_time

    # assert
    assert len(errors) == 0, f'Errors: {errors}'
    assert len(results) == num_requests
    assert total_time < 30, f'Took {total_time:.2f}s, expected < 30'
    for i, status_code, resp_time in results:
        assert status_code == 200, f'Req {i} failed: {status_code}'
        assert resp_time < 25, f'Req {i} took {resp_time:.2f}s'


@pytest.mark.slow
def test_concurrent_downloads__50_reqs__under_15s(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    # arrange
    num_requests = 50
    results = []
    errors = []
    start_time = time.time()

    def _metadata_side_effect(*args, **kwargs):
        mock_record = MagicMock()
        mock_record.file_id = '22345678-1234-5678-1234-000000000000'
        mock_record.filename = 'load_test.txt'
        mock_record.content_type = 'text/plain'
        mock_record.size = 20
        mock_record.user_id = 1
        return mock_record

    def _stream_side_effect(*args, **kwargs):
        return AsyncIteratorMock(b'load test content')

    mock_download_use_case_get_metadata.side_effect = _metadata_side_effect
    mock_download_use_case_get_stream.side_effect = _stream_side_effect

    def download_file(i):
        try:
            response = e2e_client.get(
                f'/22345678-1234-5678-1234-{i:012d}',
                headers=auth_headers,
            )
            results.append(
                (
                    i,
                    response.status_code,
                    time.time() - start_time,
                )
            )
        except httpx.HTTPError as e:
            errors.append(
                (
                    i,
                    str(e),
                    time.time() - start_time,
                )
            )

    # act
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(download_file, i) for i in range(num_requests)
        ]
        for future in as_completed(futures):
            future.result()

    total_time = time.time() - start_time

    # assert
    assert len(errors) == 0, f'Errors: {errors}'
    assert len(results) == num_requests
    assert total_time < 15, f'Took {total_time:.2f}s, expected < 15'
    for i, status_code, resp_time in results:
        assert status_code == 200, f'Req {i} failed: {status_code}'
        assert resp_time < 12, f'Req {i} took {resp_time:.2f}s'


@pytest.mark.slow
def test_mixed_workload__100_cycles__under_60s(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_upload_use_case_execute,
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
):
    # arrange
    num_cycles = 100
    results = []
    errors = []
    start_time = time.time()

    mock_upload_use_case_execute.side_effect = _make_upload_side_effect(
        '32345678',
    )

    def _metadata_side_effect(*args, **kwargs):
        mock_record = MagicMock()
        mock_record.file_id = '32345678-1234-5678-1234-000000000000'
        mock_record.filename = 'mixed.txt'
        mock_record.content_type = 'text/plain'
        mock_record.size = 25
        mock_record.user_id = 1
        return mock_record

    def _stream_side_effect(*args, **kwargs):
        return AsyncIteratorMock(b'mixed content')

    mock_download_use_case_get_metadata.side_effect = _metadata_side_effect
    mock_download_use_case_get_stream.side_effect = _stream_side_effect

    def upload_download_cycle(i):
        try:
            upload_resp = e2e_client.post(
                '/upload',
                files={
                    'file': (
                        f'mixed_{i}.txt',
                        f'mixed content {i}'.encode(),
                        'text/plain',
                    ),
                },
                headers=auth_headers,
            )

            if upload_resp.status_code != 200:
                errors.append(
                    (
                        i,
                        f'Upload: {upload_resp.status_code}',
                        time.time() - start_time,
                    )
                )
                return

            dl_resp = e2e_client.get(
                f'/32345678-1234-5678-1234-{i:012d}',
                headers=auth_headers,
            )

            results.append(
                (
                    i,
                    upload_resp.status_code,
                    dl_resp.status_code,
                    time.time() - start_time,
                )
            )
        except httpx.HTTPError as e:
            errors.append(
                (
                    i,
                    str(e),
                    time.time() - start_time,
                )
            )

    # act
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [
            executor.submit(upload_download_cycle, i)
            for i in range(num_cycles)
        ]
        for future in as_completed(futures):
            future.result()

    total_time = time.time() - start_time

    # assert
    assert len(errors) == 0, f'Errors: {errors}'
    assert len(results) == num_cycles
    assert total_time < 60, f'Took {total_time:.2f}s, expected < 60'
    for i, up_status, dl_status, cycle_time in results:
        assert up_status == 200, f'Upload {i}: {up_status}'
        assert dl_status == 200, f'Download {i}: {dl_status}'
        assert cycle_time < 55, f'Cycle {i}: {cycle_time:.2f}s'


@pytest.mark.slow
def test_extreme_concurrency__500_reqs__stable(
    e2e_client,
    mock_auth_middleware,
    mock_http_client,
    mock_storage_service,
    auth_headers,
    mock_upload_use_case_execute,
):
    # arrange
    num_requests = 500
    results = []
    errors = []
    start_time = time.time()

    mock_upload_use_case_execute.side_effect = _make_upload_side_effect(
        '42345678',
    )

    def extreme_upload(i):
        try:
            response = e2e_client.post(
                '/upload',
                files={
                    'file': (
                        f'extreme_{i}.txt',
                        f'extreme content {i}'.encode(),
                        'text/plain',
                    ),
                },
                headers=auth_headers,
            )
            results.append(
                (
                    i,
                    response.status_code,
                    time.time() - start_time,
                )
            )
        except httpx.HTTPError as e:
            errors.append(
                (
                    i,
                    str(e),
                    time.time() - start_time,
                )
            )

    # act
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [
            executor.submit(extreme_upload, i) for i in range(num_requests)
        ]
        for future in as_completed(futures):
            future.result()

    total_time = time.time() - start_time

    # assert
    assert total_time < 120, f'Took {total_time:.2f}s, expected < 120'
    success_count = len(
        [r for r in results if r[1] == 200],
    )
    total = success_count + len(errors)
    success_rate = success_count / total
    assert success_rate > 0.99, f'Success rate {success_rate:.2%} too low'
    assert len(errors) == 0, f'{len(errors)} transport errors: {errors[:5]}'
