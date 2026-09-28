import { ApiError } from '../commonRequest';

export function createApiError(responseData: unknown, status?: number): ApiError {
  let payload: unknown;
  if (typeof responseData === 'string') {
    try {
      payload = JSON.parse(responseData);
    } catch {
      payload = { error: responseData };
    }
  } else {
    payload = responseData ?? {};
  }
  return new ApiError('', payload, status);
}
