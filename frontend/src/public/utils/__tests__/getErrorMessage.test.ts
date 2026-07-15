import {
  getErrorMessage,
  isPaidFeatureError,
  normalizeToCustomError,
  UNKNOWN_ERROR,
  ICustomError,
} from '../getErrorMessage';

// --- Helper: creates an ApiError-shaped object (duck typing, no import) ---
function createApiError(
  message: string,
  data: Record<string, unknown>,
  status?: number,
): { message: string; data: Record<string, unknown>; status?: number; name: string } {
  const error = new Error(message) as Error & { data: Record<string, unknown>; status?: number };
  error.name = 'ApiError';
  error.data = data;
  error.status = status;
  return error;
}

// ========================================================================
// normalizeToCustomError
// ========================================================================
describe('normalizeToCustomError', () => {
  // --- Shape 1: ApiError (payload in .data) ---
  it('unwraps ApiError with code in .data', () => {
    const apiError = createApiError(
      'File not found',
      {
        code: 'FILE_001',
        message: 'File not found',
      },
      404,
    );

    const result = normalizeToCustomError(apiError);

    expect(result).toEqual({
      code: 'FILE_001',
      message: 'File not found',
      details: undefined,
    });
  });

  it('unwraps ApiError with details in .data', () => {
    const apiError = createApiError(
      'File size exceeds limit',
      {
        code: 'FILE_003',
        message: 'File size exceeds limit',
        details: { reason: 'Maximum allowed size is 100MB' },
      },
      413,
    );

    const result = normalizeToCustomError(apiError);

    expect(result).toEqual({
      code: 'FILE_003',
      message: 'File size exceeds limit',
      details: { reason: 'Maximum allowed size is 100MB' },
    });
  });

  it('uses Error.message when .data has no message', () => {
    const apiError = createApiError(
      'Axios level error',
      {
        code: 'INFRA_005',
      },
      500,
    );

    const result = normalizeToCustomError(apiError);

    expect(result?.code).toBe('INFRA_005');
    expect(result?.message).toBe('Axios level error');
  });

  it('unwraps ApiError with detail field in .data', () => {
    const apiError = createApiError(
      'Not found',
      {
        code: 'not_found',
        message: 'Not found',
        detail: 'Not found.',
      },
      404,
    );

    const result = normalizeToCustomError(apiError);

    expect(result?.detail).toBe('Not found.');
  });

  it('skips .data when payload has no code, message, or detail keys (e.g. { error: "..." })', () => {
    const apiError = createApiError(
      'Server Error',
      {
        error: 'Internal Server Error',
      },
      500,
    );

    const result = normalizeToCustomError(apiError);

    expect(result?.code).toBe('');
    expect(result?.message).toBe('Server Error');
  });

  it('uses err.detail when data has message key but detail only on error', () => {
    const apiError = createApiError('', { message: 'Validation failed' }, 400);
    Object.assign(apiError, { detail: 'Field is required' });

    const result = normalizeToCustomError(apiError);

    expect(result?.message).toBe('Validation failed');
    expect(result?.detail).toBe('Field is required');
  });

  // --- Shape 2: ICustomError (code + message at top level) ---
  it('returns ICustomError as-is when code and message are present', () => {
    const error: ICustomError = {
      code: 'error__processes__wrong_task',
      message: 'Wrong task',
    };

    const result = normalizeToCustomError(error);

    expect(result).toBe(error); // same reference, not a copy
  });

  it('returns object as-is when code and detail are present without message', () => {
    const error = {
      code: 'token_not_valid',
      detail: 'Given token not valid',
    };

    const result = normalizeToCustomError(error);

    expect(result).toBe(error);
    expect(result?.detail).toBe('Given token not valid');
  });

  // --- Shape 3: Error ---
  it('extracts message from plain Error', () => {
    const error = new Error('Network Error');

    const result = normalizeToCustomError(error);

    expect(result).toEqual({ code: '', message: 'Network Error' });
  });

  it('includes err.detail on Error when .data gate does not match', () => {
    const error = Object.assign(new Error(''), {
      detail: 'You do not have permission to perform this action.',
    });

    const result = normalizeToCustomError(error);

    expect(result).toEqual({
      code: '',
      message: '',
      detail: 'You do not have permission to perform this action.',
    });
  });

  // --- Edge cases ---
  it('returns undefined for null', () => {
    expect(normalizeToCustomError(null)).toBeUndefined();
  });

  it('returns undefined for undefined', () => {
    expect(normalizeToCustomError(undefined)).toBeUndefined();
  });

  it('returns undefined for primitive (number)', () => {
    expect(normalizeToCustomError(42)).toBeUndefined();
  });

  it('returns undefined for empty string', () => {
    expect(normalizeToCustomError('')).toBeUndefined();
  });

  it('returns undefined for object without code or message', () => {
    expect(normalizeToCustomError({ foo: 'bar' })).toBeUndefined();
  });
});

