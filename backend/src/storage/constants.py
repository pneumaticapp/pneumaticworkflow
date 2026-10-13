from datetime import timedelta

MAX_FILE_ID_LENGTH = 512

UNNAMED_FILE = 'unnamed_file'

BINARY_CONTENT_TYPE = 'application/octet-stream'

FILE_ID_PATTERN = r'^[A-Za-z0-9_.-]{1,512}$'

CONTENT_TYPE_PATTERN = r'^[a-zA-Z0-9!#$&^_.+-]+/[a-zA-Z0-9!#$&^_.+-]+$'

FILENAME_PATTERN = r'^[^\x00-\x1f\x7f/\\\[\]()]{1,255}$'

STORAGE_TIMEOUT_SECONDS = 75

MAX_IMPORT_BYTES = 25 * 1024 * 1024

CLEANUP_FILE_ID_NAMESPACE = 'pneumatic:mcp:'

UPLOAD_SESSION_TTL = timedelta(hours=1)

CLEANUP_MIN_AGE = timedelta(hours=24)

LEASE_DURATION = timedelta(seconds=90)

RETRY_DELAY = timedelta(seconds=30)

IMPORT_MAX_ATTEMPTS = 5

IMPORT_MAX_RUNNING_PER_ACCOUNT = 2

DISPATCH_BATCH_SIZE = 100

CLEANUP_BATCH_SIZE = 100

STORAGE_IMPORT_PATH = '/internal/mcp/import'

STORAGE_CLEANUP_PATH = '/internal/mcp/cleanup'

UPLOAD_STATE_RETENTION = timedelta(days=30)
UPLOAD_PRUNE_BATCH_SIZE = 500
