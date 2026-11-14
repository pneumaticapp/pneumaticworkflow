import { ApiError } from '../ApiError';

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
