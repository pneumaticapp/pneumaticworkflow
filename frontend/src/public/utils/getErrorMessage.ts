export interface ICustomError {
  code: string;
  message: string;
  details?: {
    name?: string;
    api_name?: string;
    reason: string;
  };
  detail?: string;
}

const BLANK_VALUE_ERROR = 'value: this field may not be blank.';
const CHECKLIST_ITEM_API_NAME_PREFIX = 'citem-';

export const DEFAULT_ERROR_CODE = 'error__unknown_code';
export const UNKNOWN_ERROR = 'Something Went Wrong';

const paidFeaturesErrors = ['error__conditions__paid_feature', 'error__template__public_is_paid_feature'];

const errorMapper: { [key: string]: string } = {
  [DEFAULT_ERROR_CODE]: UNKNOWN_ERROR,
  error__processes__wrong_task: 'task.not-found',
  error__google_invites__no_gsuite: 'users.google-invites-failed-domain',
  error__google_invites__failed_domain: 'users.google-invites-no-gsuite',
  error__payment__subscription_expired: '',
  error__conditions__paid_feature: 'templates.conditions.buy-plan-modal',
  error__template__public_is_paid_feature: 'template.kick-off-form-share.paid-feature',
  'Failed to fetch': 'error.fetch-failed',

  // File Service error codes
  FILE_001: 'file-service.file-not-found',
  FILE_002: 'file-service.access-denied',
  FILE_003: 'file-service.size-exceeded',
  AUTH_001: 'file-service.auth-failed',
  PERM_001: 'file-service.permission-denied',
  VAL_001: 'file-service.invalid-file-size',
  VAL_002: 'file-service.missing-required-field',
  STORAGE_002: 'file-service.upload-failed',
  STORAGE_003: 'file-service.download-failed',

  'Checklist items not exists or invalid.': 'validation.checklist-items-invalid',
};

const mapValidationMessage = (normalized: ICustomError): string | undefined => {
  const messageLower = normalized.message?.trim()?.toLowerCase() || '';
  const reasonLower = normalized.details?.reason?.trim()?.toLowerCase() || '';
  const isBlankValueError = messageLower === BLANK_VALUE_ERROR || reasonLower === BLANK_VALUE_ERROR;

  if (!isBlankValueError) {
    return undefined;
  }

  const apiName = normalized.details?.api_name || '';
  if (apiName.startsWith(CHECKLIST_ITEM_API_NAME_PREFIX)) {
    return 'validation.checklist-item-empty';
  }

  return 'validation.field-empty';
};

/**
 * Normalize any error shape to ICustomError.
 *
 * Handles three error shapes that exist in the codebase:
 *
 * 1. ApiError (from axios interceptor) — payload sits in `.data`:
 *    File Service: { data: { code: "FILE_003", message: "..." }, status: 413 }
 *    Django/DRF:   { data: { detail: "..." }, status: 4xx } — often no code
 *
 * 2. Plain ICustomError (from auth saga resolved promises):
 *    { code: "error__processes__wrong_task", message: "Wrong task" }
 *
 * 3. Native Error (from throws, network errors):
 *    { message: "Network Error" } — detail may sit on error from Object.assign
 *
 * Uses duck typing — no coupling to ApiError class.
 */
export function normalizeToCustomError(error: unknown): ICustomError | undefined {
  if (!error || typeof error !== 'object') {
    return undefined;
  }

  const err = error as Record<string, unknown>;

  const isErrorMessage = typeof err.message === 'string';
  const isErrorDetail = typeof err.detail === 'string';
  const isErrorCode = typeof err.code === 'string';

  const errorMessage = isErrorMessage ? (err.message as string) : '';
  const errorDetail = isErrorDetail ? (err.detail as string) : '';

  if (err.data && typeof err.data === 'object') {
    const data = err.data as Record<string, unknown>;

    if ('code' in data || 'message' in data || 'detail' in data) {
      const code = typeof data.code === 'string' ? (data.code as string) : '';
      const message = (typeof data.message === 'string' && data.message) || errorMessage;
      const detail = (typeof data.detail === 'string' && data.detail) || errorDetail;

      return {
        code,
        message,
        details: data.details as ICustomError['details'],
        ...(detail ? { detail } : {}),
      };
    }
  }

  if (isErrorCode && (isErrorMessage || isErrorDetail)) {
    return error as ICustomError;
  }

  if (isErrorMessage || isErrorDetail) {
    return {
      code: '',
      message: errorMessage,
      ...(errorDetail ? { detail: errorDetail } : {}),
    };
  }

  return undefined;
}

export const getErrorMessage = (error?: unknown) => {
  const normalized = normalizeToCustomError(error);
  if (!normalized) {
    return UNKNOWN_ERROR;
  }

  const { code, message, details, detail } = normalized;

  const dictionaryErrorMessage = errorMapper[code] ?? errorMapper[message];

  if (typeof dictionaryErrorMessage === 'string') {
    return dictionaryErrorMessage;
  }

  const validationMessage = mapValidationMessage(normalized);
  if (validationMessage) {
    return validationMessage;
  }

  if (detail) {
    return errorMapper[detail] || detail || UNKNOWN_ERROR;
  }

  const reasonLower = details?.reason?.trim()?.toLowerCase();
  const messageLower = message?.trim()?.toLowerCase() || '';
  const shouldAppendDetails = Boolean(reasonLower && reasonLower !== messageLower);

  const errorDetails =
    details?.reason && shouldAppendDetails && (details.name ? `${details.name}: ${details.reason}` : details.reason);
  const errorMessage = [message, errorDetails].filter(Boolean).join('\n');

  return errorMessage || UNKNOWN_ERROR;
};

export const isPaidFeatureError = (error?: unknown) => {
  const normalized = normalizeToCustomError(error);
  if (!normalized) {
    return false;
  }

  return paidFeaturesErrors.includes(normalized.code);
};
