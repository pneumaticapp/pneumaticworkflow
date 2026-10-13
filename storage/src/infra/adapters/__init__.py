"""Infrastructure adapters (S3, external services)."""

from .storage_service import StorageService, StorageServiceHolder

__all__ = [
    'StorageService',
    'StorageServiceHolder',
]
