import { ConnectorError, MESSAGES, type ErrorCode } from '../core/errors.js';
import { PneumaticApiError } from '../pneumatic/client.js';

const STATUS_CODES: Record<number, ErrorCode> = {
  400: 'validation_error',
  401: 'unauthorized',
  403: 'forbidden',
  404: 'not_found',
  409: 'conflict',
  413: 'too_large',
  422: 'validation_error',
  429: 'rate_limited',
};

const RETRYABLE = new Set<ErrorCode>(['timeout', 'unavailable', 'rate_limited']);

// These failures guarantee that nothing was changed, so even writes can be retried.
const SAFE_TO_RETRY = new Set<ErrorCode>(['rate_limited']);

const UNCERTAIN = new Set<ErrorCode>(['timeout', 'unavailable', 'invalid_response', 'internal_error']);

const MAX_DETAIL_LENGTH = 1000;

export function toConnectorError(error: unknown): ConnectorError {
  if (error instanceof ConnectorError) {
    return error;
  }
  if (error instanceof PneumaticApiError) {
    const code = STATUS_CODES[error.status] ?? 'unavailable';
    // 4xx bodies are the user's own Pneumatic validation messages; they help the model fix its input.
    const detail = error.status < 500 && error.status !== 401 ? error.detail : undefined;
    return new ConnectorError(code, detail, error.status);
  }
  if (error instanceof DOMException && error.name === 'TimeoutError') {
    return new ConnectorError('timeout');
  }
  if (error instanceof TypeError && error.message === 'fetch failed') {
    return new ConnectorError('unavailable');
  }
  return new ConnectorError('internal_error');
}

export interface PublicError {
  code: ErrorCode;
  message: string;
  retryable: boolean;
  status?: number;
  detail?: string;
}

export function publicError(error: ConnectorError, isWrite: boolean): PublicError {
  let message = MESSAGES[error.code];
  if (isWrite && UNCERTAIN.has(error.code)) {
    message += ' The outcome may be unknown; check the current state before retrying the action.';
  }
  return {
    code: error.code,
    message,
    retryable: RETRYABLE.has(error.code) && (!isWrite || SAFE_TO_RETRY.has(error.code)),
    ...(error.status ? { status: error.status } : {}),
    ...(error.detail ? { detail: error.detail.slice(0, MAX_DETAIL_LENGTH) } : {}),
  };
}