// ========================================================================
// getErrorMessage — ICustomError shape (direct objects)
// ========================================================================
describe('getErrorMessage', () => {
  it('returns UNKNOWN_ERROR when error is undefined', () => {
    expect(getErrorMessage(undefined)).toBe(UNKNOWN_ERROR);
  });

  it('returns UNKNOWN_ERROR when error is null', () => {
    expect(getErrorMessage(null)).toBe(UNKNOWN_ERROR);
  });

  it('returns message when code is not in errorMapper', () => {
    const error: ICustomError = {
      code: 'SOME_UNKNOWN_CODE',
      message: 'Server is on fire',
    };
    expect(getErrorMessage(error)).toBe('Server is on fire');
  });

  it('returns mapped value when code matches errorMapper (backend codes)', () => {
    const error: ICustomError = {
      code: 'error__processes__wrong_task',
      message: 'wrong task message',
    };
    expect(getErrorMessage(error)).toBe('task.not-found');
  });

  it('returns detail when no code/message mapper match', () => {
    const error = {
      code: 'unmapped_code',
      message: 'unmapped_message',
      detail: 'The actual detail string',
    } as ICustomError;
    expect(getErrorMessage(error)).toBe('The actual detail string');
  });

  it('returns detail from ApiError.data when Error.message is empty (DRF without code)', () => {
    const apiError = createApiError(
      '',
      {
        detail: 'You do not have permission to perform this action.',
      },
      403,
    );

    expect(getErrorMessage(apiError)).toBe('You do not have permission to perform this action.');
  });

  it('returns UNKNOWN_ERROR when message is empty and code not in mapper', () => {
    const error: ICustomError = {
      code: 'unmapped_code',
      message: '',
    };
    expect(getErrorMessage(error)).toBe(UNKNOWN_ERROR);
  });

  // --- File Service error codes (ICustomError shape) ---
  it('maps FILE_001 to file-service.file-not-found', () => {
    const error: ICustomError = { code: 'FILE_001', message: 'File not found' };
    expect(getErrorMessage(error)).toBe('file-service.file-not-found');
  });

  it('maps FILE_002 to file-service.access-denied', () => {
    const error: ICustomError = { code: 'FILE_002', message: 'Access denied' };
    expect(getErrorMessage(error)).toBe('file-service.access-denied');
  });

  it('maps FILE_003 to file-service.size-exceeded', () => {
    const error: ICustomError = { code: 'FILE_003', message: 'Size exceeded' };
    expect(getErrorMessage(error)).toBe('file-service.size-exceeded');
  });

  it('maps AUTH_001 to file-service.auth-failed', () => {
    const error: ICustomError = { code: 'AUTH_001', message: 'Auth failed' };
    expect(getErrorMessage(error)).toBe('file-service.auth-failed');
  });

  it('maps PERM_001 to file-service.permission-denied', () => {
    const error: ICustomError = { code: 'PERM_001', message: 'Permission denied' };
    expect(getErrorMessage(error)).toBe('file-service.permission-denied');
  });

  it('maps VAL_001 to file-service.invalid-file-size', () => {
    const error: ICustomError = { code: 'VAL_001', message: 'Invalid size' };
    expect(getErrorMessage(error)).toBe('file-service.invalid-file-size');
  });

  it('maps VAL_002 to file-service.missing-required-field', () => {
    const error: ICustomError = { code: 'VAL_002', message: 'Missing field' };
    expect(getErrorMessage(error)).toBe('file-service.missing-required-field');
  });

  it('maps STORAGE_002 to file-service.upload-failed', () => {
    const error: ICustomError = { code: 'STORAGE_002', message: 'Upload failed' };
    expect(getErrorMessage(error)).toBe('file-service.upload-failed');
  });

  it('maps STORAGE_003 to file-service.download-failed', () => {
    const error: ICustomError = { code: 'STORAGE_003', message: 'Download failed' };
    expect(getErrorMessage(error)).toBe('file-service.download-failed');
  });

  // --- File Service error codes through ApiError (REAL production shape) ---
  it('maps FILE_003 from ApiError.data to file-service.size-exceeded', () => {
    const apiError = createApiError(
      'File size exceeds limit',
      {
        code: 'FILE_003',
        message: 'File size exceeds limit',
      },
      413,
    );

    expect(getErrorMessage(apiError)).toBe('file-service.size-exceeded');
  });

  it('maps AUTH_001 from ApiError.data to file-service.auth-failed', () => {
    const apiError = createApiError(
      'Authentication failed',
      {
        code: 'AUTH_001',
        message: 'Authentication failed',
      },
      401,
    );

    expect(getErrorMessage(apiError)).toBe('file-service.auth-failed');
  });

  it('maps PERM_001 from ApiError.data to file-service.permission-denied', () => {
    const apiError = createApiError(
      'Permission denied',
      {
        code: 'PERM_001',
        message: 'Permission denied',
      },
      403,
    );

    expect(getErrorMessage(apiError)).toBe('file-service.permission-denied');
  });

  it('maps backend code from ApiError.data', () => {
    const apiError = createApiError(
      'wrong task message',
      {
        code: 'error__processes__wrong_task',
        message: 'wrong task message',
      },
      400,
    );

    expect(getErrorMessage(apiError)).toBe('task.not-found');
  });

  it('falls back to ApiError.data.message for unmapped codes', () => {
    const apiError = createApiError(
      'DB error',
      {
        code: 'DB_001',
        message: 'Database connection error',
      },
      503,
    );

    expect(getErrorMessage(apiError)).toBe('Database connection error');
  });

  it('falls back to Error.message for plain Errors', () => {
    const error = new Error('Network Error');
    expect(getErrorMessage(error)).toBe('Network Error');
  });

  // --- Infrastructure codes — fallback ---
  it('falls back to message for unmapped infrastructure code DB_001', () => {
    const error: ICustomError = { code: 'DB_001', message: 'Database connection error' };
    expect(getErrorMessage(error)).toBe('Database connection error');
  });

  it('falls back to message for unmapped code INFRA_005', () => {
    const error: ICustomError = { code: 'INFRA_005', message: 'Internal server error' };
    expect(getErrorMessage(error)).toBe('Internal server error');
  });

  // --- Details handling ---
  it('appends details.name + details.reason when both present and reason differs from message', () => {
    const error: ICustomError = {
      code: 'some_backend_code',
      message: 'Validation error',
      details: {
        name: 'email',
        reason: 'Email is required',
      },
    };
    expect(getErrorMessage(error)).toBe('Validation error\nemail: Email is required');
  });

  it('does not append details when reason matches message', () => {
    const error: ICustomError = {
      code: 'some_backend_code',
      message: 'Email is required',
      details: {
        name: 'email',
        reason: 'Email is required',
      },
    };
    expect(getErrorMessage(error)).toBe('Email is required');
  });

  it('appends details.reason without name when name is missing (File Service pattern)', () => {
    const error = {
      code: 'unmapped_fs_code',
      message: 'Some error occurred',
      details: {
        reason: 'Storage unavailable',
      },
    } as ICustomError;
    expect(getErrorMessage(error)).toBe('Some error occurred\nStorage unavailable');
  });

  it('does not append File Service details when reason matches message', () => {
    const error = {
      code: 'unmapped_fs_code',
      message: 'Storage unavailable',
      details: {
        reason: 'Storage unavailable',
      },
    } as ICustomError;
    expect(getErrorMessage(error)).toBe('Storage unavailable');
  });

  it('handles ApiError.data with details (File Service full payload)', () => {
    const apiError = createApiError(
      'File size exceeds limit',
      {
        code: 'unmapped_storage_code',
        message: 'Upload failed',
        details: { reason: 'Maximum allowed size is 100MB' },
      },
      503,
    );

    expect(getErrorMessage(apiError)).toBe('Upload failed\nMaximum allowed size is 100MB');
  });

  // --- Edge cases ---
  it('returns empty string for error__payment__subscription_expired', () => {
    const error: ICustomError = {
      code: 'error__payment__subscription_expired',
      message: 'Subscription expired',
    };
    expect(getErrorMessage(error)).toBe('');
  });

  it('returns mapped message via message key when code is unmapped but message is in mapper', () => {
    const error: ICustomError = {
      code: 'random_code',
      message: 'Failed to fetch',
    };
    expect(getErrorMessage(error)).toBe('error.fetch-failed');
  });
});

