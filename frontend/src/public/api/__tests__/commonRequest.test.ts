import { createApiError } from '../utils/createApiError';

describe('error interceptor logic (unit)', () => {
  function extractPayload(responseData: any) {
    const data = responseData;
    const payload = typeof data === 'string' ? { error: data } : (data ?? {});
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

  it('parses JSON string into object instead of wrapping in { error } (responseType empty regression)', () => {
    const jsonString =
      '{"code":"validation_error","message":"Cannot delete a fieldset template that is used in templates.","details":{}}';

    const error = createApiError(jsonString, 400);

    expect(error.message).toBe('Cannot delete a fieldset template that is used in templates.');
    expect(error.status).toBe(400);
    expect((error.data as Record<string, unknown>).code).toBe('validation_error');
  });
});
