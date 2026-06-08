import { ApiError } from '../commonRequest';

describe('ApiError', () => {
  it('creates an instance with message, data, and status', () => {
    const error = new ApiError('Something failed', { code: 'ERR_001' }, 500);

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.message).toBe('Something failed');
    expect(error.data).toEqual({ code: 'ERR_001' });
    expect(error.status).toBe(500);
    expect(error.name).toBe('ApiError');
  });

  it('preserves file service error payload with code field', () => {
    const payload = {
      code: 'FILE_003',
      message: 'File size exceeds limit',
      details: { reason: 'Maximum allowed size is 100MB' },
    };
    const error = new ApiError('File size exceeds limit', payload, 413);

    expect(error.status).toBe(413);
    expect(error.data).toEqual(payload);
    expect((error.data as any).code).toBe('FILE_003');
  });

  it('preserves file service permission error', () => {
    const payload = {
      code: 'PERM_001',
      message: 'Permission denied',
    };
    const error = new ApiError('Permission denied', payload, 403);

    expect(error.status).toBe(403);
    expect((error.data as any).code).toBe('PERM_001');
  });

  it('handles string data as payload', () => {
    const error = new ApiError('Server error', 'Internal Server Error', 500);

    expect(error.data).toBe('Internal Server Error');
    expect(error.message).toBe('Server error');
  });

  it('handles null data as payload', () => {
    const error = new ApiError('Network error', null, undefined);

    expect(error.data).toBeNull();
    expect(error.status).toBeUndefined();
  });

  it('handles empty object as payload', () => {
    const error = new ApiError('Unknown', {}, 400);

    expect(error.data).toEqual({});
  });
});

/**
 * Tests for the error interceptor logic.
 *
 * The interceptor (commonRequest.ts:94-111) does:
 *   const data = error.response?.data;
 *   const payload = typeof data === 'string' ? { error: data } : data ?? {};
 *   const message = payload.message || payload.error || error.message;
 *   return Promise.reject(new ApiError(message, payload, error.response?.status));
 *
 * We test the logic inline since the actual interceptor is attached to an
 * axios instance that requires extensive mocking of config, env, and auth.
 */
describe('error interceptor logic (unit)', () => {
  // Replicate the interceptor's payload extraction logic
  function extractPayload(responseData: any) {
    const data = responseData;
    const payload = typeof data === 'string' ? { error: data } : data ?? {};
    return payload;
  }

  function extractMessage(payload: any, fallbackMessage: string) {
    return payload.message || payload.error || fallbackMessage;
  }

  it('extracts data from response.data object', () => {
    const data = { code: 'FILE_003', message: 'File size exceeds limit' };

    const payload = extractPayload(data);

    expect(payload).toEqual(data);
    expect(payload.code).toBe('FILE_003');
  });

  it('handles string data as { error: data }', () => {
    const data = 'Internal Server Error';

    const payload = extractPayload(data);

    expect(payload).toEqual({ error: 'Internal Server Error' });
  });

  it('handles null data as empty object', () => {
    const payload = extractPayload(null);

    expect(payload).toEqual({});
  });

  it('handles undefined data as empty object', () => {
    const payload = extractPayload(undefined);

    expect(payload).toEqual({});
  });

  it('creates ApiError with message from payload.message', () => {
    const payload = { code: 'FILE_003', message: 'File size exceeds limit' };
    const message = extractMessage(payload, 'Axios fallback');

    expect(message).toBe('File size exceeds limit');
  });

  it('falls back to payload.error when no message', () => {
    const payload = { error: 'Service unavailable' };
    const message = extractMessage(payload, 'Axios fallback');

    expect(message).toBe('Service unavailable');
  });

  it('falls back to error.message when no payload message/error', () => {
    const payload = {};
    const message = extractMessage(payload, 'Network Error');

    expect(message).toBe('Network Error');
  });

  it('preserves file service error format through pipeline', () => {
    // Simulate full interceptor flow for a File Service error
    const responseData = {
      code: 'FILE_003',
      message: 'File size exceeds limit',
      details: { reason: 'Maximum allowed size is 100MB' },
    };

    const payload = extractPayload(responseData);
    const message = extractMessage(payload, 'fallback');
    const error = new ApiError(message, payload, 413);

    // Verify the complete error matches what getErrorMessage expects
    expect(error.message).toBe('File size exceeds limit');
    expect(error.status).toBe(413);
    expect((error.data as any).code).toBe('FILE_003');
    expect((error.data as any).details.reason).toBe('Maximum allowed size is 100MB');
  });

  it('preserves code field from file service response (no camelCase)', () => {
    // Key test: error interceptor does NOT apply mapToCamelCase to errors
    // so 'code' stays 'code' (not transformed)
    const responseData = { code: 'AUTH_001', message: 'Authentication failed' };

    const payload = extractPayload(responseData);

    // 'code' is already camelCase-safe, but verify it's not mangled
    expect(payload.code).toBe('AUTH_001');
    expect(payload.message).toBe('Authentication failed');
  });
});
