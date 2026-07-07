import { ApiError } from '../commonRequest';

export function createApiError(responseData: unknown, status?: number): ApiError {
  const payload = typeof responseData === 'string' ? { error: responseData } : responseData ?? {};
  return new ApiError('', payload, status);
}
