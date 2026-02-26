"""Error messages constants."""

# Domain errors - File operations
MSG_FILE_001 = 'File not found'
MSG_FILE_002 = "File with ID '{file_id}' not found"
MSG_FILE_003 = "File with ID '{file_id}' not found in account {account_id}"
MSG_FILE_004 = 'Access to file denied'
MSG_FILE_005 = "User {user_id} has no access to file '{file_id}'"
MSG_FILE_006 = 'File size exceeds limit'
MSG_FILE_007 = 'File size {size} bytes exceeds limit {max_size} bytes'
MSG_FILE_008 = 'File already exists'

# Authentication errors
MSG_AUTH_001 = 'Authentication failed'
MSG_AUTH_003 = 'Token is expired'
MSG_AUTH_005 = 'Invalid token'
MSG_AUTH_007 = 'Token identification error'

# Permission errors
MSG_PERM_001 = 'Permission denied'
MSG_PERM_002 = 'Access denied for public tokens'

# Storage errors
MSG_STORAGE_001 = 'Failed to upload file to storage'
MSG_STORAGE_002 = 'Upload failed: {details}'
MSG_STORAGE_003 = 'Failed to download file from storage'
MSG_STORAGE_004 = 'Download failed: {details}'
MSG_STORAGE_005 = 'Failed to create storage bucket'
MSG_STORAGE_006 = 'Bucket creation failed: {details}'
MSG_STORAGE_007 = 'File not found in storage'
MSG_STORAGE_008 = "File '{file_path}' not found in bucket '{bucket_name}'"
MSG_STORAGE_009 = 'Failed create bucket: {details}'
MSG_STORAGE_010 = 'Failed to upload file: {details}'
MSG_STORAGE_011 = 'Failed to download file: {details}'

# Database errors
MSG_DB_001 = 'Database connection failed'
MSG_DB_002 = 'Database connection error: {details}'
MSG_DB_003 = 'Database operation failed'
MSG_DB_004 = "Database operation '{operation}' failed: {details}"
MSG_DB_005 = 'Database transaction failed'
MSG_DB_006 = 'Database transaction error: {details}'
MSG_DB_007 = 'Database constraint violation'
MSG_DB_008 = 'Constraint violation: {constraint} - {details}'
MSG_DB_009 = 'Database connection error during {operation}: {details}'
MSG_DB_010 = 'File record creation failed: {details}'

# External service errors
MSG_EXT_001 = 'Redis connection failed'
MSG_EXT_002 = 'Redis connection error: {details}'
MSG_EXT_003 = 'Redis operation failed'
MSG_EXT_004 = "Redis operation '{operation}' failed"
MSG_EXT_005 = 'HTTP client request failed'
MSG_EXT_006 = "HTTP request to '{url}' failed"
MSG_EXT_007 = 'HTTP request timeout'
MSG_EXT_008 = "HTTP request to '{url}' timed out after {timeout}s"
MSG_EXT_009 = 'External service unavailable'
MSG_EXT_011 = 'Failed to connect to Redis: {details}'
MSG_EXT_012 = 'Redis get operation failed for key "{key}": {details}'
MSG_EXT_013 = 'Failed to unpickle value for key "{key}": {details}'
MSG_EXT_014 = 'HTTP request failed: {details}'

# Validation errors
MSG_VAL_001 = 'Invalid file size'
MSG_VAL_003 = 'Invalid file type'
MSG_VAL_005 = 'Invalid token format'
MSG_VAL_007 = 'Missing required field'
MSG_VAL_009 = 'Invalid input format'
MSG_VAL_011 = 'Validation failed'
