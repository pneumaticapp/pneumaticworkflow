import { ApiError } from '../commonRequest';
import { createApiError } from '../utils/createApiError';

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

describe('error interceptor logic (unit)', () => {
  function extractPayload(responseData: any) {
    const data = responseData;
    const payload = typeof data === 'string' ? { error: data } : data ?? {};
    return payload;
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

  it('preserves file service error format through pipeline', () => {
    const responseData = {
      code: 'FILE_003',
      message: 'File size exceeds limit',
      details: { reason: 'Maximum allowed size is 100MB' },
    };

    const error = createApiError(responseData, 413);

    expect(error.message).toBe('File size exceeds limit');
    expect(error.status).toBe(413);
    expect((error.data as any).code).toBe('FILE_003');
    expect((error.data as any).details.reason).toBe('Maximum allowed size is 100MB');
  });

  it('preserves code field from file service response (no camelCase)', () => {
    const responseData = { code: 'AUTH_001', message: 'Authentication failed' };

    const payload = extractPayload(responseData);
    expect(payload.code).toBe('AUTH_001');
    expect(payload.message).toBe('Authentication failed');
  });
  it('copies payload.message to error.message via Object.assign', () => {
    const error = createApiError({ message: 'Permission denied', code: 'PERM_001' }, 403);

    expect(error.message).toBe('Permission denied');
    expect(error.status).toBe(403);
  });

  it('creates ApiError with empty message for payload without message field (regression #47550)', () => {
    const error = createApiError({ detail: 'Some technical error from Django' }, 500);

    expect(error.message).toBe('');
    expect(error.data).toEqual({ detail: 'Some technical error from Django' });
    expect(error.status).toBe(500);
  });
});

