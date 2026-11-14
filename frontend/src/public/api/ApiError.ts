import { InterceptorError } from './InterceptorError';

export class ApiError extends InterceptorError {
  status?: number;

  data?: unknown;

  [key: string]: unknown;

  constructor(message: string, payload: unknown, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.data = payload;
    this.status = status;
    if (payload && typeof payload === 'object') {
      Object.assign(this, payload);
    }
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}