// ========================================================================
// isPaidFeatureError
// ========================================================================
describe('isPaidFeatureError', () => {
  it('returns true for error__conditions__paid_feature (ICustomError)', () => {
    const error: ICustomError = {
      code: 'error__conditions__paid_feature',
      message: 'Paid feature',
    };
    expect(isPaidFeatureError(error)).toBe(true);
  });

  it('returns true for error__template__public_is_paid_feature (ICustomError)', () => {
    const error: ICustomError = {
      code: 'error__template__public_is_paid_feature',
      message: 'Paid feature',
    };
    expect(isPaidFeatureError(error)).toBe(true);
  });

  it('returns true for paid feature error via ApiError.data', () => {
    const apiError = createApiError(
      'Paid feature',
      {
        code: 'error__conditions__paid_feature',
        message: 'Paid feature',
      },
      403,
    );

    expect(isPaidFeatureError(apiError)).toBe(true);
  });

  it('returns false for non-paid feature error', () => {
    const error: ICustomError = {
      code: 'FILE_001',
      message: 'File not found',
    };
    expect(isPaidFeatureError(error)).toBe(false);
  });

  it('returns false for non-paid feature ApiError', () => {
    const apiError = createApiError(
      'File not found',
      {
        code: 'FILE_001',
        message: 'File not found',
      },
      404,
    );

    expect(isPaidFeatureError(apiError)).toBe(false);
  });

  it('returns false for undefined error', () => {
    expect(isPaidFeatureError(undefined)).toBe(false);
  });

  it('returns false for null error', () => {
    expect(isPaidFeatureError(null)).toBe(false);
  });
});
