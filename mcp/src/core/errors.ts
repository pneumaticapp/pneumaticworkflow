export type ErrorCode =
  | 'invalid_arguments'
  | 'unauthorized'
  | 'forbidden'
  | 'not_found'
  | 'conflict'
  | 'validation_error'
  | 'rate_limited'
  | 'too_large'
  | 'not_configured'
  | 'source_error'
  | 'cancelled'
  | 'timeout'
  | 'unavailable'
  | 'invalid_response'
  | 'internal_error';

export const MESSAGES: Record<ErrorCode, string> = {
  invalid_arguments: 'Invalid tool arguments. Check the tool input schema.',
  unauthorized: 'The Pneumatic API key is invalid or was revoked. Reconnect with a valid key.',
  forbidden: 'The connected user cannot perform the requested action on this object.',
  not_found: 'The requested object does not exist or is unavailable to the connected user.',
  conflict: 'The request conflicts with the current object state.',
  validation_error: 'Pneumatic rejected the request. Check field values and the current object state.',
  rate_limited: 'Pneumatic is busy. Try again later.',
  too_large: 'The file exceeds the size limit.',
  not_configured: 'File storage is not configured for this connector (PNEUMATIC_FILES_URL).',
  source_error: 'The source URL could not be downloaded; nothing was uploaded to Pneumatic.',
  cancelled: 'The user did not confirm the action, so nothing was changed.',
  timeout: 'Pneumatic did not respond within the time limit.',
  unavailable: 'Pneumatic is temporarily unavailable.',
  invalid_response: 'Pneumatic returned an unexpected response.',
  internal_error: 'The tool could not be completed.',
};

export class ConnectorError extends Error {
  constructor(
    readonly code: ErrorCode,
    readonly detail?: string,
    readonly status?: number,
  ) {
    super(detail ?? MESSAGES[code]);
    this.name = 'ConnectorError';
  }
}
